"""Predict a known-class label. This does not detect unknown species."""
import argparse
import json
import joblib
from .features import extract as extract_v1, FEATURE_SPEC
from .features_v2 import extract
from .develop import feature_code_hash


def predict(image, model_path):
    bundle = joblib.load(model_path)
    if "feature_id" in bundle:
        if bundle["feature_code_sha256"] != feature_code_hash():
            raise ValueError("Model and feature code differ")
        features = extract(image, bundle["feature_id"])
    else:
        if bundle["feature_spec"] != FEATURE_SPEC:
            raise ValueError("Model and feature implementation differ")
        features = extract_v1(image)
    return str(bundle["model"].predict(features[None])[0])

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("image")
    p.add_argument("--model", default="models/optimized.joblib")
    p.add_argument("--compare", action="store_true", help="Compare deployed baseline and optimized models")
    a = p.parse_args()
    if a.compare:
        print(json.dumps({"before":predict(a.image,"models/baseline.joblib"),
                          "after":predict(a.image,"models/optimized.joblib")},ensure_ascii=False,indent=2))
    else:
        print(predict(a.image,a.model))
    print("Phân loại trong 6 lớp đã học. Chưa có cơ chế từ chối loài ngoài tập này.")
