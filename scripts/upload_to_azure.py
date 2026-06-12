import argparse
import os
from pathlib import Path

from azure.storage.blob import BlobServiceClient


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", required=True, help="Archivo local")
    parser.add_argument("--blob", required=True, help="Ruta destino en Azure Blob Storage")
    args = parser.parse_args()

    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.getenv("AZURE_CONTAINER_NAME", "data")

    if not connection_string:
        raise RuntimeError("Falta AZURE_STORAGE_CONNECTION_STRING")

    local_path = Path(args.local)
    if not local_path.exists():
        raise FileNotFoundError(local_path)

    service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = service_client.get_blob_client(container=container_name, blob=args.blob)

    with open(local_path, "rb") as f:
        blob_client.upload_blob(f, overwrite=True)

    print(f"Subido {local_path} -> {args.blob}")


if __name__ == "__main__":
    main()
