# Checklist de evidencias para entrega final

## GitHub

- [ ] Repositorio creado.
- [ ] Rama `dev` creada.
- [ ] Rama `prod` creada.
- [ ] README completo.
- [ ] Dockerfile presente.
- [ ] Workflow `.github/workflows/deploy.yml` presente.
- [ ] Pruebas en `tests/` presentes.

## Azure Blob Storage

- [ ] Modelo ONNX subido a `models/nutrition_model.onnx`.
- [ ] Datos de prueba subidos a `datasets/nutrition_test_data.csv`.
- [ ] Archivo `logs/predicciones_dev.txt` creado o generado por endpoint dev.
- [ ] Archivo `logs/predicciones_prod.txt` creado o generado por endpoint prod.

## GitHub Actions

- [ ] Workflow ejecutado por push a `dev`.
- [ ] Job `test` exitoso en `dev`.
- [ ] Job `build/promote` exitoso en `dev`.
- [ ] Workflow ejecutado por push a `prod`.
- [ ] Job `test` exitoso en `prod`.
- [ ] Job `build/promote` exitoso en `prod`.

## Azure Container Apps

- [ ] Endpoint dev creado.
- [ ] Endpoint prod creado.
- [ ] Endpoint dev responde `/health`.
- [ ] Endpoint prod responde `/health`.
- [ ] Endpoint dev responde `/predict`.
- [ ] Endpoint prod responde `/predict`.

## Sustentación

- [ ] Mostrar arquitectura.
- [ ] Mostrar repo y ramas.
- [ ] Mostrar workflow.
- [ ] Mostrar Azure Blob Storage con modelo/datos/logs.
- [ ] Mostrar endpoints funcionando.
- [ ] Explicar pruebas automáticas.
- [ ] Explicar cómo se despliega un nuevo modelo.
