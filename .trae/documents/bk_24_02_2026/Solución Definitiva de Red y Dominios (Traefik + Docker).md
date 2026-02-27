## 1. Sincronización de Variables de Entorno (.env)
- Actualizar `NEXT_PUBLIC_API_URL` a `http://api.salesagent.local`.
- Revisar y corregir todas las URLs de Clerk para asegurar que usen `http://salesagent.local`.
- Verificar que `TRAEFIK_NETWORK` coincida exactamente con `web_gateway_local`.

## 2. Refactorización de Docker Compose
- Asegurar que `visionarias_brain` (API) y `visionarias_client` (Next.js) estén en la red `gateway` (que apunta a `web_gateway_local`).
- Validar las etiquetas (labels) de Traefik para que coincidan con los nuevos dominios.

## 3. Configuración de CORS en Backend
- Buscar el archivo de configuración de FastAPI (normalmente `src/main.py`) y añadir los dominios `.local` a la lista de orígenes permitidos (`allow_origins`).

## 4. Limpieza de Caché y Reinicio
- Realizar un `docker compose down` y `up -d` para asegurar que Next.js tome las nuevas variables de entorno de Clerk y la API.
- Recomendar la limpieza de cookies de `localhost` y `salesagent.local` en el navegador para romper el loop de Clerk.