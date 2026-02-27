Voy a modificar el archivo `backend/src/admin/app.py` para agregar el control de permisos de API Keys en el panel de administración.

### Pasos de Implementación:

1.  **Modificar `render_tenant_manager` en `backend/src/admin/app.py`**:
    *   **Sección "Editar Cliente"**:
        *   Localizaré el formulario de edición de Tenants (alrededor de la línea 741).
        *   Agregaré un checkbox: `Permitir uso de Keys de Plataforma`.
        *   Vincularé este checkbox al campo existente `can_use_platform_keys` del modelo `Tenant`.
        *   Incluiré este campo en la lógica de guardado (`db.commit()`).
    
    *   **Sección "Crear Cliente" (Opcional pero recomendado)**:
        *   Agregaré el mismo checkbox en el formulario de creación para establecer el permiso desde el inicio.

### Resultado Esperado:
*   En la pestaña "Tenants" del Admin, al seleccionar un cliente, verás una nueva opción para habilitar/deshabilitar el uso de tus claves maestras (`OPENAI_API_KEY` del `.env`).
*   Si lo desactivas, el sistema backend (ya implementado en `factory.py`) obligará al tenant a tener sus propias claves configuradas para poder usar la IA.
