import os
from pathlib import Path
from typing import Dict, Any

import numpy as np
import onnxruntime as ort


FEATURES = [
    "energy_kcal_100g",
    "saturated_fat_100g",
    "sodium_100g",
    "sugars_100g",
    "health_score",
]


def calc_health_score_from_payload(payload: Dict[str, Any]) -> float:
    """Calcula el Health Impact Score usado en el notebook.

    Nota: en este proyecto, sodium_100g se interpreta como miligramos por 100 g,
    siguiendo la transformación realizada en el notebook para OpenFoodFacts.
    """
    sat = max(float(payload.get("saturated_fat_100g", 0) or 0), 0)
    sod = max(float(payload.get("sodium_100g", 0) or 0), 0)
    sug = max(float(payload.get("sugars_100g", 0) or 0), 0)
    method = str(payload.get("method", "otro")).lower()

    risk_sat = min(sat / 20.0, 1.0)
    risk_sod = min(sod / 900.0, 1.0)
    risk_sug = min(sug / 30.0, 1.0)

    risk = 0.4 * risk_sat + 0.4 * risk_sod + 0.2 * risk_sug

    if method == "frito":
        risk = min(1.0, risk + 0.2)

    return max(0.0, min(1.0, 1.0 - risk))


class NutritionOnnxPredictor:
    def __init__(self, model_path: str | None = None):
        self.model_path = model_path or os.getenv(
            "NUTRITION_MODEL_PATH",
            "models/nutrition_model.onnx",
        )
        model_file = Path(self.model_path)
        if not model_file.exists():
            raise FileNotFoundError(
                f"No se encontró el modelo ONNX en {self.model_path}. "
                "El modelo debe descargarse desde Azure Blob Storage antes de ejecutar la API."
            )

        self.session = ort.InferenceSession(str(model_file), providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name
        self.output_names = [o.name for o in self.session.get_outputs()]

    def _build_input(self, payload: Dict[str, Any]) -> np.ndarray:
        enriched_payload = dict(payload)
        if "health_score" not in enriched_payload or enriched_payload.get("health_score") is None:
            enriched_payload["health_score"] = calc_health_score_from_payload(enriched_payload)

        values = [float(enriched_payload[name]) for name in FEATURES]
        return np.array([values], dtype=np.float32)

    def _extract_probability(self, raw_probability_output: Any, label: int) -> float:
        """Extrae probabilidad de salida ONNX generada por skl2onnx."""
        if raw_probability_output is None:
            return float(label)

        if isinstance(raw_probability_output, list) and raw_probability_output:
            first = raw_probability_output[0]
            if isinstance(first, dict):
                return float(first.get(1, first.get("1", first.get(label, 0.0))))

        try:
            arr = np.asarray(raw_probability_output)
            if arr.ndim == 2 and arr.shape[1] >= 2:
                return float(arr[0, 1])
            if arr.size == 1:
                return float(arr.ravel()[0])
        except Exception:
            pass

        return float(label)

    def predict(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        x = self._build_input(payload)
        outputs = self.session.run(None, {self.input_name: x})

        label_output = outputs[0]
        label = int(np.asarray(label_output).ravel()[0])

        probability_output = outputs[1] if len(outputs) > 1 else None
        probability = self._extract_probability(probability_output, label)

        return {
            "label": label,
            "recomendable": bool(label == 1),
            "probabilidad_recomendable": round(float(probability), 6),
        }
