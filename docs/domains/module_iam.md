---
module: IAM
status: active
---

# IAM (Identity & Access Management)

Autenticacion, autorizacion y aislamiento multi-tenant. Orquesta la relacion entre Clerk (identidad externa) y la DB local (autorizacion y datos de negocio).

## Domain Concepts

- **Auth Sandwich**: 3 capas — Clerk (identidad/JWT), Webhooks (sync a DB local), Backend (autorizacion por `user_tenants`).
- **`clerk_id`**: Vinculo inmutable entre Clerk y la tabla `users`. Si el webhook de sync falla, el usuario existe en Clerk pero no en DB -> **403** en la API.

## Architecture Decisions

- **Resolucion de tenant (prioridad)**: (1) Header `X-Tenant-ID` (UUID o slug), (2) Primer tenant activo del usuario en `user_tenants`.
- **Sync oportunista**: `get_user_from_token` sincroniza `clerk_id` y `full_name` si difieren del token. Si el email no esta en el JWT, hace fallback a Clerk API (lento pero funcional).
- **ContextVars**: `tenant_id` se propaga via `src.core.context.set_tenant_id()` para logs y auditoria sin pasar argumentos explicitos.

## Business Rules

- Todo request autenticado resuelve a un User + Tenant. Sin tenant -> 403.
- La verificacion de acceso al tenant es estricta: se valida en `user_tenants` que el link este `is_active=True`.
- Usuarios sin tenant son redirigidos al flujo de Onboarding (`/onboarding`).

## Edge Cases

- **Desincronizacion Clerk vs DB**: Frontend verifica `publicMetadata.tenant_id` en Clerk; backend verifica `user_tenants`. Si el webhook de metadata falla, pueden divergir (acceso en uno, denegado en otro).
- **Cache pollution en frontend**: Usuario cambia de Tenant A a B, React Query devuelve datos cacheados de A. Solucion: `fetchClient` agrega `?_t={tenant_id}` como cache buster.
- **Navegacion cross-tenant manual**: Cambiar el ID en la URL devuelve 403; frontend redirige a `/forbidden`.

## CRITICAL -- Do Not Violate

- `clerk_id` es inmutable una vez asignado. Nunca reasignarlo a otro usuario.
- Toda query de datos DEBE filtrar por `tenant_id`. Sin excepcion.
- Nunca exponer el JWT completo o `clerk_id` en response bodies publicos.
