"""Pilot HPO on development data only. The test set is never scored here."""
import argparse
import hashlib
import json
import platform
import time
from pathlib import Path

import joblib
import numpy as np
import optuna
import pandas as pd
import sklearn
from sklearn.metrics import f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from .features import extract, FEATURE_SPEC


def pipeline(params):
    return make_pipeline(StandardScaler(), SVC(**params, cache_size=512))


def cv_scores(X, y, folds, params):
    scores = []
    for fold in sorted(set(folds)):
        train, valid = folds != fold, folds == fold
        model = pipeline(params)
        model.fit(X[train], y[train])
        scores.append(f1_score(y[valid], model.predict(X[valid]), average="macro", zero_division=0))
    return scores


def run(images, manifest, out, trials=20, seeds=(11, 29, 47)):
    if trials <= 10:
        raise ValueError("Use >10 trials so TPE runs beyond its ten random startup trials.")
    out, images, manifest = Path(out), Path(images), Path(manifest)
    if (out / "protocol.json").exists():
        raise FileExistsError("Run output already exists; use a new output folder.")
    out.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(manifest)
    if df.groupby("group").split.nunique().max() != 1:
        raise ValueError("Group leakage between development and test")
    dev = df[df.split == "development"].reset_index(drop=True)
    if dev.groupby("group").cv_fold.nunique().max() != 1:
        raise ValueError("Group leakage across folds")
    y, folds = dev.label.to_numpy(), dev.cv_fold.to_numpy()
    if sorted(set(folds)) != [0, 1, 2]:
        raise ValueError("Expected three frozen folds")
    protocol = {"status": "pilot; development CV only", "trials_per_method_per_seed": trials,
                "sampler_seeds": list(seeds), "split_seed": 2026, "cv_seed": 2027,
                "metric": "macro_f1", "cv_folds": 3, "test_evaluated": False,
                "n_development": len(dev), "n_test_held_out": int((df.split == "test").sum()),
                "features": FEATURE_SPEC,
                "search_space": {"kernel": ["linear", "rbf"], "C": {"low": 1e-3, "high": 1e3, "log": True},
                                 "gamma_for_rbf_only": {"low": 1e-5, "high": 1e-1, "log": True}},
                "baseline": {"kernel": "rbf", "C": 1.0, "gamma": "scale"},
                "tpe_startup_trials": 10, "pruning": False, "n_jobs": 1,
                "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
                "versions": {"python": platform.python_version(), "sklearn": sklearn.__version__,
                             "numpy": np.__version__, "optuna": optuna.__version__},
                "fit_budget_cv": 3 + 2 * len(seeds) * trials * 3,
                "selection_rule": "largest development CV mean; ties baseline, random, then TPE in recorded order"}
    (out / "protocol.json").write_text(json.dumps(protocol, indent=2))
    t0 = time.perf_counter()
    X = np.stack([extract(images / p) for p in dev.path])
    feature_seconds = time.perf_counter() - t0
    np.savez_compressed(out / "development_features.npz", X=X, y=y, folds=folds, paths=dev.path.to_numpy(dtype=str))
    print(f"Development features: {X.shape}; test images not loaded", flush=True)
    t0 = time.perf_counter()
    base_scores = cv_scores(X, y, folds, protocol["baseline"])
    baseline = {"method": "baseline", "seed": None, "best_cv_macro_f1": float(np.mean(base_scores)),
                "fold_scores": base_scores, "params": protocol["baseline"],
                "seconds": time.perf_counter() - t0}
    print("BASELINE", baseline, flush=True)
    summaries, trial_rows = [baseline], []
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    for method in ("random", "tpe"):
        for seed in seeds:
            sampler = optuna.samplers.RandomSampler(seed=seed) if method == "random" else optuna.samplers.TPESampler(seed=seed, n_startup_trials=10)
            study = optuna.create_study(direction="maximize", sampler=sampler)
            started = time.perf_counter()

            def objective(trial):
                params = {"kernel": trial.suggest_categorical("kernel", ["linear", "rbf"]),
                          "C": trial.suggest_float("C", 1e-3, 1e3, log=True)}
                if params["kernel"] == "rbf":
                    params["gamma"] = trial.suggest_float("gamma", 1e-5, 1e-1, log=True)
                tick = time.perf_counter()
                scores = cv_scores(X, y, folds, params)
                value = float(np.mean(scores))
                row = {"method": method, "seed": seed, "trial": trial.number + 1,
                       "cv_macro_f1": value, "fold_scores": scores,
                       "params": params, "seconds": time.perf_counter() - tick,
                       "elapsed_seconds": time.perf_counter() - started}
                trial_rows.append(row)
                with (out / "trials.jsonl").open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(row) + "\n")
                trial.set_user_attr("fold_scores", scores)
                return value

            study.optimize(objective, n_trials=trials, n_jobs=1)
            best = study.best_trial
            summary = {"method": method, "seed": seed, "best_cv_macro_f1": best.value,
                       "fold_scores": best.user_attrs["fold_scores"], "params": best.params,
                       "best_trial": best.number + 1, "seconds": time.perf_counter() - started}
            summaries.append(summary)
            (out / "summary.json").write_text(json.dumps(summaries, indent=2))
            print("DONE", summary, flush=True)
    winner = max(summaries, key=lambda r: r["best_cv_macro_f1"])
    model = pipeline(winner["params"]).fit(X, y)
    joblib.dump({"model": model, "feature_spec": FEATURE_SPEC,
                 "manifest_sha256": protocol["manifest_sha256"], "selection": winner}, out / "selected_model.joblib")
    (out / "selection.json").write_text(json.dumps({"winner": winner, "test_evaluated": False,
            "feature_seconds": feature_seconds, "total_cv_fits": protocol["fit_budget_cv"],
            "refit_count": 1}, indent=2))
    pd.DataFrame([{**r, "params": json.dumps(r["params"]), "fold_scores": json.dumps(r["fold_scores"])} for r in trial_rows]).to_csv(out / "trials.csv", index=False)
    return summaries


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--images", default="data/raw")
    p.add_argument("--manifest", default="data/audit/manifest.csv")
    p.add_argument("--out", default="results/pilot")
    p.add_argument("--trials", type=int, default=20)
    a = p.parse_args()
    run(a.images, a.manifest, a.out, a.trials)
