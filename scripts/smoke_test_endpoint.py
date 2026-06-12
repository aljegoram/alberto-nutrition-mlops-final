import argparse
import json
import requests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="URL base del endpoint, ejemplo https://xxx.azurecontainerapps.io")
    args = parser.parse_args()

    payload = {
        "item_name": "Producto demo",
        "energy_kcal_100g": 120,
        "saturated_fat_100g": 1.2,
        "sodium_100g": 200,
        "sugars_100g": 3.0,
    }
    response = requests.post(args.url.rstrip("/") + "/predict", json=payload, timeout=30)
    print("Status:", response.status_code)
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    response.raise_for_status()


if __name__ == "__main__":
    main()
