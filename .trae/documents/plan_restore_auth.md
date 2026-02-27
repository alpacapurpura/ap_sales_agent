# Plan de Restauración de Autenticación y Sincronización (Clerk + Webhooks)

## Diagnóstico
El sistema presenta una pantalla en blanco tras el login debido a una **desincronización crítica entre Clerk, el Backend y el Frontend**.
1.  **Falta de Webhooks:** El backend no tiene endpoints para escuchar eventos de Clerk (`user.created`, `user.updated`). Esto impide que los usuarios se creen/actualicen en la base de datos local automáticamente.
2.  **Metadata Faltante:** Al no sincronizarse, el campo `publicMetadata.tenant_id` en Clerk (vital para el frontend) no se está estableciendo o actualizando.
3.  **Bloqueo en Frontend:** El componente `TenantGuard` bloquea el acceso a usuarios sin `tenant_id`, y al intentar redirigir a `/onboarding`, se produce un bucle o bloqueo porque dicha ruta también está protegida incorrectamente.

## Estrategia de Solución
Restauraremos el mecanismo de sincronización mediante Webhooks y ajustaremos el Frontend para manejar usuarios sin organización ("huérfanos") de manera elegante.

### 1. Backend: Implementación de Webhooks de Clerk
Crearemos un módulo dedicado para manejar la sincronización de usuarios de manera segura y eficiente.

- **Nuevo Archivo:** `backend/src/modules/iam/api/webhooks.py`
  - Implementación de verificación de firma con `svix`.
  - Manejo de eventos: `user.created`, `user.updated`, `user.deleted`.
  - Lógica de sincronización: Crear/Actualizar usuario en tabla `users`.
  - **Nota:** No asignaremos tenants automáticamente (respetando la regla de negocio "solo Admin crea tenants"), pero aseguraremos que el usuario exista en la BD para futuras asignaciones.

- **Registro en Main:**
  - Actualizar `backend/src/main.py` para incluir el router de webhooks bajo `/api/v1/webhooks`.

### 2. Frontend: Desbloqueo de Ruta de Onboarding
Permitiremos que los usuarios sin tenant accedan a una página de aterrizaje segura en lugar de quedar en el limbo.

- **Ajuste de Middleware:**
  - Modificar `frontend/src/middleware.ts` para excluir `/onboarding` de la protección estricta de tenant (manteniendo la autenticación de Clerk).
- **Ajuste de TenantGuard:**
  - Modificar `frontend/src/components/auth/tenant-guard.tsx` para permitir el paso si la ruta actual es `/onboarding`.
- **Creación de Página de Onboarding:**
  - Crear `frontend/src/app/(main)/onboarding/page.tsx` con un mensaje claro: "Bienvenido. Tu cuenta ha sido creada. Por favor contacta al administrador para que te asigne una organización." (O un botón de "Crear Organización" si decidimos habilitarlo para ciertos roles en el futuro).

### 3. Verificación
- Iniciar sesión con un usuario nuevo -> Verificar creación en BD Backend.
- Iniciar sesión con usuario existente -> Verificar actualización de datos.
- Acceso sin tenant -> Debe mostrar página de Onboarding, no blanco.

## Archivos Afectados
1.  `backend/src/modules/iam/api/webhooks.py` (Nuevo)
2.  `backend/src/main.py`
3.  `frontend/src/middleware.ts`
4.  `frontend/src/components/auth/tenant-guard.tsx`
5.  `frontend/src/app/(main)/onboarding/page.tsx` (Nuevo)

## Dependencias Nuevas
- Backend: `svix` (para verificar firmas de Clerk).
