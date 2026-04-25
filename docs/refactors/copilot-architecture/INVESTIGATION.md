# Copilot Extractor + Focus Mode — Informe de Investigación

Fecha: 2026-04-24. Branch: `development`. Estado: research — NO código.

Base: 4 exploradores BE/FE + web research 2026 (LangGraph, slot-filling, ToolMessage.artifact, OTel GenAI).
Refs recientes aplicados: `595d5a84`, `59c6c0bb`, `384ad265` (SSoT por dominio, hint dinámico paths, sanitizer safety net).

---

## 1. Estado actual — hechos verificados

### 1.1 Orchestrator + persistence

- **NO hay checkpointer LangGraph**. `copilot_graph = workflow.compile()` en `backend/src/modules/copilot/application/orchestrator/graph.py:712` sin arg. Grafo stateless entre requests; state en RAM durante turn.
- **Rehydrate manual cada turn**: `chat.py:447-448` lee `procedure_state` (JSONB) → hidrata `state["guided_state"]` + `state["active_extraction_job"]`.
- **Persistencia guided**: `copilot_conversations.procedure_state` JSONB (`conversation_model.py:56`), sibling keys `"guided"` + `"active_extraction_job"`. Read-merge-write sin lock → race si 2 tools escriben concurrentes.
- **GuidedState shape** (`guided/state.py:15-50`): `domain, entity_id, current_block_id, completed_blocks[], started_at`. Navegación lineal; no concepto "sección completa" más allá de threshold coverage.
- **Context budget** (`context_budget.py`): sliding window 15K tokens, preserva últimas 3 turns, resumen de older-msgs en `SystemMessage` (primeros 80 chars). Tool-result truncado a 4KB en SSE pero **no en history enviado al LLM** → balloon riesgo en conversaciones focus largas.

### 1.2 Tool responses — inventario

31 tools auditadas. Shapes:

