"""Feature ablation and fair HPO. This module never opens test images."""
import argparse
from datetime import datetime, timezone
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
from sklearn.metrics import f1_score, accuracy_score, classification_report

from .experiment import pipeline
from .features_v2 import CANDIDATES, extract

DEFAULT = {"kernel": "rbf", "C": 1.0, "gamma": "scale"}
SEEDS = (11, 29, 47, 71, 101)
TRIALS = 40


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def feature_code_hash():
    root = Path(__file__).parent
    return {name: digest(root / name) for name in ["features.py", "features_v2.py"]}


def get_development(manifest):
    df = pd.read_csv(manifest)
    if df.groupby("group").split.nunique().max() != 1:
        raise ValueError("Group leakage across development/test")
    dev = df[df.split == "development"].reset_index(drop=True)
    if sorted(dev.cv_fold.unique()) != [0,1,2] or dev.groupby("group").cv_fold.nunique().max() != 1:
        raise ValueError("Invalid frozen folds")
    if df.pixel_sha256.nunique() != len(df):
        raise ValueError("Duplicate pixels in manifest")
    return dev


def load_features(images, manifest, out, feature_id):
    dev = get_development(manifest)
    for row in dev.itertuples():
        if digest(Path(images) / row.path) != row.file_sha256:
            raise ValueError(f"Development image changed: {row.path}")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    cache = out / f"{feature_id}.npz"
    expected = {"manifest_sha256": digest(manifest), "feature_code_sha256": feature_code_hash(),
                "feature_id": feature_id, "scope": "development_only"}
    meta_path = cache.with_suffix(".json")
    if cache.exists() and meta_path.exists() and json.loads(meta_path.read_text()) == expected:
        with np.load(cache, allow_pickle=False) as data:
            if list(data["paths"]) != dev.path.tolist():
                raise ValueError("Feature cache row order mismatch")
            return data["X"].copy(), dev
    X = np.stack([extract(Path(images)/p, feature_id) for p in dev.path])
    np.savez_compressed(cache, X=X, paths=dev.path.to_numpy(dtype=str))
    dump(meta_path, expected)
    return X, dev


def evaluate_cv(X, dev, params):
    y, folds = dev.label.to_numpy(dtype=str), dev.cv_fold.to_numpy()
    pred = np.empty_like(y)
    scores, train_scores = [], []
    for fold in range(3):
        train, valid = folds != fold, folds == fold
        model = pipeline(params).fit(X[train], y[train])
        pred[valid] = model.predict(X[valid])
        scores.append(f1_score(y[valid], pred[valid], average="macro", zero_division=0))
        train_scores.append(f1_score(y[train], model.predict(X[train]), average="macro", zero_division=0))
    return {"mean_cv_macro_f1": float(np.mean(scores)), "std_cv_macro_f1": float(np.std(scores, ddof=1)),
            "fold_scores": scores, "train_fold_scores": train_scores,
            "oof_macro_f1": f1_score(y, pred, average="macro", zero_division=0),
            "oof_accuracy": accuracy_score(y, pred)}, pred


def ablate(images, manifest, root):
    root = Path(root)
    out = root / "ablation"
    if (out / "summary.json").exists():
        raise FileExistsError("Ablation already exists. Use a fresh output root for a new experiment.")
    out.mkdir(parents=True, exist_ok=True)
    dump(out / "protocol.json", {"created_utc": datetime.now(timezone.utc).isoformat(), "candidates": CANDIDATES,
         "default_params": DEFAULT, "metric": "mean_cv_macro_f1", "manifest_sha256": digest(manifest),
         "test_evaluated": False, "selection_rule": "max CV, then lowest dimension, then declaration order"})
    rows = []
    for feature_id, dimension in CANDIDATES.items():
        tick = time.perf_counter()
        X, dev = load_features(images, manifest, root / "cache", feature_id)
        feature_seconds = time.perf_counter()-tick
        tick = time.perf_counter()
        scores, pred = evaluate_cv(X, dev, DEFAULT)
        row = {"feature_id": feature_id, "dimension": dimension, **scores,
               "feature_seconds": feature_seconds, "cv_seconds": time.perf_counter()-tick}
        rows.append(row)
        pd.DataFrame({"path": dev.path, "label": dev.label, "fold": dev.cv_fold, "prediction": pred}).to_csv(out / f"oof_{feature_id}.csv", index=False)
        dump(out / "summary.json", rows)
        print("ABLATION", json.dumps(row), flush=True)
    best = max(rows, key=lambda x: (x["mean_cv_macro_f1"], -x["dimension"]))
    dump(out / "selection.json", {"selected_feature_id": best["feature_id"], "selection": best,
                                 "test_evaluated": False})
    pd.DataFrame([{k:v for k,v in r.items() if not isinstance(v,list)} for r in rows]).to_csv(out / "summary.csv", index=False)


