
# Solución al Bucle de Redireccionamiento de Clerk

El error "infinite redirect loop... keys do not match" ocurre principalmente por dos razones en entornos Dockerizados con dominios personalizados (`salesagent.local`):

1.  **Desincronización de Llaves (Build vs Runtime):** `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` se "quema" en la imagen de Docker al momento de construirla (build time). Si cambiaste la llave en el `.env` pero no reconstruiste la imagen desde cero, el Frontend (navegador) usa la llave vieja y el Backend (servidor Next.js) usa la llave nueva del `.env`. Esto causa que el token sea inválido.
2.  **Falta de URLs Explícitas:** Al usar un dominio `.local`, Clerk necesita saber explícitamente a dónde redirigir, ya que la detección automática puede fallar detrás de un proxy (Traefik).

## Plan de Acción

1.  **Configurar URLs de Clerk:** Agregaré las variables de entorno `NEXT_PUBLIC_CLERK_SIGN_IN_URL`, `_SIGN_UP_URL`, etc., al archivo `.env` para forzar el comportamiento correcto.
2.  **Permitir Origen Local:** Actualizaré `frontend/next.config.js` para permitir `salesagent.local` como origen de desarrollo válido (eliminando la advertencia de los logs).
3.  **Reconstrucción Forzada:** Ejecutaré `docker compose up -d --build` para asegurar que la llave pública actual se inyecte correctamente en el build del frontend.
