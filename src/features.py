"""Fixed, per-image descriptors; no learned preprocessing or augmentation."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps
from skimage.color import rgb2gray, rgb2hsv
from skimage.feature import hog, local_binary_pattern

FEATURE_SPEC = {
    "version": "hog-hsv-lbp-v1",
    "resize": [96, 96],
    "hog": {"orientations": 9, "pixels_per_cell": [16, 16], "cells_per_block": [2, 2], "block_norm": "L2-Hys"},
    "hsv_bins_per_channel": 16,
    "lbp": {"P": 8, "R": 1, "method": "uniform", "bins": 10},
    "dimension": 958,
}


def load_rgb(path: str | Path) -> Image.Image:
    with Image.open(path) as im:
        return ImageOps.exif_transpose(im).convert("RGB")


def extract(path: str | Path) -> np.ndarray:
    im = load_rgb(path).resize((96, 96), Image.Resampling.LANCZOS)
    rgb = np.asarray(im, dtype=np.float32) / 255.0
    gray = rgb2gray(rgb)
    shape = hog(gray, orientations=9, pixels_per_cell=(16, 16),
                cells_per_block=(2, 2), block_norm="L2-Hys")
    hsv = rgb2hsv(rgb)
    colors = [np.histogram(hsv[..., c], bins=16, range=(0, 1))[0] / (96 * 96)
              for c in range(3)]
    lbp = local_binary_pattern(np.rint(gray * 255).astype(np.uint8), 8, 1, method="uniform")
    texture = np.histogram(lbp, bins=10, range=(0, 10))[0] / (96 * 96)
    result = np.concatenate([shape, *colors, texture]).astype(np.float32)
    if result.shape != (FEATURE_SPEC["dimension"],) or not np.isfinite(result).all():
        raise ValueError(f"Invalid feature vector: {path}")
    return result
