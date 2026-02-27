Voy a proceder con la limpieza del módulo "Avatares de Marca" obsoleto, asegurando que la nueva implementación en "Sobre la Marca" se mantenga intacta.

### Plan de Ejecución:

1.  **Actualizar Menú Lateral (`app-sidebar.tsx`)**:
    *   Eliminaré el ítem "Avatares de Marca" de la configuración de navegación en `frontend/src/components/layout/app-sidebar.tsx` para que desaparezca del menú principal.

2.  **Eliminar Rutas Obsoletas**:
    *   Borraré la carpeta `frontend/src/app/(dashboard)/avatars` y todo su contenido (`page.tsx`, `new/page.tsx`, `[id]/page.tsx`). Esto eliminará las páginas antiguas que ya no se usan.

3.  **Mantenimiento de Componentes**:
    *   **Conservaré** `frontend/src/components/avatars/avatar-form.tsx`, ya que este componente es vital y está siendo reutilizado por el nuevo `AvatarManager` en la sección "Sobre la Marca".
    *   **Conservaré** `frontend/src/components/brand/avatar-manager.tsx`, que contiene la nueva lógica centralizada.

Esta acción eliminará el acceso y el código de la sección antigua sin afectar la funcionalidad migrada, manteniendo una estructura de carpetas lógica donde los componentes de UI (`components/avatars`) están separados de las páginas de rutas (`app/...`).