---
name: copilot-expert
description: "Use cuando reportes/investigues bug del copilot module: loops infinitos, cards faltantes, conversaciones vacías al refresh, extracción que falla, trazas que mienten, tools que no ejecutan, costos disparados, routing equivocado, prompt cache roto, mutaciones que no persisten, channel format ignorado, voseo en outputs. Activa también para extender (agregar provider, tool, workflow, channel, KB chunk) sin romper invariantes. Triggers: 'bug copilot', 'loop copilot', 'card no aparece', 'conversación vacía', 'documento no extrae', 'agente no responde', 'tool no ejecuta', 'trazas mienten', 'tokens burned', 'extract_document_to_fields falla', 'propose_field_updates no persiste', 'format_for_channel ignored', 'voseo en respuesta', 'cache hit rate', 'cuántos tokens', 'agregar provider', 'agregar workflow', 'agregar tool transversal', 'agregar canal'."
---

# Copilot Expert

Copilot = "Claude Code de marketing": deep_agent harness sobre LangGraph, discovery por convención, plan_card visible, RAG curado, channel-aware, observabilidad event-sourced. **Diseñado en 11 fases (F0-F11) por expertos**. Bugs casi siempre = ejecución, no diseño.

**Regla cero:** verificá que algo existe (grep + schema + registry + repo) ANTES de declarar "falta X" o "hay que crear Y". Si decís "no existe", grepeá primero.

---

## Stop. Lee primero, no asumas.

| Concern | SSoT | Cuándo |
|---|---|---|
| Debug runtime / trazas mintiendo / loop / card no aparece | `.claude/rules/copilot-resilience.md` | **siempre primero** en cualquier bug |
| Observability module structure / costos / pricing / PII / retention | `.claude/rules/copilot-observability.md` | tocar `observability/` o queries de costo |
| Mapa de docs internos | `docs/domains/copilot/INDEX.md` | navegar el módulo |
| Arquitectura redesign | `docs/domains/copilot/redesign-2026-04/02-architecture-target.md` | entender topología |
| Cómo migró cada fase | `docs/domains/copilot/redesign-2026-04/learnings/F{N}-*.md` | gotchas históricos por capa |
| Resultados QA | `docs/domains/copilot/testing-2026-04/results/TP*.md` | qué se midió y dió |
| Fixes post-redesign | `docs/domains/copilot/fpos-2026-04/results/FP*.md` | hooks H1-H8 cerrados |
| SSE v2 + blocks | `docs/domains/copilot/CONTRACT-MULTIMODAL.md` + `sse-protocol.md` | streaming/cards |
| Spanish neutro | `.claude/rules/spanish-text.md` | cualquier texto user-facing |

---

## Diagnóstico — orden estricto (no saltarse)

```
1. Conversation ID + tenant_id → query copilot_trace_event
2. Si no hay trazas del turn → bug observabilidad (recorder), NO el feature
3. Si trazas con status='error' → identificar capa (route / tool / persist / kwargs / stream)
4. Si trazas status='ok' pero síntoma persiste → trazas mintiendo (Fix turn_end status)
5. copilot_llm_call (provider/model/tokens/costo/duration_ms) — leer cost+model de columnas tipadas, NO del JSONB legacy
6. copilot_conversations.messages JSONB para shape exacto
7. copilot_routing_log (tier/classifier/confidence/tools_available)
8. copilot_mutation_journal (cambios via propose_field_updates)
9. Streamlit admin /trazas /copilot-routing /costo-copilot /copilot-quality /marketing-kb
10. docker logs visionarias_brain_dev SOLO si trazas no alcanzan
```

Queries esenciales: ver `.claude/rules/copilot-resilience.md` §"Debug copilot".

---

## Arquitectura inmutable — NO tocar sin entender

**Topología F0-F11 (cementada):**

