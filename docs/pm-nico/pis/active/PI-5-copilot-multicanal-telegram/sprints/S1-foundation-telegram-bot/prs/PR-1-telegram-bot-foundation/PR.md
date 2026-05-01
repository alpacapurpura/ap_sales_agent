# PR-1-telegram-bot-foundation

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-1-telegram-bot-foundation |
| Sprint padre | S1-foundation-telegram-bot |
| PI padre | PI-5-copilot-multicanal-telegram |
| Estado | discovery |
| Tipo | feature (cross-stack BE+FE+agentic) |
| Esfuerzo | **L** |
| Owner PM | /pm |
| Claimed by session | — |

## Problema (user-facing)

JTBD: "Cuando estoy fuera de la laptop, quiero poder consultar mi negocio o dejar encargos al copilot, para no perder tiempo ni momentum."

Hoy el copilot solo vive in-app web. Dueño en celular, reunión, calle = sin acceso. Necesita canal mobile-first.

## Outcome esperado

Dueño linkeado a `@nicolify_copilot_bot` puede:
- Preguntar al copilot por chat Telegram → recibir respuesta texto Markdown V2
- Recibir CTA "lo vemos en web" cuando intent requiere tool web-only
- Setup en <60s desde `/settings/copilot/telegram` modal con botón "Conectar Telegram"

Métrica: usuario completa link end-to-end < 60s p95. Latencia respuesta primer token (LLM async pipeline) < 5s p95.

## Walking skeleton (mínimo viable cohesivo)

Cohesivo cross-stack en 1 PR (Opus 4.7[1M]):

1. **BE — bot adapter copilot** `copilot/infrastructure/channels/telegram_bot.py` (NO compartir `connections/infrastructure/channels/telegram.py` — separación física)
2. **BE — webhook endpoint** `/api/v1/copilot/telegram/webhook` (FastAPI router en `copilot/api/`) non-blocking, valida `X-Telegram-Bot-Api-Secret-Token`, encola en ARQ
3. **BE — ARQ worker** `copilot/infrastructure/workers/telegram_worker.py` consume cola, procesa via copilot orchestrator con `channel='telegram'`, envía respuesta vía bot API con rate limiting (`asyncio.Semaphore(30)` + per-chat lock)
4. **BE — tablas + migration** `copilot_channel_links` + `copilot_link_tokens` (idempotente raw SQL `CREATE TABLE IF NOT EXISTS`)
5. **BE — magic link service** `copilot/application/services/telegram_link_service.py` genera HMAC-SHA256 token, guarda hash, valida `/start TOKEN`, vincula `chat_id`
6. **BE — tool registry extension** `ToolGroupMeta.available_channels: frozenset[str]` + clasificación research §5
7. **BE — redirect template** tool no disponible → response "requiere editor web" + URL
8. **BE — orchestrator extension** acepta `channel='telegram'` (filter tools por channel)
9. **BE — sanitize** `sanitize_payload` antes persistir messages (`chat_id`/`text`/`message_id` only)
10. **BE — orchestrator memory** reuso `CopilotConversationModel` con cols nuevas `channel_type` + `channel_chat_id` (memory config Telegram-specific = S2 — MVP usa default config web)
11. **FE — settings page** `app/(main)/[tenantId]/(dashboard)/settings/copilot/telegram/page.tsx` con botón "Conectar Telegram" + estado linked/unlinked
12. **FE — flow** click → `POST /api/v1/copilot/telegram/link-tokens` → recibe `deep_link_url` + `token_id` → `window.open(deep_link_url)` + polling `/api/v1/copilot/telegram/link-status?token_id=X` cada 3s × 60s → confirma linked
13. **Arch fitness test** `test_copilot_telegram_bot_token_is_global` (env var distinto de `TELEGRAM_BOT_TOKEN`)
14. **Arch fitness test** `test_copilot_channel_links_no_cross_module_fk` (cero FK desde `copilot_channel_links` a `sales_agent_*`)
15. **Tests** unit (HMAC token, rate limiter, sanitize), integration (webhook flow end-to-end), arch fitness
16. **Docs** `current-state/copilot.md` capability "Telegram channel — DMs linkeados magic link"

