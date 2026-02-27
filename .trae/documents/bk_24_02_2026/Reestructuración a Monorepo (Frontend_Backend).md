# Plan de Reestructuración: Monorepo (Frontend/Backend)

Sí, es **muy conveniente** separar el proyecto en dos carpetas padres (`frontend` y `backend`). Esta estructura "Monorepo" es el estándar industrial porque:
1.  **Separación de Responsabilidades**: Evita mezclar configuraciones de Node.js con Python.
2.  **Limpieza**: La raíz solo contiene orquestación (`docker-compose.yml`) y variables globales (`.env`).
3.  **CI/CD**: Facilita crear pipelines de despliegue independientes.

## Pasos de Implementación

### 1. Crear Estructura de Directorios
Crearemos la carpeta `backend` y moveremos los activos del "cerebro" (Brain) allí.

**Nueva Estructura Propuesta:**
```text
/ (root)
├── docker-compose.yml   # Orquestador Global
├── .env                 # Secretos Globales
├── data/                # Volúmenes de BD (Postgres, Redis, Qdrant)
├── frontend/            # Next.js App
└── backend/             # FastAPI App
    ├── src/             # Código Fuente
    ├── scripts/         # Tests y utilidades
    ├── cloudflare/      # Configuración de Túnel
    ├── model_cache/     # Modelos de Embeddings
    ├── Dockerfile       # Definición de Imagen
    ├── requirements.txt # Dependencias
    └── .dockerignore    # Ignorados de Docker
```

### 2. Mover Archivos
Ejecutaremos comandos para mover las carpetas y archivos actuales a `backend/`.
*   `src/` -> `backend/src/`
*   `scripts/` -> `backend/scripts/`
*   `cloudflare/` -> `backend/cloudflare/`
*   `model_cache/` -> `backend/model_cache/`
*   `Dockerfile`, `requirements.txt`, `.dockerignore` -> `backend/`

### 3. Actualizar `docker-compose.yml`
Modificaremos las rutas de construcción y volúmenes para que apunten a la nueva carpeta `backend`.

**Cambios Clave:**
*   **Contexto de Build**: `build: .` pasará a `build: ./backend`.
*   **Volúmenes de Código**: `.:/app` pasará a `./backend:/app`.
*   **Cloudflare Tunnel**: `./cloudflare/...` pasará a `./backend/cloudflare/...`.

### 4. Verificación
*   Reconstruiremos los contenedores (`docker compose up -d --build`).
*   Verificaremos que el "Hot Reload" del backend siga funcionando (al editar archivos en `backend/src`).

¿Apruebas este plan de reestructuración?