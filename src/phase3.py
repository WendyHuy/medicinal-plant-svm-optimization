"""Four-parameter SVM search and nested grouped CV on development only."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import time

import joblib
import numpy as np
import optuna
import pandas as pd
import sklearn
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedGroupKFold

from .develop import digest, dump, feature_code_hash, load_features
from .evaluate import paired_bootstrap
from .experiment import pipeline

SEEDS = (11, 29, 47, 71, 101)
SEARCHES = ("random3", "random4", "tpe4")
DEFAULT = {"kernel": "rbf", "C": 1.0, "gamma": "scale", "class_weight": None}


def utc():
    return datetime.now(timezone.utc).isoformat()


def grouped_folds(y, groups, n_splits, seed):
    folds = np.full(len(y), -1, dtype=int)
    cv = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    for fold, (train, valid) in enumerate(cv.split(np.zeros(len(y)), y, groups)):
        if set(groups[train]) & set(groups[valid]):
            raise ValueError("Group leakage")
        if set(y[train]) != set(y) or set(y[valid]) != set(y):
            raise ValueError("Missing classes in fold")
        folds[valid] = fold
    if (folds < 0).any():
        raise ValueError("Unassigned row")
    return folds


def score_cv(X, y, folds, params):
    values = []
    for fold in sorted(np.unique(folds)):
        a, b = folds != fold, folds == fold
        model = pipeline(params).fit(X[a], y[a])
        values.append(float(f1_score(y[b], model.predict(X[b]), average="macro", zero_division=0)))
    return values


def search(X, y, folds, name, seed, trials, scope, journal):
    sampler = (optuna.samplers.TPESampler(seed=seed, n_startup_trials=10)
               if name == "tpe4" else optuna.samplers.RandomSampler(seed=seed))
    study = optuna.create_study(direction="maximize", sampler=sampler)
    records = []
    start = time.perf_counter()

    def objective(trial):
        params = {"kernel": trial.suggest_categorical("kernel", ["linear", "rbf"]),
                  "C": trial.suggest_float("C", 1e-3, 1e3, log=True)}
        if params["kernel"] == "rbf":
            params["gamma"] = trial.suggest_float("gamma", 1e-5, 1e-1, log=True)
        params["class_weight"] = (trial.suggest_categorical("class_weight", [None, "balanced"])
                                  if name != "random3" else None)
        tick = time.perf_counter()
        scores = score_cv(X, y, folds, params)
        row = {"scope": scope, "search": name, "seed": seed, "trial": trial.number + 1,
               "params": params, "inner_fold_scores": scores,
               "mean_inner_macro_f1": float(np.mean(scores)),
               "seconds": time.perf_counter() - tick,
               "elapsed_seconds": time.perf_counter() - start}
        records.append(row)
        with journal.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row) + "\n")
        return row["mean_inner_macro_f1"]

    study.optimize(objective, n_trials=trials, n_jobs=1)
    best = min(records, key=lambda r: (-r["mean_inner_macro_f1"], r["params"]["C"], r["trial"]))
    return {"scope": scope, "search": name, "seed": seed,
            "params": best["params"], "best_trial": best["trial"],
            "best_inner_macro_f1": best["mean_inner_macro_f1"],
            "inner_fold_scores": best["inner_fold_scores"],
            "search_seconds": time.perf_counter() - start}, records


def select_four(rows, baseline_score):
    means = {"baseline": baseline_score}
    for name in ("random4", "tpe4"):
        means[name] = float(np.mean([r["best_inner_macro_f1"] for r in rows if r["search"] == name]))
    method = max(means, key=means.get)  # insertion order is the declared tie rule
    if method == "baseline":
        return {"search": method, "params": DEFAULT, "method_mean_best_inner": means}
    best = min([r for r in rows if r["search"] == method],
               key=lambda r: (-r["best_inner_macro_f1"], r["params"]["C"], r["best_trial"], r["seed"]))
    return {**best, "method_mean_best_inner": means}


def metrics(y, pred, labels):
    return {"macro_f1": float(f1_score(y, pred, labels=labels, average="macro", zero_division=0)),
            "accuracy": float(accuracy_score(y, pred)),
            "correct": int(np.sum(y == pred)), "n": len(y),
            "classification_report": classification_report(y, pred, labels=labels, output_dict=True, zero_division=0),
            "confusion_matrix": confusion_matrix(y, pred, labels=labels).tolist(), "labels": labels}


def run(images="data/raw", manifest="data/audit/manifest.csv", out="results/phase3", trials=40):
    if trials != 40:
        raise ValueError("Release protocol requires exactly 40 trials; change the protocol for other budgets")
    out, manifest = Path(out), Path(manifest)
    if (out / "protocol.json").exists():
        raise FileExistsError("Run already started. Do not overwrite recorded experiments.")
    out.mkdir(parents=True, exist_ok=True)
    protocol = {"created_utc": utc(), "feature_id": "texture128", "scope": "development_only",
        "test_used": False, "historical_test_already_open": True,
        "manifest_sha256": digest(manifest), "feature_code_sha256": feature_code_hash(),
        "runner_sha256": digest(__file__), "written_protocol_sha256": digest("docs/PHASE3_PROTOCOL.md"),
        "seeds": list(SEEDS), "searches": list(SEARCHES), "trials_per_search_seed_scope": trials,
        "outer_folds": 5, "outer_seed": 2031, "inner_folds": 3, "inner_seed_base": 2032,
        "nested_trials": 3000, "full_development_trials": 600, "total_hpo_cv_fits": 10800,
        "four_parameter_space": {"kernel": ["linear", "rbf"], "C_log": [1e-3, 1e3],
            "gamma_log_rbf_only": [1e-5, 1e-1], "class_weight": [None, "balanced"]},
        "baseline": DEFAULT, "tpe_startup_trials": 10, "pruning": False, "n_jobs": 1,
        "selection": "baseline/random4/tpe4 by mean best-inner CV across seeds; configuration by inner CV only",
        "limitation": "Fixed feature family previously selected on the same development data; groups are duplicate heuristics, not verified plant IDs. Not an external validation.",
        "versions": {"python": platform.python_version(), "numpy": np.__version__,
                     "sklearn": sklearn.__version__, "optuna": optuna.__version__}}
    dump(out / "protocol.json", protocol)
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    tick = time.perf_counter()
    X, dev = load_features(images, manifest, out / "cache", "texture128")
    feature_seconds = time.perf_counter() - tick
    y = dev.label.to_numpy(dtype=str)
    groups = dev.group.to_numpy(dtype=str)
    labels = sorted(np.unique(y).tolist())
    outer = grouped_folds(y, groups, 5, 2031)
    outer_df = dev[["path", "label", "group"]].copy()
    outer_df["outer_fold"] = outer
    outer_df.to_csv(out / "outer_assignments.csv", index=False)
    predictions = {"baseline": np.empty_like(y), "selected4": np.empty_like(y)}
    for name in SEARCHES:
        for seed in SEEDS:
            predictions[f"{name}_seed{seed}"] = np.empty_like(y)
    all_summaries, records, selection_rows, fit_rows = [], [], [], []
    journal = out / "trials.jsonl"
    started = time.perf_counter()
    for fold in range(5):
        a, b = outer != fold, outer == fold
        Xt, yt = X[a], y[a]
        inner = grouped_folds(yt, groups[a], 3, 2032 + fold)
        inner_df = dev.loc[a, ["path", "label", "group"]].copy()
        inner_df["inner_fold"] = inner
        inner_df.to_csv(out / f"inner_assignments_outer{fold}.csv", index=False)
        base_scores = score_cv(Xt, yt, inner, DEFAULT)
        model = pipeline(DEFAULT).fit(Xt, yt)
        predictions["baseline"][b] = model.predict(X[b])
        rows = []
        for name in SEARCHES:
            for seed in SEEDS:
                summary, log = search(Xt, yt, inner, name, seed, trials, f"outer_{fold}", journal)
                rows.append(summary); all_summaries.append(summary); records.extend(log)
                tick = time.perf_counter()
                model = pipeline(summary["params"]).fit(Xt, yt)
                predictions[f"{name}_seed{seed}"][b] = model.predict(X[b])
                fit_rows.append({"scope": f"outer_{fold}", "search": name, "seed": seed,
                                 "refit_seconds": time.perf_counter() - tick})
                dump(out / "search_summaries.json", all_summaries)
                print("SEARCH", json.dumps(summary), flush=True)
        choice = select_four(rows, float(np.mean(base_scores)))
        model = pipeline(choice["params"]).fit(Xt, yt)
        predictions["selected4"][b] = model.predict(X[b])
        selection_rows.append({"outer_fold": fold, "train_n": int(a.sum()), "validation_n": int(b.sum()),
                               "baseline_inner_scores": base_scores, "choice": choice})
        dump(out / "outer_selections.json", selection_rows)
        print("OUTER_COMPLETE", fold, choice["search"], flush=True)

    for name, pred in predictions.items():
        outer_df[name] = pred
    outer_df.to_csv(out / "nested_predictions.csv", index=False)
    values = {name: metrics(y, pred, labels) for name, pred in predictions.items()}
    aggregate = {}
    for name in SEARCHES:
        scores = [values[f"{name}_seed{s}"]["macro_f1"] for s in SEEDS]
        aggregate[name] = {"mean_oof_macro_f1": float(np.mean(scores)),
                           "sd_between_seeds": float(np.std(scores, ddof=1)), "seed_scores": scores}
    bootstrap = paired_bootstrap(y, {k: predictions[k] for k in ("baseline", "selected4")},
                                 groups, "selected4", iterations=2000, seed=2033)
    bootstrap["limitation"] = "Conditional OOF diagnostic; outer-fold training sets overlap; feature family was previously selected on this data and groups are heuristic. Not an external-validation confidence interval."
    evaluation = {"scope": "nested_grouped_cv_on_previous_development", "n": len(y),
        "metrics": values, "search_aggregate": aggregate, "bootstrap_diagnostic": bootstrap,
        "delta_selected4_minus_baseline": values["selected4"]["macro_f1"] - values["baseline"]["macro_f1"],
        "n_outer_folds": 5, "new_test_evaluation": False}
    dump(out / "nested_evaluation.json", evaluation)

    # Deployment selection is independent of the outer-validation scores.
    full_rows = []
    full_folds = dev.cv_fold.to_numpy()
    baseline_full = score_cv(X, y, full_folds, DEFAULT)
    for name in SEARCHES:
        for seed in SEEDS:
            summary, log = search(X, y, full_folds, name, seed, trials, "full_development", journal)
            full_rows.append(summary); all_summaries.append(summary); records.extend(log)
            dump(out / "search_summaries.json", all_summaries)
            print("SEARCH", json.dumps(summary), flush=True)
    choice = select_four(full_rows, float(np.mean(baseline_full)))
    frozen = {"frozen_utc": utc(), "params": choice["params"], "selection": choice,
              "training_images": len(y), "feature_id": "texture128", "n_features": X.shape[1],
              "protocol_sha256": digest(out / "protocol.json"), "manifest_sha256": digest(manifest),
              "feature_code_sha256": feature_code_hash(), "test_used_for_selection": False,
              "external_validation_completed": False, "baseline_full_fold_scores": baseline_full}
    dump(out / "frozen_selection.json", frozen)
    tick = time.perf_counter()
    model = pipeline(choice["params"]).fit(X, y)
    fit_seconds = time.perf_counter() - tick
    bundle = {"model": model, "feature_id": "texture128", "params": choice["params"],
              "feature_code_sha256": feature_code_hash(), "manifest_sha256": digest(manifest),
              "frozen_selection_sha256": digest(out / "frozen_selection.json"),
              "release": "0.3.0", "scope": "six_leaf_classes_only"}
    model_path = Path("models/phase3_optimized.joblib")
    joblib.dump(bundle, model_path, compress=3)
    training = metrics(y, model.predict(X), labels)
    metadata = {**{k: v for k, v in frozen.items() if k != "selection"},
                "selected_search": choice["search"], "model_file": model_path.name,
                "model_sha256": digest(model_path), "model_bytes": model_path.stat().st_size,
                "fit_seconds": fit_seconds, "training_macro_f1": training["macro_f1"],
                "supported_labels": labels, "unknown_species_detection": False,
                "score_is_probability": False, "nested_oof_macro_f1_selected_policy": values["selected4"]["macro_f1"]}
    dump("models/phase3_metadata.json", metadata)
    dump(out / "training_metrics.json", training)
    pd.DataFrame(fit_rows).to_csv(out / "refit_timings.csv", index=False)
    temporary = out / "trials.complete.tmp"
    temporary.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
    temporary.replace(journal)
    dump(out / "completed.json", {"completed_utc": utc(), "trial_count": len(records),
        "hpo_cv_fit_count": len(records) * 3, "baseline_cv_fit_count": 18,
        "outer_refit_count": 85, "final_refit_count": 1,
        "feature_seconds": feature_seconds, "search_and_evaluation_seconds": time.perf_counter() - started,
        "new_holdout_evaluation": False, "model_sha256": digest(model_path),
        "runner_sha256": digest(__file__)})
    print("COMPLETE", json.dumps({"nested": {k: values[k]["macro_f1"] for k in ["baseline", "selected4"]},
                                  "final_params": choice["params"]}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--images", default="data/raw")
    parser.add_argument("--manifest", default="data/audit/manifest.csv")
    parser.add_argument("--out", default="results/phase3")
    args = parser.parse_args()
    run(args.images, args.manifest, args.out)
