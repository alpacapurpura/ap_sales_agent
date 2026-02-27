Perfecto, procederé con la implementación completa (Backend + Frontend).

### Plan de Ejecución

1.  **Base de Datos (`src/services/models.py`)**:
    *   Agregaré la tabla `AgentTrace` para registrar el flujo nodo a nodo.
    *   Agregaré la tabla `LLMCallLog` para registrar los prompts exactos y respuestas.

2.  **Lógica de Negocio (`src/services/repository.py`)**:
    *   Implementaré funciones `create_trace` y `create_llm_log` para guardar datos de forma segura.

3.  **Sistema de Tracing (`src/core/tracing.py`)**:
    *   Crearé el decorador `@trace_node` que intercepta automáticamente la entrada y salida de cada función del grafo.

4.  **Instrumentación (`src/core/nodes.py` y LLM)**:
    *   Aplicaré los decoradores a `node_router`, `node_manager`, `node_generator`, etc.
    *   Modificaré `LLMFactory` para que reporte los prompts usados al sistema de log.

5.  **Visualización (`src/admin/app.py`)**:
    *   Crearé la pestaña "🕵️ Auditoría" en tu panel admin para que puedas ver el historial de trazas filtrado por usuario.

Comienzo de inmediato.