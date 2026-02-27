Voy a implementar una política de seguridad estricta para el acceso a Tenants, eliminando la auto-asignación y forzando una redirección a una página de error explicativa.

### 1. Backend: Restricción de Acceso (Error 403)
Modificaré `backend/src/api/dependencies.py` para:
-   **Eliminar** la lógica de creación automática de Tenants y asignación por defecto.
-   **Validar** estrictamente si `user.tenant_id` existe.
-   **Lanzar** una excepción `HTTP 403 Forbidden` si el usuario es "huérfano", con el mensaje exacto solicitado:
    > *"No tiene los permisos suficientes para acceder a las funciones. Por favor contáctese con el administrador de su organización o, si quiere adquirir una suscripción comuníquese a hola@alpacapurpura.lat"*

### 2. Frontend: Interceptor de Seguridad y Página de Error
Para manejar este error de forma elegante en la interfaz:

#### A. Nuevo Cliente HTTP (`src/lib/http-client.ts`)
Crearé un "wrapper" centralizado para `fetch` que:
-   Interceptará automáticamente todas las respuestas con status `403`.
-   Redirigirá al usuario a la ruta `/forbidden` sin necesidad de código repetitivo en cada componente.

#### B. Página de Acceso Denegado (`src/app/forbidden/page.tsx`)
Crearé una nueva página con diseño Shadcn UI que mostrará:
-   Icono de alerta/seguridad.
-   El mensaje amigable explicando la situación.
-   Botón para volver al inicio o cerrar sesión.

#### C. Actualización de Servicios API
Refactorizaré `src/lib/api/settings.ts` (y otros servicios relevantes) para usar este nuevo `fetchClient` en lugar del `fetch` nativo, asegurando que la protección aplique a toda la aplicación.