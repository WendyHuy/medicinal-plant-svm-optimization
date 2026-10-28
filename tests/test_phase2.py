import json
import tempfile
import unittest
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.metrics import f1_score, accuracy_score
from src.features_v2 import extract, CANDIDATES
from src.features import extract as extract_v1
from src.develop import digest, feature_code_hash
from src.evaluate import f1_from_ids, paired_bootstrap, evaluate

ROOT=Path(__file__).resolve().parents[1]


class DescriptorAndStatisticsChecks(unittest.TestCase):
    def test_descriptors_handle_constant_and_color_images(self):
        with tempfile.TemporaryDirectory() as directory:
            for kind in ["constant","color"]:
                a=np.full((48,80,3),127,dtype=np.uint8)
                if kind=="color":a[:24,:,1]=250
                path=Path(directory)/f"{kind}.png";Image.fromarray(a).save(path)
                for fid,dimension in CANDIDATES.items():
                    features=extract(path,fid)
                    self.assertEqual(features.shape,(dimension,));self.assertTrue(np.isfinite(features).all())
                np.testing.assert_array_equal(extract(path,"v1"),extract_v1(path))
                full=extract(path,"enhanced128")
                np.testing.assert_array_equal(full[1764:],extract(path,"texture128"))

    def test_bootstrap_metric_matches_sklearn_with_missing_predictions(self):
        y=np.array([0,0,1,1,2,2]);pred=np.array([0,0,0,0,0,0])
        self.assertAlmostEqual(f1_from_ids(y,pred,3),f1_score(y,pred,average="macro"))

    def test_paired_bootstrap_identical_models_has_zero_difference(self):
        y=np.array(["a","a","b","b","b","a"])
        pred=np.array(["a","b","b","a","b","a"])
        groups=np.array(["g0","g1","g2","g3","g4","g5"])
        result=paired_bootstrap(y,{"baseline":pred,"tpe":pred.copy()},groups,"tpe",iterations=100)
        self.assertEqual(result["selected_minus_baseline_macro_f1_ci95"],[0.,0.])

    def test_paired_bootstrap_respects_groups_with_two_members(self):
        y=np.array(["a","a","a","b","b","b"])
        opposite=np.array(["b","b","b","a","a","a"])
        groups=np.array(["a1","a1","a2","b1","b2","b3"])
        result=paired_bootstrap(y,{"baseline":opposite,"tpe":y},groups,"tpe",iterations=100)
        np.testing.assert_allclose(result["selected_minus_baseline_macro_f1_ci95"],[1.,1.])


class Phase2ArtifactsChecks(unittest.TestCase):
    def test_deployed_models_match_frozen_choice_and_checksums(self):
        metadata=json.loads((ROOT/'models/metadata.json').read_text())
        frozen_path=ROOT/'results/phase2/final/frozen_selection.json'
        frozen=json.loads(frozen_path.read_text())
        self.assertEqual(metadata['selected_method'],frozen['selected_method'])
        for filename,info in metadata['files'].items():
            path=ROOT/'models'/filename
            self.assertEqual(digest(path),info['sha256'])
            self.assertEqual(path.stat().st_size,info['bytes'])
            bundle=joblib.load(path)
            self.assertEqual(bundle['feature_code_sha256'],feature_code_hash())
            self.assertEqual(bundle['frozen_selection_sha256'],digest(frozen_path))
            self.assertEqual(bundle['manifest_sha256'],digest(ROOT/'data/audit/manifest.csv'))
            self.assertEqual(bundle['model'][0].n_samples_seen_,778)
            method='baseline' if filename=='baseline.joblib' else frozen['selected_method']
            self.assertEqual(bundle['params'],frozen['best_by_method'][method]['params'])

    def test_ablation_and_caches_are_development_only(self):
        root=ROOT/"results/phase2"
        if not (root/"ablation/selection.json").exists():self.skipTest("Ablation not run")
        df=pd.read_csv(ROOT/"data/audit/manifest.csv");expected=df[df.split=="development"].path.tolist()
        for fid in CANDIDATES:
            p=root/f"cache/{fid}.npz"
            if not p.exists():continue
            with np.load(p,allow_pickle=False) as data:
                self.assertEqual(list(data["paths"]),expected)
                self.assertTrue(np.isfinite(data["X"]).all())

    def test_frozen_models_have_same_training_rows_and_code(self):
        root=ROOT/"results/phase2/final";frozen_path=root/"frozen_selection.json"
        if not frozen_path.exists():self.skipTest("Models not frozen")
        frozen=json.loads(frozen_path.read_text())
        self.assertFalse(frozen["test_evaluated_at_freeze"])
        self.assertEqual(frozen["feature_code_sha256"],feature_code_hash())
        for name in frozen["models_to_evaluate"]:
            p=root/f"{name}.joblib"
            if not p.exists():self.skipTest("Download or retrain model artifacts")
            b=joblib.load(p)
            self.assertEqual(b["frozen_selection_sha256"],digest(frozen_path))
            self.assertEqual(b["model"][0].n_samples_seen_,778)

    def test_hpo_budget_and_logged_scores(self):
        root=ROOT/"results/phase2/hpo"
        if not (root/"trials.csv").exists():self.skipTest("HPO not completed")
        df=pd.read_csv(root/"trials.csv")
        self.assertEqual(len(df),400)
        self.assertTrue((df.groupby(["method","seed"]).size()==40).all())
        for row in df.itertuples():
            self.assertAlmostEqual(row.cv_macro_f1,np.mean(json.loads(row.fold_scores)),places=12)
        for row in json.loads((root/"summary.json").read_text()):
            subset=df[(df.method==row["method"])&(df.seed==row["seed"])]
            self.assertAlmostEqual(row["best_cv_macro_f1"],subset.cv_macro_f1.max(),places=12)

    def test_final_metrics_recompute_from_predictions_and_locked_choice(self):
        root=ROOT/"results/phase2";out=root/"evaluation"
        if not (out/"completed.json").exists():self.skipTest("Holdout not evaluated")
        df=pd.read_csv(out/"predictions.csv");metrics=json.loads((out/"metrics.json").read_text())
        frozen=json.loads((root/"final/frozen_selection.json").read_text())
        comparison=json.loads((out/"comparison.json").read_text())
        self.assertEqual(len(df),194)
        self.assertEqual(comparison["selected_before_test"],frozen["selected_method"])
        for name,value in metrics.items():
            self.assertAlmostEqual(value["test_macro_f1"],f1_score(df.label,df[name],average="macro"),places=12)
            self.assertAlmostEqual(value["test_accuracy"],accuracy_score(df.label,df[name]),places=12)
        with self.assertRaises(FileExistsError):
            evaluate(ROOT/"data/raw",ROOT/"data/audit/manifest.csv",root)


if __name__=="__main__":unittest.main(verbosity=2)
