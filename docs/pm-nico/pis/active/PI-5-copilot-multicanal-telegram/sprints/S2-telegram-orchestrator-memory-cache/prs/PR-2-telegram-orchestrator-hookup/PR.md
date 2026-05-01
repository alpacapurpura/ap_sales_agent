# PR-2-telegram-orchestrator-hookup

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-2-telegram-orchestrator-hookup |
| Sprint padre | S2-telegram-orchestrator-memory-cache |
| PI padre | PI-5-copilot-multicanal-telegram |
| Estado | in-progress |
| Tipo | feature |
| Esfuerzo | L |
| Owner PM | /pm |
| Claimed by session | 2026-04-30 — agentic surface only (modules/copilot/) |

## Problema (user-facing)

Hoy el dueño linkeado a `@nicolify_copilot_bot` (PR-1 shipped commit `c1fa2909`) recibe **placeholder reply** ("recibí tu mensaje desde Telegram") cuando escribe al bot — no hay copilot real respondiendo. Memory config + cache fragment + tool filter runtime + format adapter Telegram-specific son los componentes que falta cablear para que el bot responda con el copilot orchestrator real.

JTBD: "Cuando estoy fuera de la laptop, quiero consultar el estado de mi negocio en Telegram y recibir respuesta del **mismo copilot** que uso en la web — no un bot distinto, no respuestas genéricas, sí mismo conocimiento + voz."

## Outcome esperado

Dueño linkeado escribe al bot Telegram → recibe respuesta **del copilot orchestrator real** con:
- Misma KB + tools + voz que copilot web
- Tool subset filtered runtime (web-only excluded — `navigation`, `guided`, `landing` mutations, `offer_section` mutations responden via `redirect_to_web` template)
- Formato Telegram MarkdownV2 escapado (no breaking chars)
- Ventana de memoria optimizada para Telegram (3000 raw tokens, 15 msgs, summary 600 chars — más amplia que web por sesiones espaciadas)
- Prefijo cacheable Anthropic ≥1024 tokens (cache hit ahorro 90% input cost desde 3er turno)

Métrica medible:
- Webhook handler 200ms (preservado PR-1)
- Latencia first-token p95 < 5s (medible S2 con orchestrator real, no medible PR-1)
- Cache hit rate > 60% en conversación ≥3 turnos (instrumentar via observabilidad existente `copilot_llm_call`)

## Walking skeleton (mínimo viable cohesivo)

Single PR cohesivo agentic-only:
1. Worker linked branch invoca orchestrator real (reemplaza placeholder)
2. Conversation lookup por `(tenant_id, user_id, channel_type='telegram', channel_chat_id)`
3. `TELEGRAM_CONTEXT_WINDOW_CONFIG` + inyección por channel en `ContextWindowBuilder`/`RollingSummarizer`
4. `TELEGRAM_CHANNEL_CONTEXT` cacheable fragment ≥1024 tokens en `system_prompt_layout.py`
5. `get_tools_for_context(context, channel='telegram')` runtime filter
6. `format_for_channel(channel='telegram', parse_mode='MarkdownV2')` adapter post-orchestrator
7. Tests integration end-to-end + tests memory + arch fitness cache prefix

Cohesivo porque TODOS tocan path: webhook → worker → orchestrator → memory → tools → format → bot send. Splittear = artificial (cada pieza solo cobra sentido al cablear el flow completo).

## Soluciones consideradas

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A. Hookup completo cohesivo (1 PR)** | Cohesión funcional natural; Opus 4.7[1M] handle scope L; 1 architect + 1 builder + 1 auditor | Requiere disciplina alcance (no bloat) | **ELEGIDA** |
| B. Splittear PR-2a (orchestrator hookup) + PR-2b (memory config) + PR-2c (cache fragment) | Cada PR mini-tested aislado | Memory + cache + hookup no testean fin a fin sin los 3 cableados — splittear obliga mocks artificiales y refactor cuando se integra | descartada — fragmentación sin valor |
| C. Diferir cache fragment a PR futuro | Foco S2 = orchestrator hookup únicamente | Sin `TELEGRAM_CHANNEL_CONTEXT` el prefijo cacheable Telegram cae <1024 → cache miss 100% → costo Anthropic 10× sin ganancia | descartada — D-PI5-009 explícito |

## Validación técnica preliminar (Technical Sanity Check)

> PM consumió handoff S1 + research file existente (`2026-04-30-telegram-bot-copilot-patterns.md` §1 + §6). Architect formaliza CONTRACT en su fase.

