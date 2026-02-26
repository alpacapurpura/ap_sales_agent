# Despliegue con GitHub Actions (CI/CD Automático)

Este método automatiza todo el proceso de construcción y despliegue cada vez que haces un `push` a la rama `main` en GitHub. Es la forma profesional de desplegar, pero requiere configuración de secretos y uso de minutos de GitHub Actions (o un Self-Hosted Runner).

## Archivos Relacionados

1.  **Workflow**: `.github/workflows/ci-cd.yml` (Define los pasos del pipeline).
2.  **Script Remoto**: `despliegue/github_actions/deploy.sh` (Este script se copia y ejecuta en el servidor).

## Configuración de Secretos

Para que GitHub pueda acceder a tu servidor y desplegar, debes configurar los siguientes secretos en tu repositorio (Settings -> Secrets and variables -> Actions):

| Secreto | Descripción | Valor |
| :--- | :--- | :--- |
| `SSH_HOST` | IP del servidor | `161.132.41.191` |
| `SSH_USER` | Usuario SSH | `root` |
| `SSH_PORT` | Puerto SSH | `22022` |
| `SSH_KEY` | Tu llave privada SSH | Contenido de `id_rsa` |
| `GHCR_PAT` | Token de Acceso Personal | Token de GitHub con permiso `read:packages` |
| `PROD_ENV_FILE` | Archivo .env completo | Copia todo el contenido de tu `.env.prod` local |
| `NEXT_PUBLIC_...` | Variables de Frontend | `NEXT_PUBLIC_API_URL`, etc. |

## Cómo Desplegar

Simplemente haz un cambio en tu código, haz commit y push a `main`:

```bash
git add .
git commit -m "feat: nueva funcionalidad"
git push origin main
```

## Monitoreo

1.  Ve a la pestaña **"Actions"** en tu repositorio de GitHub.
2.  Verás el flujo de trabajo en ejecución.
3.  Haz clic en el nombre del commit para ver los detalles.
4.  Si algo falla (círculo rojo), haz clic en el paso fallido para ver los logs y corregir el error.

### Solución de Problemas Comunes

*   **"Payment Failed"**: Si te quedaste sin minutos gratuitos, usa el método de **Despliegue Local** (`despliegue/local/`) o configura un Self-Hosted Runner en tu servidor para seguir usando este método gratis.
