"""Figures from actual audit and pilot logs; no test-set evaluation."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from .features import load_rgb


def make_plots():
    out = Path("results/figures")
    out.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_csv("data/audit/manifest.csv")
    source = pd.read_csv("data/audit/source_manifest.csv")
    counts = pd.concat([source.label.value_counts().rename("Source files"),
                        manifest.label.value_counts().rename("Unique pixels")], axis=1).sort_index()
    ax = counts.plot.barh(figsize=(9, 4.4), color=["#bbd4c7", "#16644b"])
    ax.set(xlabel="Image count", ylabel="", title="Data audit: 1,217 files / 972 unique images")
    plt.tight_layout(); plt.savefig(out / "data_audit.png", dpi=170); plt.close()
    dev = manifest[manifest.split == "development"]
    fig, axes = plt.subplots(2, 6, figsize=(12, 4.8))
    for col, label in enumerate(sorted(dev.label.unique())):
        for row, path in enumerate(dev.loc[dev.label == label, "path"].iloc[:2]):
            axes[row, col].imshow(load_rgb(Path("data/raw") / path))
            axes[row, col].axis("off")
            if row == 0:
                axes[row, col].set_title(label.replace(" ", "\n"), fontsize=10)
    fig.suptitle("Development images only - source: BDMediLeaves / CC BY 4.0")
    fig.tight_layout(); fig.savefig(out / "development_samples.png", dpi=150); plt.close(fig)
    trials = pd.read_csv("results/pilot/trials.csv")
    summary = json.loads(Path("results/pilot/summary.json").read_text())
    baseline = summary[0]["best_cv_macro_f1"]
    fig, ax = plt.subplots(figsize=(8.3, 4.3))
    for method, color in [("random", "#486fbd"), ("tpe", "#17825d")]:
        curves = []
        for _, group in trials[trials.method == method].groupby("seed"):
            curves.append(group.sort_values("trial").cv_macro_f1.cummax().to_numpy())
        a = np.stack(curves); x = np.arange(1, a.shape[1]+1)
        ax.plot(x, a.mean(axis=0), label=method.upper(), color=color)
        ax.fill_between(x, a.min(axis=0), a.max(axis=0), alpha=.13, color=color)
    ax.axhline(baseline, color="#9d5b36", ls="--", label="Default SVM")
    ax.set(xlabel="Trials per seed", ylabel="Best CV Macro-F1", title="Pilot: mean and range over 3 sampler seeds")
    ax.legend(); ax.grid(alpha=.2); fig.tight_layout(); fig.savefig(out / "convergence.png", dpi=170); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8.3, 4.1))
    for i, method in enumerate(["random", "tpe"]):
        values = [s["best_cv_macro_f1"] for s in summary if s["method"] == method]
        ax.scatter([i-.07, i, i+.07], values, color=["#486fbd", "#17825d"][i], s=65)
        ax.plot([i-.23, i+.23], [np.mean(values)]*2, color="black", lw=2)
    ax.axhline(baseline, ls="--", color="#9d5b36", label="Default SVM")
    ax.set(xticks=[0,1], xticklabels=["Random Search", "TPE"], ylabel="Best CV Macro-F1", title="Seed variability - not independent test performance")
    ax.legend(); ax.grid(axis="y", alpha=.2);fig.tight_layout();fig.savefig(out / "seed_variability.png", dpi=170);plt.close(fig)
    pairs = pd.read_csv("data/audit/near_duplicate_candidates.csv")
    if len(pairs):
        fig, axes = plt.subplots(min(6, len(pairs)), 2, figsize=(7, 3.3*min(6,len(pairs))), squeeze=False)
        for i, record in enumerate(pairs.head(6).to_dict("records")):
            for j, key in enumerate(["path_a", "path_b"]):
                axes[i,j].imshow(load_rgb(Path("data/raw") / record[key]));axes[i,j].axis("off")
                axes[i,j].set_title(f"Candidate {i+1}; pHash distance={record['phash_distance']}")
        fig.tight_layout();fig.savefig(out / "duplicate_review.png", dpi=150);plt.close(fig)


if __name__ == "__main__":
    make_plots()
