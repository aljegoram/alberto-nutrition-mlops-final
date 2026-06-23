import os
from fastapi import FastAPI

from app.schemas import NutritionInput, PredictionResponse
from app.onnx_predictor import NutritionOnnxPredictor
from app.azure_blob import append_prediction_log

app = FastAPI(
    title="Asesor Nutricional MLOps",
    description="API de inferencia para modelo nutricional ONNX con logging en Azure Blob Storage.",
    version="1.0.0",
)

_predictor: NutritionOnnxPredictor | None = None


def get_predictor() -> NutritionOnnxPredictor:
    global _predictor
    if _predictor is None:
        _predictor = NutritionOnnxPredictor()
    return _predictor


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "nutrition-advisor",
        "environment": os.getenv("APP_ENV", "dev"),
    }


@app.post("/predict", response_model=PredictionResponse)
def predict(input_data: NutritionInput):
    payload = input_data.model_dump()
    prediction = get_predictor().predict(payload)

    ambiente = os.getenv("APP_ENV", "dev")
    model_path = os.getenv("NUTRITION_MODEL_PATH", "models/nutrition_model.onnx")

    if prediction["recomendable"]:
        interpretation = "Producto potencialmente recomendable según el modelo nutricional."
    else:
        interpretation = "Producto no recomendable o requiere revisión según el modelo nutricional."

    response = {
        "ambiente": ambiente,
        "item_name": payload.get("item_name", "producto_sin_nombre"),
        "recomendable": prediction["recomendable"],
        "label": prediction["label"],
        "probabilidad_recomendable": prediction["probabilidad_recomendable"],
        "interpretacion": interpretation,
        "modelo": model_path,
        "demo_message": "Cambio visible en predict desplegado desde GitHub Actions",
    }

    append_prediction_log({
        "environment": ambiente,
        "request": payload,
        "response": response,
    })

    return response


@app.post("/recommend", response_model=PredictionResponse)
def recommend(input_data: NutritionInput):
    """Alias académico para demostrar interacción de usuario final con el asesor."""
    return predict(input_data)
