---
name: production-deployer
description: Skill oficial para realizar pases a producción seguros en Visionarias. Gestiona despliegues locales y vía GitHub Actions, asegurando integridad de datos (BD), salud del frontend y generación de changelogs de negocio.
---

# Guía de Despliegue a Producción (Visionarias)

Esta habilidad guía el proceso crítico de llevar cambios al entorno productivo. Sigue estrictamente los pasos para evitar caídas o pérdida de datos.

## Paso 1: Selección de Método (OBLIGATORIO)

**PREGUNTA AL USUARIO:** "¿Deseas realizar el despliegue mediante **GitHub Actions** (CI/CD Automático) o de forma **Local** (Manual en Servidor)?"

- Si la respuesta es **Local**: Ve al Paso 2.
- Si la respuesta es **GitHub Actions**: Ve al Paso 3.

---

## Paso 2: Despliegue Local (Trigger desde Laptop)

Este método utiliza un script local que orquesta el despliegue en el servidor remoto siguiendo el estándar **Push -> Pull**.

### 2.1 Verificación Previa (Safety Checks)
Ejecuta las siguientes validaciones antes de tocar nada:
1. **Estado del Repositorio**: Asegúrate de estar en `main` y sin cambios pendientes.
   ```bash
   git status
   ```
2. **Sincronización**: Debes hacer PUSH de tus cambios locales antes de desplegar. El servidor hará PULL de `origin/main`.
   ```bash
   git push origin main
   ```

### 2.2 Ejecución del Script Maestro
El framework de despliegue se encuentra en `despliegue/local`.
Ejecuta el script de despliegue que:
1. Verifica commits pendientes.
2. Sube `.env.prod` (secretos) por SCP.
3. Se conecta por SSH y hace `git pull`.
4. Ejecuta el build y migraciones en el servidor.

```bash
./despliegue/local/deploy_local.sh
```

### 2.3 Validación Post-Despliegue
- El script verificará automáticamente:
  - **Status**: Contenedores `visionarias_brain` (API) y `visionarias_client` (Frontend) corriendo.
  - **Health**: Endpoints `/health` respondiendo 200 OK.
  - **DB**: Migraciones aplicadas (o sincronizadas con `stamp head` si ya existían tablas).

**Resolución de Problemas Comunes:**
1. **Migraciones Fallidas**: Si Alembic dice "relation already exists", el script intentará `alembic stamp head` automáticamente. Si falla, revisar logs de `backend`.
2. **Git Auth en Servidor**: El servidor debe tener acceso a GitHub (SSH Key o Token) para hacer `git pull`. El script asume que esto está configurado.
3. **Docker Build**: En producción, las imágenes se construyen localmente en el servidor (`build: .`) usando el código actualizado por git.

---

## Paso 3: Despliegue vía GitHub Actions

Este método utiliza workflows automatizados en la nube.

### 3.1 Configuración de Secretos
Asegúrate de que el repositorio tenga configurados los siguientes secretos:
- `SSH_HOST`, `SSH_USER`, `SSH_KEY` (Para acceso al servidor).
- `DATABASE_URL` (Para tests de integración).
- `OPENAI_API_KEY` (Si los tests lo requieren).

### 3.2 Disparo del Workflow
- Haz un push a la rama `main` para iniciar el despliegue.
- Monitorea el progreso en la pestaña "Actions" de GitHub.
- Los workflows están definidos en `despliegue/github_actions/`.

---

## Paso 4: Generación de Changelog de Negocio

Independientemente del método, debes generar un resumen de cambios para los stakeholders.
Usa el template en `despliegue/CHANGELOG_TEMPLATE.md` y llénalo con información de los commits recientes.

**Reglas de Negocio para el Log:**
- Traduce términos técnicos a valor para el usuario.
- Agrupa por: ✨ Nuevas Funcionalidades, 🐛 Correcciones, 🔧 Mejoras Técnicas.
- Ejemplo: "feat: add auth" -> "✨ Ahora los usuarios pueden iniciar sesión de forma segura."

## Recursos del Framework
- **Scripts Locales**: `despliegue/local/`
- **Workflows GitHub**: `despliegue/github_actions/`
- **Tests de Integridad**: `despliegue/tests/pre-deploy-check.py`
