# Sprint S2 — Telegram Orchestrator Hookup + Memory Config + Cache Fragment

## Meta

| Campo | Valor |
|---|---|
| Sprint ID | S2-telegram-orchestrator-memory-cache |
| PI padre | PI-5-copilot-multicanal-telegram |
| Estado | in-progress |
| Inicio | 2026-04-30 |
| Cierre estimado | 2026-04-30 (1 PR cohesivo amplio Opus 4.7[1M]) |
| Cierre real | — |
| Owner PM | /pm |

## Objetivo (1 línea)

Reemplazar placeholder MVP de PR-1 con copilot orchestrator real invocado por canal Telegram: worker linked branch llama `invoke_copilot_orchestrator(channel='telegram', tenant_id, user_id, conversation_id_lookup_by_channel_chat_id)`, memoria con `TELEGRAM_CONTEXT_WINDOW_CONFIG` distinto del web, prefijo cacheable `TELEGRAM_CHANNEL_CONTEXT` ≥1024 tokens umbral Anthropic, tool registry filter validado runtime + channel format adapter MarkdownV2 antes de enviar respuesta via bot.

## Pre-handoff (input desde sprint anterior)

> Input desde `../S1-foundation-telegram-bot/handoff.md` (S1 cerrado 2026-04-30 con PR-1 shipped en commit `c1fa2909`, PI-handoff en `ede52aed`).

- **Decisiones consolidadas S1:**
  - D-PI5-006 → `TELEGRAM_CONTEXT_WINDOW_CONFIG` (3000 raw, 15 msgs, summary 600 chars, nudge 12000) **CRÍTICO S2 PR-2**
  - D-PI5-007 → `CopilotConversationModel` con cols `channel_type` + `channel_chat_id` (✅ live PR-1)
  - D-PI5-008 → NO vector retrieval Qdrant en MVP
  - D-PI5-009 → `TELEGRAM_CHANNEL_CONTEXT` cacheable fragment ≥1024 tokens umbral **CRÍTICO S2 PR-2**
  - D-PI5-024 → tools telegram-allowed (12+ groups, ya en `ToolGroupMeta` PR-1)
  - D-PI5-IMPL-005 → linked state DERIVED from queries (FE pattern, no aplica S2 — cero cambios FE)
- **Surface disponible (live):**
  - APIs: `POST /api/v1/copilot/telegram/webhook` (NON-BLOCKING + secret_token + private filter), link-tokens/link-status/link CRUD
  - DB: `copilot_channel_links`, `copilot_link_tokens`, `copilot_conversations.channel_type`+`channel_chat_id` (live)
  - Code agentic: `copilot/infrastructure/channels/telegram_bot.py::CopilotTelegramBot`, `copilot/infrastructure/workers/telegram_worker.py::process_copilot_telegram_turn` (placeholder reply MVP), `copilot/application/services/telegram_link_service.py`, `copilot/application/tools/telegram_redirect.py`, `copilot/application/tools/registry.py::ToolGroupMeta` + `is_group_available_in_channel()` + `get_tools_for_context(channel='web')` filter
  - FE: `/{tenantId}/settings/copilot/telegram` page + `<TelegramLinkingClient />` (live, no cambia S2)
  - Arch fitness baseline: 8 tests `test_copilot_telegram_separation.py` ratchet
- **Riesgos abiertos:**
  - Migration 120 stuck behind broken migration 114 (pre-existing) — out of scope S2
  - Telegram cache prefix <1024 sin studio_snapshot → `TELEGRAM_CHANNEL_CONTEXT` mitiga
  - LLM orchestrator hookup pendiente → ESTE sprint
  - Bot username squatted al deploy → Chris BotFather pre-deploy (action item out of scope S2)
- **Skills/agentes recomendados:**
  - `nicolify-context-builder` (Haiku) pre-flight obligatorio (PR ≥M)
  - `nicolify-architect` (Opus) → CONTRACT design memory config + cache fragment + orchestrator hookup
  - `nicolify-agentic` (Opus) → implementer single-surface (modules/copilot only)
  - `nicolify-agentic-auditor` (Opus) → audit memory + cache + tool filter runtime + format adapter correctness
  - Skills domain: `copilot-expert`, `tessl__langgraph`, `tessl__graceful-degradation`
  - **Sin frontend builder/auditor** (cero cambios FE)
  - **Sin backend builder/auditor** (cero cambios módulos negocio)

