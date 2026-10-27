"""Checks for leakage, saved outputs, and reproducible feature/model use."""
import hashlib
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from src.experiment import cv_scores
from src.features import extract

ROOT = Path(__file__).resolve().parents[1]


class ResearchChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = pd.read_csv(ROOT / "data/audit/manifest.csv")
        cls.protocol = json.loads((ROOT / "results/pilot/protocol.json").read_text())

    def test_no_image_or_group_leakage(self):
        df = self.manifest
        self.assertEqual(df.pixel_sha256.nunique(), len(df))
        self.assertEqual(df.groupby("group").split.nunique().max(), 1)
        dev = df[df.split == "development"]
        self.assertEqual(dev.groupby("group").cv_fold.nunique().max(), 1)
        for fold in range(3):
            self.assertEqual(set(dev[dev.cv_fold == fold].label), set(df.label))

    def test_cache_excludes_test_images(self):
        data = np.load(ROOT / "results/pilot/development_features.npz", allow_pickle=True)
        self.assertEqual(set(data["paths"]), set(self.manifest[self.manifest.split == "development"].path))
        self.assertFalse(set(data["paths"]) & set(self.manifest[self.manifest.split == "test"].path))
        self.assertTrue(np.isfinite(data["X"]).all())

    def test_scaler_fits_only_training_rows_in_cv(self):
        X = np.arange(180, dtype=float).reshape(30, 6)
        y = np.tile(["a", "b"], 15)
        folds = np.repeat([0, 1, 2], 10)
        seen = []
        original = StandardScaler.fit
        def observed(obj, values, *args, **kwargs):
            seen.append(values.copy())
            return original(obj, values, *args, **kwargs)
        with patch.object(StandardScaler, "fit", observed):
            cv_scores(X, y, folds, {"kernel": "linear", "C": 1.0})
        self.assertEqual(len(seen), 3)
        for fold, values in enumerate(seen):
            np.testing.assert_array_equal(values, X[folds != fold])

    def test_manifest_matches_model_and_protocol(self):
        digest = hashlib.sha256((ROOT / "data/audit/manifest.csv").read_bytes()).hexdigest()
        bundle = joblib.load(ROOT / "results/pilot/selected_model.joblib")
        self.assertEqual(digest, self.protocol["manifest_sha256"])
        self.assertEqual(digest, bundle["manifest_sha256"])
        self.assertFalse(self.protocol["test_evaluated"])

    def test_equal_budgets_and_summary_matches_logs(self):
        trials = pd.read_csv(ROOT / "results/pilot/trials.csv")
        summary = json.loads((ROOT / "results/pilot/summary.json").read_text())
        sizes = trials.groupby(["method", "seed"]).size()
        self.assertEqual(len(sizes), 6)
        self.assertTrue((sizes == self.protocol["trials_per_method_per_seed"]).all())
        self.assertTrue(trials.cv_macro_f1.between(0, 1).all())
        for row in summary[1:]:
            subset = trials[(trials.method == row["method"]) & (trials.seed == row["seed"])]
            self.assertAlmostEqual(row["best_cv_macro_f1"], subset.cv_macro_f1.max(), places=12)

    def test_image_to_saved_model_roundtrip(self):
        data = np.load(ROOT / "results/pilot/development_features.npz", allow_pickle=True)
        image_path = ROOT / "data/raw" / str(data["paths"][0])
        if not image_path.exists():
            self.skipTest("Download source images to run the image roundtrip check")
        fresh = extract(image_path)
        np.testing.assert_allclose(fresh, data["X"][0], rtol=0, atol=0)
        model = joblib.load(ROOT / "results/pilot/selected_model.joblib")["model"]
        self.assertEqual(model.predict(fresh[None])[0], model.predict(data["X"][:1])[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
