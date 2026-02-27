Tienes toda la razón, es una excelente observación.

Si mantenemos `target: dev` fijo, el perfil `production` levantaría la versión de desarrollo (lenta y pesada), lo cual **no es correcto** para un entorno productivo real.

Para solucionar esto y que `--profile production` funcione como esperas (imagen optimizada, sin hot-reload), debemos **separar la definición del servicio** en el `docker-compose.yml`.

### Plan Actualizado

#### 1. `frontend/Dockerfile` (Multi-Stage)
Crearé el Dockerfile con las etapas: `base`, `deps`, `dev`, `builder`, `runner`.

#### 2. `docker-compose.yml` (Separación de Servicios)
Dividiré el servicio `client_dashboard` en dos definiciones distintas para evitar conflictos:

*   **Servicio 1: `client_dashboard_dev`**
    *   **Profile**: `development`
    *   **Target**: `dev`
    *   **Volúmenes**: Monta `./frontend:/app` (Hot Reload activado).
    *   **Comando**: `npm run dev`.
    *   **Container Name**: `visionarias_client_dev`

*   **Servicio 2: `client_dashboard_prod`**
    *   **Profile**: `production`
    *   **Target**: `runner`
    *   **Volúmenes**: Sin volúmenes de código (solo caché si es necesario).
    *   **Comando**: Ejecuta el servidor optimizado (`server.js`).
    *   **Container Name**: `visionarias_client`

### ¿Qué implica esto?
1.  **Desarrollo**: Ejecutas `docker compose --profile development up` -> Levanta la versión con hot-reload.
2.  **Producción**: Ejecutas `docker compose --profile production up` -> Levanta la versión compilada, ligera y rápida.

¿Te parece bien esta separación explícita para garantizar el mejor rendimiento en ambos escenarios?
