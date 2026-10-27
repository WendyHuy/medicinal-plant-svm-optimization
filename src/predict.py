"""Predict a known-class label. This does not detect unknown species."""
import argparse
import joblib
from .features import extract, FEATURE_SPEC

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("image")
    p.add_argument("--model", default="results/pilot/selected_model.joblib")
    a = p.parse_args()
    bundle = joblib.load(a.model)
    if bundle["feature_spec"] != FEATURE_SPEC:
        raise ValueError("Model and feature implementation differ")
    print(bundle["model"].predict(extract(a.image)[None])[0])
    print("Phân loại trong 6 lớp đã học; chưa đánh giá trên tập kiểm tra độc lập.")