## Plan PRs (folders)

> Sprint sizing Opus 4.7[1M]: **1 PR cohesivo amplio agentic-only**. Single surface = cero paralelización builder, single architect, single auditor. ~2 ejecuciones Chris (architect + builder-con-auto-audit).

| PR | Folder | Descripción | Agentes/skills | Esfuerzo | Estado |
|---|---|---|---|---|---|
| PR-2 | `prs/PR-2-telegram-orchestrator-hookup/` | Worker linked branch invoca copilot orchestrator real con `channel='telegram'` + lookup conversation por `(channel_type='telegram', channel_chat_id)` + `TELEGRAM_CONTEXT_WINDOW_CONFIG` (3000/15/600/12000) + `TELEGRAM_CHANNEL_CONTEXT` cacheable fragment ≥1024 tokens en `system_prompt_layout.py` + `get_tools_for_context(context, channel='telegram')` filter runtime + `format_for_channel(channel='telegram', parse_mode='MarkdownV2')` adapter post-orchestrator + tests integration end-to-end (mock Telegram update → ARQ enqueue → worker → orchestrator → mock bot send) happy path linked + unlinked CTA + /start TOKEN + tests memory config inyección por channel + arch fitness test prefijo cacheable Telegram ≥1024 tokens | architect (Opus) → agentic builder (Opus) → agentic-auditor (Opus) | **L** | not-started |

Detalle PR-2 en `prs/PR-2-telegram-orchestrator-hookup/PR.md`. Prompts pre-cocidos en `prs/PR-2-telegram-orchestrator-hookup/prompts/`.

## Criterio éxito sprint

- [ ] Worker `process_copilot_telegram_turn` linked branch invoca `invoke_copilot_orchestrator(channel='telegram', tenant_id, user_id, conversation_id_lookup)` (sin placeholder)
- [ ] `CopilotConversationRepository.get_by_channel(tenant_id, user_id, channel_type='telegram', channel_chat_id)` lookup retorna conversation row o crea nueva
- [ ] `TELEGRAM_CONTEXT_WINDOW_CONFIG` ContextWindowConfig dataclass con valores D-PI5-006 (RAW_WINDOW_TOKENS=3000, RAW_WINDOW_MAX_MESSAGES=15, RAW_WINDOW_MIN_MESSAGES=4, SUMMARY_MAX_CHARS=600, SUMMARY_TARGET_TOKENS=200, NUDGE_AFTER_TOTAL_TOKENS=12000, NUDGE_HARD_LIMIT_TOKENS=20000, NUDGE_AFTER_MESSAGE_COUNT=20)
- [ ] `ContextWindowBuilder` + `RollingSummarizer` reciben config inyectado por canal (`channel='telegram'` → telegram config; `channel='web'` → default config existente; otros → default)
- [ ] `TELEGRAM_CHANNEL_CONTEXT` fragment añadido a `CACHEABLE_FRAGMENTS` en `system_prompt_layout.py`. Compute prefijo cacheable Telegram sample ≥1024 tokens (umbral Anthropic prompt cache)
- [ ] Orchestrator usa `get_tools_for_context(context, channel='telegram')` cuando `context.channel == 'telegram'` — tools web-only (`navigation`, `guided`, `landing` mutations, `offer_section` mutations) excluded del registry runtime
- [ ] Channel format adapter: respuesta orchestrator final → `format_for_channel(channel='telegram', parse_mode='MarkdownV2')` antes `bot.send_message` (escapa chars especiales `_*[]()~\`>#+-=|{}.!`)
- [ ] Tests integration end-to-end (asyncio): mock Telegram update payload → webhook handler enqueue ARQ → worker pulled → conversation lookup → orchestrator invocado → respuesta formateada → mock bot adapter send. Cubren happy path linked + unlinked CTA + `/start TOKEN` linking
- [ ] Tests memory: `ContextWindowBuilder(channel='telegram')` aplica `TELEGRAM_CONTEXT_WINDOW_CONFIG`; `channel='web'` aplica default; default 'web' fallback para channel desconocido
- [ ] Arch fitness test: `test_telegram_cache_prefix_meets_anthropic_threshold` — sample compute con tenant minimal (sin studio_snapshot/form_data) confirma prefijo cacheable ≥1024 tokens
- [ ] Coverage tests + lint (ruff) + arch tests pass NATIVE WSL
- [ ] `current-state/copilot.md` actualizado: capability "Canal Telegram — orchestrator real + memory cost-aware + prefijo cacheable Anthropic"
- [ ] PR-2 `RESULT.md` escrito + lineage update