## Soluciones consideradas

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A — Reutilizar `connections/infrastructure/channels/telegram.py`** | Menos código nuevo | Acopla copilot↔sales_agent. Viola D-PI5-005 (separación física) | descartada |
| **B — Bot adapter copilot dedicado en `copilot/infrastructure/channels/`** | Separación física. Cero FK cruzada. Schema dedicado. Pattern reusable WA futuro | Code dup parcial (HMAC, format escape — pero `shared/agent_observability/channels/format.py` reutilizable) | **ELEGIDA** |
| **C — Adapter en `connections/` + dispatcher routing copilot vs sales_agent** | Centraliza adapters | Viola D-PI5-005. Routing runtime fragil | descartada |

## Validación técnica preliminar (Technical Sanity Check)

Realizada via research file `research/2026-04-30-telegram-bot-copilot-patterns.md` + paths código referencia §"Código Nicolify de referencia" (12 paths confirmados existentes).

- Modules afectados: `copilot/` (primary), `shared/` (format reuse), `core/` (env var add)
- Modules NO afectados: `sales_agent/`, `connections/` (importante — separación)
- Blockers conocidos: ninguno. Reuso `escape_markdown_v2`, `sanitize_payload`, ARQ stack, Redis stack, FastAPI patterns
- Tiempo estimado architect: 1 ejecución (~600s)
- Tiempo estimado builders paralelos: 1 ejecución c/u BE/agentic + FE (~600s c/u)

## Existing systems audit (architect-mandatory)

> Architect ejecuta esta auditoría EN SU FASE antes de proponer nuevo módulo/adapter. Greps obligatorios documentados en CONTRACT.md sección "EXTEND vs NEW decisions".

Subsystems que PR-1 toca:

### 1. Telegram adapter
- `grep -rn "Telegram" backend/src/modules/connections/infrastructure/channels/`
- `grep -rn "TELEGRAM_BOT_TOKEN\|telegram_bot_token" backend/src/`
- Decision esperada: **NEW** en `copilot/infrastructure/channels/` por D-PI5-005. Reuso `shared/agent_observability/channels/format.py::escape_markdown_v2()`

### 2. Webhook handler pattern
- Read `backend/src/modules/connections/api/telegram.py` (referencia)
- Decision esperada: **NEW** endpoint `/api/v1/copilot/telegram/webhook` siguiendo MISMO pattern (non-blocking + ARQ enqueue) pero en `copilot/api/`

### 3. ARQ worker pattern
- `grep -rn "arq\|ARQ" backend/src/`
- Decision esperada: **EXTEND** ARQ stack — añadir queue `copilot_telegram_turns`

### 4. Magic link / token HMAC
- `grep -rn "secrets.token\|hmac" backend/src/`
- Decision esperada: **NEW** `copilot/application/services/telegram_link_service.py`

### 5. Conversation model
- Read `backend/src/modules/copilot/infrastructure/models/conversation_model.py`
- Decision esperada: **EXTEND** añadir cols `channel_type` + `channel_chat_id` (migration idempotente)

### 6. Tool registry
- Read `backend/src/modules/copilot/application/tools/registry.py`
- Decision esperada: **EXTEND** añadir dataclass `ToolGroupMeta` con campo `available_channels: frozenset[str]`

### 7. Sanitizer
- Read `backend/src/modules/copilot/infrastructure/prompts/sanitizer.py`
- Decision esperada: **EXTEND** apenas — `sanitize_payload` ya existe, aplicar a messages Telegram antes persistir

### 8. Frontend settings page
- `find frontend/src/app -path "*settings*copilot*"` — verificar si existe
- Decision esperada: **NEW** route group `app/(main)/[tenantId]/(dashboard)/settings/copilot/telegram/`

## Cross-stack scope

| Surface | Owner builder | Skills | Auditor |
|---|---|---|---|
| `modules/copilot/api/` (webhook + endpoints magic link) | `nicolify-agentic` (Opus) | `copilot-expert` + `tessl__fastapi` | `nicolify-agentic-auditor` |
| `modules/copilot/application/` (orchestrator ext + memory ext + link service + tool registry meta) | `nicolify-agentic` (Opus) | `copilot-expert` + `tessl__langgraph` | `nicolify-agentic-auditor` |
| `modules/copilot/infrastructure/` (bot adapter + ARQ worker + models + migration) | `nicolify-agentic` (Opus) | `copilot-expert` | `nicolify-agentic-auditor` |
| `modules/connections/` | NO toca (regla R1) | — | — |
| Migration Alembic idempotente | `nicolify-agentic` | — | `nicolify-agentic-auditor` |
| `frontend/src/app/(main)/[tenantId]/(dashboard)/settings/copilot/telegram/` | `nicolify-frontend` (Sonnet) | `frontend-expert` + `tessl__shadcn-ui` + `tessl__react-patterns` | `nicolify-frontend-auditor` |
| `frontend/src/features/copilot/` (hook `useTelegramLinking`) | `nicolify-frontend` (Sonnet) | `frontend-expert` + `tessl__zod` | `nicolify-frontend-auditor` |
| Arch tests `backend/tests/architecture/` | `nicolify-agentic` | — | `nicolify-agentic-auditor` |