- **Modules afectados:** `modules/copilot/` (single surface — application/memory + application/orchestrator + application/tools + infrastructure/workers). Cero `modules/{brand,offer,...}`. Cero frontend. Cero migration DB (cols ya añadidas PR-1).
- **Blockers conocidos:** ninguno bloqueante. Migration 114 pre-existing NO bloquea S2 (no requiere migration nueva).
- **Tiempo estimado:** ~2 ejecuciones Chris (architect + builder-con-auto-audit). PR scope L pero single-surface = sin paralelización builder.
- **Alternativas técnicas:**
  - Memory config inyección: param canal en constructor `ContextWindowBuilder(channel='telegram')` vs lookup en `__call__`. Architect decide. Default 'web' preserva backward compat.
  - Cache fragment placement: dentro `CACHEABLE_FRAGMENTS` global vs sub-list condicional por channel. Architect decide segun cómo `system_prompt_layout` ya estructura fragments.
  - Conversation lookup: SELECT FOR UPDATE (pessimistic) vs UNIQUE constraint + INSERT ON CONFLICT (optimistic). Architect decide según concurrency expectativa.

## Existing systems audit (architect-mandatory ANTES de proponer nueva capa)

> NO-NEW-LAYER rule. Antes de inventar memory builder paralelo, cache fragment paralelo, orchestrator wrapper paralelo — VERIFICAR existentes.

Subsistemas que toca este PR + greps obligatorios:

- [ ] **Context window builder + rolling summarizer** (memory):
  - `find backend/src/modules/copilot/application/memory/ -type f -name "*.py"`
  - `grep -rn "ContextWindowConfig\|ContextWindowBuilder\|RollingSummarizer\|RAW_WINDOW_TOKENS" backend/src/modules/copilot/`
  - **Esperado:** EXTEND `ContextWindowBuilder` con param channel + crear nueva instancia `TELEGRAM_CONTEXT_WINDOW_CONFIG` en mismo módulo. NO duplicar builder.
- [ ] **System prompt layout + cache fragments**:
  - `grep -rn "CACHEABLE_FRAGMENTS\|CACHE_BOUNDARY_MARKER\|system_prompt_layout\|STATIC_IDENTITY\|LIGHTHOUSE\|MODULES_LIST" backend/src/modules/copilot/`
  - **Esperado:** EXTEND `system_prompt_layout.py` añadiendo `TELEGRAM_CHANNEL_CONTEXT` fragment. NO crear `telegram_prompt_layout.py` paralelo.
- [ ] **Tool registry filter por canal**:
  - `grep -rn "ToolGroupMeta\|available_channels\|get_tools_for_context\|is_group_available_in_channel" backend/src/modules/copilot/`
  - **Esperado:** EXTEND llamada `get_tools_for_context()` desde orchestrator pasando `channel` param ya soportado PR-1. NO nueva función `get_telegram_tools()`.
- [ ] **Channel format adapter** (MarkdownV2 escape):
  - `grep -rn "format_for_channel\|escape_markdown_v2\|parse_mode" backend/src/modules/copilot/ backend/src/shared/`
  - **Esperado:** EXTEND llamada `format_for_channel()` post-orchestrator. Reusar `escape_markdown_v2` existente (`shared/agent_observability/channels/format.py`). NO inline escape ad-hoc.
- [ ] **Orchestrator invocation** (entrypoint):
  - `grep -rn "invoke_copilot_orchestrator\|run_orchestrator\|CopilotOrchestrator" backend/src/modules/copilot/application/orchestrator/`
  - **Esperado:** EXTEND llamada existente con `channel='telegram'` param. Si entrypoint no soporta channel → flag § 16 architect open question (architect decide signature change).
- [ ] **Conversation repository lookup**:
  - `grep -rn "CopilotConversationRepository\|get_by_channel\|channel_chat_id" backend/src/modules/copilot/`
  - **Esperado:** EXTEND repo con método `get_or_create_by_channel(tenant_id, user_id, channel_type, channel_chat_id)` si no existe. NO nuevo repo paralelo.

Decisión EXTEND vs NEW debe estar en CONTRACT § Existing Systems Audit con paths reales + LOC referenciadas.

## Decisiones diferidas (explícitas)

- HITL escalation sales_agent ↔ copilot → S3 PR-3
- Push notifs proactivas + encargos in-app inbox → S4 PR-4
- Multi-role tool filter implementation (filtros por `role`) → PI futuro
- Vector retrieval Qdrant Telegram conversations (D-PI5-008) → post-launch si feedback "no recuerda contexto viejo"
- Voice messages + cards interactivas avanzadas → PI futuro
- Migration 114 fix pre-existing → ticket separado fuera scope PI-5
- Bot username squat protection + setWebhook script automatizado → S5 PR-5

## Out of scope

