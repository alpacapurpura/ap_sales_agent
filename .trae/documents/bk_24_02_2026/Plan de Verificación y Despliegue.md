# Plan de Verificación y Despliegue (Corregido)

Entendido. Ajusto el plan para adherirme estrictamente a las reglas de desarrollo (`docker-dev-rules.md`), específicamente usando el perfil `development`.

## 1. Verificación de Código (Linting & Fixes)
*   **Backend (Python)**: Ejecutar `ruff check backend/src --fix` para asegurar calidad de código en los nuevos módulos de WhatsApp (`src/api/routers/whatsapp.py`, `src/channels/whatsapp.py`, `src/main.py`).
*   **Frontend (Next.js)**: Ejecutar `npm run lint` en `frontend/` para validar los componentes React creados.

## 2. Despliegue de Infraestructura
*   **Levantamiento**: Ejecutar el comando oficial de desarrollo:
    ```bash
    docker compose --profile development up -d --build
    ```
    Esto levantará `whatsapp_engine` junto con `api_dev`, `client_dashboard_dev` y bases de datos, ignorando los servicios de producción.

## 3. Verificación de Salud (Health Check)
*   **Estado de Contenedores**: Verificar que `visionarias_whatsapp` (nuevo) y `visionarias_brain_dev` estén `Up`.
*   **Logs**: Revisar logs de arranque de la API (`docker logs visionarias_brain_dev`) para confirmar que el router de WhatsApp se cargó sin errores.

## 4. Testing Funcional Rápido (Smoke Test)
*   **Prueba de Conectividad**: Ejecutar un script simple (o `curl`) contra `http://localhost:8000/api/v1/whatsapp/status` (simulando auth o verificando respuesta 401/403 que indica que el endpoint existe).
*   **Frontend**: Confirmar que la compilación de Next.js (`visionarias_client_dev`) finalizó exitosamente.

Procederé con la ejecución inmediata de este flujo.