PR es **agentic + frontend** — NO toca módulos negocio. Backend builder NO se invoca (regla cardinal: copilot = agentic territorio).

## Riesgos PR-1

| # | Riesgo | Mitigación | Owner |
|---|---|---|---|
| R1 | Builder agentic spawnea cambios en `connections/` (refactor mistakenly) | Architect CONTRACT.md explicit: "PR-1 NO toca `modules/connections/`. Shared logic = `shared/`" | Architect |
| R2 | Webhook lento bloquea ARQ enqueue | Test load 100 RPS handler — `< 200ms p99` | Backend builder + auditor |
| R3 | Token Telegram en logs builder | Sanitize logs handler. Env var `COPILOT_TELEGRAM_BOT_TOKEN` siempre via `Settings`, nunca hardcoded | Builder + auditor |
| R4 | Migration breaks prod (cols ADD on `copilot_conversations`) | `ADD COLUMN IF NOT EXISTS` idempotente. Test clone DB pre-merge | Builder + auditor |
| R5 | FE polling 3s × 60s == 20 requests para user que abandona | Cancel polling al unmount + visibility change | Frontend builder |
| R6 | Telegram username squatted al deploy | Chris reserva pre-architect (action item PI.md) | Chris |

## Copilot-first checklist

- [x] **¿Operable desde copilot?** — sí, este PR ES copilot-first (extiende canal)
- [x] **¿Tools accesibles vía Telegram?** — subset clasificado D-PI5-024 (12+ tool groups operables)
- [x] **¿Surface admin?** — futuro, sin scope MVP
- [x] **¿Observabilidad?** — `copilot_trace_event` + telegram_worker logs estructurados

## Decisiones diferidas

| Tema | Razón | Cuándo |
|---|---|---|
| `TELEGRAM_CONTEXT_WINDOW_CONFIG` específico | MVP default config web suficiente foundation | S2 PR-2 |
| `TELEGRAM_CHANNEL_CONTEXT` cacheable fragment | S2 (optim post foundation) | S2 PR-2 |
| HITL `node_escalation` migration | S3 dedicado (cross-module) | S3 PR-3 |
| Push notifs proactivas | S4 dedicado | S4 PR-4 |
| Voice messages | Post-MVP feedback | PI futuro |
| Multi-role tool filter impl | Schema OK, lógica futuro | PI futuro |

## Aprobaciones / blockers Chris

| Item | Estado |
|---|---|
| Reservar `@nicolify_copilot_bot` BotFather (cuenta Nicolify) | **PENDING Chris** — pre-architect ideal, NO blocker (architect diseña sin token; builder lo necesita al integration test) |
| Provee token al secrets manager (`COPILOT_TELEGRAM_BOT_TOKEN` env var) | PENDING Chris — pre-builder integration test |
| Confirmar username (si squatted alternativos: `@nicolify_bot`, `@nicolify_assistant_bot`, `@copilot_nicolify_bot`) | PENDING Chris |

## Próximos pasos (orchestration)

1. Chris ejecuta `prompts/00-context-prep.md` → `nicolify-context-builder` (Haiku) produce `CONTEXT-BRIEF.md`
2. Chris ejecuta `prompts/01-architect-start.md` → `nicolify-architect` produce `CONTRACT.md` cross-stack + arch decisions + spawnea `ux-flow-architect` paralelo → `UI-SPEC.md` settings page
3. Chris ejecuta `prompts/02-builder-start.md` → spawn paralelo `nicolify-agentic` (BE/agentic) + `nicolify-frontend` (FE). Cada builder spawnea su auditor en auto-fix loop hasta PASS
4. Chris ejecuta `prompts/04-pm-close.md` → /pm cierra PR (RESULT.md + current-state/copilot.md update)
