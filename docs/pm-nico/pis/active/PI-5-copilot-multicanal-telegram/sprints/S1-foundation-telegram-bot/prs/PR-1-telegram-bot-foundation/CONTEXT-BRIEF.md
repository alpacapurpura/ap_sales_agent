# CONTEXT-BRIEF — PR-1 telegram-bot-foundation

**Generated:** 2026-04-30 (PM main thread direct, post Haiku context-builder timeout). Faithfulness: clean. Subsystem keywords: telegram, webhook, bot, hmac, magic_link, channel_link, arq, queue, channel_format, sanitize_payload.

## §1 PR summary

PI-5 S1 PR-1 cross-stack (agentic + frontend) foundation. Bot global Nicolify `@nicolify_copilot_bot` (1 token env var distinto de sales_agent) + webhook non-blocking + ARQ async worker + magic link onboarding + tablas `copilot_channel_links` + `copilot_link_tokens` + tool registry extension `ToolGroupMeta.available_channels` + redirect template + arch fitness tests separación física copilot↔sales_agent.

## §2 CONTRACT decisions (PR.md → architect)

CONTRACT pending architect run. PR.md walking skeleton 16 sub-deliverables. CONTRACT debe formalizar:
- Schema tablas nuevas + cols (idempotent migration)
- Endpoints `/api/v1/copilot/telegram/{webhook,link-tokens,link-status}` Pydantic v2
- ARQ queue `copilot_telegram_turns` + job signature
- Tool registry `ToolGroupMeta` dataclass extension
- Bot adapter `copilot/infrastructure/channels/telegram_bot.py` interface
- Sanitize + rate limit + webhook secret validation specs

## §3 UI-SPEC decisions

Pending architect spawn de `ux-flow-architect` skill. Walking skeleton FE: `/settings/copilot/telegram` page + modal + `useTelegramLinking` hook + polling 3s × 60s.

## §4 current-state/copilot.md

Módulo activo. Capacidades sólidas: chat UI, LangGraph orchestrator, tools transversales (extract_document_to_fields, propose_field_updates, format_for_channel), Module Registry, route-based tool selection, cards, trace observability, prompt caching cycle 25-25, tier routing, cost tracking, domain event bus, subagent isolation, outbox migration ready, voice rate limit + media limits, suggestions engine. **NO existe canal Telegram para copilot hoy** — solo in-app web. Esta PR introduce primer canal externo.

## §5 Rules cargadas (architect phase)

- `tenant-isolation.md` — todo query con `tenant_id` filter (incluye `copilot_channel_links`)
- `backend-ddd.md` — Inside-Out (domain → infra → app → api). FastAPI `redirect_slashes=False`. AsyncSession. Pydantic v2 ConfigDict
- `backend-migrations.md` — idempotent raw SQL `CREATE TABLE IF NOT EXISTS`, `ALTER TABLE x ADD COLUMN IF NOT EXISTS`. NUNCA `op.create_table()`/`op.add_column()`
- `frontend-fsd.md` — Server Components default. RHF + Zod. Tailwind + cn(). No `any`. fetchClient inyecta `X-Tenant-ID`
- `copilot-resilience.md` + `copilot-observability.md` — todo write observability `try/except + structlog warning`. Sanitize PII via `sanitize_payload`
- `parallel-safety.md` — M1-M8: development único branch. NO pull/force/revert. Stage por nombre. Filesystem compartido OK con extend
- `tdd-mandatory.md` — RED → GREEN → REFACTOR. Tests primero
- `spanish-text.md` — UI strings tuteo neutro LatAm (no voseo)
- `debugging.md` — root cause only. Regression test FIRST

## §6 git diff main..HEAD

