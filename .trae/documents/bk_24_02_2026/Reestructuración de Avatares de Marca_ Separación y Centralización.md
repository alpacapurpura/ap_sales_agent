Voy a proceder con la reestructuración completa del sistema de Avatares para separarlo del Ecosistema de Ofertas y hacerlo un módulo independiente y reutilizable.

### 1. Backend: Nueva API de Avatares
Implementaré la lógica de negocio real que actualmente está mockeada.
*   **Repositorio (`AvatarRepository`)**: Crearé `src/services/db/repositories/avatar.py` para manejar las operaciones en la base de datos (CRUD y gestión de `is_default`).
*   **Router (`avatars.py`)**: Crearé `src/api/routers/avatars.py` con los endpoints:
    *   `GET /avatars`: Listar todos los avatares disponibles.
    *   `POST /avatars`: Crear nuevo avatar.
    *   `PUT /avatars/{id}`: Actualizar configuración (ICP, Anti-Avatar, Voz).
    *   `POST /avatars/{id}/set_default`: Marcar como principal.
*   **Registro**: Integraré el nuevo router en la aplicación principal (`main.py`).

### 2. Frontend: Nuevo Módulo "Avatares de Marca"
Crearé una sección dedicada en el dashboard para gestionar la identidad de marca.
*   **Cliente API**: Crearé `src/lib/api/avatar.ts` para conectar con los nuevos endpoints.
*   **Páginas**:
    *   `src/app/(dashboard)/avatars/page.tsx`: Vista de cuadrícula con todos los avatares. Indicador visual del "Principal".
    *   `src/app/(dashboard)/avatars/new/page.tsx` y `[id]/page.tsx`: Formulario reutilizable para editar la identidad.
*   **Sidebar**: Actualizaré `src/components/layout/app-sidebar.tsx` para agregar la entrada "Avatares" (Icono: Users).

### 3. Frontend: Integración en Oferta
Modificaré el flujo de edición de ofertas para usar selección en lugar de creación.
*   **Selector de Avatar**: En `src/app/(dashboard)/offer-studio/offer/[id]/avatar/page.tsx`, reemplazaré el formulario actual por un selector (Dropdown/Cards) que lista los avatares existentes.
*   **Lógica de Negocio**: Al seleccionar un avatar, se actualizará el `avatar_id` del producto. Por defecto, pre-seleccionará el avatar marcado como `is_default`.

Esta arquitectura permite que múltiples ofertas compartan el mismo "Avatar Principal" y centraliza la gestión de la identidad de marca, mejorando la UX y la mantenibilidad.