## Out of scope (este sprint)

| Item | Razón | Sprint destino |
|---|---|---|
| HITL escalation sales_agent ↔ copilot | Cross-module mayor (sales_agent + copilot + interrupt LangGraph) — sprint dedicado | S3 PR-3 |
| Push notifs proactivas + encargos in-app inbox | Capability separada (push engine + tabla `copilot_owner_todos`) | S4 PR-4 |
| Multi-role tool filter implementation | Schema OK PR-1, lógica filtro futuro PI | PI futuro |
| Migration 114 fix pre-existing | Bug pre-existing fuera scope PI-5 | Separate ticket |
| Vector retrieval Qdrant Telegram conversations | D-PI5-008 deferido hasta feedback "no me recuerda lo que le dije" | Post-launch |
| Voice messages Telegram | MVP texto + docs | PI futuro |
| Cards interactivas avanzadas | Telegram inline keyboards básicos suficiente MVP | PI futuro si patterns emergen |

## Decisiones a tomar durante sprint

(append-only conforme aparezcan)

| Fecha | Decisión | PR |
|---|---|---|
| 2026-04-30 | Sprint sizing 1 PR amplio agentic-only (vs splittear memory/cache/orchestrator). Razón: cohesivo (todos tocan path orchestrator + memory) + Opus 4.7[1M] permite scope L | PR-2 |

## Riesgos

| Riesgo | Mitigación | Owner |
|---|---|---|
| Cambio firma `ContextWindowBuilder.__init__` rompe call sites web existentes | Default param `channel='web'` preserva backward compat. Tests baseline web pre-existing pass | Architect → Builder |
| `TELEGRAM_CHANNEL_CONTEXT` add a `CACHEABLE_FRAGMENTS` invalida cache web (cambia byte-prefix global) | Fragment SOLO se añade cuando `context.channel == 'telegram'`; web prefijo intacto | Architect |
| Tool filter runtime falla silenciosamente (orchestrator pasa channel='telegram' pero registry retorna tools web-only por bug) | Test integration verifica registry filtered output ≠ default 'web' set; arch fitness test count groups Telegram-allowed = 12 | Architect → Builder |
| Format adapter doble-escape MarkdownV2 (orchestrator ya devuelve Markdown + adapter escapa otra vez) | Test caso real: orchestrator output con backticks/asterisks → adapter escapa → bot.send_message recibe sin error Telegram API | Builder |
| Conversation lookup race condition (2 mensajes Telegram simultáneos crean 2 conversations duplicadas) | UNIQUE constraint `(tenant_id, user_id, channel_type, channel_chat_id)` o lookup-or-create con SELECT FOR UPDATE | Architect |
| Migration 120 stuck → S2 no puede aplicar nueva migration si requerida | S2 NO requiere migration nueva (cols ya existen PR-1). Si emerge necesidad → escalate Chris | PM |

## Cierre

Al cerrar:
1. Llenar `learnings.md` (qué funcionó, qué no, sorpresas — especially patterns reuse `ContextWindowBuilder` por inyección config + cache fragment threshold compute técnica)
2. Llenar `handoff.md` con decisiones consolidadas para S3: HITL escalation patterns, surface orchestrator + memory + tool filter live para reusar, riesgos abiertos
3. Marcar sprint `done` en este `sprint.md`
4. Verificar `prs/PR-2-*/RESULT.md` escrito + `current-state/copilot.md` actualizado con lineage
5. Si learnings impactan proceso global → append `../../../../process/process-learnings.md`