def tune(images, manifest, root):
    root = Path(root)
    out = root / "hpo"
    if (out / "protocol.json").exists():
        raise FileExistsError("HPO already started; use a fresh output root for a new experiment.")
    out.mkdir(parents=True, exist_ok=True)
    feature_id = json.loads((root / "ablation/selection.json").read_text())["selected_feature_id"]
    X, dev = load_features(images, manifest, root / "cache", feature_id)
    protocol = {"created_utc": datetime.now(timezone.utc).isoformat(), "feature_id": feature_id,
                "manifest_sha256": digest(manifest), "feature_code_sha256": feature_code_hash(),
                "metric": "mean_cv_macro_f1", "seeds": list(SEEDS), "trials_per_seed_per_method": TRIALS,
                "tpe_startup_trials": 10, "n_jobs": 1, "pruning": False, "test_evaluated": False,
                "search_space": {"kernel": ["linear","rbf"], "C_log_range": [1e-3,1e3], "rbf_gamma_log_range": [1e-5,1e-1]},
                "baseline": DEFAULT, "versions": {"python": platform.python_version(), "sklearn": sklearn.__version__,
                                                     "optuna": optuna.__version__, "numpy": np.__version__}}
    dump(out / "protocol.json", protocol)
    records, summaries = [], []
    baseline, baseline_pred = evaluate_cv(X, dev, DEFAULT)
    dump(out / "baseline.json", baseline)
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    for method in ("random","tpe"):
        for seed in SEEDS:
            sampler = optuna.samplers.RandomSampler(seed=seed) if method=="random" else optuna.samplers.TPESampler(seed=seed,n_startup_trials=10)
            study = optuna.create_study(direction="maximize", sampler=sampler)
            started = time.perf_counter()
            def objective(trial):
                params = {"kernel":trial.suggest_categorical("kernel", ["linear","rbf"]),
                          "C":trial.suggest_float("C",1e-3,1e3,log=True)}
                if params["kernel"] == "rbf":
                    params["gamma"] = trial.suggest_float("gamma",1e-5,1e-1,log=True)
                tick = time.perf_counter()
                # Training scores are not needed on every trial.
                folds, y = dev.cv_fold.to_numpy(), dev.label.to_numpy(dtype=str)
                scores = []
                for fold in range(3):
                    a,b = folds != fold, folds == fold
                    m = pipeline(params).fit(X[a], y[a])
                    scores.append(f1_score(y[b],m.predict(X[b]),average="macro",zero_division=0))
                row = {"method":method,"seed":seed,"trial":trial.number+1,"params":params,
                       "fold_scores":scores,"cv_macro_f1":float(np.mean(scores)),
                       "seconds":time.perf_counter()-tick,"elapsed_seconds":time.perf_counter()-started}
                records.append(row)
                with (out / "trials.jsonl").open("a") as fh:
                    fh.write(json.dumps(row)+"\n")
                trial.set_user_attr("fold_scores",scores)
                return row["cv_macro_f1"]
            study.optimize(objective,n_trials=TRIALS,n_jobs=1)
            best = min(study.trials, key=lambda t: (-t.value,t.params["C"],t.number))
            row = {"method":method,"seed":seed,"best_cv_macro_f1":best.value,"params":best.params,
                   "best_trial":best.number+1,"fold_scores":best.user_attrs["fold_scores"],
                   "seconds":time.perf_counter()-started}
            summaries.append(row)
            dump(out / "summary.json", summaries)
            print("HPO",json.dumps(row),flush=True)
    pd.DataFrame([{**r,"params":json.dumps(r["params"]),"fold_scores":json.dumps(r["fold_scores"])} for r in records]).to_csv(out/"trials.csv",index=False)
    # Complete the streaming log atomically from the same finished records.
    tmp_log=out/"trials.complete.tmp"
    tmp_log.write_text("\n".join(json.dumps(r) for r in records)+"\n")
    tmp_log.replace(out/"trials.jsonl")
    method_scores = {"baseline":baseline["mean_cv_macro_f1"]}
    for method in ("random","tpe"):
        method_scores[method] = float(np.mean([r["best_cv_macro_f1"] for r in summaries if r["method"]==method]))
    selected_method = max(method_scores, key=method_scores.get)
    best_by_method = {"baseline": {"params":DEFAULT,"best_cv_macro_f1":baseline["mean_cv_macro_f1"]}}
    for method in ("random","tpe"):
        best_by_method[method] = min([r for r in summaries if r["method"]==method],
                                    key=lambda r:(-r["best_cv_macro_f1"],r["params"]["C"],r["best_trial"],r["seed"]))
    frozen = {"frozen_utc":datetime.now(timezone.utc).isoformat(),"manifest_sha256":digest(manifest),
              "feature_code_sha256":feature_code_hash(),"feature_id":feature_id,
              "selected_method":selected_method,"method_mean_best_cv":method_scores,
              "best_by_method":best_by_method,"test_evaluated_at_freeze":False,
              "selection_rule":"method by mean best-CV across seeds, configuration by best-CV within that method",
              "models_to_evaluate":["v1_default","baseline","random","tpe"]}
    final = root / "final"
    final.mkdir(parents=True,exist_ok=True)
    dump(final / "frozen_selection.json",frozen)
    for name in frozen["models_to_evaluate"]:
        fid = "v1" if name=="v1_default" else feature_id
        params = DEFAULT if name=="v1_default" else best_by_method[name]["params"]
        Xm, dm = load_features(images,manifest,root/"cache",fid)
        tick=time.perf_counter();model=pipeline(params).fit(Xm,dm.label)
        fit_seconds=time.perf_counter()-tick
        train_pred=model.predict(Xm)
        report = {"train_macro_f1":f1_score(dm.label,train_pred,average="macro",zero_division=0),
                  "train_accuracy":accuracy_score(dm.label,train_pred),"fit_seconds":fit_seconds,
                  "support_vectors":int(model[-1].n_support_.sum())}
        # OOF outputs are diagnostics, not unbiased final estimates after model selection.
        cv,pred=evaluate_cv(Xm,dm,params)
        report["cv"] = cv
        dump(final/f"{name}_train.json",report)
        pd.DataFrame({"path":dm.path,"label":dm.label,"cv_fold":dm.cv_fold,"prediction":pred}).to_csv(final/f"{name}_oof.csv",index=False)
        joblib.dump({"model":model,"feature_id":fid,"params":params,"feature_code_sha256":feature_code_hash(),
                     "manifest_sha256":digest(manifest),"frozen_selection_sha256":digest(final/"frozen_selection.json")},final/f"{name}.joblib",compress=3)
    print("FROZEN",json.dumps(frozen),flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("stage",choices=["ablate","tune"])
    p.add_argument("--images",default="data/raw")
    p.add_argument("--manifest",default="data/audit/manifest.csv")
    p.add_argument("--out",default="results/phase2")
    a=p.parse_args()
    (ablate if a.stage=="ablate" else tune)(a.images,a.manifest,a.out)
