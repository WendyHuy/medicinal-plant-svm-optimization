"""Predeclared handcrafted descriptor candidates; each depends on one image only."""
import numpy as np
from PIL import Image
from skimage.color import rgb2gray, rgb2hsv
from skimage.feature import hog, local_binary_pattern, graycomatrix, graycoprops
from .features import load_rgb, extract as extract_v1

CANDIDATES = {
    "v1": 958,
    "v1_no_color": 910,
    "texture128": 126,
    "enhanced128": 1890,
    "center128": 1890,
}


def extract(path, feature_id):
    if feature_id not in CANDIDATES:
        raise ValueError(f"Unknown feature ID: {feature_id}")
    if feature_id in {"v1", "v1_no_color"}:
        v = extract_v1(path)
        return v if feature_id == "v1" else np.r_[v[:900], v[-10:]]
    im = load_rgb(path)
    if feature_id == "center128":
        w, h = im.size
        im = im.crop((round(.1*w), round(.1*h), round(.9*w), round(.9*h)))
    im = im.resize((128, 128), Image.Resampling.LANCZOS)
    rgb = np.asarray(im, dtype=np.float32) / 255.
    gray = rgb2gray(rgb)
    g8 = np.rint(gray*255).astype(np.uint8)
    hsv = rgb2hsv(rgb)
    colors = [np.histogram(hsv[..., c], bins=16, range=(0, 1))[0] / (128*128) for c in range(3)]
    texture = []
    for points, radius in [(8, 1), (16, 2), (24, 3)]:
        lbp = local_binary_pattern(g8, points, radius, method="uniform")
        texture.append(np.histogram(lbp, bins=points+2, range=(0, points+2))[0] / (128*128))
    glcm = graycomatrix(g8//8, distances=[1, 3], angles=[0, np.pi/4, np.pi/2, 3*np.pi/4],
                       levels=32, symmetric=True, normed=True)
    cooccurrence = []
    for prop in ["contrast", "dissimilarity", "homogeneity", "energy", "correlation", "ASM"]:
        values = graycoprops(glcm, prop)
        cooccurrence.extend([values.mean(axis=1), values.std(axis=1)])
    parts = [*colors, *texture, *cooccurrence]
    if feature_id != "texture128":
        parts.insert(0, hog(gray, orientations=9, pixels_per_cell=(16,16),
                            cells_per_block=(2,2), block_norm="L2-Hys"))
    result = np.concatenate(parts).astype(np.float32)
    if result.shape != (CANDIDATES[feature_id],) or not np.isfinite(result).all():
        raise ValueError(f"Invalid descriptor: {path}, {feature_id}")
    return result
