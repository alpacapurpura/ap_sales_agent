La búsqueda a la base de datos para obtener la última versión de `state_transition.j2` ocurre en la llamada a `prompt_loader.render(...)`.

### Flujo de Ejecución Detallado:

1.  **Llamada desde el Nodo Manager**:
    En `src/core/nodes.py`, línea 95, se invoca:
    ```python
    transition_prompt = prompt_loader.render("state_transition.j2", ...)
    ```

2.  **Lógica de `PromptLoader.render`** (`src/core/prompts/base.py`):
    *   **Paso A (Check Caché):** Verifica si `state_transition` está en `self._cache` y si su TTL (< 60s) es válido.
    *   **Paso B (Consulta DB):** Si no está en caché o expiró, llama a `self._get_from_db("state_transition")`.
        *   Esta función ejecuta un `SELECT` a la tabla `prompt_versions` filtrando por `is_active=True` y ordenando por versión descendente.
    *   **Paso C (Fallback):** Si la DB falla o no tiene registros, carga el archivo físico `src/core/prompts/templates/state_transition.j2`.

### Conclusión
El sistema **siempre intenta ir a la base de datos** (respetando el TTL de 60 segundos) para asegurar que se use la versión más reciente editada desde el panel de administración, cumpliendo con tu requisito de "hot-reloading".

¿Hay algo más que desees verificar sobre este flujo?