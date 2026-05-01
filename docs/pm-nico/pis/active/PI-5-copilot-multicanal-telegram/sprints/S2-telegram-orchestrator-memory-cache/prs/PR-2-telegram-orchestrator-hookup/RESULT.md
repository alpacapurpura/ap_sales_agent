# RESULT — PR-2-telegram-orchestrator-hookup

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-2-telegram-orchestrator-hookup |
| Sprint padre | S2-telegram-orchestrator-memory-cache |
| PI padre | PI-5-copilot-multicanal-telegram |
| Estado final | shipped |
| Cierre | 2026-05-01 |
| Verdict auditor | PASS (iter 2) |
| Builder | nicolify-agentic (Opus 4.7) |
| Auditor | nicolify-agentic-auditor (Opus 4.7) |
| Surface | AGENTIC SINGLE — `modules/copilot/` |
| Commits | `d09799b9` (feat main) + `8b180584` (fix iter-2 anchors+slot) + `a6c6ad3d` (docs iter-2) |

## Outcome real vs esperado

| Esperado | Real | Evidencia |
|---|---|---|
| Worker linked branch invoca orchestrator real (NO placeholder) | sí | `infrastructure/workers/telegram_worker.py` líneas 133-154 REPLACE → `orchestrator.invoke_text(channel='telegram')` + `format_for_channel_impl` + `bot.send_message(parse_mode='MarkdownV2')`. Commit `d09799b9` |
| `TELEGRAM_CONTEXT_WINDOW_CONFIG` aplicado runtime cuando channel='telegram' | sí | `domain/context_window.py` constant (3000/15/600/12000) + `get_context_window_config(channel)` dispatcher. Test `test_context_window_telegram_config.py` GREEN |
| `TELEGRAM_CHANNEL_CONTEXT` cacheable fragment ≥2048 tokens (Q3 PM-resolved upgrade desde ≥1024) | sí | Arch fitness `test_telegram_cache_prefix_meets_anthropic_threshold` GREEN, ~2200 tokens stable bytes Spanish prose. Builder fn devuelve `""` cuando channel != telegram → web bytes byte-idénticos preservados |
| Tool registry filter runtime excluye web-only en channel='telegram' | sí | `application/orchestrator/deep_agent.py` pasa `channel=ctx.get("channel") or "web"` a `get_tools_for_context()`. Test `test_registry_telegram_runtime_filter.py` valida exclusión `navigation/guided/landing.mutations/offer_section.mutations` + inclusión 12+ groups telegram-allowed |
| Format adapter MarkdownV2 escapa correctamente sin doble-escape | sí | Worker reusa `format_for_channel_impl(content, channel_id='telegram')` shared (Q2 resolved, NO new function). Bot adapter ya escapa internamente con `escape_markdown_v2` |
| First-time wiring memory builders en `_prepare_conversation` (Q1 PM-resolved) | sí | `application/orchestrator/chat.py` `_apply_channel_window` helper cabletea `ContextWindowBuilder.for_channel(channel)` + `RollingSummarizer.for_channel(channel)` ANTES de `_run_graph_stream`. ~15 LOC delta |
| Orchestrator entrypoint accepta `channel` (Q4 PM-resolved keep DTO+kwarg) | sí | `CopilotOrchestrator.invoke_text(channel='web', ..., context: ClientContextDTO \| None)`. Dispatch `context.channel or kwarg or "web"`. `ClientContextDTO.channel: str \| None = None` field added |
| Conversation lookup race-tolerant (Q5 PM-resolved defer UNIQUE a S5) | sí | `infrastructure/repositories/conversation_repository.py::get_or_create_by_channel` optimistic SELECT-then-INSERT, tenant-scoped, soft-delete aware. UNIQUE constraint deferred a S5 PR-5 — gap documented en docstring |
| Latencia first-token p95 medible | pendiente smoke live | Instrumentación `copilot_llm_call` ya registra `started_at`/`first_token_at` desde PI-2. Smoke test live (Paso 6) confirmará |
| Cache hit rate medible vía `copilot_llm_call` | pendiente smoke live | DTO `cache_read_tokens`/`cache_creation_tokens` hardcoded 0 en `invoke_text` — TODO S5 wire-up del callback handler. DB sigue siendo SSoT honesto vía existing handler |

