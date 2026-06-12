# CHANGELOG

## [1.0.0] - Proyecto final MLOps

### Agregado

- Estructura inicial del proyecto final.
- API FastAPI para inferencia nutricional.
- Carga de modelo ONNX con ONNX Runtime.
- Registro de predicciones en Azure Blob Storage.
- Script de entrenamiento y exportación a ONNX.
- Scripts de descarga y carga de artefactos en Azure Blob Storage.
- Pruebas unitarias del modelo.
- Pipeline CI/CD con GitHub Actions para ramas `dev` y `prod`.
- Dockerfile para construir contenedor de inferencia.
- Documentación de arquitectura, demo y evidencias.

### Decisiones

- El modelo `.onnx` no se guarda en el repositorio.
- Los datos de prueba no se guardan en el repositorio.
- Azure Blob Storage se usa como almacenamiento externo de modelo, datos y logs.
- Azure Container Apps se usa como solución cloud para endpoints `dev` y `prod`.