| Nivel | Cantidad | Ejemplos |
|---|---|---|
| SÍ compliant envelope `{text, llm_content, ui_action}` | 2 | (ninguno 100%) |
| PARCIAL (text+ui_action, falta `llm_content`/`error`/`session_hint`) | 19 | `extract_from_url`, guided/*, `propose_field_updates` |
| NO compliant (raw markdown o raw JSON string) | 10 | `get_lead_summary`, `get_pipeline_overview`, `search_knowledge_base`, `module_tools`, `web_research` |

**Worst offenders**: tools retornan `str(json.dumps({...}))` y LLM las regurgita como JSON en chat — síntoma que motivó `384ad265` + `output_sanitizer.py`. **El sanitizer es parche; contrato real = shape enforcement en el tool.**

Mix dict vs string(json) es inconsistente: `navigation.py` retorna dict, la mayoría str. LangChain soporta `response_format="content_and_artifact"` (`ToolMessage.artifact`) — no usado.

### 1.3 Flujos extracción — duplicación

| Dim | URL (worker) | DOC (inline) |
|---|---|---|
| Entry | `extract_from_url` | `extract_from_doc` + `extract_document_to_fields` |
| Exec | ARQ worker `run_{brand,offer}_extraction` | `DocumentProcessor.extract_from_text` inline |
| Persist DB | **SÍ auto** (worker escribe `service.extract_all()`) | **NO** (delta en Redis → user aprueba via `propose_field_updates`) |
| Eventos | Section + Job completed | Section + Job completed (mismo) |
| Subscriber | `extraction_card_flow.py` (nav pills + summary card) | Idem |
| buyer_persona | ❌ no worker | ✅ soportado |

**Duplicación confirmada**:
- Label maps (80+ LOC) en `extraction_tools.py:170-202` **y** `extract_from_doc.py:45-77`.
- `_err` / error envelopes duplicados.
- `_compose_target_label` lógica idéntica.
- `source_tool="extract_from_url"` **hardcoded** en subscriber (`extraction_card_flow.py:244`) incluso cuando origen es doc → observabilidad mentirosa.
- `nav_route_template=None` desde doc → subscriber cae en legacy fallback path.

**Divergencia intencional**:
- URL = bulk, commit auto. DOC = preview + approve. UX diferente por razón válida.
- Scope `visuals` solo URL (docs no tienen CSS/colores).

**Concurrency gap**: `_record_active_extraction_job` read-merge-write sin lock. 2 docs paralelos en misma conversation → último job sobrescribe primero silenciosamente. No hay transaction guard ni optimistic lock.

### 1.4 Persisters — homologación parcial

3 persisters, signatures *casi* idénticas pero no homologadas:

```
BrandPersister.persist(tenant_id, mapa_global, fields_to_persist) -> None
OfferPersister.persist(tenant_id, mapa_global, fields_to_persist, entity_id=None) -> None
BuyerPersonaPersister.persist(tenant_id, mapa_global, fields_to_persist, entity_id=None) -> UUID | None
```

No hay `Protocol`/`ABC` base ni arch test enforçando contrato. Nada bloquea 4to persister con firma distinta.

### 1.5 FE — focus mode inventory

- **sidebarState** (`copilot-store.ts:181`): `"collapsed" | "rail" | "full"`. **No existe "focus"**.
- **use-guided-entity-creation**: YA dispara create → openPanel → `sendMessage(promptFor(domain))`. Session ephemeral.
- **use-copilot-ui-action**: maneja `guided_started` / `guided_block_advanced` / `guided_completed` / `interview_complete`. **No** `enter_focus`/`exit_focus`/`update_progress`.
- **Progress visual**: `CheckpointCard`, `CopilotHeader` ("Bloque N/M · label"), `ProcedureProgress` stepper. **No** progress bar dedicado focus.
- **Session reload**: `conversationId` sí persiste (localStorage). **Session guiada NO** — se re-hidrata al próximo mensaje cuando backend re-emite `guided_started`.
- **Nav lock**: **no existe**. Ni `useBeforeUnload`, ni `router.events.on`, ni guard en sidebarState.
- **Cards soportados** (BlockDispatcher): proposal, metric_summary, comparison, checklist, multi_option, alternatives, clarify, checkpoint, interview_complete, extraction_summary, navigation.

### 1.6 Observability

- `trace_recorder.record()` acepta `dict[str, Any]` — **sin schema Pydantic**. Best-effort write.
- Events: `turn_start/end`, `llm_call`, `tool_call`, `card_emitted`, `error`, `node_enter/exit`.
- Payload cap 4KB por campo. `source_tool` hardcoded tras subscriber → pierde rastro origen real (url vs doc).
- **No hay `session_id` de focus mode** en traces → no se puede reconstruir una sesión de interview end-to-end.

---

## 2. Patrones 2026 aplicables

### 2.1 LangGraph checkpointer — ESTABLE 2026

- `AsyncPostgresSaver` de facto producción. Setup una vez (migrations propias).
- `thread_id` convención comunidad: `f"{tenant_id}:{user_id}:{conversation_id}"`. **RLS Postgres obligatorio** para aislamiento tenant — LangGraph no enforza.
- Alternativa `langgraph-redis` 0.1.0 sub-ms retrieval, pero TTL pierde time-travel. Nuestro caso: form filling 20-turn con recovery → Postgres mejor.
- Refs: `reference.langchain.com/python/langgraph.checkpoint.postgres/aio/AsyncPostgresSaver` (2025-2026).

### 2.2 Interrupts + HITL — ESTABLE 2026

- `interrupt({"prompt": "¿X?"})` dentro de nodo pausa grafo, persiste state, FE resume con `Command(resume="Y")`.
- Encaja **natural** para focus mode slot-filling: cada slot = interrupt.
- Functional API (`@entrypoint` + `@task`) alternativa más pythonic — menos boilerplate para flujos lineales.
- Gotcha: Langfuse no merge traces cross-resume (issue langfuse #10962). LangSmith/OTel sí.

### 2.3 Hybrid state-machine + LLM (StateFlow) — RECOMENDADO 2026

- Puro LLM-driven slot-filling → drift, hallucination. Puro FSM → pierde ventaja conversacional.
- **Hybrid domina 2026**: rails (graph/FSM) + LLM para parse/extract/confirm/rephrase.
- StateFlow (arxiv 2403.11322) reportó 4-6× cost reduction vs ReAct puro.
- Encaja: `block_generator.py` ya define secuencia lineal de bloques — promover a FSM formal con transitions `answer_ready / needs_clarify / skip / complete`.

### 2.4 ToolMessage.artifact — ESTABLE 2026

- Return tuple `(content_for_llm: str, artifact: dict)` con `response_format="content_and_artifact"`.
- Canónico para separar payload LLM (markdown/texto) de payload app (ui_action, session_hint).
- Elimina raíz del bug JSON-regurgitation que motivó `output_sanitizer.py`.
- Tipado Pydantic en artifact → `ToolResponse(text, llm_content, ui_action, error, session_hint)` enforçable.

### 2.5 Context engineering — ESTABLE 2026

- `trim_messages` + `SummarizationNode` (langmem) como `pre_model_hook`.
- Anthropic `memory` tool + server-side compaction: -84% tokens en web-search 100-turn eval. Si rotamos a Claude-only agents, relevante.
- Tool-result compaction manual: preservar `tool_call_id`, truncar `content` a N chars — no hay util oficial, patrón común.

### 2.6 Observability — OTel GenAI ESTABLE early-2026

- Semantic conventions `gen_ai.*` estables (input/output tokens, model, system, response.id).
- LangSmith E2E OTel support shipped.
- Nuestro `copilot_trace_event` ya es 80% del camino — falta schema Pydantic + alineación `gen_ai.*`.

---

## 3. Tradeoffs clave

### 3.1 Checkpointer Postgres vs Redis

| | Postgres | Redis |
|---|---|---|
| Durabilidad | Durable, WAL | TTL-based, evict |
| Tiempo read/write | ~10-50ms | <1ms |
| Time-travel | ✅ completo | ❌ TTL |
| Setup | migration + RLS | deploy nuevo service |
| Carga actual | visionarias_postgres compartido | no tenemos Redis persistente cluster-grade |

**Recomendación: Postgres**. Nuestras conversaciones son de duración humana (horas, no ms). Ya tenemos infra. TTL Redis rompería "reanudar mañana".

### 3.2 Persist-directo (worker URL) vs Propose-approve (inline DOC)

- Worker URL bulk auto-commit justificado: puede durar 2min, user no va a esperar. UX: "inicia, te aviso cuando termine".
- DOC preview+approve también justificado: inline rápido, user quiere revisar antes commit.
- **Decisión 2026 propuesta**: mantener **ambos modos como flag del worker unificado**. `commit_mode: "auto" | "preview"` en `ExtractionJob`. Subscriber único elige UX según flag.

### 3.3 Focus mode: BE-state vs FE-state

- BE-state (Postgres + checkpointer + focus_state sibling en procedure_state): survive reload, multi-device, durable.
- FE-state (Zustand persist localStorage): rápido, sin DB hit, pierde multi-device.
- **Recomendación: BE es SSoT**, FE mirror. Patrón convención 2026. FE localStorage solo para "last conversation", no para progreso form.

### 3.4 Sanitizer retirement

- Sanitizer es parche del síntoma JSON-regurgitation.
- Raíz = tools retornan JSON strings, LLM lo copia al AIMessage final.
- **Retirement seguro** cuando: (a) 100% tools migradas a `ToolMessage.artifact`, (b) arch test `test_no_tool_returns_json_as_string` en verde, (c) 2 sprints sin hit de sanitizer en producción.

---

## 4. Gaps que bloquean focus mode hoy

1. **No checkpointer** → no resume mid-turn, no multi-device.
2. **No session state de focus** (qué bloque está user viendo, qué falta). `GuidedState` es minimal; falta `visible_block_ids`, `dismissed_cards`, `locale`, `mode` (conversational/doc/url).
3. **Tools sin contrato formal** → sanitizer parchea; no hay enforcement al agregar nuevo dominio.
4. **Persisters no homologados** → agregar landing/assets/crm enrichment requerirá nuevo persister con firma distinta.
5. **source_tool hardcoded** → trazas no permiten separar "user subió doc" vs "user pegó URL" en summary card.
6. **No concurrency control** en `active_extraction_job` → pérdida silenciosa de jobs paralelos.
7. **FE no tiene focus sidebarState** ni nav lock ni progreso persistido.
8. **context_budget no compacta tool_results** → balloon en interviews largas.

---

## 5. Top-3 patrones a adoptar (mandatorio)

1. **`AsyncPostgresSaver` + `thread_id` por `tenant:user:conv`**. Resuelve (1), (2) y abre puerta a `interrupt()` para interview.
2. **`ToolMessage.artifact` con Pydantic `ToolResponse`**. Resuelve (3), retira sanitizer eventualmente, estandariza UI actions.
3. **Hybrid StateFlow para interview**: bloques ya existen — promoverlos a FSM formal con transitions + `interrupt()` por slot requerido.

## 6. Riesgos de implementación

- **RLS Postgres**: si adoptamos `AsyncPostgresSaver`, checkpoints viven en tabla global — requiere RLS o filtrado aplicativo tenant-aware. Omisión = potencial cross-tenant leak.
- **Migration legacy conversations**: guided_state existente en `procedure_state["guided"]` debe coexistir con checkpointer nuevo durante rollout. Dual-read feature flag 2 sprints.
- **Tool migration scope**: 31 tools × test × review = 3-4 sprints solo para envelope. Ratchet pattern: solo nuevas tools obligan contrato, legacy migran on-touch.
- **LangGraph `interrupt()` en SSE v2**: hay que verificar si el stream actual (`chat.py` `_persist_messages` + accumulator) maneja pause/resume de forma limpia. Spike 1-2 días.
- **Focus mode vs copilot libre**: UX crítica — cuando user escapa del flow, ¿kills session o conserva estado? Decisión humana.

---

## 7. Fuentes 2026 consultadas

- LangGraph PostgresSaver: reference.langchain.com/python/langgraph.checkpoint.postgres/aio (2025-2026)
- HITL `interrupt()`: docs.langchain.com/oss/python/langchain/human-in-the-loop
- LangChain blog "Making it easier to build HITL with interrupt" (2025-01)
- Functional API: blog.langchain.com/introducing-the-langgraph-functional-api (2025)
- ToolMessage.artifact: python.langchain.com/docs/how_to/tool_artifacts
- StateFlow (FSM+LLM): arxiv.org/html/2403.11322v1
- MemGuide missing-slot guided: arxiv.org/html/2505.20231v2
- Context Engineering: blog.langchain.com/context-engineering-for-agents (2025)
- Anthropic memory tool: platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool
- OTel GenAI 2026: dev.to/chunxiaoxx/ai-agent-observability-in-2026
- Checkpoint bloat mitigation: azguards.com/distributed-systems/the-checkpoint-bloat-...
- Multi-tenant LangGraph: forum.langchain.com/t/multi-tenant-per-user-checkpoint...