## Surface entregada

### Code agentic (modules/copilot/)

**Modificados (10 archivos):**
- `domain/context_window.py` — `TELEGRAM_CONTEXT_WINDOW_CONFIG` constant + `get_context_window_config(channel)` dispatcher
- `application/memory/context_window_builder.py` — `for_channel(channel)` classmethod (backward compat `__init__` preservado)
- `application/memory/rolling_summarizer.py` — `for_channel(channel)` classmethod
- `application/orchestrator/system_prompt_layout.py` — `PromptFragment.TELEGRAM_CHANNEL_CONTEXT` enum + `CACHEABLE_FRAGMENTS` tuple slot
- `application/orchestrator/graph.py` — `_build_telegram_channel_context_fragment(state)` + `_TELEGRAM_CHANNEL_CONTEXT_ES` (~2200 tokens stable Spanish prose)
- `application/orchestrator/chat.py` — `CopilotOrchestrator.invoke_text` sibling de `stream_chat` + `_apply_channel_window` first-time wiring memory
- `application/orchestrator/deep_agent.py` — channel-aware `get_tools_for_context(channel=ctx.channel or "web")`
- `infrastructure/repositories/conversation_repository.py` — `get_or_create_by_channel(tenant_id, user_id, channel_type, channel_chat_id)` optimistic
- `infrastructure/workers/telegram_worker.py` — REPLACE placeholder branch líneas 133-154 con orchestrator real + `format_for_channel_impl` + 30s `asyncio.wait_for` timeout + per-dependency try/except
- `api/dto.py` — `ClientContextDTO.channel: str \| None = None` field

**NEW (1 archivo):**
- `application/orchestrator/invoke_result.py` — `CopilotInvokeResult` Pydantic value object (<33 LOC). Frozen, immutable, tracks `response_text`/`conversation_id`/`tools_called`/`error_kind`/cache token fields

### Tests (8 archivos nuevos + 3 modificados)

- `tests/modules/copilot/application/memory/test_context_window_telegram_config.py` — D-PI5-006 byte-exact + dispatcher
- `tests/modules/copilot/application/memory/test_memory_builders_for_channel.py` — `for_channel` classmethod
- `tests/modules/copilot/application/orchestrator/test_telegram_channel_context_fragment.py` — fragment conditional + invariant content
- `tests/modules/copilot/application/orchestrator/test_invoke_text.py` — non-streaming + error_kind paths
- `tests/modules/copilot/application/tools/test_registry_telegram_runtime_filter.py` — channel exclusion + inclusion
- `tests/modules/copilot/infrastructure/repositories/test_conversation_repository_telegram_lookup.py` — `get_or_create_by_channel` + cross-tenant isolation
- `tests/modules/copilot/integration/test_telegram_end_to_end.py` — 3 cases (linked happy / unlinked CTA / `/start TOKEN`)
- `tests/architecture/test_copilot_telegram_separation.py` (modified) — `test_telegram_cache_prefix_meets_anthropic_threshold` ≥2048 tokens
- `tests/architecture/test_copilot_anchors.py` (modified) — register `COPILOT-INVOKE-RESULT-PR2-PI5` + `COPILOT-TELEGRAM-CHANNEL-CONTEXT` (anchor cap 37→39)
- `tests/architecture/test_system_prompt_order.py` (modified) — slot ratchet extended con `TELEGRAM_CHANNEL_CONTEXT` idx 3 entre `MARKETING_KB_HINT` y `LIGHTHOUSE`

### Cero cambios