| Capa | Owns | Editar = riesgo |
|---|---|---|
| `copilot/domain/` | ports (CopilotProvider, DataAccessProvider, BaseCopilotProvider), workflow, output_channels, module_registry | Cambios cascada al ratchet + tests fitness |
| `copilot/infrastructure/` | repos (conv, inspirations, pinned_memory, mutation_journal, workflow_metric, marketing_kb_store), persisters, qdrant | Schema drift |
| `copilot/application/` | orchestrator (chat, deep_agent, system_prompt_layout, graph), tools, workflows engine, observability (judge, node_trace, rag_goldens), data_access | Lógica de negocio |
| `copilot/api/` | FastAPI thin routes | Contract |
| `copilot/observability/` | recording (callback + sanitization + turn_envelope), pricing, cost, persistence, reporting, workers | Hot-path latency |

**Registries (no hardcodear):**
- `module_registry` (F1) — descubre `src.modules.{name}.copilot_provider:provider`
- `ROUTE_TOOL_MAP` + `_BASE_TOOL_GROUPS` + `ALWAYS_AVAILABLE_GROUPS` (F1+F4+F5+F7)
- `MARKETING_KB_HINT` slot 3 system prompt (F10)
- `CHANNEL_FORMATS` + `register_channel` (F7)
- `CHAT_MODEL_SPEC` per provider service (post-incident 2026-04-27)
- `_default_accessors` per kind para `ask_tenant_data` (F5)
- `WorkflowProvider.workflows()` aggregator (F6)
- `EXTRACTION_CONTRACTS` (analytics, ortogonal)

**Anchors (`[COPILOT-*]`):** registry tiene cap 36/36 desde F11. Agregar 1+ requiere bumpear `tests/architecture/test_copilot_anchors.py:96`.

**Ratchet `copilot → módulo` import: 22 frozen.** Solo shrinks. Nuevo provider = no toca el ratchet (consume domain abstracción, no concreción).

**System prompt order (F8 §5.2 + F10 slot 3):**
```
[1 cacheable cross-tenant] static_identity
[2 cacheable cross-tenant] tools_hint
[3 cacheable cross-tenant] marketing_kb_hint        ← F10
[4 cacheable per-tenant]   lighthouse (brand_summary)  ← F3
[5 cacheable per-tenant]   editable_catalog
[6 cacheable per-tenant]   modules_list
[CACHE_BOUNDARY_MARKER]
[7 volatile per-turn] completion_snapshot + behavior + guided + studio  ← F0/F8
[8 volatile per-turn] inspirations_layer  ← F4
[9 volatile per-turn] workflow_state hint (cuando F12 cutover)
[10 volatile per-turn] channel_intent_hint  ← FP2
[11 volatile per-turn] deep_agent_suffix  ← F2 (siempre al final)
```

Reordenar = romper cache + cascada en goldens (`test_system_prompt_order.py`, `test_brand_lighthouse_in_system_prompt.py`).

---

## Principios meta — leer antes de tocar

1. **Diseñado por expertos.** Cada decisión está documentada en `learnings/`. Si pensás "esto está mal" → leer learning de la fase responsable. 90% de las veces hay razón.

2. **Alta cohesión.** Cada subpaquete una sola responsabilidad. Lógica nueva va donde corresponde semánticamente, no donde es cómodo. Ej: brand_summary repo vive en `brand/`, no en `copilot/` — es cache derivado de brand (F3).

3. **Bajo acoplamiento.** Cross-module imports prohibidos fuera de `shared/links/` o `_PROVIDER_CONTRACT_IMPORTS`. Necesitás data de otro módulo → port en `shared/links/` o domain event. Provider pattern existe para no acoplar.

4. **No premature refactor.** Bug se arregla con N líneas → fix con N líneas. Refactor paralelo va a `docs/mejoras-proceso/to-do.md`. Cada fase entrega UNA cosa.

5. **No hardcoded.** Field names ← `schema_introspection`. Routes ← `navigation_map`. Tools ← `tools/registry`. Models ← `module_registry`. Pricing ← `model_pricing_snapshot`. Si encontrás hardcoded, raíz del bug está cerca.

6. **TDD obligatorio.** Test que reproduce bug PRIMERO. Sin test reproductor no hay fix. Single root cause per fix.

