import os
from pathlib import Path

from app.onnx_predictor import NutritionOnnxPredictor


def test_model_responds_with_defined_input():
    model_path = os.getenv("NUTRITION_MODEL_PATH", "artifacts/models/nutrition_model.onnx")
    assert Path(model_path).exists(), f"No existe el modelo ONNX en {model_path}"

    predictor = NutritionOnnxPredictor(model_path=model_path)
    result = predictor.predict({
        "energy_kcal_100g": 120,
        "saturated_fat_100g": 1.2,
        "sodium_100g": 0.2,
        "sugars_100g": 3.0,
    })

    assert result["label"] in [0, 1]
    assert isinstance(result["recomendable"], bool)
    assert 0.0 <= result["probabilidad_recomendable"] <= 1.0
