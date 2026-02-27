Entendido. Procederé a duplicar el guardado de `email` y `phone` en las columnas dedicadas de la tabla `User` para facilitar su acceso y futuras integraciones, manteniendo también la copia en `profile_data`.

### Plan Actualizado

1.  **Modificar `src/services/repository.py`**:
    *   Actualizar la función `update_user_profile`.
    *   Agregar lógica para extraer `email` y `phone` del diccionario `psychographics_update` entrante.
    *   Si existen estos valores, asignarlos directamente a los atributos `user.email` y `user.phone` del modelo SQLAlchemy antes de hacer el commit.

2.  **Verificar `src/admin/app.py`**:
    *   Revisar `render_user_profile_card`. Como ya lee de `user.email` y `user.phone`, con el cambio anterior la visualización funcionará automáticamente para los nuevos datos que entren.
    *   *(Opcional)* Agregar lógica de fallback en la vista por si acaso queremos ver datos antiguos que solo estén en el JSON, pero la prioridad es cumplir tu requerimiento de guardado dual.

Con esto, cada vez que el agente detecte un correo o teléfono, quedará registrado tanto en el perfil flexible (JSON) como en las columnas rígidas de la base de datos.