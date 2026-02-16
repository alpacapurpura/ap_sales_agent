# Framework de Despliegue a Producción (Visionarias)

Este directorio contiene todas las herramientas, scripts y configuraciones necesarias para desplegar la aplicación de forma segura y consistente.

## Estructura del Framework

### 📂 `local/` (Despliegue Manual)
Scripts para ejecutar despliegues directamente en el servidor (`laptopchris`).
- **`deploy.sh`**: Script maestro. Realiza pull, tests, backup de BD, build y reinicio de contenedores.
  - **Seguridad**: Incluye `pg_dump` automático antes de cualquier cambio.
  - **Logs**: Genera `DEPLOY_CHANGELOG.md` basado en commits.

### 📂 `github_actions/` (CI/CD Automático)
Workflows para GitHub Actions.
- **`ci.yml`**: Ejecuta linter y tests en cada Pull Request.
- **`cd.yml`**: Construye imágenes Docker y despliega a producción al hacer push a `main`.

### 📂 `tests/` (Verificación)
Scripts de salud y pre-requisitos.
- **`pre-deploy-check.py`**: Verifica variables de entorno, conexión a BD y estructura del frontend antes de iniciar el despliegue.

## Cómo Usar

1. **Para Despliegue Local**:
   ```bash
   ./despliegue/local/deploy.sh
   ```

2. **Para GitHub Actions**:
   Configura los secretos en el repositorio y haz push a la rama `main`.

3. **Generar Changelog**:
   El script local lo genera automáticamente. Para GitHub, revisa la salida del workflow o usa el template `CHANGELOG_TEMPLATE.md`.

---
*Mantenido por el equipo de Visionarias AI.*
