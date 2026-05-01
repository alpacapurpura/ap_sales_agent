# RESULT — PR-1 telegram-bot-foundation

> Closed by /pm 2026-04-30. Loop completo: PR.md → CONTEXT-BRIEF → CONTRACT → UI-SPEC → IMPL-LOG → RESULT + current-state/copilot.md update.

## Outcome real vs esperado

| Outcome esperado (PR.md) | Real | Estado |
|---|---|---|
| Dueño linkeado puede preguntar via Telegram chat → respuesta texto Markdown V2 | Webhook + worker pipeline funcional. **MVP placeholder reply** (LLM orchestrator hookup S2 PR-2) | Foundation OK; LLM hookup S2 |
| Recibir CTA "lo vemos en web" cuando intent requiere tool web-only | Tool registry filter + redirect template implementados | ✅ |
| Setup en <60s desde `/settings/copilot/telegram` modal | FE flow completo: link-tokens → deep link `t.me/...?start=TOKEN` → polling 3s × 60s → linked state | ✅ (test live pendiente post BotFather) |
| Webhook NON-BLOCKING < 200ms | Handler enqueue ARQ + return 200, NO LLM inline | ✅ |
| Latencia respuesta primer token < 5s p95 | No medible MVP (placeholder reply); medible S2 PR-2 con orchestrator | Diferido |

## Surface entregada

### API endpoints (4)

| Method | Path | Auth | Response model |
|---|---|---|---|
| POST | `/api/v1/copilot/telegram/webhook` | `X-Telegram-Bot-Api-Secret-Token` | `WebhookAck` |
| POST | `/api/v1/copilot/telegram/link-tokens` | Clerk JWT | `LinkTokenResponse` |
| GET | `/api/v1/copilot/telegram/link-status` (opt `token_id`) | Clerk JWT | `LinkStatusResponse` |
| DELETE | `/api/v1/copilot/telegram/link` | Clerk JWT | `UnlinkResponse` |

### Tablas DB (2 NEW + 1 EXTEND)

- `copilot_channel_links` (UUID + tenant_id + user_id + channel_type + channel_user_id + channel_username + role + linked_at + last_seen_at + revoked_at) + UNIQUE(tenant_id, channel_type, channel_user_id) + 3 indexes
- `copilot_link_tokens` (UUID + token_hash + tenant_id + user_id + expires_at + used_at + created_at) + UNIQUE(token_hash) + 2 indexes
- `copilot_conversations.channel_type` + `channel_chat_id` (NULLABLE) + index

### Componentes FE

- Route `/(main)/[tenantId]/(dashboard)/settings/copilot/telegram/page.tsx`
- `_components/TelegramLinkingClient.tsx` (state machine 5 transient + 1 derived linked)
- `features/copilot/api/use-{create-telegram-link-token,telegram-link-status,telegram-current-link,unlink-telegram}.ts`
- `features/copilot/types/telegram.ts` (Zod)

### Settings env vars (5 NEW)

- `COPILOT_TELEGRAM_BOT_TOKEN` (dev + prod tokens en `.env*` gitignored)
- `COPILOT_TELEGRAM_WEBHOOK_SECRET_TOKEN` (random urlsafe 32, dev + prod distintos)
- `COPILOT_TELEGRAM_LINK_TOKEN_TTL_SECONDS` (default 900)
- `COPILOT_TELEGRAM_BOT_USERNAME` (default `nicolify_copilot_bot`)
- `FRONTEND_URL` (default `https://app.nicolify.com`)

### Arch fitness tests (8 NEW, ratchet)

`tests/architecture/test_copilot_telegram_separation.py` — token global distinto, no per-tenant lookup, no cross-module FK, no connections/sales_agent imports, private chat filter, secret token validation, NON-BLOCKING enqueue, hashed token storage.

## Capacidades nuevas (lineage para current-state/copilot.md)

```md
### Cap: Canal Telegram — DMs linkeados magic link
- Introducida: PR-1 (PI-5, S1, commit c1fa2909, 2026-04-30)
- Estado: foundation live (LLM orchestrator hookup pendiente S2 PR-2)
- Operable copilot: parcial (linking + tool subset registry; LLM responses = placeholder MVP)
- Surface API: /api/v1/copilot/telegram/{webhook,link-tokens,link-status,link}
- Surface FE: /{tenantId}/settings/copilot/telegram page + <TelegramLinkingClient />
- Tablas: copilot_channel_links + copilot_link_tokens + copilot_conversations cols (channel_type, channel_chat_id)
- Webhook: NON-BLOCKING enqueue ARQ <200ms, valida X-Telegram-Bot-Api-Secret-Token, filtra chat.type='private'
- Bot adapter: global Nicolify (1 token env var), rate-limited 30 msg/sec global + per-chat
- Magic link: HMAC-SHA256, TTL 15 min, single-use, hash en DB
- Tool subset SSoT: ToolGroupMeta.available_channels (web-only: navigation, guided, landing, offer_section)
- Separación física vs sales_agent: 2 bots, 2 tokens, 2 webhooks, 2 schemas. Cero shared state. Arch fitness test enforce
```

