import argparse
import os
from pathlib import Path

from azure.storage.blob import BlobServiceClient


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--blob", required=True, help="Ruta del blob en Azure Storage")
    parser.add_argument("--out", required=True, help="Ruta local de salida")
    args = parser.parse_args()

    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.getenv("AZURE_CONTAINER_NAME", "data")

    if not connection_string:
        raise RuntimeError("Falta AZURE_STORAGE_CONNECTION_STRING")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = service_client.get_blob_client(container=container_name, blob=args.blob)

    with open(out_path, "wb") as f:
        f.write(blob_client.download_blob().readall())

    print(f"Descargado {args.blob} -> {out_path}")


if __name__ == "__main__":
    main()