7. **Best-effort observability.** Recorder nunca debe romper turn. Try/except + structlog warning + `db.rollback()`.

8. **Tenant isolation.** Toda query filtra `tenant_id` excepto KB curado tenant-agnóstico (`marketing_kb` Qdrant collection, F10).

---

## Anti-patrones recurrentes — checklist antes de declarar bug

| Síntoma | Causa común (NO suposición — patrón cementado) |
|---|---|
| Loop infinito agent | Route resolver no extrae entity_id (route nuevo) + sin anti-loop guard parent + sin partial persist |
| Conversación vacía al refresh | `acc.messages = []` en exception path de `chat.py` |
| Trazas dicen `status='ok'` pero falló | `set_turn_error` no llamado en except block del orchestrator |
| Card no aparece | SSE v2 `block_append` no emitido por handler de tool |
| Tool no ejecuta | Tool no en `ROUTE_TOOL_MAP` para esa ruta o no en `ALWAYS_AVAILABLE_GROUPS` |
| `format_for_channel` ignorado pese a "WhatsApp" | `channel_intent` middleware no inyecta hint (FP2) |
| Mutation no persiste | `ProposalCard.handleApply` sin `activeBridge` + sin fallback `/mutations/apply` (FP1) |
| Tokens disparados DeepSeek/Kimi | `max_tokens → max_completion_tokens` rewrite LangChain `BaseChatOpenAI` |
| `Completions.create() got 'max_output_tokens'` | Falta normalizer en `providers/_kwargs.py` para protocol |
| Cache hit rate 0% | Prefix < 1024 tokens (sin lighthouse, sin editable_catalog) o reorden rompió contiguidad |
| `cache_hit_rate` siempre `NULL` en JSONB | `_build_turn_end_data` no mergea `usage.as_log_dict()` |
| Voseo en output user-facing | Prompt template hardcoded voseo (`copilot_system_static.j2`, `subagents/*.py`) — F4 fix `_VOSEO_RE` regex sweep |
| Provider scan abre Postgres en boot | DB connection en module-load time (F4 gotcha) — diferir a `__call__` |
| `pkgutil` no encuentra módulos | Namespace packages (`assets/connections/iam/sales_agent` sin `__init__.py`) → filesystem scan |
| `pg_insert` rompe SQLite | `constraint=` no portable → usar `index_elements=[...]` |
| `func.now()` ORDER BY no determinístico | Segundo precision SQLite → Python-side `default=utc_now` para microsecond |
| Test pasa standalone, falla en suite | Modelo SQLA nuevo no registrado en `tests/conftest.py::db_engine` |
| `pg_insert.excluded.X` AttributeError | Column con alias Python ≠ SQL name → renombrar a paridad |
| Subagent ejecuta tools del parent | `SubAgent` TypedDict sin `tools=[]` explícito hereda toolset |
| `extra="forbid"` rompe payloads | Pydantic state schema rechaza keys legacy → considerar `extra="allow"` o cleanup |
| Tool group collision `id()` | Provider importa `tool` desde path no-canónico → debe ser misma instancia |
| `structlog` `event=...` TypeError | Kwarg reservado → usar `event_name=` |
| Discovery cache stale en tests | Falta `_reset_provider_discovery()` autouse fixture |
| `ON CONFLICT` constraint name SQLite | `index_elements=[...]` (heredado F2) |
| Anchor budget exhausto | Cap 36/36 → bumpear `test_copilot_anchors.py:96` antes de agregar |

---

## Bug-fix protocol

```
1. Reproducir → query trazas de la conv afectada
2. Capa identificada (1 de 8): routing / system_prompt / tool_dispatch / deep_agent / persist / kwargs / streaming / observability
3. RED: test que reproduce el bug en aislamiento (Vitest si FE, pytest si BE)
4. Fix mínimo — no scope creep
5. GREEN: test verde + suite afectada verde + arch tests verdes
6. Quality gates: ruff check + ruff format + pytest del módulo + pytest architecture
7. Replay end-to-end: si síntoma original era live, reproducir manualmente
8. Si emerge tech debt → docs/mejoras-proceso/to-do.md
9. Commit conventional: type(scope-id): summary
```

