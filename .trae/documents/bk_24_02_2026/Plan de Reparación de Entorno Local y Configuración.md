# Plan de Diagnóstico y Reparación de Configuración Local

## Diagnóstico
El problema de "Cargando..." infinito se debe a un **Bloqueo de Contenido Mixto (Mixed Content)** y/o problemas de conectividad Cross-Origin.
1.  Estás accediendo localmente por `http://salesagent.local` (HTTP).
2.  El frontend intenta conectarse a la API por `https://api.laptopchris.alpacapurpura.lat` (HTTPS, vía Cloudflare).
3.  El navegador bloquea solicitudes de HTTP a HTTPS o fallan por CORS/Latencia del túnel.
4.  Además, el contenedor `api_dev` no tiene la etiqueta de Traefik para `api.salesagent.local`, por lo que si intentaras usar esa URL local, fallaría.

## Pasos de Ejecución

### 1. Corrección de Variables de Entorno (.env)
Ajustaremos la configuración para que el entorno local sea **puramente local**, eliminando la dependencia de Cloudflare para el desarrollo diario (excepto para los webhooks que sí lo requieren).
-   **Acción**: Cambiar `NEXT_PUBLIC_API_URL` a `http://localhost:8000`.
    -   *Por qué*: Esto permite que tu navegador (Chrome/Edge) conecte directamente al contenedor de la API expuesto en el puerto 8000, sin pasar por internet ni túneles, resolviendo el problema de "Cargando" inmediatamente.

### 2. Actualización de Docker Compose
Añadiremos soporte para `api.salesagent.local` en Traefik, por si decides usar ese dominio en el futuro (y para consistencia con `salesagent.local`).
-   **Acción**: Agregar etiqueta `traefik.http.routers.visionarias_api_local.rule=Host(\`api.salesagent.local\`)` al servicio `api_dev`.

### 3. Limpieza de Código Hardcodeado
Eliminaremos la lógica frágil que intenta "adivinar" la URL y las listas estáticas de dominios.
-   **Frontend (`src/lib/config.ts`)**: Simplificar para usar estrictamente la variable de entorno.
-   **Backend (`src/main.py`)**: Limpiar la lista `default_origins` y asegurar que se respeten las variables de configuración.

### 4. Verificación de Calidad y Reinicio
-   **Ruff**: Ejecutaré `ruff check src --fix` dentro del contenedor para corregir cualquier problema de sintaxis o importación en Python.
-   **Reinicio**: Reiniciar los contenedores para aplicar los cambios de `.env` y `docker-compose.yml`.

### Resultado Esperado
-   Al entrar a `http://salesagent.local`, el frontend cargará instantáneamente conectándose a `http://localhost:8000`.
-   Los webhooks de Telegram/Google seguirán funcionando a través de la URL de Cloudflare (que sigue configurada en `API_DOMAIN` y el túnel).
