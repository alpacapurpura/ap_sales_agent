# Plan Definitivo: Chain of Thought (CoT) Persistente en Base de Datos

He revisado las mejores prácticas de 2025/2026 (Reasoning Models, CoT) y tu arquitectura de base de datos. La solución más robusta y limpia es implementar CoT en el prompt y persistir el razonamiento en la tabla `agent_traces` existente.

## 1. Prompt Engineering: CoT Estructurado (`state_transition.j2`)
Transformaré el prompt del "Manager" para que no solo decida, sino que **piense paso a paso** siguiendo las reglas de tu documento `FUNNEL_ESTRATÉGICO...md`.

**Nueva Estructura del Prompt:**
1.  **Contexto**: Reglas de negocio explícitas (Ramas 1, 2, 3, Descalificación, Preguntas Clave).
2.  **Instrucción CoT**: "Antes de responder JSON, genera un bloque `<thought_process>`".
3.  **Pasos de Razonamiento**:
    *   *Extracción*: ¿Qué datos dio el usuario? (Facturación, Dolor, etc.)
    *   *Validación*: ¿Coincide con la regla de transición de la etapa actual?
    *   *Decisión*: ¿Avanzar, quedarse o descalificar?

## 2. Lógica del Nodo Manager (`src/core/nodes.py`)
El LLM devolverá un texto mixto (XML + JSON). Actualizaré `node_state_manager` para:
1.  **Separar**: Extraer el contenido dentro de `<thought_process>...</thought_process>`.
2.  **Parsear JSON**: Extraer el bloque JSON final para la lógica del código.
3.  **Inyectar en Estado**: Guardar el razonamiento extraído en una nueva variable `state["latest_reasoning"]`.

## 3. Persistencia en Base de Datos (Sin Migraciones)
Aprovecharé tu infraestructura actual (`src/services/repository.py`):
*   El decorador `@trace_node` ya guarda el `output_state` en la tabla `agent_traces` (columna JSONB).
*   Al añadir `latest_reasoning` al `AgentState` (en `src/core/state.py`), este se guardará automáticamente en cada traza.
*   **Resultado**: Podrás auditar el pensamiento del agente consultando la tabla `agent_traces` o tu dashboard, viendo exactamente por qué tomó cada decisión.

## Pasos de Ejecución
1.  **Actualizar Schema**: Agregar campo `latest_reasoning` a `AgentState`.
2.  **Reescribir Prompt**: Implementar lógica CoT + Reglas del Funnel en `state_transition.j2`.
3.  **Actualizar Nodo**: Implementar parsing de XML/JSON en `node_state_manager`.

Esta solución cumple con "Obtener info", "Calificar" y "Decidir" con alta precisión y trazabilidad total.