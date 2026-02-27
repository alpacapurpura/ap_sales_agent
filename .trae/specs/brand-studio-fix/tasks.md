# Tareas de Implementación

- [x] **Backend: Repositorio de Avatares** <!-- id: 0 -->
    - Implementar `update(avatar_id, data)` en `AvatarRepository`.
    - Implementar `delete(avatar_id)` en `AvatarRepository`.
    - Implementar `set_global_default(tenant_id, avatar_id)` (transacción para desmarcar anteriores).

- [x] **Backend: API de Avatares** <!-- id: 1 -->
    - Agregar ruta `PATCH /{avatar_id}` en `api/avatars.py`.
    - Agregar ruta `DELETE /{avatar_id}` en `api/avatars.py`.
    - Agregar ruta `POST /{avatar_id}/set-default` en `api/avatars.py`.

- [x] **Frontend: Fix Extracción** <!-- id: 2 -->
    - Modificar `extractFullBrand` en `frontend/src/features/brand/api/index.ts`.
    - Lógica: Si `data` no es `FormData`, convertir el objeto JSON a `FormData` antes de enviar. Eliminar el header `application/json` en este caso.

- [x] **Integración: Verificación Manual** <!-- id: 3 -->
    - Reiniciar backend.
    - Probar flujo completo de Brand Studio.
