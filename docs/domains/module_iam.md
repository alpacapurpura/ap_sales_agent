---
module: "IAM (Identity & Access Management)"
status: "active"
core_files:
  # BACKEND
  - "backend/src/modules/iam/domain/user.py"
  - "backend/src/modules/iam/infrastructure/models/user_tenant_model.py"
  - "backend/src/modules/iam/api/dependencies.py"
  # FRONTEND
  - "frontend/src/middleware.ts"
  - "frontend/src/components/auth/tenant-guard.tsx"
  - "frontend/src/lib/http-client.ts"
api_routes:
  - "GET /api/v1/auth/me"
  - "GET /api/v1/tenants/"
  - "POST /api/v1/tenants/"
  - "POST /api/v1/webhooks/clerk"
---

## 1. Propósito del Negocio (El "Por Qué")
Este módulo es el núcleo de seguridad y organización de la plataforma. Su propósito es gestionar la identidad de los usuarios (a través de Clerk), administrar la pertenencia a múltiples organizaciones (Tenants) y garantizar el **aislamiento estricto de datos**. Resuelve el problema de "quién es el usuario" y "qué datos puede ver", asegurando que un usuario nunca acceda a información de una organización a la que no pertenece, incluso si tiene una sesión válida.

## 2. Reglas de Negocio Estrictas (Business Rules)
Estas reglas son inquebrantables y están reforzadas por la base de datos y la lógica del dominio.

- **Regla 1 (Validación Dual):** Un token válido de Clerk **NO** es suficiente para acceder a la API; el usuario debe existir obligatoriamente en la tabla local `public.users`. Si no existe, se deniega el acceso (403).
- **Regla 2 (Aislamiento por Contexto):** Toda petición a recursos protegidos debe incluir el header `X-Tenant-ID`. El backend rechaza cualquier petición donde el usuario autenticado no tenga una relación activa (`UserTenant`) con el `tenant_id` proporcionado.
- **Regla 3 (Unicidad Global):** El `email` del usuario y el `slug` del Tenant son identificadores únicos globales en todo el sistema. No pueden existir duplicados.
- **Regla 4 (Inmutabilidad de Identidad):** El `clerk_id` es la fuente de verdad inmutable para la identidad. No se permite la modificación manual de este ID en la base de datos local.
- **Regla 5 (Jerarquía de Roles):** Los permisos se evalúan en el contexto del Tenant. Un usuario puede ser `admin` en la Organización A y `viewer` en la Organización B.

## 3. Mapa de Código (The "Where")
Ubicación exacta de la lógica crítica.

- **Backend (Dominio):** `backend/src/modules/iam/domain/` (Modelos `User`, `Tenant`)
- **Backend (API):** `backend/src/modules/iam/api/` (Routers y `dependencies.py` para auth)
- **Frontend (Estado/Hooks):** `frontend/src/features/settings/hooks/use-tenants.ts` (Sincronización de contexto)
- **Frontend (UI Principal):** `frontend/src/components/auth/tenant-guard.tsx` (Protección de rutas)
- **Base de Datos (Modelos):** `backend/src/modules/iam/infrastructure/models/` (Tablas `users`, `tenants`, `user_tenants`)

## 4. Casos Borde Conocidos (Edge Cases)
Escenarios complejos manejados por el sistema.

- **Usuario "Huérfano" (Sin Tenant):** Si un usuario se registra pero no ha creado ni sido invitado a ninguna organización, el `TenantGuard` lo redirige forzosamente al flujo de `/onboarding`.
- **Navegación Cross-Tenant:** Si un usuario intenta acceder manualmente a una URL de un tenant al que no pertenece (ej. cambiando el ID en la barra de direcciones), el backend devuelve `403 Forbidden` y el frontend lo redirige a su tenant por defecto o al login.
- **Desincronización de Webhook:** En el raro caso de que Clerk cree un usuario pero el webhook de sincronización falle, el usuario verá un error de "Cuenta no configurada" al intentar loguearse, requiriendo una resincronización manual o reintento del evento.
- **Tokens Caducados en Navegación:** El cliente HTTP intercepta errores `401` silenciosos y, gracias a la integración con Clerk, intenta refrescar el token en segundo plano antes de redirigir al login.
