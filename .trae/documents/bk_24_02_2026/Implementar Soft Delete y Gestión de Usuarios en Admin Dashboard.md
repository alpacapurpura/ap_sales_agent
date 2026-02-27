Implementaré un sistema de **"Soft Delete" (Desactivación)** para los usuarios del sistema (Admin/Staff), siguiendo las mejores prácticas de auditoría.

### Estrategia Técnica
Dado que estos usuarios tienen historial (logs, prompts creados), borrarlos físicamente rompería la integridad de la base de datos.
1.  **Modificar Visualización**: En lugar de borrar la fila de la DB, cambiaremos el estado `is_active = False`.
2.  **Interfaz de Usuario (UX)**:
    *   Agregaré una columna de "Acciones" en la tabla de usuarios.
    *   Incluiré un botón "Desactivar" con un diálogo de confirmación (Popover/Expander) para evitar clics accidentales.
    *   Los usuarios desactivados se mostrarán visualmente distintos (ej. tachados o en gris) o se filtrarán con un toggle "Ver inactivos".
3.  **Lógica de Re-activación**:
    *   Al intentar crear un usuario nuevo, si el email ya existe pero está inactivo, el sistema ofrecerá "Reactivar Usuario" en lugar de fallar o crear duplicados.

### Plan de Implementación
1.  **Editar `backend/src/admin/app.py`**:
    *   Modificar la sección `render_tenant_manager`.
    *   Reemplazar el `st.dataframe` simple por una iteración visual que permita botones por fila (o usar `st.data_editor` con lógica de borrado, pero botones es más explícito para acciones críticas).
    *   Implementar la lógica `user.is_active = False` al confirmar.
    *   Actualizar el formulario de creación para detectar y manejar usuarios inactivos ("Upsert" lógico).

Esta solución cumple con tu requerimiento de robustez, auditoría y reincorporación futura.