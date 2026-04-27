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

2. **`copilot_llm_call`** (typed event-sourced LLM-call log, post 2026-04 rebuild):
   ```sql
   -- Toda la actividad LLM de un turn (provider, model, tokens, costo, duration).
   SELECT role, provider, model_responded, input_tokens, output_tokens,
          cached_read_tokens, cost_usd, duration_ms, status
   FROM copilot_llm_call
   WHERE tenant_id = :tenant_id AND turn_id = :turn_id
   ORDER BY started_at;

   -- Costo agregado por ciclo billing (usa la SQL function de Phase 3).
   SELECT compute_cycle_start(:tenant_id, CURRENT_DATE) AS cycle_start,
          SUM(cost_usd) AS cycle_cost_usd,
          COUNT(*) AS calls,
          COUNT(DISTINCT turn_id) AS turns
   FROM copilot_llm_call
   WHERE tenant_id = :tenant_id
     AND occurred_on >= compute_cycle_start(:tenant_id, CURRENT_DATE);

   -- MV pre-agregada (refrescada hourly por aggregate_refresh_task).
   SELECT * FROM mv_daily_llm_cost_per_tenant
   WHERE tenant_id = :tenant_id ORDER BY day DESC LIMIT 30;
   ```
   Cost+model están en columnas tipadas, **no en el JSONB de `copilot_trace_event.turn_end.data`**. El JSONB legacy compat (`model`, `prompt_tokens`, `cost_usd`) sigue rellenado por `turn_envelope._legacy_compat_keys` para no romper consumers viejos, pero `copilot_llm_call` es la fuente de verdad.

3. **`copilot_conversations.messages`** (JSONB con user/AI/Tool messages + tool_calls):
   ```sql
   SELECT jsonb_pretty(messages) FROM copilot_conversations WHERE id = :conv_id;
   ```

4. **`copilot_events`** (comportamiento usuario: accepted/rejected/nudge_*).
5. **`copilot_routing_log`** (tier + classifier + tools_available).
6. **`copilot_mutation_journal`** (cambios via `propose_field_updates`).

7. **Streamlit admin** — UI lista para navegar lo anterior sin SQL:
   - **`/trazas`** — timeline turn-a-turn. Cada row de `event_type='llm_call'` trae `cost_usd` joineado de `copilot_llm_call` por `span_id`.
   - **`/copilot-routing`** — tier distribution + latency p50/p95 + costo USD por modelo (lee `copilot_llm_call` directo, no JSONB).
   - **`/costo-copilot`** — dashboard de costo por tenant en ciclo 25-25 (Phase 3).

8. **docker logs** solo si trazas no alcanzan (stack trace crudo).

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

## Subagentes (deepagents `task` tool) — contrato de aislamiento

LangGraph `astream_events(version="v2")` bubble-uppea events de subgraphs anidados. Cuando el deep agent invoca un sub-agente vía `task` tool, ese sub-agente corre en un compiled graph nested y sus events (chat_model_stream + chat_model_end) llegan al loop principal junto con los del parent. Sin clasificación, el orquestador trata ambos por igual → tokens del sub-agente leak al user + AIMessage final del sub-agente se duplica en `copilot_conversations.messages`.

### Contrato

1. **Clasificación obligatoria.** Todo event consumido en el stream loop pasa por `stream_provenance.policy_for(event)`. NO branchear directo por `event["event"]` sin consultar la matriz. Detección via:
   - `metadata.langgraph_checkpoint_ns` con `|` separador (señal primaria),
   - `metadata.langgraph_path` con componente `task` o `task:<id>` (fallback).

2. **Subagentes drop.** Events clasificados `EventOrigin.SUBAGENT`:
   - `on_chat_model_stream` → DROP (no entran al `text_block` del user),
   - `on_chat_model_end` → DROP (no se appendean a `acc.messages`).
   El reporte final del sub-agente llega al parent como `ToolMessage` vía `Command(update={"messages": [...]})` que `deepagents` emite en `_return_command_with_state_update`.

3. **`_handle_tool_end` desempaqueta `Command`.** Helper `_extract_tool_message` normaliza output a `ToolMessage` cubriendo 3 shapes: `ToolMessage`, `str`, `Command`. Sin esto el `tool_call(task)` queda sin matching `tool_message` y LangGraph rompe en el siguiente turn al recargar historial.

4. **Parent NO re-resume el reporte.** Regla en `deep_agent.py::_DEEP_AGENT_SUFFIX_ES`: la próxima respuesta tiene 3 partes (intro 1 línea + reporte del sub-agente con cambios mínimos + pregunta accionable). Re-redactar gasta tokens, duplica contenido en pantalla, y rompe la traza del razonamiento.

5. **Caps preventivos.** `subagent_budget.SubagentBudget` (defaults: 2 task/turn, depth 1, 6 iter internas). Excede → `SubagentBudgetError`.

### Prohibido (subagentes)

- Hardcodear nombres de subagentes en `chat.py` o el orquestador. Política agnóstica al nombre.
- `astream_events(subgraphs=False)` para "fixear" el leak. Necesitamos los events para trace (`node_trace`) — sólo filtrar surfacing via `policy_for`.
- Modificar la library `deepagents`. Workaround vía wrappers locales en `chat.py` y `subagent_budget.py`.
- Capturar `AIMessage` de events nested sin pasar por la matriz. La línea `accumulated_messages.append(output)` debe venir DETRÁS de un `policy_for(event) is StreamPolicy.CAPTURE_HISTORY`.

### Tests obligatorios

- `tests/modules/copilot/test_stream_provenance.py` — clasificador con fixtures de los 3 orígenes + matriz exhaustiva.
- `tests/modules/copilot/test_subagent_stream_isolation.py` — 1 test por subagente registrado + replay end-to-end de turn con `task`.
- `tests/architecture/test_subagent_isolation_invariants.py` — ratchet: cada subagente nuevo debe estar en `REGISTERED_SUBAGENTS_RATCHET` y tener cobertura.
