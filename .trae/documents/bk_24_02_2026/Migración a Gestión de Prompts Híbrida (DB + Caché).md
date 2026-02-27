# Plan de Ejecución: Sistema de Gestión de Prompts Híbrido

Implementaré la solución aprobada siguiendo estos pasos técnicos:

## 1. Capa de Datos (PostgreSQL)
*   **Modificar `src/services/models.py`**: Definir la clase `PromptVersion` con soporte para JSONB.
*   **Actualizar Schema**: Crear un script temporal `scripts/update_db_prompts.py` para crear la tabla en la base de datos existente (ya que no usas Alembic activamente, usaré `Base.metadata.create_all`).

## 2. Migración de Contenido (Seed)
*   **Script `scripts/seed_prompts.py`**:
    *   Escaneará `src/core/prompts/templates/*.j2`.
    *   Para cada archivo, creará la `versión 1` en la base de datos.
    *   Intentará inferir variables usando regex simple `{{ variable }}`.
    *   Establecerá metadatos por defecto.

## 3. Lógica de Negocio (Core)
*   **Refactorizar `src/core/prompts/base.py`**:
    *   La clase `PromptLoader` ahora intentará leer de la BD primero.
    *   Implementará un caché simple en memoria (diccionario con TTL o LRU Cache) para no saturar la BD.
    *   Mantendrá el fallback a disco por seguridad.

## 4. Interfaz de Usuario (Admin)
*   **Actualizar `src/admin/app.py`**:
    *   Agregar nueva opción en el Sidebar: "Gestión de Prompts".
    *   Crear la función `render_prompt_manager()` que permita:
        *   Ver lista de prompts.
        *   Editar contenido.
        *   Guardar nueva versión (INSERT).
        *   Ver historial.

## 5. Verificación
*   Ejecutaré el Admin y verificaré que pueda modificar un prompt y que el cambio se refleje en el sistema.
