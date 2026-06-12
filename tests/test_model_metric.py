import os
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score

from app.onnx_predictor import NutritionOnnxPredictor, FEATURES


def test_model_metric_is_above_threshold():
    model_path = os.getenv("NUTRITION_MODEL_PATH", "artifacts/models/nutrition_model.onnx")
    test_data_path = os.getenv("TEST_DATA_PATH", "artifacts/data/nutrition_test_data.csv")
    threshold = float(os.getenv("MIN_ACCEPTABLE_ACCURACY", "0.70"))

    assert Path(model_path).exists(), f"No existe el modelo ONNX en {model_path}"
    assert Path(test_data_path).exists(), f"No existen datos de prueba en {test_data_path}"

    df = pd.read_csv(test_data_path)
    required = FEATURES + ["label"]
    missing = [c for c in required if c not in df.columns]
    assert not missing, f"Faltan columnas en datos de prueba: {missing}"

    predictor = NutritionOnnxPredictor(model_path=model_path)
    y_true = []
    y_pred = []

    for _, row in df.iterrows():
        payload = {feature: float(row[feature]) for feature in FEATURES}
        result = predictor.predict(payload)
        y_true.append(int(row["label"]))
        y_pred.append(int(result["label"]))

    accuracy = accuracy_score(y_true, y_pred)
    assert accuracy >= threshold, f"Accuracy {accuracy:.4f} menor que umbral {threshold:.4f}"
