# Proyecto Final MLOps — Asesor Nutricional con despliegue automático de modelos ONNX

## 1. Propósito del repositorio

Este repositorio implementa una solución MLOps para un **asesor nutricional** que permite desplegar automáticamente nuevos modelos de recomendabilidad nutricional en ambientes separados de desarrollo y producción.

La solución usa:

- modelo en formato **ONNX**;
- datos y modelo almacenados fuera del repositorio en **Azure Blob Storage**;
- API de inferencia con **FastAPI**;
- contenedor **Docker**;
- pruebas automáticas con **pytest**;
- pipeline **CI/CD con GitHub Actions**;
- despliegue en **Azure Container Apps**;
- endpoints separados para ramas `dev` y `prod`;
- registro de predicciones en archivos `.txt` dentro de Azure Blob Storage.

> Este proyecto tiene finalidad académica. No debe usarse como recomendador médico o nutricional real sin validación profesional.

---

## 2. Problema abordado

El proyecto parte de un asesor nutricional basado en contenido, orientado a apoyar la selección de productos alimenticios para perfiles con restricciones nutricionales, por ejemplo insuficiencia hepática.

El modelo recibe variables nutricionales por cada 100 gramos de producto:

| Variable | Descripción |
|---|---|
| `energy_kcal_100g` | Energía en kcal por 100g |
| `saturated_fat_100g` | Grasas saturadas por 100g |
| `sodium_100g` | Sodio por 100g |
| `sugars_100g` | Azúcares por 100g |

El modelo ONNX predice si un producto es:

| Label | Significado |
|---|---|
| `1` | Recomendable |
| `0` | No recomendable |

---

## 3. Requerimientos principales cubiertos

| Requerimiento del proyecto final | Implementación en este repo |
|---|---|
| Repositorio GitHub con CI/CD | `.github/workflows/deploy.yml` |
| Ramas `dev` y `prod` | Pipeline configurado para `push` a `dev` y `prod` |
| Endpoint por rama | Azure Container Apps `nutrition-advisor-dev` y `nutrition-advisor-prod` |
| Etapa `test` | Job `test` en GitHub Actions |
| Etapa `build/promote` | Job `build_promote` en GitHub Actions |
| Modelo ONNX fuera del repo | Descarga desde Azure Blob Storage |
| Datos de prueba fuera del repo | Descarga desde Azure Blob Storage |
| Contenedor Docker | `Dockerfile` |
| API para usuario final | `app/main.py` con FastAPI |
| Registro TXT de predicciones | `predicciones_dev.txt` y `predicciones_prod.txt` en Azure Blob Storage |

---

## 4. Arquitectura general

```text
Usuario final
   |
   v
Endpoint DEV o PROD en Azure Container Apps
   |
   v
Contenedor Docker con FastAPI
   |
   v
ONNX Runtime carga nutrition_model.onnx
   |
   v
Predicción nutricional
   |
   v
Azure Blob Storage registra predicción en TXT
```

Diagrama detallado:

- [`docs/architecture.md`](docs/architecture.md)

---

## 5. Estructura del repositorio

```text
nutrition-mlops-final/
├── README.md
├── CHANGELOG.md
├── Dockerfile
├── requirements.txt
├── .gitignore
├── .dockerignore
├── app/
│   ├── main.py
│   ├── schemas.py
│   ├── onnx_predictor.py
│   └── azure_blob.py
├── training/
│   └── train_export_onnx.py
├── scripts/
│   ├── download_from_azure.py
│   ├── upload_to_azure.py
│   └── smoke_test_endpoint.py
├── tests/
│   ├── test_model_response.py
│   └── test_model_metric.py
├── docs/
│   ├── architecture.md
│   ├── demo_script.md
│   └── evidence_checklist.md
├── infra/
│   └── azure_container_apps.md
└── .github/
    └── workflows/
        └── deploy.yml
```

---

## 6. Flujo CI/CD

El workflow se ejecuta cada vez que se hace `push` a las ramas:

```text
dev
prod
```

### 6.1. Rama `dev`

```text
push a dev
→ descarga modelo ONNX desde Azure Blob Storage
→ descarga datos de prueba desde Azure Blob Storage
→ ejecuta pruebas unitarias
→ construye imagen Docker
→ publica imagen en GHCR
→ despliega en endpoint dev
→ las predicciones se registran en predicciones_dev.txt
```

### 6.2. Rama `prod`

```text
push a prod
→ descarga modelo ONNX desde Azure Blob Storage
→ descarga datos de prueba desde Azure Blob Storage
→ ejecuta pruebas unitarias
→ construye imagen Docker
→ publica imagen en GHCR
→ despliega en endpoint prod
→ las predicciones se registran en predicciones_prod.txt
```

