Entendido. Tienes razón, debemos ser coherentes con el patrón Factory que acabamos de implementar y evitar parches sucios.

### Análisis Arquitectónico
El problema es una **inconsistencia en el contrato de datos**:
1.  **Factory (`create_initial_state`)**: Define que el campo `user_id` del `AgentState` debe ser un identificador.
2.  **API (`routes.py`)**: Actualmente le pasa el `incoming.user_id` (Telegram ID) al Factory.
3.  **Core (`tracing.py`)**: Espera que `state["user_id"]` sea un UUID de base de datos para crear la relación Foreign Key en la tabla `traces`.

### Solución Limpia (Clean Code)
En lugar de "parchar" el tracing para que adivine, corregiremos el flujo de datos desde el origen (`routes.py`) respetando la arquitectura.

1.  **Ajuste en `src/api/routes.py`**:
    *   Ya tenemos el objeto `user` (modelo DB) recuperado/creado en la línea 41-50.
    *   Al llamar a `create_initial_state`, pasaremos explícitamente `user.id` (UUID) en lugar de `incoming.user_id`.
    *   *Nota*: Esto no rompe el envío de mensajes de vuelta, porque `routes.py` mantiene `incoming.user_id` en su variable local para construir el `OutgoingMessage` al final del proceso. El Core del agente no necesita saber el ID de Telegram, solo el UUID interno.

2.  **Limpieza en `src/core/tracing.py`**:
    *   Eliminaré toda la lógica "sucia" de `try/except` y búsquedas de repositorio para resolver IDs.
    *   El decorador asumirá (correctamente por contrato) que `state['user_id']` es un UUID válido. Esto hace el código de tracing mucho más rápido, limpio y menos propenso a errores.

3.  **Validación**:
    *   Esto asegura que cada `Trace` creado tenga un `user_id` válido asociado a la tabla `users`.
    *   Al existir el `Trace` válido, los `LLMCallLog` se asociarán correctamente.

Esta solución alinea las tres capas (API, Core/State, Servicios) bajo un mismo entendimiento del `user_id`, eliminando la ambigüedad.