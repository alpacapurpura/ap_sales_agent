# Clerk JWT: Agregar email claim

## Problema

El backend hace un HTTP call a `api.clerk.com/v1/users/{id}` por cada request
porque el JWT no contiene el email del usuario. Esto agrega 100-500ms de latencia
por request (4+ calls por page load = 400-2000ms desperdiciados).

Log indicador: `fetching_email_from_clerk_api_fallback` en los logs del backend.

## Fix (Clerk Dashboard)

1. Ir a [Clerk Dashboard](https://dashboard.clerk.com/) → **Sessions** → **Customize session token**
2. En el editor JSON, agregar:
   ```json
   {
     "email": "{{user.primary_email_address}}"
   }
   ```
3. Click **Save**

## Verificación

1. Cerrar sesión y volver a entrar en la app
2. Revisar logs del backend: `docker logs visionarias_brain_dev --tail 50`
3. NO debe aparecer `fetching_email_from_clerk_api_fallback`
4. NO debe aparecer `HTTP Request: GET https://api.clerk.com/v1/users/`

## Código relacionado

- Backend fallback: `backend/src/modules/iam/api/dependencies.py` líneas 156-191
- El fallback extrae email desde Clerk API cuando el JWT no lo incluye
