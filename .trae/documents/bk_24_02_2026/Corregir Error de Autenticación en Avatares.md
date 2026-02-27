# Corrección de Error 403 en Módulo de Avatares

He detectado que el error "Error al cargar los avatares" se debe a que el frontend **no está enviando el token de autenticación** en las peticiones a la API de Avatares, lo que provoca un rechazo `403 Forbidden` por parte del backend.

He verificado que tu usuario `alpacapurpura@gmail.com` existe en la base de datos y tiene los permisos correctos, por lo que el problema es puramente de comunicación entre el cliente y el servidor.

## Pasos de Implementación

### 1. Refactorizar Cliente API (`frontend/src/lib/api/avatar.ts`)
Actualizaré todas las funciones de `avatarApi` para requerir un `token` y enviarlo en los headers, estandarizándolo con el resto de la aplicación (como `admin.ts`).

-   **Cambio:** Agregar argumento `token: string` a `listAvatars`, `createAvatar`, etc.
-   **Header:** Incluir `Authorization: Bearer ${token}` en cada `fetch`.

### 2. Actualizar Componente UI (`frontend/src/app/(dashboard)/avatars/page.tsx`)
Modificaré la página para obtener el token de sesión actual usando Clerk y pasarlo al cliente API.

-   **Hook:** Integrar `useAuth` de `@clerk/nextjs`.
-   **Query:** Actualizar `useQuery` para obtener el token antes de llamar a `listAvatars`.
-   **Mutations:** Actualizar las funciones de `create`, `update`, `delete` y `setDefault` para inyectar el token dinámicamente.

## Verificación
1.  Recargar la página de Avatares.
2.  Confirmar que desaparece el mensaje de error y se muestra la lista (o el estado vacío).
3.  Verificar en los logs del backend que la petición retorna `200 OK`.
