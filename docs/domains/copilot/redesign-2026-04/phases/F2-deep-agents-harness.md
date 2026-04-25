# F2 — Deep Agents harness

**Pre-req:** F1 cerrada (provider discovery en uso, offer migrado).
**Sprints estimados:** 2.
**Bloquea:** F4, F5 (ambas usan subagentes y scratchpad).
**Valor entregado:** plan_card visible, scratchpad filesystem ephemeral, capacidad de spawn_subagent para tareas pesadas.

---

## §1 Objetivo

Reemplazar el `agent_node` ReAct simple por un harness `langchain-deepagents` que aporta:

- **Planning tool** (`write_todos`) → plan visible al usuario antes de actuar.
- **Filesystem virtual** (read/write/edit_file, ls, glob, grep) sobre `StateBackend` ephemeral por conversación.
- **Subagent tool** (`spawn_subagent`) → context isolation para auditorías / queries pesadas.
- **System prompt estructurado** estilo Claude Code: tool-use, planning, verification.

Mantener compat con golden tests F0. La conversación simple no nota cambio; solo las tareas complejas se vuelven más estructuradas.

---

## §2 Pre-lectura específica

- `learnings/F1-provider-pattern.md`.
- `02-architecture-target.md §1`, §5 (scratchpad).
- `backend/src/modules/copilot/application/orchestrator/graph.py` (entender ReAct loop actual).
- `backend/src/modules/copilot/application/memory/context_window_builder.py` (NO tocar, integrar).
- Docs `langchain-deepagents` (versión fijada en F0).

---

## §3 Research mandate (abril 2026)

Queries WebSearch:

- `langchain-deepagents StateBackend StoreBackend Postgres custom 2026`
- `deepagents subagent context isolation patterns production 2026`
- `LangGraph deepagents migration ReAct agent_node 2026`
- `deepagents system prompt template Claude Code style 2026`

WebFetch:

- Docs oficial Deep Agents (https://docs.langchain.com/oss/python/deepagents/overview).
- README repo `langchain-ai/deepagents` versión fijada.

Tessl tiles:

- `tessl__langgraph` — releer.

Productos:

- API exacta `create_deep_agent(...)` versión X.Y.Z.
- Cómo registrar tools custom + builtin coexistir.
- Cómo customizar system prompt manteniendo planning behavior.
- Pattern para `StoreBackend` custom (Postgres) si se necesita persist en F2 o aplazable a fase futura.

---

## §4 Lo que NO se toca

- Routing 4-tier (`model_router`).
- Context window builder + rolling summarizer.
- Trace recorder.
- SSE v2 protocol (extender es OK, romper NO).
- Provider pattern de F1.
- Cards UI (proposal, clarify_card, etc.) — pueden recibir nuevos campos para mostrar plan, no breaking.

---

## §5 Deliverables

### 5.1 Deep Agent harness en orchestrator

`backend/src/modules/copilot/application/orchestrator/deep_agent.py`:

- Construye el agent con `create_deep_agent(tools=..., model=..., instructions=..., subagents=...)`.
- Tools = transversales (`copilot/tools/`) + tools de cada provider activo (vía discovery F1).
- Subagents inicialmente vacíos (F4 + F5 los llenan).
- System prompt: template Jinja `prompts/copilot_deep_agent.j2` con secciones bien marcadas (cacheable prefix).

### 5.2 Scratchpad

- `StateBackend` default (ephemeral per-conversation, vive en `CopilotState`).
- Tools builtins expuestos: `write_todos`, `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`.
- Tabla preparada `copilot_pinned_memory` (ver `02-architecture-target.md §5`) — migración Alembic idempotente. Implementación de `pin_to_memory` puede ir tras F2 (placeholder OK).

### 5.3 Subagent infrastructure

- API `spawn_subagent(name, prompt, context?)` registrada como tool.
- Subagent dummy `audit_inspector` para validar el flow end-to-end (F4/F5 lo reemplazan con casos reales).
- Context isolation verificado con test (subagent NO accede al state del main).

### 5.4 SSE adaptation

Extender SSE v2 para emitir progreso del planning:

- `block_start` con type `plan_card` cuando el agent escribe TODOs.
- `block_delta` actualizando estado (`pending`/`in_progress`/`completed`).

NO romper bloques existentes. Solo agregar.

### 5.5 Tests

- Unit del harness con mock LLM.
- Golden F0 corriendo verde (críticos).
- Nuevos golden tests:
  - Tarea simple → respuesta directa, sin write_todos.
  - Tarea compleja → write_todos visible + step-by-step.
  - Subagent dummy ejecuta con context aislado.
  - Scratchpad escribe/lee dentro de la conversación.

### 5.6 Migration backwards compat

- Feature flag `COPILOT_DEEP_AGENT_V2` (default off durante F2 dev, on al cerrar).
- Si flag off → ReAct legacy. Si on → deep agent.
- Eliminar ReAct **después** de F4 + F5 estables (en F8 si todo OK).

---

## §6 Quality gates

- `/test-backend` + `/test-frontend` verdes.
- Golden tests F0 verdes con flag ON.
- Manual: conversación compleja en `/offer-studio` muestra plan_card actualizándose.
- Latencia: medir y comparar pre-F2 vs post-F2 (puede subir un poco por planning overhead — aceptable).

---

## §7 Riesgos

| Riesgo | Mitigación |
|---|---|
| `langchain-deepagents` requiere versión específica langgraph que choca con código actual | Aislar test dep, si choque grave → fork local mínimo. |
| Planning overhead degrada UX en chats simples | Heurística: skip planning si message <30 chars y sin tools previstos. |
| Scratchpad se llena de basura dentro de la sesión | Cap por path-count + size en StateBackend wrapper. |
| Subagents recursivos | Cap profundidad (max 2 niveles). |

---

## §8 Definición de hecho

- [ ] `deep_agent.py` construye agent funcional.
- [ ] Tools builtins disponibles.
- [ ] Subagent dummy ejecuta con isolation.
- [ ] Migration `copilot_pinned_memory` aplicada.
- [ ] SSE emite plan_card.
- [ ] Golden F0 verdes con flag on.
- [ ] Nuevos golden F2 verdes.
- [ ] Latencia documentada.
- [ ] `learnings/F2-deep-agents.md` + `prompts/F3-start.md`.

---

## §9 Notas para F3 + F4 + F5

- API exacta del subagent tool: cómo F4 (`url_analyzer`) y F5 (`data_query`) se registran.
- Cómo el system prompt acepta inyecciones de F3 (`brand_lighthouse`).
- Si scratchpad necesita extensiones para F4 (paths con frontmatter, metadata).