- Cero cambios FE (`/{tenantId}/settings/copilot/telegram` page + `<TelegramLinkingClient />` ya completos PR-1)
- Cero cambios DB schema (cols `channel_type` + `channel_chat_id` + tablas `copilot_channel_links` + `copilot_link_tokens` ya live PR-1)
- Cero cambios módulos negocio (`brand`, `offer`, `analytics`, `connections`, etc.)
- Cero cambios `modules/sales_agent/` (separación física D-PI5-005 mantenida)
- Cero cambios `core/config.py` Settings (env vars Telegram ya añadidas PR-1)
- Cero cambios webhook handler `POST /api/v1/copilot/telegram/webhook` (NON-BLOCKING + secret_token + private filter ya live PR-1)

## Copilot-first checklist

- [x] **¿Operable conversacional desde copilot?** — sí. ESTE PR ES LA PIEZA QUE HACE COPILOT TELEGRAM REAL. El propio outcome es copilot-first activación.
- [x] **¿Qué tools nuevos requiere?** — ningún tool nuevo. Reusa registry existente con filter `channel='telegram'`. Tools telegram-allowed activos: `awareness`, `analytics`, `crm`, `sales_agent`, `extraction`, `knowledge_search`, `data_query`, `document`, `channel_format`, `pin_to_memory`, `mutation` (parcial), `offer_ladder` (consulta).
- [x] **¿Cards/UI nueva?** — ninguna. FE completo PR-1.
- [x] **Si NO copilot → razón documentada** — N/A (es copilot-first 100%)

## Agentes / skills recomendados

(Ver `process/agent-routing-matrix.md`)

| Fase | Agente/skill | Prompt pre-coce | Entregable esperado |
|---|---|---|---|
| Pre-flight contexto | `nicolify-context-builder` (Haiku) | `prompts/00-context-prep.md` | `CONTEXT-BRIEF.md` |
| Pre-design | `nicolify-architect` (Opus) | `prompts/01-architect-start.md` | `CONTRACT.md` |
| UX | — (cero cambios FE) | — | — |
| Implementation | `nicolify-agentic` (Opus) — single surface agentic | `prompts/02-builder-start.md` | code + tests + `IMPL-LOG.md` (auto-spawnea auditor) |
| Audit | `nicolify-agentic-auditor` (Opus) — auto-spawned por builder | `prompts/03-auditor-start.md` | `REVIEW-agentic.md` |
| Cierre | `/pm` | `prompts/04-pm-close.md` | `RESULT.md` + `current-state/copilot.md` update |

Skills domain a invocar (builder + auditor obligatorios):
- `copilot-expert` (memory + orchestrator + tool registry + cache fragments deep knowledge)
- `tessl__langgraph` (state machine patterns si orchestrator usa LangGraph)
- `tessl__graceful-degradation` (timeout/fallback si orchestrator dependencies fallan)

## Surface impactada

| Tipo | Path / nombre | Cambio |
|---|---|---|
| Code agentic | `backend/src/modules/copilot/application/memory/context_window_builder.py` | EXTEND con param `channel` (default 'web' backward compat) |
| Code agentic | `backend/src/modules/copilot/application/memory/rolling_summarizer.py` | EXTEND con param `channel` si configura summary_max_chars distinto |
| Code agentic | `backend/src/modules/copilot/domain/context_window.py` (o módulo equivalente) | NEW `TELEGRAM_CONTEXT_WINDOW_CONFIG: ContextWindowConfig` constant con valores D-PI5-006 |
| Code agentic | `backend/src/modules/copilot/application/orchestrator/system_prompt_layout.py` | EXTEND `CACHEABLE_FRAGMENTS` con `TELEGRAM_CHANNEL_CONTEXT` (≥1024 tokens cuando `context.channel == 'telegram'`) |
| Code agentic | `backend/src/modules/copilot/application/tools/registry.py` | (ya soporta `channel`) — verifica orchestrator pasa correctly |
| Code agentic | `backend/src/modules/copilot/application/orchestrator/{orchestrator entrypoint}.py` | EXTEND para aceptar `channel` param + propagarlo a memory builder + tool registry + format adapter |
| Code agentic | `backend/src/modules/copilot/infrastructure/workers/telegram_worker.py` | REPLACE placeholder reply con `await invoke_copilot_orchestrator(channel='telegram', tenant_id, user_id, conversation_lookup, message_text)` + `format_for_channel(...)` antes `bot.send_message` |
| Code agentic | `backend/src/modules/copilot/infrastructure/repositories/conversation_repository.py` (o equiv) | EXTEND con `get_or_create_by_channel(tenant_id, user_id, channel_type, channel_chat_id)` |
| Code shared (READ ONLY) | `backend/src/shared/agent_observability/channels/format.py::escape_markdown_v2` | reuso, NO modificar |
| Tests | `backend/tests/modules/copilot/application/memory/test_context_window_telegram_config.py` | NEW — config inyección por channel |
| Tests | `backend/tests/modules/copilot/integration/test_telegram_end_to_end.py` | NEW — webhook → ARQ → worker → orchestrator → mock bot send (3 cases: linked happy / unlinked CTA / `/start TOKEN` linking) |
| Tests | `backend/tests/architecture/test_copilot_telegram_separation.py` | EXTEND con `test_telegram_cache_prefix_meets_anthropic_threshold` (≥1024 tokens sample) |
| `current-state/` | `docs/pm-nico/current-state/copilot.md` | append capability "Canal Telegram — orchestrator real + memory cost-aware + prefijo cacheable Anthropic" + lineage |

