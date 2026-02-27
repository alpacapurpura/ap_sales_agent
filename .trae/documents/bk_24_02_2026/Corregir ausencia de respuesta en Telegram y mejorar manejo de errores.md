Gracias por sugerirme revisar los logs. Efectivamente, encontré el error crítico:

**El Error:**
`Invalid state update`: El sistema está fallando porque el estado inicial contiene campos (`detected_intent`, `security_flag`, `priority_level`) que **no están definidos** en el esquema `AgentState`. LangGraph rechaza estos datos extra, provocando que el agente colapse antes de responder.

**El Plan de Corrección:**

1.  **Corregir `src/core/state.py`**:
    *   Agregar los campos faltantes (`detected_intent`, `security_flag`, `priority_level`) a la definición de la clase `AgentState` para que coincidan con lo que genera `create_initial_state`.

2.  **Mejorar Robustez (Prevención)**:
    *   **`src/api/routes.py`**: Implementar el mensaje de error "fallback" para que, si vuelve a ocurrir un error interno, el bot te avise ("Lo siento, error técnico...") en lugar de quedarse callado.
    *   **`src/channels/telegram.py`**: Limpiar el token de Telegram (`.strip()`) para evitar errores de configuración.

Esto solucionará el problema de raíz y asegurará que el bot responda.