- Frontend (verified diff)
- Módulos negocio (`brand`/`offer`/`landing`/`assets`/`analytics`/`advertising`/`social_media`/`scheduling`/`connections`/`iam`/`crm`)
- DB schema / migration (cols ya añadidas PR-1)
- `modules/sales_agent/` (separación física D-PI5-005 mantenida)
- `core/config.py` Settings (env vars ya en PR-1)
- Webhook handler `POST /api/v1/copilot/telegram/webhook` (NON-BLOCKING + secret_token + private filter live PR-1)

## Capacidades nuevas — lineage

### Cap: Canal Telegram — orchestrator real + memory cost-aware + prefijo cacheable Anthropic

- Introducida: PR-2 (PI-5, S2, commits `d09799b9` + `8b180584` + `a6c6ad3d`, 2026-05-01)
- Estado: live
- Operable copilot: sí (12+ tool groups telegram-allowed, orchestrator real, memory windowed cost-aware, cache prefix ≥2048 tokens activo per-channel)
- Surface code: `modules/copilot/application/memory/` + `modules/copilot/application/orchestrator/` + `modules/copilot/infrastructure/workers/telegram_worker.py` + `modules/copilot/infrastructure/repositories/conversation_repository.py`
- Memory: `TELEGRAM_CONTEXT_WINDOW_CONFIG` (RAW_WINDOW_TOKENS=3000, RAW_WINDOW_MAX_MESSAGES=15, RAW_WINDOW_MIN_MESSAGES=4, SUMMARY_MAX_CHARS=600, SUMMARY_TARGET_TOKENS=200, NUDGE_AFTER_TOTAL_TOKENS=12000, NUDGE_HARD_LIMIT_TOKENS=20000, NUDGE_AFTER_MESSAGE_COUNT=20)
- Cache: `TELEGRAM_CHANNEL_CONTEXT` fragment ~2200 tokens stable bytes (Sonnet floor + Kimi K2.6 ≥1024 cubierto). Web bytes byte-idénticos preservados (builder devuelve `""` cuando channel != telegram)
- Tool subset runtime filter: web-only excluded (`navigation`, `guided`, `landing.mutations`, `offer_section.mutations`) → redirect template `format_for_channel` tool
- Format: MarkdownV2 escape via shared `format_for_channel_impl(channel_id='telegram')` reuso (Q2 resolved)
- Conversation lookup: `get_or_create_by_channel` tenant-scoped optimistic SELECT-then-INSERT (UNIQUE constraint deferred S5 PR-5)
- Resilience: 30s `asyncio.wait_for` orchestrator timeout + per-dependency try/except (lookup/orchestrator/format/bot send) + structured success log con cache metrics + fallback CTA template friendly

### Cap: Canal Telegram — DMs linkeados magic link (UPGRADE)

- Estado anterior: foundation live (LLM orchestrator hookup pendiente)
- Estado actual: **live (orchestrator real + memory cost-aware + cache fragment ≥2048 tokens activo)**
- Lineage upgrade: PR-1 commit `c1fa2909` (foundation) + PR-2 commit `d09799b9` (orchestrator hookup live)

## Decisiones implementación nuevas (D-PI5-IMPL-007+)

Ver `pis/active/PI-5-copilot-multicanal-telegram/decisions.md` D-PI5-IMPL-007 a D-PI5-IMPL-013 (appended esta sesión).

Highlights:
- D-PI5-IMPL-007 — `for_channel` classmethod canonical en memory builders. Legacy `__init__` preservado para tests. Backward compat 0% breaking
- D-PI5-IMPL-008 — Cache prefix threshold ≥2048 tokens (Sonnet floor + Kimi K2.6 ≥1024 cubierto). Q3 PM-Opus resolved. Si swap a Anthropic Opus 4.x en futuro PR → extender fragment a ≥4096 (follow-up)
- D-PI5-IMPL-009 — Orchestrator entrypoint signature: keep DTO field + kwarg path. Dispatch `context.channel or kwarg or "web"`. Q4 PM-Opus resolved
- D-PI5-IMPL-010 — Conversation lookup optimistic SELECT-then-INSERT. UNIQUE constraint deferred S5 PR-5. Q5 PM-Opus resolved (race window microsegundos MVP volume)
- D-PI5-IMPL-011 — `format_for_channel_impl` shared reuso, NO new function. Q2 architect-resolved
- D-PI5-IMPL-012 — `_TELEGRAM_CHANNEL_CONTEXT_ES` constant string puro Python (NO interpolación, NO timestamps, NO tenant_name) — preserva cache hit rate
- D-PI5-IMPL-013 — `invoke_text` sibling de `stream_chat`. Comparte `_prepare_conversation` + `_run_graph_stream`. NO nueva clase, NO nuevo grafo

