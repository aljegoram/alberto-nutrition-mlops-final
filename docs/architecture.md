# Arquitectura del sistema de despliegue automático

## Diagrama Mermaid

```mermaid
flowchart TD
    A[Push a rama dev o prod] --> B[GitHub Actions]
    B --> C[Test]
    C --> C1[Descargar modelo ONNX desde Azure Blob]
    C --> C2[Descargar datos de prueba desde Azure Blob]
    C --> C3[Prueba: modelo responde]
    C --> C4[Prueba: métrica >= umbral]
    C --> D[Build/Promote]
    D --> D1[Descargar modelo ONNX]
    D --> D2[Construir imagen Docker]
    D --> D3[Publicar imagen en GHCR]
    D --> E{Rama}
    E -->|dev| F[Azure Container App DEV]
    E -->|prod| G[Azure Container App PROD]
    F --> H[Endpoint DEV]
    G --> I[Endpoint PROD]
    H --> J[Usuario llama /predict]
    I --> K[Usuario llama /predict]
    J --> L[Registrar predicciones_dev.txt en Azure Blob]
    K --> M[Registrar predicciones_prod.txt en Azure Blob]
```

## Componentes

| Componente | Rol |
|---|---|
| GitHub | Versionamiento y gestión de ramas |
| GitHub Actions | Automatización CI/CD |
| Azure Blob Storage | Almacenamiento externo de modelo, datos y logs |
| ONNX Runtime | Ejecución portable del modelo |
| FastAPI | API para usuario final |
| Docker | Empaquetado de la aplicación |
| GHCR | Registro de imágenes Docker |
| Azure Container Apps | Despliegue cloud de endpoints dev/prod |

## Separación de ambientes

| Rama | Endpoint | Archivo de predicciones |
|---|---|---|
| dev | nutrition-advisor-dev | logs/predicciones_dev.txt |
| prod | nutrition-advisor-prod | logs/predicciones_prod.txt |
