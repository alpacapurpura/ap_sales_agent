# Sprint S1 — Foundation Telegram Bot + Linking + Tool Subset

## Meta

| Campo | Valor |
|---|---|
| Sprint ID | S1-foundation-telegram-bot |
| PI padre | PI-5-copilot-multicanal-telegram |
| Estado | not-started |
| Inicio | TBD (Chris autoriza) |
| Cierre estimado | TBD post PR-1 close |
| Cierre real | — |
| Owner PM | /pm |

## Objetivo (1 línea)

Dueño autenticado linkea su Telegram al copilot via magic link in-app y recibe respuestas básicas del copilot (tools subset Telegram-allowed) en `@nicolify_copilot_bot` con webhook non-blocking + ARQ worker async.

## Pre-handoff (input desde sprint anterior)

> No hay sprint anterior. Input directo del PI:

- Decisiones tomadas: D-PI5-001..031 (`../../decisions.md` + `research/2026-04-30-telegram-bot-copilot-patterns.md`)
- Surface disponible:
  - `connections/infrastructure/channels/telegram.py` — adapter Telegram existente (sales_agent) → referencia patrón
  - `connections/api/telegram.py` — webhook handler existente (sales_agent) → referencia patrón
  - `copilot/application/orchestrator/` — orchestrator copilot (recibirá nuevo channel='telegram')
  - `copilot/application/tools/registry.py` — extender con `available_channels`
  - `shared/agent_observability/channels/format.py::escape_markdown_v2()` — reutilizar formato
  - ARQ + Redis ya en stack (cola async)
- Riesgos abiertos: ninguno bloqueante (research cubrió todos)
- Skills/agentes recomendados:
  - `nicolify-context-builder` (Haiku) PR pre-flight obligatorio (PR es L scope)
  - `nicolify-architect` (Opus) → CONTRACT cross-stack
  - `nicolify-agentic` (Opus) — copilot is agentic surface
  - `nicolify-backend` (Sonnet) — `connections/api/telegram.py` extension + tablas + migration (módulos negocio + connections)
  - `nicolify-frontend` (Sonnet) — `/settings/copilot/telegram` modal + polling
  - `ux-flow-architect` skill — UI-SPEC settings page modal
  - `nicolify-agentic-auditor` (Opus) — copilot surface
  - `nicolify-backend-auditor` (Opus) — connections/migration surface
  - `nicolify-frontend-auditor` (Opus) — FE settings page

## Plan PRs (folders)

> Sprint sizing Opus 4.7[1M]: 1 PR cohesivo amplio. Cross-stack BE+FE+agentic en una ejecución coordinada con paralelización por surface.

| PR | Folder | Descripción | Agentes/skills | Esfuerzo | Estado |
|---|---|---|---|---|---|
| PR-1 | `prs/PR-1-telegram-bot-foundation/` | Cross-stack: bot adapter + webhook non-blocking + ARQ worker + magic link onboarding (BE + FE settings page) + tablas `copilot_channel_links` + `copilot_link_tokens` + tool subset SSoT (`available_channels` en `ToolGroupMeta`) + redirect template tools no-disponibles + arch fitness test "1 token global, no per-tenant" + filter `chat.type=='private'` | architect → (BE+agentic+FE paralelo) → (3 auditores) | **L** | not-started |

Detalle PR-1 en `prs/PR-1-telegram-bot-foundation/PR.md`. Prompts pre-cocidos en `prs/PR-1-telegram-bot-foundation/prompts/`.

## Criterio éxito sprint

- [ ] `@nicolify_copilot_bot` recibe `/start TOKEN` válido → vincula `chat_id`↔tenant en `copilot_channel_links`
- [ ] Bot recibe DM texto del dueño linkeado → orchestrator copilot procesa con `channel='telegram'` → respuesta Markdown V2 escapado < 4096 chars
- [ ] Bot recibe DM sin link → response template friendly con CTA URL `app.nicolify.com/[tenant]/settings/copilot/telegram`
- [ ] Bot ignora updates donde `chat.type != "private"`
- [ ] Bot rechaza updates sin `X-Telegram-Bot-Api-Secret-Token` válido (returns 401)
- [ ] Webhook handler responde 200 < 200ms (LLM procesa async via ARQ worker)
- [ ] Tool group `navigation`, `guided`, `landing mutations`, `offer_section mutations` → response template "requiere editor web"
- [ ] FE `/settings/copilot/telegram` modal con botón "Conectar Telegram" → genera token → abre `t.me/...?start=TOKEN` → polling 3s × 60s confirma `linked_at`
- [ ] Token magic link single-use + TTL 15 min validado test
- [ ] Arch fitness test `test_copilot_telegram_bot_token_is_global` en `backend/tests/architecture/`
- [ ] Sanitize `from_user.first_name`, `last_name`, `phone` antes persistir
- [ ] Coverage tests + lint + tsc + arch tests pass
- [ ] `current-state/copilot.md` actualizado con capability "Telegram channel — DMs linkeados magic link, tool subset filtered"
- [ ] PR-1 `RESULT.md` escrito + `current-state/copilot.md` lineage update

## Out of scope (este sprint)

| Item | Razón | Sprint destino |
|---|---|---|
| Conversation memory `TELEGRAM_CONTEXT_WINDOW_CONFIG` | Cohesión separada (memory + cache prefix + tool registry deeper) | S2 |
| `TELEGRAM_CHANNEL_CONTEXT` cacheable fragment | Optim post foundation | S2 |
| HITL escalation sales_agent → copilot | Cross-module mayor — sprint dedicado | S3 |
| Push notifs proactivas + encargos | Capability separada | S4 |
| Multi-user roles filter implementation | Schema OK, filtro futuro | PI futuro |
| Voice messages Telegram | MVP texto + docs | PI futuro |

## Decisiones a tomar durante sprint

(append-only conforme aparezcan)

| Fecha | Decisión | PR |
|---|---|---|
| TBD | ... | ... |

## Riesgos

| Riesgo | Mitigación | Owner |
|---|---|---|
| Username `@nicolify_copilot_bot` squatted | Chris reserva BotFather pre-PR. Alternativos: `@nicolify_bot`, `@nicolify_assistant_bot`, `@copilot_nicolify_bot` | Chris |
| Token Telegram filtrado a logs/repos | Builder usa `secrets` env var, gitignore `.env*`, sanitize logs | Backend builder |
| Webhook spam fake updates | `secret_token` Telegram + 401 strict | Backend builder |
| Conflicto namespace con sales_agent telegram adapter | Files separados `copilot/infrastructure/channels/telegram_*` (NO `connections/infrastructure/channels/telegram*`) | Architect |

## Cierre

Al cerrar:
1. Llenar `learnings.md` (qué funcionó, qué no, sorpresas — especially sobre patterns LangGraph + ARQ worker reuse)
2. Llenar `handoff.md` (decisiones consolidadas para S2: memory + cache + tool registry deepen, surface BE/FE/agentic disponible)
3. Marcar sprint `done` en este `sprint.md`
4. Verificar `prs/PR-1-*/RESULT.md` escrito + `current-state/copilot.md` actualizado con lineage
5. Si learnings impactan proceso global → append `../../../../process/process-learnings.md`