## Tests requeridos (TDD)

- `tests/modules/copilot/application/memory/test_context_window_telegram_config.py` — `TELEGRAM_CONTEXT_WINDOW_CONFIG` aplicado cuando `channel='telegram'`; default web cuando `channel='web'`; default web fallback canal desconocido
- `tests/modules/copilot/integration/test_telegram_end_to_end.py` — 3 cases:
  - Happy path linked: mock Telegram update text → enqueue → worker → conversation lookup → orchestrator returns text → format adapter MarkdownV2 → mock bot send_message called once con text escapado
  - Unlinked CTA: mock Telegram update from chat_id NO linked → CTA template friendly + URL `app.nicolify.com/[tenant]/settings/copilot/telegram` (NO orchestrator invoked)
  - `/start TOKEN` linking: mock Telegram update con `text='/start <valid_token>'` → linking service consumes token → channel_link created → confirmation message sent
- `tests/modules/copilot/application/tools/test_registry_telegram_runtime_filter.py` — `get_tools_for_context(context_with_channel='telegram')` excluye `navigation`/`guided`/`landing.mutations`/`offer_section.mutations` (response template "requiere editor web") + incluye 12+ telegram-allowed groups
- `tests/architecture/test_copilot_telegram_separation.py::test_telegram_cache_prefix_meets_anthropic_threshold` — sample compute prefijo cacheable con tenant minimal (sin studio_snapshot/form_data) + `TELEGRAM_CHANNEL_CONTEXT` fragment activo → token count ≥1024

## Aceptación

- [ ] Tests verdes: integration + memory + tool filter + arch fitness
- [ ] Lint (ruff) verde NATIVE WSL
- [ ] Mypy strict en archivos tocados
- [ ] Coverage tests modules/copilot ≥ baseline pre-PR
- [ ] `IMPL-LOG.md` completo (sub-deliverables, EXTEND-vs-NEW resoluciones por subsistema, skills consultadas, gate-runner iter, auditor iter)
- [ ] `REVIEW-agentic.md` verdict PASS sin findings críticos
- [ ] `RESULT.md` escrito por PM (outcome real medido + capability lineage + métricas)
- [ ] `current-state/copilot.md` actualizado con capability "Canal Telegram orchestrator + memory + cache" lineage commit hash
- [ ] Decisiones implementación nuevas registradas en `decisions.md` PI como D-PI5-IMPL-007+
- [ ] PR-1 capability "Canal Telegram — DMs linkeados" upgraded de "parcial (LLM placeholder)" → "live (orchestrator real)" en `current-state/copilot.md`

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Cambio firma `ContextWindowBuilder` rompe call sites web pre-existentes | Default param `channel='web'` preserva backward compat. Tests baseline web pre-existing pass sin cambios |
| `TELEGRAM_CHANNEL_CONTEXT` add a `CACHEABLE_FRAGMENTS` invalida cache web (cambia byte-prefix global) | Fragment SOLO se añade cuando `context.channel == 'telegram'` (condicional builder). Web prefijo intacto byte-idéntico |
| Orchestrator entrypoint no acepta `channel` param hoy → cambio signature breaking | Architect flag § 16 si signature change requerido. Si breaking → builder adds param con default 'web' (backward compat) |
| Format adapter doble-escape MarkdownV2 (orchestrator devuelve markdown legítimo + adapter escapa otra vez) | Test caso real: orchestrator output `"**bold** _italic_"` → adapter escapa correctamente → bot recibe sin error Telegram API. Auditor verifica |
| Conversation lookup race condition (2 mensajes Telegram simultáneos crean 2 rows duplicados) | UNIQUE constraint en DB existente PR-1 (`copilot_conversations` por canal). Lookup-or-create con `INSERT ON CONFLICT DO NOTHING RETURNING` o SELECT FOR UPDATE — architect decide |
| Cache prefix sample compute fragil (depende de tenant data shape) | Test architecture usa tenant minimal **fijo** (no real tenant data) + `TELEGRAM_CHANNEL_CONTEXT` length conocido → reproducible. Threshold 1024 con margin (e.g., target ≥1100) |
| Tool filter runtime falla silenciosa (orchestrator pasa `channel='telegram'` pero registry retorna default web set por bug) | Test integration verifica registry filtered output ≠ default 'web' set. Auditor cat 11 agentic hygiene catches |
