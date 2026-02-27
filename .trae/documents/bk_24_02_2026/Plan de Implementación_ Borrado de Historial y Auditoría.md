# Implementación de Botón "Borrar Historial" en Auditoría

## Confirmación de Seguridad
**Confirmado**: La lógica de borrado está estrictamente aislada por `user_id`.
- En Base de Datos: Todas las consultas `DELETE` incluyen `.filter(Message.user_id == user_id)`.
- En Cache (Redis): Las claves se construyen como `chat:buffer:{user_id}`, por lo que es imposible afectar a otros usuarios.

## Backend: Limpieza Profunda
1. **Actualizar `SmartBufferService`**:
   - Implementar método `clear_user_cache(user_id)` para eliminar también la memoria temporal en Redis (`chat:buffer`, `chat:meta`).
2. **Actualizar Endpoint `DELETE`**:
   - En `admin.py`, invocar la limpieza de Redis además de la limpieza de Base de Datos existente.

## Frontend: Interfaz y UX
1. **API Client**:
   - Agregar función `clearUserHistory` en `frontend/src/lib/api/audit.ts`.
2. **Componente `ContextPanel`**:
   - Agregar botón con icono de papelera (Trash2) junto a los tabs de Usuario/Agente.
   - Implementar **Alerta de Confirmación** (`AlertDialog`) para prevenir borrados accidentales.
   - Mostrar notificación (Toast) de éxito o error.

## UX/UI
- El botón será de color rojo (variante `destructive` o icono rojo) para indicar peligro.
- Requerirá doble confirmación ("¿Estás seguro? Esta acción es irreversible").
