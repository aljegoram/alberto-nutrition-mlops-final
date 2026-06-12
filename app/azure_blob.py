import json
import os
from datetime import datetime, timezone
from typing import Dict, Any

from azure.storage.blob import BlobServiceClient


def _get_blob_name() -> str:
    env = os.getenv("APP_ENV", "dev").lower()
    explicit_blob = os.getenv("PREDICTIONS_BLOB_NAME")
    if explicit_blob:
        return explicit_blob
    if env == "prod":
        return os.getenv("PREDICTIONS_PROD_BLOB_NAME", "logs/predicciones_prod.txt")
    return os.getenv("PREDICTIONS_DEV_BLOB_NAME", "logs/predicciones_dev.txt")


def append_prediction_log(payload: Dict[str, Any]) -> None:
    """Agrega una línea JSON a un archivo TXT en Azure Blob Storage.

    Para el proyecto académico se usa lectura + sobrescritura del blob. En producción real,
    se podría usar Append Blob, Event Hub, Log Analytics o Application Insights.
    """
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.getenv("AZURE_CONTAINER_NAME", "data")

    if not connection_string:
        # Permite pruebas locales sin Azure.
        print("AZURE_STORAGE_CONNECTION_STRING no definido. Log omitido.")
        return

    blob_name = _get_blob_name()
    service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = service_client.get_blob_client(container=container_name, blob=blob_name)

    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    line = json.dumps(record, ensure_ascii=False) + "\n"

    try:
        existing = blob_client.download_blob().readall().decode("utf-8")
    except Exception:
        existing = ""

    blob_client.upload_blob(existing + line, overwrite=True)