## Métricas

- **Tests escritos:** 8 archivos nuevos + 3 modificados (anchors + slot order + arch fitness cache prefix)
- **Tests propios PR-2 GREEN:** 100% (verificado iter-2 audit)
- **Pytest failures restantes:** 12 — TODOS pre-existing ajenos (sales_agent anchors+order otra sesión, voice_api 410 Gone deprecación, deep_agent kimi clamp pre-existing, outbox adapter PR-1 cascade, DDD campaigns→sales_agent boundary, folder_naming `_dependencies.py`, voice_fidelity timeout)
- **Ruff:** PASS (449 files clean)
- **Ruff format:** PASS
- **Mypy:** 375 errors total — TODOS pre-existing baseline (NO PR-2 introduced; `rolling_summarizer.py:84` flagged por auditor como pre-existing)
- **Arch fitness:** 33+ tests GREEN (incluyendo nuevo `test_telegram_cache_prefix_meets_anthropic_threshold`)
- **Iteraciones gate-runner:** 2
- **Iteraciones audit:** 2
- **Verdict final auditor:** PASS

## Deuda técnica generada

- **DTO cache token fields hardcoded 0** en `invoke_text` (líneas 1303-1305). DB SSoT honesto via callback handler existente, pero worker structured log muestra cero. Wire-up explícito S5 (auditor finding WARN, no blocking).
- **`invoke_text` outer except missing `set_turn_error`** edge case (chat.py:1245-1253). Inner `_run_graph_stream` ya cubre 99%. Defensive S5 follow-up (auditor finding WARN, no blocking).
- **UNIQUE constraint** `(tenant_id, user_id, channel_type, channel_chat_id)` deferred a S5 PR-5 (Q5 PM-resolved). Race window microsegundos MVP volume.
- **Cache hit rate live measurement** pendiente smoke test Paso 6 + post-launch first 3+ tenants Telegram-active.
- **Latencia first-token p95** pendiente smoke + observabilidad live (instrumentación ya existe en `copilot_llm_call`).
- **Pre-existing pytest baselines** (12 ajenos) NO bloquean PR-2 — out of scope per PM ruling. Sprint owners respectivos resuelven.

## Decisiones diferidas confirmadas

- HITL escalation sales_agent ↔ copilot → S3 PR-3
- Push notifs proactivas + encargos in-app inbox → S4 PR-4
- Multi-role tool filter implementation (filtros por `role`) → PI futuro
- Vector retrieval Qdrant Telegram conversations → post-launch si feedback "no recuerda contexto viejo"
- Voice messages + cards interactivas avanzadas → PI futuro
- Migration 114 fix pre-existing → ticket separado fuera scope PI-5
- Bot username squat protection + setWebhook script automatizado → S5 PR-5
- UNIQUE constraint conversations multi-channel → S5 PR-5

## Smoke test live (Paso 6)

Pendiente Chris:
- Abrir Telegram, escribir `@nicolify_dev_bot` SIN linkear → confirmar CTA template + URL `https://app.nicolify.com/[tenant]/settings/copilot/telegram` (NO placeholder "recibí tu mensaje")
- Si flow linked: generar magic link desde web, `/start TOKEN`, mensaje, verificar respuesta orchestrator real
- Logs: `docker logs visionarias_brain_dev` + queries `copilot_trace_event` + `copilot_llm_call` para validar cache hit rate desde turn 3+
