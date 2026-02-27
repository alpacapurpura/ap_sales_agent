He investigado cómo se guarda la información de trazabilidad y RAG.

### El Problema
Actualmente, el `node_response_generation` en `src/core/nodes.py` obtiene los chunks de RAG (`context_rag`), los inserta en el prompt y luego llama al servicio LLM.
Sin embargo, **el contenido de los chunks RAG no se está guardando explícitamente en el log de trazabilidad (`AgentTrace` o `LLMCallLog`)**. Solo queda "oculto" dentro del texto gigante del `prompt_rendered` en `LLMCallLog`, lo cual es difícil de leer en la UI.

Para mostrar los chunks de forma limpia en la sección "🤖 Actividad Cognitiva (LLM)", necesitamos:
1.  **Capturar los chunks**: Modificar el repositorio para que `create_llm_log` acepte un campo extra `metadata_info` o similar donde podamos guardar el `context_rag`.
2.  **Modificar el Modelo**: Agregar una columna `metadata_info` (JSONB) a la tabla `llm_call_logs` en `src/services/models.py` para almacenar datos estructurados como los chunks recuperados.
3.  **Actualizar el Nodo**: En `src/core/nodes.py`, pasar el `context_rag` al mecanismo de logging. (Nota: El logging actual ocurre dentro de `LLMFactory.generate_response` -> `repo.create_llm_log` en `src/core/llm/providers/openai.py`).
    *   *Desafío*: El decorador `@trace_node` captura el estado de entrada/salida, pero los chunks son una variable interna de la función.
    *   *Solución*: Pasaremos los chunks como parte de los metadatos al llamar a `generate_response` (si el proveedor lo soporta) o, mejor aún, haremos que el nodo guarde esta info en el estado temporalmente o la loguee explícitamente.
    *   *Mejor Aproximación*: Modificar `OpenAIService.generate_response` para aceptar `metadata` opcional y pasarlo a `repo.create_llm_log`.

### Plan de Implementación

1.  **Backend (DB Schema)**:
    *   Modificar `src/services/models.py`: Agregar `metadata_info = Column(JSONB, default={})` a `LLMCallLog`.
    *   Modificar `src/services/repository.py`: Actualizar `create_llm_log` para aceptar y guardar `metadata`.

2.  **Backend (Lógica de Nodo)**:
    *   Modificar `src/core/llm/providers/openai.py`: Aceptar un parámetro `metadata` en `generate_response` y pasarlo al repositorio.
    *   Modificar `src/core/nodes.py`: En `node_response_generation`, al llamar a `generate_response`, pasar `metadata={"rag_context": context_rag}`.

3.  **Frontend (Admin UI)**:
    *   Modificar `src/admin/app.py`: En `_render_timeline_trace`, leer `log.metadata_info.get("rag_context")`.
    *   Si existe, mostrar un expander o sección "📚 Contexto RAG Recuperado" con los chunks formateados.

Esto permitirá ver exactamente qué encontró el buscador vectorial antes de generar la respuesta.