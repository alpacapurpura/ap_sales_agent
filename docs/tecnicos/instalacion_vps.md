# Guía de Instalación en VPS (Ubuntu) - Visionarias Brain

Esta guía detalla el proceso paso a paso para desplegar la solución **Visionarias Brain** en un servidor VPS con Ubuntu, integrándose con un Traefik existente en la red `web_gateway`.

## 1. Prerrequisitos del Servidor

Asegúrate de que tu VPS cumpla con lo siguiente:

1.  **Docker & Docker Compose** instalados (v2.0+).
2.  **Git** instalado.
3.  **Red de Traefik**: Debe existir una red externa llamada `web_gateway` (o el nombre que uses para tu reverse proxy).
    *   *Verificar:* `docker network ls` (debería aparecer `web_gateway`).
    *   *Si no existe y usas otro nombre:* Anótalo, lo necesitarás en el paso 4.

## 2. Clonar el Repositorio

Accede a tu servidor vía SSH y clona el proyecto en la ruta deseada (ej. `/opt` o `/home/usuario`).

```bash
cd /ubicacion/deseada
git clone <URL_TU_REPOSITORIO_GITHUB> aisalesht
cd aisalesht
```

> **Nota:** Al clonar desde GitHub, las carpetas de datos (`data/`) y los archivos de entorno (`.env`) **NO** se descargarán porque están en el `.gitignore`. Debemos crearlos manualmente.

## 3. Preparación de Directorios y Permisos

Como las carpetas de persistencia no existen, Docker las creará como `root` si no las preparamos, lo que puede causar problemas de permisos.

Ejecuta el siguiente bloque de comandos para crear la estructura necesaria:

```bash
# Crear carpetas de datos persistentes
mkdir -p data/redis_data
mkdir -p data/qdrant_data
mkdir -p data/postgres_data

# (Opcional pero recomendado) Ajustar permisos para evitar conflictos de escritura
# Esto permite que los contenedores escriban sin problemas en los volúmenes mapeados
chmod -R 775 data/
```

> **Importante:** Verifica que la carpeta `model_cache/` sí se haya descargado (ya que **no** está en gitignore).
> `ls -la model_cache` (Debería mostrar carpetas de modelos).

## 4. Configuración del Entorno (.env)

Debes crear el archivo de variables de entorno para producción.

1.  Crea el archivo `.env`:
    ```bash
    nano .env
    ```

2.  Pega el siguiente contenido (Ajusta los valores con tus credenciales reales):

    ```ini
    # --- CONFIGURACIÓN DE PRODUCCIÓN ---
    
    # Perfil de Docker (Indispensable para activar Prod)
    PROFILE=production
    PROJECT_NAME="Visionarias Brain (PROD)"
    
    # Dominios (Deben apuntar a la IP de este VPS en tu DNS)
    API_DOMAIN=api_visionarias.alpacapurpura.lat
    DASHBOARD_DOMAIN=visionarias.alpacapurpura.lat
    
    # Red de Traefik existente (Crucial para exponer los servicios)
    TRAEFIK_NETWORK=web_gateway
    
    # Nivel de Log
    LOG_LEVEL=INFO
    
    # --- SEGURIDAD Y CREDENCIALES (CAMBIAR ESTO) ---
    API_SECRET_KEY=tu_secreto_super_seguro_produccion_2026
    
    # Proveedor de IA
    AI_PROVIDER=openai
    OPENAI_API_KEY=sk-proj-TU-CLAVE-REAL...
    OPENAI_MODEL=gpt-4-turbo-preview
    OPENAI_EMBEDDING_MODEL=text-embedding-3-large
    
    # Base de Datos (Postgres)
    POSTGRES_USER=visionarias_user
    POSTGRES_PASSWORD=tu_password_db_seguro
    POSTGRES_DB=visionarias_prod
    POSTGRES_HOST=postgres
    POSTGRES_PORT=5432
    
    # Redis & Qdrant (Internos)
    REDIS_URL=redis://redis:6379/0
    QDRANT_URL=http://qdrant:6333
    QDRANT_API_KEY= # Dejar vacío si usas la versión community interna sin auth, o configurar
    QDRANT_COLLECTION=visionarias_knowledge_prod
    
    # Prompt Source (Usar 'file' o 'db')
    PROMPT_SOURCE=file
    ```

3.  Guarda y sal (`Ctrl+O`, `Enter`, `Ctrl+X`).

## 5. Despliegue (Deploy)

Ahora levantarás los servicios usando el perfil de producción. Esto:
1.  Levantará `app` (Brain), `admin` (Dashboard), `redis`, `qdrant`, `postgres`.
2.  **NO** levantará el túnel de Cloudflare (porque es solo para dev).
3.  Conectará los servicios a la red `web_gateway`.

Ejecuta:

```bash
docker compose --profile production up -d --build
```

*   `--profile production`: Activa los servicios marcados para prod.
*   `-d`: Detached mode (segundo plano).
*   `--build`: Asegura que se construya la imagen localmente con el código más reciente y el `model_cache`.

## 6. Verificación

1.  **Estado de Contenedores:**
    ```bash
    docker compose ps
    ```
    Todos deberian estar en estado `Up` (o `running`).

2.  **Logs (en caso de error):**
    ```bash
    docker compose logs -f app
    ```
    Busca mensaje de "Application startup complete".

3.  **Acceso Web:**
    *   Ingresa a: `https://visionarias.alpacapurpura.lat`
    *   Deberías ver el Dashboard de Streamlit cargando (puede tardar unos segundos la primera vez).
    *   La conexión debe ser segura (HTTPS) gracias a que tu Traefik gestiona los certificados automáticamente.

## Solución de Problemas Comunes

*   **Error "Network not found":** Revisa que `TRAEFIK_NETWORK` en el `.env` coincida exactamente con el nombre de tu red externa (`docker network ls`).
*   **Permisos en `data/`:** Si Postgres falla al iniciar, puede ser permisos. Prueba `chown -R 999:999 data/postgres_data` (999 es el usuario default de postgres alpine).
*   **Modelos no cargan:** Verifica que la carpeta `model_cache` no esté vacía en el servidor. Si lo está, tendrás que subirla manualmente vía SCP o rsync, o dejar que el sistema intente descargar (esto último requerirá cambiar la configuración para no forzar caché local).
