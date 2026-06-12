"""
Entrenamiento real del Asesor Nutricional y exportación a ONNX.

Este script convierte la lógica del notebook
SR_Asesor_Nutricional_Basado_Contenido_Actualizado.ipynb
en un script productivo para MLOps.

Flujo:
1. Lee food_subset_clean.parquet desde Azure Blob Storage o desde ruta local.
2. Estandariza columnas nutricionales.
3. Calcula Health Impact Score (HIS) usando la fórmula del notebook.
4. Genera label binario: 1 si health_score >= 0.70, 0 en caso contrario.
5. Entrena un Pipeline(StandardScaler + MLPClassifier).
6. Evalúa accuracy, precision, recall, f1 y roc_auc.
7. Exporta el modelo a ONNX.
8. Genera datos de prueba para el pipeline CI/CD.

IMPORTANTE:
- No guardar credenciales en este archivo.
- Usar AZURE_STORAGE_CONNECTION_STRING como variable de entorno o GitHub Secret.
- El archivo .onnx generado NO debe subirse al repositorio.
"""

from __future__ import annotations

import json
import os
from io import BytesIO
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
from azure.storage.blob import BlobServiceClient
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType


FEATURES = [
    "energy_kcal_100g",
    "saturated_fat_100g",
    "sodium_100g",
    "sugars_100g",
    "health_score",
]

TARGET = "label"
MAX_ROWS_ML = int(os.getenv("MAX_ROWS_ML", "30000"))
RANDOM_STATE = 42


def read_parquet_from_azure(blob_name: str) -> pd.DataFrame:
    """Lee un archivo Parquet desde Azure Blob Storage."""
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.getenv("AZURE_CONTAINER_NAME", "data")

    if not connection_string:
        raise RuntimeError("Falta AZURE_STORAGE_CONNECTION_STRING")

    service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = service_client.get_blob_client(container=container_name, blob=blob_name)

    data = blob_client.download_blob().readall()
    return pd.read_parquet(BytesIO(data))


def load_dataset() -> pd.DataFrame:
    """Carga dataset nutricional desde Azure o desde archivo local."""
    food_blob_name = os.getenv("FOOD_BLOB_NAME", "food_subset_clean.parquet")
    local_dataset_path = Path(os.getenv("LOCAL_DATASET_PATH", food_blob_name))

    if os.getenv("AZURE_STORAGE_CONNECTION_STRING"):
        try:
            df = read_parquet_from_azure(food_blob_name)
            print(f"Dataset cargado desde Azure: {food_blob_name} -> {df.shape}")
            return df
        except Exception as exc:
            print(f"No se pudo cargar desde Azure. Se intentará fallback local. Detalle: {exc}")

    if local_dataset_path.exists():
        if local_dataset_path.suffix.lower() == ".parquet":
            df = pd.read_parquet(local_dataset_path)
        else:
            df = pd.read_csv(local_dataset_path)
        print(f"Dataset cargado localmente: {local_dataset_path} -> {df.shape}")
        return df

    raise FileNotFoundError(
        "No se pudo cargar el dataset. Define AZURE_STORAGE_CONNECTION_STRING "
        "o ubica food_subset_clean.parquet en la carpeta del proyecto."
    )


def standardize_openfoodfacts_columns(df_off: pd.DataFrame) -> pd.DataFrame:
    """Estandariza columnas siguiendo la lógica del notebook."""
    cols_off_map: Dict[str, str] = {}

    if "product_name_clean" in df_off.columns:
        cols_off_map["product_name_clean"] = "item_name"
    elif "product_name" in df_off.columns:
        cols_off_map["product_name"] = "item_name"
    else:
        # El nombre no es indispensable para entrenar, pero sí útil para trazabilidad.
        df_off = df_off.copy()
        df_off["item_name"] = "producto_sin_nombre"
        cols_off_map["item_name"] = "item_name"

    if "calories_100g" in df_off.columns:
        cols_off_map["calories_100g"] = "energy_kcal_100g"
    elif "energy_kcal_100g" in df_off.columns:
        cols_off_map["energy_kcal_100g"] = "energy_kcal_100g"
    elif "energy_100g" in df_off.columns:
        cols_off_map["energy_100g"] = "energy_kcal_100g"

    if "sat_fat_100g" in df_off.columns:
        cols_off_map["sat_fat_100g"] = "saturated_fat_100g"
    elif "saturated_fat_100g" in df_off.columns:
        cols_off_map["saturated_fat_100g"] = "saturated_fat_100g"
    elif "saturated-fat_100g" in df_off.columns:
        cols_off_map["saturated-fat_100g"] = "saturated_fat_100g"

    if "sugars_100g" in df_off.columns:
        cols_off_map["sugars_100g"] = "sugars_100g"

    use_sodium_mg_conversion = False
    if "sodium_100g" in df_off.columns:
        cols_off_map["sodium_100g"] = "sodium_100g"
        # En OpenFoodFacts suele venir en gramos. El notebook lo lleva a miligramos.
        use_sodium_mg_conversion = True

    required_after_mapping = {
        "energy_kcal_100g",
        "saturated_fat_100g",
        "sodium_100g",
        "sugars_100g",
    }

    mapped_targets = set(cols_off_map.values())
    missing = sorted(required_after_mapping - mapped_targets)
    if missing:
        raise ValueError(f"Faltan columnas nutricionales requeridas después del mapeo: {missing}")

    df = df_off[list(cols_off_map.keys())].rename(columns=cols_off_map).copy()

    if "source" not in df.columns:
        df["source"] = "OpenFoodFacts"
    if "method" not in df.columns:
        df["method"] = "otro"

    if use_sodium_mg_conversion:
        df["sodium_100g"] = pd.to_numeric(df["sodium_100g"], errors="coerce") * 1000.0

    return df