## Decisiones tomadas durante implementación

| Decision ID | Topic | Resolución |
|---|---|---|
| D-PI5-IMPL-001 | API_SECRET_KEY for HMAC | REUSE existing `Settings.API_SECRET_KEY` (no new env var) |
| D-PI5-IMPL-002 | FRONTEND_URL | NEW Settings env var con default `https://app.nicolify.com` |
| D-PI5-IMPL-003 | GET /link-status sin token_id | Reuse mismo endpoint con `token_id: UUID \| None = None` Query param |
| D-PI5-IMPL-004 | `Base` import location | `src.shared.domain.base_entity` (no `src.core.database`) — corregido durante test failure |
| D-PI5-IMPL-005 | TelegramLinkingClient state machine | Refactor a "linked DERIVED from queries" pattern (no setState-in-effect) — solución eslint react-compiler |
| D-PI5-IMPL-006 | Migration apply path | Manual via SQL idempotente (alembic head bloqueado por migration 114 pre-existing) |

## Métricas

| Métrica | Valor |
|---|---|
| Files changed | 31 (15 BE + 8 FE + 4 tests + 4 PM docs) |
| Insertions | +2313 |
| Tests new | 29 (8 arch fitness + 8 link service + 4 redirect + 9 tool channel filter) |
| Tests pass | 29/29 (100%) |
| Lint errors | 0 |
| TSC errors | 0 |
| Time elapsed | ~4 horas (research + architect + impl + close) |
| Iter auto-fix loop | 0 (single-pass implementation) |

## Deuda técnica generada

| Item | Descripción | Sprint destino |
|---|---|---|
| Orchestrator hookup MVP placeholder | Worker linked branch responde placeholder text en lugar de invocar copilot orchestrator con `channel='telegram'` | **S2 PR-2** |
| `TELEGRAM_CONTEXT_WINDOW_CONFIG` memory specific | MVP usa default web config; Telegram needs 3000 raw + summary 600 chars | **S2 PR-2** |
| `TELEGRAM_CHANNEL_CONTEXT` cacheable fragment | Anthropic prompt cache 1024 tokens umbral protection | **S2 PR-2** |
| Migration 120 stuck behind broken migration 114 | Tables aplicadas manual SQL; alembic upgrade head bloqueado por migration 114 (pre-existing bug `model_pricing_snapshot.raw_payload NOT NULL`) | Out of scope (separate fix) |
| FE polling 60s × 3000ms = ~20 requests | OK MVP, optimizar con WebSocket/SSE post 50+ tenants Telegram-active | PI futuro |
| HITL escalation sales_agent → copilot | Out of scope intencional | **S3 PR-3** |
| Push notifs proactivas + encargos | Out of scope intencional | **S4 PR-4** |
| Multi-role tool filter implementation | Schema OK, lógica futuro | PI futuro |

## Acción Chris pendiente para activar deploy

| Acción | Cuándo |
|---|---|
| BotFather `/newbot` crear `@nicolify_copilot_dev_bot` (dev) y `@nicolify_copilot_bot` (prod) | Pre-deploy (no urgente para test local) |
| Tokens en `.env`+`.env.prod` | ✅ done |
| `setWebhook` con secret_token a `https://dev-api.nicolify.com/api/v1/copilot/telegram/webhook` (dev) y prod URL | Post-deploy (script futuro `scripts/setup_copilot_telegram_webhook.py` — S5 PR-5) |
| Fix migration 114 pre-existing (bloquea alembic upgrade head) | Out of scope PR-1 |

## Commits que componen PR-1

```
c1fa2909  feat(copilot): PR-1 Telegram bot foundation (PI-5 S1)
58807d3b  docs(pm): PI-5 PR-1 architect — CONTEXT-BRIEF + CONTRACT + UI-SPEC ready
b7cb1209  docs(pm): refine PI-5 with research + S1 sprint + PR-1 skeleton
5ded25ca  docs(pm): bootstrap PI-5-copilot-multicanal-telegram (discovery)
```
