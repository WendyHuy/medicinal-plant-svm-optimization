"""Local integration API for the six-class leaf model. No upload retention."""
from functools import lru_cache
import io
import json
from pathlib import Path
import tempfile
import warnings

import joblib
from PIL import Image, UnidentifiedImageError

from .develop import digest, feature_code_hash
from .features_v2 import extract

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 20_000_000


@lru_cache(maxsize=1)
def load_release():
    meta = json.loads((ROOT / 'models/phase3_metadata.json').read_text())
    path = ROOT / 'models' / meta['model_file']
    if digest(path) != meta['model_sha256']:
        raise ValueError('Model checksum mismatch')
    bundle = joblib.load(path)
    if bundle['feature_code_sha256'] != feature_code_hash():
        raise ValueError('Feature implementation changed')
    if bundle['params'] != meta['params']:
        raise ValueError('Model metadata differs')
    return bundle, meta


def validate_image(data):
    if not data or len(data) > MAX_BYTES:
        raise ValueError('Ảnh trống hoặc lớn hơn 10 MB')
    with warnings.catch_warnings():
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        try:
            with Image.open(io.BytesIO(data)) as image:
                if image.format not in {'JPEG', 'PNG', 'WEBP'}:
                    raise ValueError('Chỉ nhận ảnh JPEG, PNG hoặc WEBP')
                if image.width * image.height > MAX_PIXELS or min(image.size) < 32:
                    raise ValueError('Kích thước ảnh không phù hợp')
                image.verify()
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
            raise ValueError('Không đọc được ảnh hợp lệ') from error


def predict_bytes(data, organ='leaf'):
    if organ != 'leaf':
        raise ValueError('Bản hiện tại chỉ được huấn luyện trên ảnh lá')
    validate_image(data)
    bundle, meta = load_release()
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'upload.image'
        path.write_bytes(data)
        vector = extract(path, bundle['feature_id'])
    model = bundle['model']
    predicted = str(model.predict(vector[None])[0])
    scores = model.decision_function(vector[None])[0]
    ranked = sorted(zip(model.classes_, scores), key=lambda item: item[1], reverse=True)
    return {'label': predicted,
            'ranked_candidates': [{'label': str(name), 'decision_score': float(score)} for name, score in ranked[:3]],
            'score_type': 'uncalibrated_svm_decision_function', 'score_is_probability': False,
            'scope': 'six_leaf_classes_only', 'unknown_species_detection': False,
            'model_sha256': meta['model_sha256'], 'release': '0.3.0',
            'notice': 'Gợi ý nhận diện trong sáu lớp đã học; cần xác minh tên cây trước khi sử dụng làm thuốc.'}


def create_app():
    from fastapi import FastAPI, File, Form, HTTPException, UploadFile
    app = FastAPI(title='Medicinal Leaf SVM', version='0.3.0',
                  description='API nghiên cứu cho ảnh lá của sáu loài đã học.')

    @app.get('/health')
    def health():
        _, meta = load_release()
        return {'status': 'ok', 'version': '0.3.0', 'labels': meta['supported_labels'],
                'supported_organs': ['leaf'], 'unknown_species_detection': False}

    @app.post('/predict')
    def predict(file: UploadFile = File(...), organ: str = Form('leaf')):
        try:
            data = file.file.read(MAX_BYTES + 1)
            return predict_bytes(data, organ)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        finally:
            file.file.close()
    return app


app = create_app()
