# S1 → S2 Handoff

> Owner: /pm. Captura decisions + surface disponible + agentes recomendados S2.

## Decisiones consolidadas S1 (input para S2)

### D-PI5-* relevantes para S2 PR-2 (memory + cache + tool deepening)

| ID | Resumen | Impact S2 |
|---|---|---|
| D-PI5-006 | Reusar `ContextWindowBuilder` + `RollingSummarizer` con `TELEGRAM_CONTEXT_WINDOW_CONFIG` (3000 raw, 15 msgs, summary 600 chars, nudge 12000) | S2 PR-2 implementa este config + path inyección |
| D-PI5-007 | Reusar `CopilotConversationModel` con cols `channel_type` + `channel_chat_id` (✅ aplicado PR-1) | S2 hookup orchestrator usa cols existentes |
| D-PI5-008 | NO vector retrieval Qdrant en MVP (diferir hasta feedback) | S2 mantiene scope sin Qdrant |
| D-PI5-009 | Añadir `TELEGRAM_CHANNEL_CONTEXT` fragment a `CACHEABLE_FRAGMENTS` ≥1024 tokens umbral | **CRÍTICO S2 PR-2** — sin esto cache miss 100% Telegram |
| D-PI5-024 | Tools telegram-allowed: 12+ tool groups (ya implementado PR-1) | S2 valida orchestrator respeta filter en runtime |
| D-PI5-IMPL-005 | Linked state DERIVED from queries (no setState-in-effect) | Confirmar siguiente FE component sigue pattern |

## Surface disponible para S2

### APIs (live)
- `POST /api/v1/copilot/telegram/webhook` — NON-BLOCKING + secret_token + private filter (LLM orchestrator hookup pendiente S2)
- `POST /api/v1/copilot/telegram/link-tokens` — Clerk JWT auth
- `GET /api/v1/copilot/telegram/link-status` — polling
- `DELETE /api/v1/copilot/telegram/link` — soft delete

### Schema DB (live)
- `copilot_channel_links` — chat_id ↔ tenant + user + role (live)
- `copilot_link_tokens` — single-use HMAC magic links (live)
- `copilot_conversations.channel_type` + `channel_chat_id` — cols extendidas (live)

### Code disponible (live)
- `copilot/infrastructure/channels/telegram_bot.py::CopilotTelegramBot` — outbound rate-limited
- `copilot/infrastructure/workers/telegram_worker.py::process_copilot_telegram_turn` — ARQ async
- `copilot/application/services/telegram_link_service.py` — HMAC + 6 service functions
- `copilot/application/tools/telegram_redirect.py` — redirect template + URL builder
- `copilot/application/tools/registry.py::ToolGroupMeta` + `is_group_available_in_channel()` + `get_tools_for_context(channel='web')` filter
- `copilot/api/_dependencies.py::copilot_async_session_factory` — worker session ctx mgr
- `copilot/api/telegram_dto.py` — 8 Pydantic v2 DTOs

### FE disponible
- `/{tenantId}/settings/copilot/telegram` page + `<TelegramLinkingClient />` (live)
- `features/copilot/api/use-{create,status,current,unlink}-telegram*` hooks (live)
- `features/copilot/types/telegram.ts` Zod schemas

### Arch fitness baseline
- 8 arch fitness tests `test_copilot_telegram_separation.py` (RATCHET — failures block CI)

## Riesgos abiertos (para S2)

| Risk | Mitigación S2 |
|---|---|
| Migration 120 stuck behind broken migration 114 | Tables aplicadas manual; alembic upgrade head pendiente fix migration 114 (pre-existing) |
| Telegram cache prefix <1024 tokens (sin studio_snapshot) | S2 PR-2 añade `TELEGRAM_CHANNEL_CONTEXT` fragment |
| LLM orchestrator hookup pendiente | S2 PR-2 wires `invoke_copilot_orchestrator(channel='telegram', tenant_id, user_id, conversation_id_lookup_by_channel_chat_id)` |
| Bot username squatted al deploy | Chris reserva BotFather pre-deploy (action item) |

## Agentes/skills recomendados S2

| Agent | Skill | Por qué |
|---|---|---|
| `nicolify-context-builder` (Haiku) | — | Pre-flight S2 (cache pattern + memory diff) |
| `nicolify-architect` (Opus) | `copilot-expert`, `tessl__langgraph` | Diseño memory config + cache fragment + orchestrator hookup |
| `nicolify-agentic` (Opus) | `copilot-expert`, `tessl__langgraph` | Implementer (hookup + memory config) |
| `nicolify-agentic-auditor` (Opus) | — | Audit memory + cache + tool filter runtime correctness |
| **PM main thread fallback** | — | Si agents truncan otra vez (5° confirm pattern), PM Opus single-author escribe directo |

## Plan macro S2 (preliminar — refinar en S2 sprint.md)

| Item | Scope |
|---|---|
| **PR-2-telegram-orchestrator-hookup** | Wire copilot orchestrator con `channel='telegram'` param. Worker linked branch invoca orchestrator + envía respuesta via bot. `TELEGRAM_CONTEXT_WINDOW_CONFIG` distinto. `TELEGRAM_CHANNEL_CONTEXT` cacheable fragment. Tool registry filter validation runtime. Tests integration end-to-end (mock Telegram → orchestrator response → mock bot send). UI-SPEC FE: ningún cambio (mismo settings page) |

## Cierre S1

S1 cerrado 2026-04-30 con 1/1 PR shipped. Cero refactor cross-sprint anticipado (foundation sólida, S2 hace hookup limpio sobre tablas + worker existentes).

Sprint S2 puede arrancar cuando Chris autorice.