def calc_his(row: pd.Series) -> float:
    """Health Impact Score del notebook, normalizado en [0, 1]."""
    sat = max(row.get("saturated_fat_100g", 0) or 0, 0)
    sod = max(row.get("sodium_100g", 0) or 0, 0)
    sug = max(row.get("sugars_100g", 0) or 0, 0)
    method = str(row.get("method", "otro")).lower()

    risk_sat = min(sat / 20.0, 1.0)
    risk_sod = min(sod / 900.0, 1.0)
    risk_sug = min(sug / 30.0, 1.0)

    risk = 0.4 * risk_sat + 0.4 * risk_sod + 0.2 * risk_sug

    if method == "frito":
        risk = min(1.0, risk + 0.2)

    score = 1.0 - risk
    return max(0.0, min(1.0, score))


def build_catalog(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Construye df_catalog con HIS y label, siguiendo el notebook."""
    df = standardize_openfoodfacts_columns(df_raw)

    numeric_cols = [
        "energy_kcal_100g",
        "saturated_fat_100g",
        "sodium_100g",
        "sugars_100g",
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    before = len(df)
    df = df.dropna(subset=["saturated_fat_100g", "sodium_100g", "sugars_100g"]).copy()
    after = len(df)
    print(f"Filas antes de eliminar nulos HIS: {before}")
    print(f"Filas después de eliminar nulos HIS: {after}")

    df["health_score"] = df.apply(calc_his, axis=1)
    df["label"] = (df["health_score"] >= 0.70).astype(int)

    # Limpieza de nombres y duplicados, como en df_catalog.
    df["item_name"] = df["item_name"].astype(str).str.strip()
    df = df[
        df["item_name"].notna()
        & (df["item_name"] != "")
        & (df["item_name"].str.lower() != "nan")
    ].copy()

    df = df.drop_duplicates(
        subset=[
            "item_name",
            "source",
            "energy_kcal_100g",
            "saturated_fat_100g",
            "sodium_100g",
            "sugars_100g",
        ]
    ).reset_index(drop=True)

    return df


def train_export_model(df_catalog: pd.DataFrame) -> None:
    """Entrena MLP real del notebook y exporta a ONNX."""
    Path("models").mkdir(parents=True, exist_ok=True)
    Path("data").mkdir(parents=True, exist_ok=True)
    Path("artifacts").mkdir(parents=True, exist_ok=True)

    ml_df = df_catalog.dropna(subset=FEATURES + [TARGET]).copy()

    if ml_df[TARGET].nunique() < 2:
        raise ValueError("La variable label tiene una sola clase. No se puede entrenar el clasificador.")

    if len(ml_df) > MAX_ROWS_ML:
        ml_sample, _ = train_test_split(
            ml_df,
            train_size=MAX_ROWS_ML,
            stratify=ml_df[TARGET],
            random_state=RANDOM_STATE,
        )
        ml_df = ml_sample.copy()
        print(f"Se usó muestra estratificada para entrenamiento: {ml_df.shape}")

    X = ml_df[FEATURES].astype(np.float32)
    y = ml_df[TARGET].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        stratify=y,
        random_state=RANDOM_STATE,
    )

    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "mlp",
                MLPClassifier(
                    hidden_layer_sizes=(32, 16),
                    activation="relu",
                    solver="adam",
                    alpha=1e-4,
                    learning_rate_init=1e-3,
                    max_iter=50,
                    early_stopping=True,
                    validation_fraction=0.15,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, y_proba)),
        "rows_catalog": int(len(df_catalog)),
        "rows_training_used": int(len(ml_df)),
        "rows_test": int(len(X_test)),
        "features": FEATURES,
        "target": TARGET,
        "model_type": "Pipeline(StandardScaler + MLPClassifier)",
    }

    initial_type = [("float_input", FloatTensorType([None, len(FEATURES)]))]
    onnx_model = convert_sklearn(model, initial_types=initial_type, target_opset=12)

    model_path = Path("models/nutrition_model.onnx")
    model_path.write_bytes(onnx_model.SerializeToString())

    test_df = X_test.copy()
    test_df[TARGET] = y_test.values
    test_df.to_csv("data/nutrition_test_data.csv", index=False)

    Path("artifacts/metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    print(f"Modelo ONNX generado en: {model_path}")
    print("Datos de prueba generados en: data/nutrition_test_data.csv")
    print("Métricas generadas en: artifacts/metrics.json")


def main() -> None:
    df_raw = load_dataset()
    df_catalog = build_catalog(df_raw)

    print("Catálogo final para entrenamiento:", df_catalog.shape)
    print("Distribución de label:")
    print(df_catalog["label"].value_counts(normalize=True).rename("proporcion"))

    train_export_model(df_catalog)


if __name__ == "__main__":
    main()
