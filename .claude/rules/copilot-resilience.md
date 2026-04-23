---
globs: "backend/src/modules/copilot/**/*.py"
description: Copilot module resilience rules
---

# Copilot Resilience

## Field Discovery
- NEVER hardcode field names en copilot tools
- Use `schema_introspection.py` para Pydantic model field discovery
- New fields/sections en existing models need NO copilot changes (auto-discovered)

## Module Registration
- New modules: add `ModuleDescriptor` to `copilot/domain/module_registry.py`
- Tools use `MODULE_REGISTRY` for data access, no direct repo imports

## Route Registration
- New routes: update `navigation_map.py` + `tools/registry.py` ROUTE_TOOL_MAP
- Route-based tool selection — only relevant tools bound per route

## Debug copilot — SIEMPRE via observabilidad persistida

Cuando el user reporta respuesta rara del copilot (card parpadea, LLM pregunta lo que no toca, tool no ejecuta, "no pasa nada"), **primer paso = revisar trazas**. No arrancar a leer código sin data.

### Orden estricto de debug

1. **`copilot_trace_event`** (SSoT de qué pasó en cada turn):
   ```sql
   -- Últimos turns de una conversación
   SELECT turn_id, event_type, name, status, duration_ms, data, created_at
   FROM copilot_trace_event
   WHERE conversation_id = :conv_id
   ORDER BY created_at;

   -- Solo turns con error
   SELECT * FROM copilot_trace_event
   WHERE tenant_id = :tenant_id AND status = 'error'
   ORDER BY created_at DESC LIMIT 20;

   -- Tool call con args + output preview
   SELECT name, status, data->'args' AS args, data->'output_preview' AS output
   FROM copilot_trace_event
   WHERE turn_id = :turn_id AND event_type = 'tool_call';
   ```
   Event types: `turn_start` / `turn_end` / `llm_call` / `tool_call` / `card_emitted` / `error` / `node_enter` / `node_exit`. Cada row trae `turn_id` (raíz) + `span_id` (propio) + `parent_span_id` (árbol).

2. **`copilot_conversations.messages`** (JSONB con user/AI/Tool messages + tool_calls):
   ```sql
   SELECT jsonb_pretty(messages) FROM copilot_conversations WHERE id = :conv_id;
   ```

3. **`copilot_events`** (comportamiento usuario: accepted/rejected/nudge_*).
4. **`copilot_routing_log`** (tier + classifier + tools_available).
5. **`copilot_mutation_journal`** (cambios via `propose_field_updates`).

6. **Streamlit admin `/trazas`** — UI lista para navegar lo anterior sin SQL. Filtra por tenant + "solo con error". Abre un turn → timeline + detalle JSON por evento.

7. **docker logs** solo si trazas no alcanzan (stack trace crudo).

### Lo que SIEMPRE debe aparecer en trazas

- 1 `turn_start` + 1 `turn_end` por cada POST `/copilot/chat`.
- 1 `llm_call` por cada invocación del modelo (agent_node inicial + re-invocación post tool).
- 1 `tool_call` por cada tool ejecutado (con `data.args` y `data.output_preview`).
- 1 `card_emitted` por cada card visible (con `card_kind` + `source_tool`).
- 1 `error` row con `error_type` + `error_message` cuando algo excepciona.

Si el user reporta un síntoma y **no hay trazas** del turn → bug de observabilidad (el recorder falló silencioso) — fix el recorder ANTES de investigar el síntoma.

### Payload caps
- `data` JSONB truncado a `MAX_PAYLOAD_CHARS = 4000` por campo (ver `trace_recorder.py`).
- Si necesitás el output completo de un tool → mirar `copilot_conversations.messages` (ToolMessage content no tiene cap).

### Prohibido
- Diagnóstico de copilot sin query previa a `copilot_trace_event`.
- Push de fix sin trace row mostrando el síntoma reproducido.
- Hardcodear prompts/args en el recorder (usa `_sanitize_payload`).
- Loggear PII sin truncar (catálogo MAX_PAYLOAD_CHARS ayuda, pero el cap es por campo — revisar payloads con texto largo).
