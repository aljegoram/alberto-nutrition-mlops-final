# Guion de sustentación — 10 minutos

## 1. Contexto del problema — 1 min

Presentar el asesor nutricional y explicar que el objetivo es automatizar el despliegue de nuevos modelos ONNX para que los usuarios puedan consumirlos mediante endpoints cloud.

## 2. Arquitectura — 2 min

Mostrar el diagrama en `docs/architecture.md` y explicar:

- GitHub con ramas `dev` y `prod`;
- modelo y datos fuera del repo en Azure Blob Storage;
- GitHub Actions con etapas `test` y `build/promote`;
- endpoints separados en Azure Container Apps;
- logs de predicciones en TXT dentro de Azure Blob Storage.

## 3. Repositorio — 1 min

Mostrar estructura:

- `app/` API;
- `training/` entrenamiento y exportación ONNX;
- `tests/` pruebas;
- `.github/workflows/deploy.yml` CI/CD;
- `Dockerfile`;
- `README.md`.

## 4. Demo de pipeline — 2 min

Mostrar GitHub Actions:

- push a `dev`;
- job `test` exitoso;
- job `build/promote` exitoso;
- imagen publicada en GHCR;
- despliegue en Azure Container Apps.

## 5. Demo de endpoint — 2 min

Probar endpoint:

```bash
curl -X POST <URL_ENDPOINT>/predict \
  -H "Content-Type: application/json" \
  -d '{"item_name":"Producto demo","energy_kcal_100g":120,"saturated_fat_100g":1.2,"sodium_100g":0.2,"sugars_100g":3.0}'
```

Mostrar respuesta y luego mostrar el archivo de predicciones en Azure Blob Storage.

## 6. Cierre — 2 min

Explicar por qué cumple:

- modelo ONNX fuera del repo;
- datos de prueba fuera del repo;
- ramas `dev` y `prod`;
- endpoints separados;
- pruebas automáticas;
- contenedor Docker;
- despliegue automático;
- logs para monitoreo posterior.