---

## 7. Variables y secretos requeridos

Configurar en GitHub → Settings → Secrets and variables → Actions.

### 7.1. Secrets

| Secret | Descripción |
|---|---|
| `AZURE_STORAGE_CONNECTION_STRING` | Cadena de conexión de Azure Storage |
| `AZURE_CREDENTIALS` | Credenciales JSON del Service Principal para `azure/login` |

### 7.2. Variables

| Variable | Ejemplo |
|---|---|
| `AZURE_CONTAINER_NAME` | `data` |
| `NUTRITION_MODEL_BLOB_NAME` | `models/nutrition_model.onnx` |
| `TEST_DATA_BLOB_NAME` | `datasets/nutrition_test_data.csv` |
| `PREDICTIONS_DEV_BLOB_NAME` | `logs/predicciones_dev.txt` |
| `PREDICTIONS_PROD_BLOB_NAME` | `logs/predicciones_prod.txt` |
| `AZURE_RESOURCE_GROUP` | `rg-nutrition-mlops-final` |
| `AZURE_CONTAINER_APP_DEV` | `nutrition-advisor-dev` |
| `AZURE_CONTAINER_APP_PROD` | `nutrition-advisor-prod` |
| `MIN_ACCEPTABLE_ACCURACY` | `0.70` |

---

## 8. Entrenamiento y exportación ONNX

Para entrenar localmente y generar el modelo ONNX:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# En Windows: venv\Scripts\activate
python -m pip install -r requirements.txt
python training/train_export_onnx.py
```

El script genera:

```text
models/nutrition_model.onnx
data/nutrition_test_data.csv
artifacts/metrics.json
```

Estos archivos **no deben subirse al repositorio**. El modelo ONNX y los datos de prueba deben subirse a Azure Blob Storage.

---

## 9. Subir modelo y datos de prueba a Azure Blob Storage

```bash
python scripts/upload_to_azure.py --local models/nutrition_model.onnx --blob models/nutrition_model.onnx
python scripts/upload_to_azure.py --local data/nutrition_test_data.csv --blob datasets/nutrition_test_data.csv
```

---

## 10. Ejecutar API local

Primero se requiere tener el modelo ONNX disponible localmente en:

```text
models/nutrition_model.onnx
```

Luego:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Probar:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"item_name":"Producto demo","energy_kcal_100g":120,"saturated_fat_100g":1.2,"sodium_100g":0.2,"sugars_100g":3.0}'
```

---

## 11. Ejecutar pruebas

```bash
python scripts/download_from_azure.py --blob models/nutrition_model.onnx --out artifacts/models/nutrition_model.onnx
python scripts/download_from_azure.py --blob datasets/nutrition_test_data.csv --out artifacts/data/nutrition_test_data.csv
pytest -q
```

Las pruebas verifican:

1. que el modelo ONNX responde con una entrada definida;
2. que el desempeño del modelo no cae por debajo del umbral configurado.

---

## 12. Construir Docker localmente

```bash
mkdir -p models
python scripts/download_from_azure.py --blob models/nutrition_model.onnx --out models/nutrition_model.onnx

docker build -t nutrition-advisor:local .
docker run -p 8000:8000 --env APP_ENV=local nutrition-advisor:local
```

---

## 13. Despliegue cloud

La solución cloud propuesta usa Azure Container Apps:

- endpoint dev: `nutrition-advisor-dev`;
- endpoint prod: `nutrition-advisor-prod`.

Ver guía:

- [`infra/azure_container_apps.md`](infra/azure_container_apps.md)

---

## 14. Sustentación

Guion sugerido:

- [`docs/demo_script.md`](docs/demo_script.md)

Checklist de evidencias:

- [`docs/evidence_checklist.md`](docs/evidence_checklist.md)

---

## 15. Consideraciones de seguridad

- El archivo `.onnx` no se versiona en GitHub.
- Los datos de prueba no se versionan en GitHub.
- La cadena de conexión de Azure Storage se maneja como secreto.
- Los logs se almacenan en Azure Blob Storage.
- Los endpoints `dev` y `prod` quedan separados por rama y por Container App.

---

## 16. Conclusión

El repositorio implementa un sistema MLOps viable para despliegue automático de nuevos modelos ONNX de recomendabilidad nutricional, usando ramas separadas, pipeline CI/CD, pruebas automáticas, contenedor Docker, endpoints cloud y monitoreo inicial mediante logs de predicciones en Azure Blob Storage.