Branch `development`. PI-5 PR-1 todavía no implementado — solo PM artifacts. Sesión paralela activa (PI-1 archived, modificaciones campaigns/segment* + frontend/features/* presentes en `git status` — NO TOCAR).

## §7 Existing systems detected (verbatim grep)

| Subsystem keyword | Path detectado | Overlap | Decisión |
|---|---|---|---|
| **telegram (sales_agent adapter)** | `src/modules/connections/infrastructure/channels/telegram.py` | 60% (HTTP client + send_message; pero usa `settings.TELEGRAM_BOT_TOKEN` y patrón legado per-tenant via `connection_id`) | **NEW** copilot adapter en `src/modules/copilot/infrastructure/channels/telegram_bot.py`. D-PI5-005 separación física. Reusa `httpx`/structlog patrón pero NO importa de connections/ |
| **telegram (sales_agent webhook)** | `src/modules/connections/api/telegram.py` | 40% (FastAPI router con `BackgroundTasks` + payload deserialization Telegram Update) | **NEW** router `src/modules/copilot/api/telegram.py`. Pattern similar (BackgroundTasks **NO** — usar ARQ enqueue per D-PI5-026), no shared imports |
| **whatsapp (webhook pattern)** | `src/modules/connections/api/whatsapp.py` | 20% (referencia FastAPI webhook structure, GET verify + POST handle) | **REFERENCE only**. NEW copilot Telegram webhook |
| **escape_markdown_v2** | `src/shared/agent_observability/channels/format.py` | 100% (utility puro) | **EXTEND/REUSE** import directo desde shared |
| **sanitize_payload** | `src/shared/agent_observability/recording/sanitization.py` | 100% (PII sanitizer existente, ya usado en copilot recording) | **EXTEND/REUSE** |
| **ARQ pool/workers** | `src/core/arq_pool.py` + `src/workers/settings.py` | 100% (stack existente, queues múltiples) | **EXTEND** añadir nueva job function `process_copilot_telegram_turn` + register en worker settings |
| **conversational_channel port** | `src/shared/links/ports/conversational_channel.py` | 30% (port abstract para "render question" flow guided — NO para webhook/orchestrator) | **NEW** parallel port pattern para bot adapter (no compatible) |
| **tool registry** | `src/modules/copilot/application/tools/registry.py` | 100% (ROUTE_TOOL_MAP, ALWAYS_AVAILABLE_GROUPS, TOOL_GROUPS, get_tools_for_context, _build_tool_groups) | **EXTEND** añadir `ToolGroupMeta` dataclass con `available_channels: frozenset[str]` + filter en `get_tools_for_context()` por `channel` param |
| **Settings env vars** | `src/core/config.py` | 100% (`TELEGRAM_BOT_TOKEN`, `API_URL`, `REDIS_URL`, etc.) | **EXTEND** añadir `COPILOT_TELEGRAM_BOT_TOKEN`, `COPILOT_TELEGRAM_WEBHOOK_SECRET_TOKEN`, `COPILOT_TELEGRAM_LINK_TOKEN_TTL_SECONDS=900` (15min) |
| **CopilotConversationModel** | `src/modules/copilot/infrastructure/models/conversation_model.py` | 100% (cols: id, tenant_id, user_id, title, messages, summary, total_tokens, etc.) | **EXTEND** añadir cols `channel_type: String(32) NULL` + `channel_chat_id: String(64) NULL` + index `(channel_type, channel_chat_id)` para lookup. Migration idempotente |
| **HMAC magic link** | grep no resultados — no existe | 0% | **NEW** `src/modules/copilot/application/services/telegram_link_service.py` |
| **channel_link / chat_id linking** | grep no resultados — no existe | 0% | **NEW** tabla `copilot_channel_links` + repository + service |
| **rate limiting (asyncio Semaphore + per-key Lock)** | `src/modules/copilot/api/voice.py`, `src/modules/copilot/api/media.py` (rate limit voice/media) | 70% (similar patrón decorator `@rate_limit_voice` etc., pero per-route) | **NEW** rate limiter en bot adapter scope (worker side) `src/modules/copilot/infrastructure/channels/telegram_rate_limiter.py`. Pattern similar pero scope distinto |

## §8 EXTEND-vs-NEW recommendations (mechanical rule applied)

| Component | Decisión | Razón |
|---|---|---|
| Bot adapter | **NEW** | D-PI5-005 separación física. Acoplar a sales_agent telegram.py = anti-pattern A2 |
| Webhook router | **NEW** | Mismo módulo distinto (copilot). Reusa pattern, no imports |
| HMAC link service | **NEW** | No existe en codebase |
| `copilot_channel_links` + `copilot_link_tokens` tablas | **NEW** | No existen. Cero FK cruzada con sales_agent_* (arch fitness test enforce) |
| `ToolGroupMeta` extension | **EXTEND** | tool registry existente, dataclass nueva pero metadata añadida |
| `CopilotConversationModel` cols | **EXTEND** | Modelo existente, ADD COLUMN IF NOT EXISTS idempotente |
| Settings env vars | **EXTEND** | Class Settings existente |
| ARQ worker registration | **EXTEND** | Stack ARQ existente |
| `escape_markdown_v2` | **REUSE** | utility puro |
| `sanitize_payload` | **REUSE** | utility puro |
| Rate limiter (worker scope) | **NEW** | Patterns voice/media son per-route, scope distinto |
| Frontend `/settings/copilot/telegram` page | **NEW** | Route group nuevo |
| Frontend `useTelegramLinking` hook | **NEW** en `frontend/src/features/copilot/api/` | Hook nuevo |

## §9 Files paths exactos (ya verificados existentes)

| Path | Estado |
|---|---|
| `backend/src/core/config.py` | EXTEND (Settings class) |
| `backend/src/modules/connections/api/telegram.py` | READ-ONLY reference |
| `backend/src/modules/connections/infrastructure/channels/telegram.py` | READ-ONLY reference |
| `backend/src/modules/connections/api/whatsapp.py` | READ-ONLY reference (webhook pattern) |
| `backend/src/modules/copilot/application/orchestrator/system_prompt_layout.py` | READ-ONLY (S2 PR-2 toca; PR-1 NO) |
| `backend/src/modules/copilot/application/tools/registry.py` | EXTEND |
| `backend/src/modules/copilot/infrastructure/models/conversation_model.py` | EXTEND |
| `backend/src/shared/agent_observability/channels/format.py` | READ-ONLY reuse `escape_markdown_v2` |
| `backend/src/shared/agent_observability/recording/sanitization.py` | READ-ONLY reuse `sanitize_payload` |
| `backend/src/shared/links/ports/conversational_channel.py` | READ-ONLY reference |
| `backend/src/core/arq_pool.py` | EXTEND register new job |
| `backend/src/workers/settings.py` | EXTEND register new worker function |
| `backend/src/modules/copilot/api/__init__.py` | EXTEND register new router |
| `backend/alembic/versions/` (122 archivos) | NEW migration |

## §10 ARQ stack confirmation

Stack existente: `arq>=0.27`. Worker entrypoint `src/workers/settings.py`. Ya hay queues múltiples (copilot_rag_eval, copilot_quality_eval, brand_summary_event_handlers). Pattern: nueva queue = nueva async function decorada + registro en `WorkerSettings.functions`.

## §11 Faithfulness gaps

Clean. Greps ejecutados manualmente desde main thread (Haiku context-builder timeout pre-write). 13 subsystems clasificados con verdict EXTEND/NEW/REUSE/REFERENCE. Architect downstream NO necesita re-ejecutar greps salvo si propone NEW layer paralelo (en cuyo caso revalida § 7).

## §12 Crítico para architect

1. **D-PI5-005 separación física = INVIOLABLE.** PR-1 NO importa de `modules/connections/`. Cualquier shared logic = `shared/`.
2. **D-PI5-026 webhook NON-BLOCKING.** Handler encola en ARQ + return 200 < 200ms. NUNCA process LLM inline (anti-pattern A8 → Telegram retry → mensajes duplicados).
3. **D-PI5-029 filter `chat.type == "private"`.** Anti-pattern A11 (bot global recibe added a grupos).
4. **D-PI5-028 `X-Telegram-Bot-Api-Secret-Token` validation.** Header obligatorio en webhook (return 401 strict si missing/invalid).
5. **D-PI5-019 magic link HMAC-SHA256, TTL 15min, single-use, hash en DB** (no plaintext token).
6. **D-PI5-030 `sanitize_payload` antes persist.** NO `username`/`first_name`/`phone` en logs.
7. **Memory specific Telegram (TELEGRAM_CONTEXT_WINDOW_CONFIG)** = OUT OF SCOPE PR-1 (S2 PR-2). MVP usa default config web.
8. **HITL** = OUT OF SCOPE PR-1 (S3 PR-3).
9. **Multi-role tool filter implementación** = OUT OF SCOPE (schema OK, lógica futuro).
10. **Tokens ya seteados** en `.env`, `.env.prod`, `backend/.env` (gitignored). Architect NO necesita gestionar tokens — solo declarar env var en Settings.

## §13 Verbatim grep commands executed

```bash
cd /home/chris/AISALESHT/backend
find src -name "*.py" | xargs grep -l "telegram" -i 2>/dev/null
grep -rn "TELEGRAM_BOT_TOKEN\|telegram_bot_token\|COPILOT_TELEGRAM" src/
find src -name "*.py" | xargs grep -l "arq\|ARQ" 2>/dev/null
grep -rn "webhook" src/modules/connections/api/
grep -rn "sanitize_payload" src/modules/copilot/
grep -rn "escape_markdown_v2\|MarkdownV2" src/shared/
cat src/shared/links/ports/conversational_channel.py
grep -E "channel|ConversationModel|class " src/modules/copilot/infrastructure/models/conversation_model.py
grep -E "class |ROUTE_TOOL|ALWAYS_AVAIL|tool_group|^def " src/modules/copilot/application/tools/registry.py
ls src/modules/copilot/api/
grep -E "class Settings|TELEGRAM|API_URL|FRONTEND_URL|REDIS" src/core/config.py
ls src/modules/copilot/infrastructure/
ls alembic/versions/*.py | wc -l
grep -E "Column|tenant_id|user_id|messages" src/modules/copilot/infrastructure/models/conversation_model.py
```

<!-- @pm: CONTEXT-BRIEF.md ready (faithfulness: clean). Downstream agent (architect) can consume it now. -->