**Regla**: si llegás al paso 4 sin haber leído el learning de la fase responsable, retroceder. El gotcha probablemente está documentado.

---

## Mapa de fases — cada una entregó UNA cosa

| Fase | Entregó | Archivo SSoT |
|---|---|---|
| F0 | Foundation cleanup, deepagents 0.5.3, golden snapshots, ratchet skip-by-default | `learnings/F0-foundation.md` |
| F1 | Provider pattern + discovery (convention + entry points), `BaseCopilotProvider`, ratchet enforce, brand pilot | `learnings/F1-provider-pattern.md` |
| F2 | Deep agent harness `build_deep_agent_graph`, plan_card via `write_todos` args, `CopilotPinnedMemoryRepository` | `learnings/F2-deep-agents-harness.md` |
| F3 | `brand_summary` lighthouse cacheable, ARQ regen, judge sync voseo regex, `_collect_context_injectors_prefix` | `learnings/F3-brand-summary-lighthouse.md` |
| F4 | URL contextual (`fetch_url` + `pin_to_memory`), `copilot_inspiration` table, `URL_ANALYZER_SUBAGENT` sandbox `tools=[fetch_url]`, `inspirations_layer` state-aware | `learnings/F4-url-contextual-scratchpad.md` |
| F5 | `ask_tenant_data` deterministic pipeline (intent NANO → query → exec → state_check → synth FAST), `DataAccessProvider` port despacha por kind, `DATA_QUERY_SUBAGENT` | `learnings/F5-ask-tenant-data.md` |
| F6 | Workflow declarativo (`Workflow` + `WorkflowEngine` Python deterministic + `handler_ref` lazy), migration 071 `workflow_state JSONB` + dual-read, pilots brand+offer | `learnings/F6-workflow-unification.md` |
| F7 | `ChannelFormat` registry + `format_for_channel` determinístico (sin LLM call), `register_channel` extension API | `learnings/F7-channel-formatter.md` |
| F8 | `LLMClassifier` NANO threshold 0.7, `compose_system_prompt` reorden cache-friendly (≥1024 tokens prefix), SSE v2 only (delete `text_chunk`), admin `/copilot-routing` | `learnings/F8-routing.md` |
| F9 | `CopilotJudge` 4-dim multi-rubric NANO single JSON, 20 goldens stub default + `RUN_LLM_JUDGE=1` opt-in, `weekly_copilot_quality_eval` ARQ lunes 05:00 UTC, `node_enter`/`node_exit` from `astream_events` | `learnings/F9-quality.md` |
| F10 | `MarketingKbStore` Qdrant tenant-agnóstica `nicolify_marketing_kb` dim 3072, `chunk_markdown` breadcrumb-aware, `knowledge_search` tool, 31 docs curados, RAG goldens (8) | `learnings/F10-marketing-kb.md` |
| F11 | Drop legacy KB residue, `build_default_router` wired (telemetry-only), `weekly_copilot_rag_eval` lunes 06:00 UTC, fix flaky `test_no_cross_domain_duplicates` | `learnings/F11-housekeeping.md` |

**Pendiente F12**: cutover `procedure_state → workflow_state` (3 sub-fases). Ver `phases/F12-procedure-state-cutover.md`.

**Observability rebuild (paralelo, cerrado):**
- Phase 1: callback handler + pricing resolver + LiteLLM sync + repos
- Phase 2: atomic switch (callback handler único, delete legacy paths)
- Phase 3: BillingCycleService + CostAggregator + MV daily + retention worker + cost alerts + `/costo-copilot` dashboard

---

## Cost guards (no quemar tokens)

