# Plan de Reparación Integral del Panel Admin (Streamlit)

El error `InvalidRequestError` persiste debido a problemas de resolución de nombres en las relaciones de SQLAlchemy (`TenantModel` -> `LeadModel`) y posibles dependencias circulares no resueltas en el entorno de ejecución actual. Aunque se actualizaron las referencias a rutas absolutas, es necesario asegurar que todos los modelos se carguen correctamente en el registro (registry) al inicio de la aplicación para evitar fallos de "lazy loading".

## Pasos de Ejecución

1.  **Corregir Relaciones Faltantes**:
    *   Actualizar `src/modules/communication/domain/channel_connection.py` para usar la ruta absoluta en la relación con `TenantModel`.

2.  **Centralizar Importación de Modelos (Bootstrap)**:
    *   Editar `backend/src/shared/infrastructure/db/models/__init__.py` para importar explícitamente **todos** los modelos del sistema. Esto actuará como un registro central.
    *   Modelos a incluir: `User`, `Tenant`, `UserTenant`, `Lead`, `Message`, `Appointment`, `ChannelConnection`, `AgentTrace`, `LLMLog`, `Product`, `PromptVersion`.

3.  **Integrar Bootstrap en Aplicaciones**:
    *   Modificar `backend/src/admin/app.py` para importar el módulo de modelos centralizado **antes** de cualquier otra lógica de negocio. Esto garantiza que SQLAlchemy conozca todas las clases antes de que se ejecute la primera consulta.
    *   Modificar `backend/src/shared/infrastructure/db/database.py` para asegurar que `init_db` también tenga acceso a todos los modelos.

4.  **Limpieza y Reinicio**:
    *   Eliminar recursivamente todos los archivos `__pycache__` y `.pyc` dentro de `backend/src` para forzar la recompilación y evitar el uso de código obsoleto.
    *   Reiniciar el contenedor `visionarias_admin_dev` para aplicar los cambios en el proceso en ejecución.

## Verificación
*   Acceder al Panel Admin y verificar que la carga de Tenants y Usuarios funcione sin errores de `Mapper`.
