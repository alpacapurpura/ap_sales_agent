# Plan de Refactorización y Buenas Prácticas

He investigado el código y preparado un plan para implementar las mejoras de mantenibilidad solicitadas (Tipado, Enums y Manejo de Errores).

## 1. Definición de Enums (`src/core/schema.py`)
Crearemos Enums para estandarizar los "Magic Strings" encontrados en `repository.py`, `state.py` y `nodes.py`.

*   **`FunnelStage`**: Para los estados del viaje del usuario (`S1_Rapport`, `S2_Discovery`, etc.).
*   **`LeadStatus`**: Para el estado de calificación (`awareness`, `qualified`, `disqualified`, etc.).
*   **`ProductLaunchStage`**: Para las etapas de lanzamiento (`pre_launch`, `open_cart`, etc.).

## 2. Refactorización de `src/services/repository.py`
*   **Tipado Estricto**: Añadir type hints de retorno a métodos clave:
    *   `create_user(...) -> User`
    *   `get_enrollment(...) -> Optional[Enrollment]`
    *   `update_enrollment(...) -> Enrollment`
    *   `get_current_launch_product(...) -> Tuple[Optional[Product], Optional[str]]`
*   **Uso de Enums**: Reemplazar strings literales por referencias a `FunnelStage` y `LeadStatus`.
*   **Manejo de Errores**:
    *   Importar `SQLAlchemyError` de `sqlalchemy.exc`.
    *   Reemplazar `except Exception as e` por `except SQLAlchemyError as e` en operaciones de base de datos.

## 3. Actualización de Modelos y Estado
*   **`src/core/state.py`**: Actualizar `AgentState` para usar los Enums en `current_state` y `launch_stage`.
*   **`src/core/nodes.py`**: Actualizar la lógica de inicialización y transición de estados para usar los Enums (ej. `node_entry_point`).

## 4. Verificación
*   Ejecutaré una verificación estática (lectura de código) para asegurar que no queden strings sueltos en los archivos modificados.