- **2 LLM calls FAST max** por pregunta (F5 patrón). Pipeline determinístico Python entre ellos.
- **NANO** para intent classification (F5/F8/F9 cementado). Modelo NANO default `gpt-4o-mini` (env override).
- **Threshold 0.7** para auto-act vs fallback (F8/F9 coherencia cross-fase).
- **LLM-judge sync regex** donde alcance (length cap, voseo) — NO segundo LLM call para reglas sintácticas.
- **Cache hit rate ≥60%** target post-deploy. Verificar con `/copilot-routing` `avg_cache_hit_rate`.
- **Stub default + `RUN_LLM_JUDGE=1` opt-in** para goldens. Real LLM solo en weekly cron.
- **6_000 calls/month judge ≈ $0.024** (F9 cost guard documentado).
- **Subagent con `tools=[]` explícito** — NO heredar toolset parent (F2 + F4 patrón).

---

## SSE v2 protocol (F8 + post-rewrite)

Eventos canónicos:
```
status (state: streaming|done) → message_start (msg_id) → block_start | block_delta | block_end | block_append (cards) → tool_start → tool_result → ui_action (legacy compat) → message_end → done | error
```

`text_chunk` legacy borrado en F8 — FE handler tolera no-op por bundles cacheados. Cualquier fase futura que toque protocolo SSE: **grep FE por handlers ANTES de tocar BE**.

Block types canónicos: `text`, `image`, `audio`, `document`, `video`, `citation`, `tool_call`, `card` (kinds: `plan_card`, `inspiration_saved`, `memory_pinned`, `proposal_card`, `clarify`).

---

## Cuándo extender (no parchear)

| Quiero agregar | Pasos cementados |
|---|---|
| Nuevo módulo Nicolify al copilot | (1) `src/modules/{name}/copilot_provider/__init__.py:provider` heredando `BaseCopilotProvider`. (2) Discovery lo encuentra automático. (3) NO editar `copilot/`. |
| Tool transversal (cross-route) | (1) `copilot/application/tools/{name}.py` con `@tool`. (2) Agregar a `_BASE_TOOL_GROUPS["{group}"]`. (3) Si transversal, agregar group a `ALWAYS_AVAILABLE_GROUPS`. (4) Update goldens `route_tool_selection.json` con `UPDATE_GOLDEN=1`. |
| Tool de un módulo | Provider expone via `tool_provider().tool_groups()`. NO editar `copilot/tools/registry.py`. |
| Nuevo `kind` para `ask_tenant_data` | (1) Agregar a `intent_classifier.SUPPORTED_KINDS`. (2) Update system prompt classifier. (3) `{module}/copilot_provider/data_access.py` con `supports(new_kind)`. |
| Nuevo canal output | `copilot/domain/output_channels.py` → `register_channel(ChannelFormat(...))`. Test arch valida. |
| Nuevo workflow | `{module}/copilot_provider/workflows.py` declarativo + `workflow_handlers.py` con `handler_ref` lazy. Discovery los encuentra. |
| Nuevo provider LLM | (1) Subclase `OpenAICompatibleService` o nuevo si protocolo distinto. (2) Declarar `CHAT_MODEL_SPEC`. (3) Agregar a `LLMRouter.build_provider_service`. (4) Pricing entra automático via LiteLLM sync diario. |
| Nuevo subagent | (1) `subagents/{name}.py` con `SubAgent` TypedDict. (2) **Declarar `tools=[explicit_list]`** — sandbox. (3) Exportar desde `subagents/__init__.py`. (4) `deep_agent.py` lo agrega via `extend()`. |
| Nuevo `[COPILOT-*]` anchor | Agregar a `tests/architecture/test_copilot_anchors.py::ANCHOR_REGISTRY`. Cap actual 36 — bumpear si supera. |
| Nuevo dominio event | `copilot/domain/events.py` subclass `DomainEvent` + classmethod `create()` + literal `EVENT_*`. Publish via `event_bus.publish(..., session=None)` (no `db=`). Subscriber opcional en `observability/recording/domain_subscribers.py`. |
| Nuevo chunk de KB | `backend/data/marketing_kb/{nuevo}.md` con front-matter válido. `python scripts/seed_nicolify_marketing_kb.py --only nuevo.md`. |

---

## Banco de patrones recurrentes (abstraídos, no incidentes)

