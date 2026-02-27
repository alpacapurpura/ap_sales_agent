# Backend & Agentic Testing Strategy

Basado en el análisis de tu backend (`src/core` para lógica agentic, `src/services` para herramientas) y las mejores prácticas de LangGraph, he diseñado 5 archivos de reglas robustos.

## 1. General Backend Rules
Reglas para FastAPI, Postgres y servicios auxiliares.
*   **`back-testing-general-new.md`**:
    *   **Enfoque**: TDD "Light". Crear test de ruta (`test_routes.py`) y test de servicio (`test_services.py`) antes de implementar.
    *   **Herramienta**: `pytest` con `pytest-asyncio` y `httpx` (para probar FastAPI).
    *   **Base de Datos**: Uso de fixtures de `pytest` para rollback automático (DB limpia tras cada test).
*   **`back-testing-general-bugs.md`**:
    *   **Protocolo**: Reproducir bug con un test unitario que falle.
    *   **Logs**: Uso de `structlog` con `context_id` para rastrear el error en Docker.

## 2. Agentic Logic Rules (LangGraph)
Reglas específicas para el "Cerebro" (`src/core`).
*   **`agentic-principles.md`**:
    *   **Filosofía**: Determinismo. Los tests no deben llamar a OpenAI real (costoso y lento).
    *   **Mocking**: Uso obligatorio de `MockLLMService` o `unittest.mock` para simular respuestas del LLM.
    *   **Nodos Puros**: Tratar cada Nodo del grafo como una función pura (`State -> State`) para testearla aisladamente.
*   **`agentic-testing-new.md`**:
    *   **Estrategia**:
        1.  **Unit Test**: Probar el Nodo individualmente (ej. `node_router` redirige bien?).
        2.  **Graph Test**: Probar el flujo completo con `langgraph.compile()` y mocks.
    *   **Snapshot**: Verificar que el `AgentState` mantiene su integridad estructural.
*   **`agentic-testing-bugs.md`**:
    *   **Trace**: Usar LangSmith (si está activo) o logs de `tracing.py` para ver dónde se desvió el agente.
    *   **Regression**: Si el agente alucinó, crear un test case con ese prompt específico y verificar que la nueva lógica lo corrige (usando evaluación semántica o keywords).

## Ubicación y Permisos
*   Todos los scripts temporales irán a: `/home/chris/AISALESHT/backend/scripts/temp`.
*   Se forzará `chmod +x` y `chown` en los scripts generados.
*   Ejecución siempre vía Docker: `docker exec -t visionarias_brain pytest ...`.

¿Procedemos a crear estos 5 archivos de reglas?
