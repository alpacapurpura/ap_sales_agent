# Solución para Auditoría Vacía

El problema es idéntico al que corregimos en el módulo de Avatares: las peticiones API del módulo de Auditoría (`audit.ts`) **no están enviando el token de autenticación**. Aunque existen 10 mensajes en la base de datos para tu tenant, el backend rechaza las peticiones del frontend con un error `403 Forbidden` porque el cliente no se identifica.

## Pasos de Implementación

### 1. Refactorizar Cliente API (`frontend/src/lib/api/audit.ts`)
Actualizaré todas las funciones del módulo de auditoría para requerir y enviar el token de Clerk.

-   **Importar:** `fetchClient` (para manejo de errores estandarizado).
-   **Actualizar Funciones:**
    -   `useAuditUsers` -> Inyectar token.
    -   `useUserDetails` -> Inyectar token.
    -   `useUserTimeline` -> Inyectar token.
    -   `useTraceDetails` -> Inyectar token.
    -   `clearUserHistory` -> Inyectar token.

### 2. Actualizar Componentes UI (`frontend/src/components/audit/...`)
Modificaré los componentes que consumen estos hooks para obtener el token mediante `useAuth` y pasarlo a las funciones API.

-   **`UserList`** (`user-list.tsx`): Actualizar llamada a `useAuditUsers`.
-   **`ChatTimeline`** (`chat-timeline.tsx`): Actualizar llamada a `useUserTimeline` y `useUserDetails`.
-   **`TraceInspector`** (`trace-inspector.tsx`): Actualizar llamada a `useTraceDetails`.

### 3. Verificación
1.  Recargar la página de Auditoría.
2.  Confirmar que se carga la lista de usuarios en el panel izquierdo.
3.  Al seleccionar un usuario, verificar que aparece el historial de conversaciones.

**Nota:** Este es un patrón recurrente. Estoy corrigiendo módulo por módulo según lo reportas, pero la solución de fondo (inyectar el token) es la misma.
