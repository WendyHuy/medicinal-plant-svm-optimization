"""Audit source images, group duplicate candidates, then freeze grouped splits."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from scipy.fft import dctn
from sklearn.model_selection import StratifiedGroupKFold
from .features import load_rgb


def phash(im):
    a = np.asarray(im.convert("L").resize((32, 32), Image.Resampling.LANCZOS), dtype=float)
    low = dctn(a, norm="ortho")[:8, :8].ravel()[1:]
    return sum(int(x) << i for i, x in enumerate(low > np.median(low)))


def audit(root, out):
    root, out = Path(root).resolve(), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if (out / "manifest.csv").exists():
        raise FileExistsError("A frozen manifest already exists. Use a NEW output directory.")
    paths = sorted(p for p in root.rglob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"})
    if not paths:
        raise ValueError("No images found in the original-image directory.")
    records, hashes, errors = [], [], []
    for p in paths:
        relative = p.relative_to(root)
        try:
            im = load_rgb(p)
            parts = relative.parts
            # Supports class/image and class/train/image, with optional wrappers.
            is_split = len(parts) >= 3 and parts[-2].strip().lower() in {"train", "test", "validation", "val"}
            label = parts[-3] if is_split else parts[-2]
            h = hashlib.sha256(str(im.size).encode() + im.tobytes()).hexdigest()
            records.append({"path": relative.as_posix(), "label": label,
                            "source_split": parts[-2].strip().lower() if is_split else "unspecified",
                            "width": im.width, "height": im.height, "pixel_sha256": h,
                            "file_sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
            # D4 transforms catch common rotations and flips; grouping is conservative.
            variants = [im] + [im.transpose(op) for op in
                        [Image.Transpose.ROTATE_90, Image.Transpose.ROTATE_180, Image.Transpose.ROTATE_270,
                         Image.Transpose.FLIP_LEFT_RIGHT, Image.Transpose.FLIP_TOP_BOTTOM,
                         Image.Transpose.TRANSPOSE, Image.Transpose.TRANSVERSE]]
            hashes.append([phash(v) for v in variants])
        except Exception as exc:
            errors.append({"path": str(relative), "error": str(exc)})
    if errors:
        (out / "corrupt_files.json").write_text(json.dumps(errors, indent=2))
        raise ValueError(f"{len(errors)} unreadable files; resolve before splitting.")
    df = pd.DataFrame(records)
    df.to_csv(out / "source_manifest.csv", index=False)
    source_groups = df.groupby("pixel_sha256")
    source_leakage = {
        "source_counts": df.groupby(["label", "source_split"]).size().unstack(fill_value=0).to_dict(),
        "exact_duplicate_groups": int((source_groups.size() > 1).sum()),
        "exact_groups_crossing_source_splits": int((source_groups.source_split.nunique() > 1).sum()),
        "original_test_images_also_in_original_train": int(df[df.source_split == "test"].pixel_sha256.isin(df[df.source_split == "train"].pixel_sha256).sum()),
        "original_test_images": int((df.source_split == "test").sum()),
    }
    (out / "source_split_leakage.json").write_text(json.dumps(source_leakage, indent=2))
    conflicts = df.groupby("pixel_sha256").label.nunique()
    if (conflicts > 1).any():
        raise ValueError("Identical decoded image has contradictory labels.")
    duplicate_mask = df.duplicated("pixel_sha256", keep="first")
    df.loc[duplicate_mask].to_csv(out / "exact_duplicates_removed.csv", index=False)
    hashes = [h for h, keep in zip(hashes, ~duplicate_mask) if keep]
    df = df.loc[~duplicate_mask].reset_index(drop=True)
    parent = list(range(len(df)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    candidates = []
    for i in range(len(df)):
        for j in range(i):
            distance = min((hashes[i][0] ^ h).bit_count() for h in hashes[j])
            if distance <= 4:
                parent[find(i)] = find(j)
                candidates.append({"path_a": df.at[j, "path"], "path_b": df.at[i, "path"],
                                   "label_a": df.at[j, "label"], "label_b": df.at[i, "label"],
                                   "phash_distance": distance,
                                   "source_split_crossing": df.at[j, "source_split"] != df.at[i, "source_split"]})
    df["group"] = [f"g{find(i):05d}" for i in range(len(df))]
    pairs = pd.DataFrame(candidates, columns=["path_a", "path_b", "label_a", "label_b", "phash_distance", "source_split_crossing"])
    pairs.to_csv(out / "near_duplicate_candidates.csv", index=False)
    outer = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=2026)
    development, test = next(outer.split(df, df.label, df.group))
    df["split"] = "development"
    df.loc[test, "split"] = "test"
    df["cv_fold"] = -1
    inner = StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=2027)
    d = df.iloc[development]
    for fold, (_, valid) in enumerate(inner.split(d, d.label, d.group)):
        df.loc[d.index[valid], "cv_fold"] = fold
    for split in ["development", "test"]:
        if set(df.loc[df.split == split, "label"]) != set(df.label):
            raise ValueError(f"Missing class in {split}")
    for fold in range(3):
        if set(df.loc[df.cv_fold == fold, "label"]) != set(df.label):
            raise ValueError(f"Missing class in CV fold {fold}")
    if df.groupby("group").split.nunique().max() != 1:
        raise AssertionError("Group leakage across outer split")
    if df[df.split == "development"].groupby("group").cv_fold.nunique().max() != 1:
        raise AssertionError("Group leakage across CV folds")
    df.to_csv(out / "manifest.csv", index=False)
    summary = {
        "source_images": len(paths), "readable_images": len(records), "corrupt_images": len(errors),
        "exact_duplicates_removed": int(duplicate_mask.sum()), "images_kept": len(df),
        "classes": dict(sorted(Counter(df.label).items())),
        "dimensions": {f"{w}x{h}": n for (w, h), n in Counter(zip(df.width, df.height)).items()},
        "near_duplicate_candidate_pairs": len(candidates), "groups": df.group.nunique(),
        "largest_group": int(df.groupby("group").size().max()),
        "cross_label_candidate_pairs": int(sum(c["label_a"] != c["label_b"] for c in candidates)),
        "source_split_crossing_candidate_pairs": int(sum(c["source_split_crossing"] for c in candidates)),
        "split_counts": df.groupby(["label", "split"]).size().unstack(fill_value=0).to_dict(),
        "test_status": "held out; not scored during the pilot",
        "grouping_limit": "63-bit pHash distance <= 4 under D4 transforms is a heuristic, not a verified leaf/plant specimen ID.",
        "source_limit": "Supplier labels this archive Non Augmented; filenames can still contain augmented. Raw camera provenance is unverified.",
        "manifest_sha256": hashlib.sha256((out / "manifest.csv").read_bytes()).hexdigest(),
    }
    (out / "audit.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return df


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--images", required=True)
    p.add_argument("--out", default="data/audit")
    a = p.parse_args()
    audit(a.images, a.out)