### Pattern: Loop infinito del agent
**Síntoma**: agent llama mismo tool repetidamente → GraphRecursionError → conversación vacía al refresh.
**5 capas a verificar (orden estricto):**
1. ¿Route resolver extrae `entity_id` correcto? (`graph.py::_resolve_studio_context` regex)
2. ¿Existe anti-loop guard? (`tool_call_dedup.py::ToolCallDedupTracker` per-turn)
3. ¿`recursion_limit` configurado? (`COPILOT_RECURSION_LIMIT` env, default 25)
4. ¿Partial persist en exception path? (no wipe `acc.messages` en catch)
5. ¿Trazas honestas? (`set_turn_error` en orchestrator's catch + `_TurnErrorFlag` en envelope)

### Pattern: Card no aparece pese a tool firing
**Síntoma**: tool se ejecutó (visible en `copilot_trace_event`), pero FE no muestra card.
**Verificar (orden):**
1. `_handle_tool_end_v2` retorna `block_append` SSE event para ese tool
2. `_tool_result_to_block(tool_name, tool_output)` mapea correctamente
3. FE `copilot-api.ts` parser tiene case para el block type
4. `CardBlock.tsx` o renderer correspondiente acepta el `card_kind`

### Pattern: Conversación vacía al refresh
**Síntoma**: turn completó (FE vio respuesta), refresh muestra conv blank.
**Causa única**: exception en `_run_graph_stream` → `acc.messages = []` antes del persist. Fix: NO wipear acc, dejar persist con state acumulado.

### Pattern: Trazas dicen `ok` pero falló
**Síntoma**: query `copilot_trace_event` muestra `turn_end status='ok'` pero hubo error real.
**Causa única**: orchestrator catchea exception internamente → envelope ve clean exit → marca ok. Fix: `acc.obs.set_turn_error(error_kind, error_message)` en cada except block antes del SSE error yield.

### Pattern: Kwarg drift entre providers
**Síntoma**: `Completions.create() got unexpected keyword argument 'X'` solo para algunos providers.
**Causa única**: traducción canónica vive solo en uno de los providers. Fix: hoistear a `providers/_kwargs.py::normalize_openai_protocol_kwargs` (SSoT) — ambos `OpenAIService` y `OpenAICompatibleService` consumen.

### Pattern: Cache hit rate cae a 0%
**Síntoma**: `/copilot-routing` muestra cache hit ~0% sostenido.
**Verificar (orden):**
1. Prefix size ≥1024 tokens contiguos sin cambios (`compose_system_prompt(static_only_fragments)`)
2. Lighthouse populated (`brand_summary` table no vacía para el tenant)
3. Editable_catalog populado (módulos discoverables)
4. Reorden reciente que insertó volatile entre cacheable

### Pattern: Voseo persiste pese a regex sweep
**Síntoma**: outputs user-facing tienen "tenés/podés/querés" tras varios fixes.
**Verificar (orden):**
1. Prompt templates `.j2` (`copilot_system_static.j2`, `_modules.j2`, etc) — texto hardcoded
2. Subagent system prompts (`subagents/*.py`) — strings inline
3. Tool descriptions (Pydantic Field descriptions, docstrings que el LLM lee)
4. SSoT externos como `_DEEP_AGENT_SUFFIX_ES` en `deep_agent.py`
5. Channel format `structure_hint` en `output_channels.py`

`_VOSEO_RE` en `brand_summary_regen.py` es la regex canónica. Test `test_deep_agent_prompt_voseo_compliance.py` cubre el suffix.

### Pattern: ProposalCard click sin persist
**Síntoma**: user click "Aplicar" en ProposalCard, UI muestra "Aplicado" verde, pero `copilot_mutation_journal` vacío + form fields vacíos al refresh.
**Causa única**: bridge no conectado → no-op silent. Fix FP1: fallback POST `/mutations/apply` con natural-key idempotency (`(tenant, conv, message, field_path)` partial unique index).

### Pattern: Channel format ignorado
**Síntoma**: user pide "armame copy WhatsApp" → respuesta prosa estructura genérica, `format_for_channel` no fired en trazas.
**Causa única**: tool no force-bound, LLM no inferred. Fix FP2: `channel_intent_detector` regex middleware → `state["channel_intent"]` → hint inyectado en system prompt → LLM lo elige.

---

## Checklist pre-cierre de bug-fix

- [ ] Test reproductor RED → GREEN (commitado en mismo PR)
- [ ] Suite afectada verde aislada
- [ ] `test_copilot_anchors.py` verde (cap respetado)
- [ ] `test_no_new_copilot_module_imports.py` verde (ratchet 22 frozen)
- [ ] `test_copilot_provider_compliance.py` verde
- [ ] `test_deep_agent_harness_invariants.py` verde si tocaste harness
- [ ] `test_system_prompt_order.py` verde si tocaste prompt
- [ ] Goldens regenerados con `UPDATE_GOLDEN=1` si cambiaste `_BASE_TOOL_GROUPS` / `ALWAYS_AVAILABLE_GROUPS` / `ROUTE_TOOL_MAP` / route resolver
- [ ] Lint + format clean (`ruff check` + `ruff format --check`)
- [ ] Docker container healthy post-restart
- [ ] Replay manual del síntoma original (si era live)
- [ ] Spanish neutro verificado (`_VOSEO_RE` sweep si user-facing)
- [ ] PII sanitizada si tocaste `recording/` (regex en `sanitization.py`)
- [ ] Trace recorder honest (`set_turn_error` si catcheaste exception)
- [ ] Tech debt nuevo → `docs/mejoras-proceso/to-do.md`

---

## Comandos cementados

```bash
# Suite copilot completa (sin flakies aislados)
cd backend && .venv/bin/pytest tests/modules/copilot/ tests/architecture/ tests/admin/ tests/quality/ \
  -q -o addopts="" --timeout=120 \
  --ignore=tests/modules/copilot/test_streaming_integration.py

# Streaming aislado (heredado flaky F0+)
cd backend && .venv/bin/pytest tests/modules/copilot/test_streaming_integration.py -q

# Goldens
cd backend && .venv/bin/pytest tests/modules/copilot/golden/ -q

# Regenerar goldens (cambio intencional)
cd backend && UPDATE_GOLDEN=1 .venv/bin/pytest tests/modules/copilot/golden/ -q

# Arch tests fitness
cd backend && .venv/bin/pytest tests/architecture/test_copilot_*.py tests/architecture/test_no_new_copilot_module_imports.py tests/architecture/test_workflow_compliance.py tests/architecture/test_channel_formatter_compliance.py -q

# Real LLM judge (weekly opt-in)
RUN_LLM_JUDGE=1 .venv/bin/pytest tests/quality/golden/ -q

# Trazas de una conv específica
docker exec visionarias_postgres psql -U postgres -d visionarias_logs -c "
SELECT created_at, event_type, name, status, duration_ms, LEFT(data::text, 300)
FROM copilot_trace_event WHERE conversation_id = ':conv_id'
ORDER BY created_at;"

# Cost por ciclo billing 25-25
docker exec visionarias_postgres psql -U postgres -d visionarias_logs -c "
SELECT compute_cycle_start(:tenant_id, CURRENT_DATE) AS cycle_start,
       SUM(cost_usd) AS cycle_cost, COUNT(*) AS calls
FROM copilot_llm_call
WHERE tenant_id = :tenant_id AND occurred_on >= compute_cycle_start(:tenant_id, CURRENT_DATE);"

# Reload backend post-edit
docker compose restart api_dev
```

---

## Anchor — qué hago primero

Cuando reportes bug del copilot, mi primer mensaje SIEMPRE va a ser:

```
1. Stop. Lee primero.
2. Conv ID + tenant_id?
3. Query copilot_trace_event de esa conv.
4. Identifico capa (1-8 anti-patrones).
5. Verifico que algo "falte" antes de declararlo (grep + registry + repo).
6. RED test → fix mínimo → quality gates → replay.
```

Sin esos 6 pasos cumplidos, no toco código.
