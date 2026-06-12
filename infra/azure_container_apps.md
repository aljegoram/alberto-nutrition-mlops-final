# Guía de infraestructura — Azure Container Apps

## 1. Recursos propuestos

| Recurso | Nombre sugerido |
|---|---|
| Resource Group | `rg-nutrition-mlops-final` |
| Storage Account | usar el existente o uno nuevo |
| Blob Container | `data` |
| Container Apps Environment | `cae-nutrition-mlops` |
| Container App DEV | `nutrition-advisor-dev` |
| Container App PROD | `nutrition-advisor-prod` |

## 2. Crear Container Apps Environment

```bash
az extension add --name containerapp --upgrade

az group create \
  --name rg-nutrition-mlops-final \
  --location brazilsouth

az containerapp env create \
  --name cae-nutrition-mlops \
  --resource-group rg-nutrition-mlops-final \
  --location brazilsouth
```

## 3. Crear aplicaciones iniciales

Se puede crear con una imagen pública temporal. Luego GitHub Actions actualizará la imagen real.

```bash
az containerapp create \
  --name nutrition-advisor-dev \
  --resource-group rg-nutrition-mlops-final \
  --environment cae-nutrition-mlops \
  --image mcr.microsoft.com/azuredocs/containerapps-helloworld:latest \
  --target-port 80 \
  --ingress external

az containerapp create \
  --name nutrition-advisor-prod \
  --resource-group rg-nutrition-mlops-final \
  --environment cae-nutrition-mlops \
  --image mcr.microsoft.com/azuredocs/containerapps-helloworld:latest \
  --target-port 80 \
  --ingress external
```

## 4. Obtener URLs

```bash
az containerapp show \
  --name nutrition-advisor-dev \
  --resource-group rg-nutrition-mlops-final \
  --query properties.configuration.ingress.fqdn \
  -o tsv

az containerapp show \
  --name nutrition-advisor-prod \
  --resource-group rg-nutrition-mlops-final \
  --query properties.configuration.ingress.fqdn \
  -o tsv
```

## 5. Service Principal para GitHub Actions

```bash
az ad sp create-for-rbac \
  --name sp-github-nutrition-mlops \
  --role contributor \
  --scopes /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/rg-nutrition-mlops-final \
  --sdk-auth
```

El JSON resultante se guarda como secret de GitHub:

```text
AZURE_CREDENTIALS
```

## 6. Nota de seguridad

No subir cadenas de conexión a GitHub. Usarlas solo como secretos de GitHub Actions y secretos de Azure Container Apps.
