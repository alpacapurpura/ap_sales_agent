# PI-5-copilot-multicanal-telegram — Copilot Multicanal: Telegram MVP

## Meta

| Campo | Valor |
|---|---|
| PI ID | PI-5-copilot-multicanal-telegram |
| Estado | discovery (research **done** — sprint planning) |
| Tema | Extender copilot al canal Telegram. Pattern multicanal extensible (WhatsApp + IG DM = futuros PIs separados, OUT OF SCOPE) |
| Owner PM | /pm |
| Inicio | 2026-04-30 |
| Cierre estimado | TBD post research |
| Cierre real | — |

## Outcome esperado

**Cuantitativo:** dueño autenticado puede consultar ≥10 capacidades clave de su negocio (sales, métricas, leads recientes, status campañas) y dejar ≥3 tipos de "encargos" desde Telegram con latencia <3s p95. >=70% adopción Telegram link entre tenants activos a 30 días post-launch.

**Cualitativo:** dueño dice "el copilot me responde como mi account manager — le pregunto desde el celular sin abrir laptop, me avisa cuando hay algo importante, le dejo encargos para cuando vuelva al escritorio".

## JTBD (job to be done)

> Cuando estoy fuera de la laptop (celular, reunión, calle), quiero consultar el estado de mi negocio o dejar encargos a mi copilot, para no perder tiempo ni momentum mientras estoy lejos del escritorio.

Casos de uso típicos:
1. **Consultar estado** — "¿cómo van las ventas hoy?", "¿qué pasó con la campaña de Meta?", "¿hay leads nuevos?"
2. **Dejar encargos** — "anota una idea para campaña: X", "recordame revisar Y mañana", "preparame un resumen de Z para cuando entre a la web"
3. **Recibir alertas proactivas** — copilot avisa: bajón métrica clave, lead alto ticket esperando respuesta, campaña fuera de presupuesto
4. **HITL — sales_agent escala al dueño** — sales_agent está cerrando un lead alto ticket, necesita decisión sensible (ajuste pricing, autorización descuento, respuesta crítica). Copilot pausa al sales_agent, pregunta al dueño en Telegram, propaga respuesta de vuelta al sales_agent en sesión activa con el lead

## Hipótesis

- **H1:** Dueño usa más Telegram que web fuera de horario laboral. Mobile-first consulta = ganancia productividad real.
- **H2:** HITL Telegram baja churn de leads alto ticket (hoy se enfrían cuando dueño tarda en responder edge case sales_agent).
- **H3:** "Encargos" persistentes (TODOs propagados a in-app) = ganancia retención (user vuelve a la web a procesarlos).
- **H4:** Bot global Nicolify (no per-tenant) escala a 1000+ tenants sin costo incremental Telegram.

## Scope

### In-scope (PI-5)

| Item | Detalle |
|---|---|
| **Telegram bot global Nicolify** | `@nicolify_copilot_bot` (1 token env var, único, NO per-tenant). DMs únicamente, NO grupos |
| **Linking chat_id ↔ tenant** | Magic link in-app `/settings/copilot/telegram` → deep link `t.me/bot?start=TOKEN` → bot vincula. Token TTL + single-use |
| **Open + auth in-message** | Bot accesible público; sin link responde CTA hacia signup |
| **Tool subset map SSoT** | Cada tool registry tiene flag `available_in_channels: ["web", "telegram"]`. Tools no disponibles → response template friendly "lo vemos cuando entres a la web" |
| **Conversation memory cost-aware** | Pattern hybrid (recent N + summary older + vector retrieval) — research file definirá detalle |
| **Notificaciones proactivas** | Copilot push messages al dueño linked. MVP triggers: alerts métricas críticas + sales_agent HITL escalation + reminders encargos pendientes |
| **HITL sales_agent escalation** | LangGraph interrupt pattern. Sales_agent pause → notify copilot Telegram → wait owner response → resume con respuesta inyectada. Timeout default = sales_agent procede con criterio propio + responde lead "te confirmo en breve" |
| **Encargos persistencia** | "Anota encargo: X" → guarda en tabla `copilot_owner_todos` → muestra inbox in-app cuando dueño vuelve |
| **Multi-user roles arquitectura prep** | Tabla `copilot_channel_link` con campo `role` extensible (default `owner` MVP) |
| **Switch sales_agent vs copilot** | Separación física por bot identity (2 bots distintos = 2 tokens). Cero shared state. Sales_agent telegram bot = futuro PI separado |
| **Arch fitness tests** | Test: `copilot_telegram_bot_token_is_global` (no per-tenant). Test: `copilot_channel_link_no_cross_module_fk` (no FK a sales_agent_*) |

### Out-of-scope (este PI)

| Item | Por qué |
|---|---|
| WhatsApp bridge | PI separado futuro — Meta API limits + auth distinto |
| IG DM / TikTok DM bots | Use case distinto (training material reels, no conversación dueño) |
| Sales_agent telegram bot per-tenant | Otro PI (sales_agent module) — este PI solo asegura no cruzarse |
| Grupos Telegram (promo/venta) | Sales_agent territory, no copilot |
| Multi-user roles UI/CRUD | MVP solo dueño. Solo tabla preparada |
| Voz (audio messages Telegram) | Diferido; MVP texto + docs/PDFs (Telegram nativo file upload) |
| Cards interactivas avanzadas | MVP usa Telegram inline keyboards básicos. Cards complejas → "lo vemos en web" |

## Decisiones de arquitectura clave (post research)

> Detalle full + razones en `decisions.md` D-PI5-001..031 + `research/2026-04-30-telegram-bot-copilot-patterns.md`.

| Área | Decisión | Reuso codebase |
|---|---|---|
| **Bot identity** | Global único `@nicolify_copilot_bot`, env var `COPILOT_TELEGRAM_BOT_TOKEN`. Distinto de `TELEGRAM_BOT_TOKEN` (sales_agent). | `connections/infrastructure/channels/telegram.py` adapter pattern |
| **Webhook routing** | `/api/v1/copilot/telegram/webhook` global. Sales_agent webhook futuro queda separado | `connections/api/telegram.py` referencia |
| **Handler non-blocking** | Encola en ARQ/Redis < 200ms, devuelve 200. Worker async procesa LLM | Pattern existente sales_agent |
| **Filtrado** | Solo `chat.type == "private"`. Ignora grupos/supergrupos/canales | — |
| **Auth webhook** | `X-Telegram-Bot-Api-Secret-Token` header validado | Estándar Telegram |
| **Identity user** | `from_user.id` (numérico, inmutable). `username` solo display, mutable | — |
| **Schema canal** | Tabla nueva `copilot_channel_links` (separada de sales_agent). Identity = `from_user.id` | — |
| **Conversation memory** | `ContextWindowBuilder` + `RollingSummarizer` con `TELEGRAM_CONTEXT_WINDOW_CONFIG` (3000 tokens, 15 msgs, summary 600 chars). Misma `CopilotConversationModel` con cols `channel_type`+`channel_chat_id`. NO vector retrieval MVP | `copilot/application/memory/*` |
| **Cache prefijo** | Añadir `TELEGRAM_CHANNEL_CONTEXT` a `CACHEABLE_FRAGMENTS` ≥1024 tokens umbral Anthropic | `copilot/application/orchestrator/system_prompt_layout.py` |
| **HITL escalation** | Tabla `hitl_requests`. Sales_agent `node_escalation` → `interrupt()` LangGraph. Copilot Telegram notifica → resume `Command(resume=...)`. Timeout 15 min → `decision_fallback` | `sales_agent/application/agents/sales/{nodes,tools}.py` + `AgentStateCheckpointModel` |
| **Magic link** | `t.me/nicolify_copilot_bot?start=TOKEN`. HMAC-SHA256, TTL 15 min, single-use, hash en DB. Tabla `copilot_link_tokens` | `secrets.token_urlsafe`, HMAC stdlib |
| **Onboarding UX** | FE in-app polling 3s × 60s `/api/v1/copilot/telegram-link-status?token_id=X`. Bot sin link → CTA template friendly, NO auth in-chat | — |
| **Tool subset SSoT** | `ToolGroupMeta.available_channels: frozenset[str]` (default `{"web","telegram","whatsapp"}`). Web-only: `navigation`, `guided`, `landing` mutations, `offer_section` mutations | `copilot/application/tools/registry.py` extension |
| **Multi-user roles** | Schema preparado (`role` enum `owner|assistant|finance_admin|marketing_lead`). MVP solo `owner`. Filtro por rol = futuro PI | — |
| **Rate limit** | Worker `asyncio.Semaphore(30)` global + per-chat lock. NO en handler | `asyncio.Lock` stdlib |
| **PII** | `sanitize_payload()` antes persistir. Solo `chat_id`/`text`/`message_id` en logs | `copilot/infrastructure/prompts/sanitizer.py` |
| **Files** | ≤20MB `getFile` → `document_processor`. >20MB redirect web | `document_processor` existente |
| **Switch sales_agent ↔ copilot** | Separación física: 2 bots, 2 tokens, 2 webhooks, 2 schemas. Cero shared state. Arch fitness test enforce | — |

## Research dependencies

| File | Estado |
|---|---|
| `docs/pm-nico/research/2026-04-30-telegram-bot-copilot-patterns.md` | ✅ done. 7 secciones + 31 decisiones consolidadas + paths código referencia |

## Sprints (refinados post research)

| Sprint | Tema | PRs | Estado |
|---|---|---|---|
| **S1** | Foundation Telegram bot + linking + tool subset | PR-1 cross-stack bot adapter + webhook + magic link onboarding (BE+FE) + `copilot_channel_links` + `copilot_link_tokens` tables. Cohesivo cross-stack | not-started |
| **S2** | Memory + tool subset + non-link UX | PR-2 `TELEGRAM_CONTEXT_WINDOW_CONFIG` + `channel_type/channel_chat_id` cols + `TELEGRAM_CHANNEL_CONTEXT` cacheable fragment + `ToolGroupMeta.available_channels` SSoT + redirect template tools no-disponibles | not-started |
| **S3** | HITL sales_agent ↔ copilot | PR-3 cross-module: `hitl_requests` tabla + `node_escalation` migration interrupt() + copilot HITL notification + resume worker + timeout cron | not-started |
| **S4** | Notifs proactivas + encargos | PR-4 push engine alerts (métricas críticas, reminders) + `copilot_owner_todos` tabla + in-app inbox surface | not-started |
| **S5** | Arch fitness + docs + observabilidad | PR-5 arch tests (token global, cero FK cruzada copilot↔sales_agent) + `current-state/copilot.md` + `current-state/sales-agent.md` actualizados + telemetría Telegram (latencia, rate limit hits, HITL timeout rate) | not-started |

Sprint sizing target: 1 PR cohesivo amplio por sprint (Opus 4.7[1M] permite scope grande). Total 5 PRs.

## Riesgos identificados

| # | Riesgo | Mitigación preliminar |
|---|---|---|
| R1 | Telegram username `@nicolify_copilot_bot` squatted | Reservar en BotFather PRE-PR (acción Chris) |
| R2 | Webhook scalability 1000+ tenants single endpoint | Async processing + queue (Redis ya en stack). Confirmar pattern post research |
| R3 | HITL latency leads esperan demasiado | Timeout default + sales_agent fallback "te confirmo en breve". Detalle post research |
| R4 | PII en logs Telegram messages | Sanitize antes persistir (ya pattern Nicolify — `sanitize_payload`) |
| R5 | Tool subset incompleto MVP → user frustración | Catalog amplio MVP (≥30 tools telegram-allowed). Audit pre-launch |
| R6 | Cross-canal conversation merge ambiguo | Per-canal session_id distinto. Web in-app y Telegram = sesiones separadas pero memory compartida vía vector retrieval |
| R7 | Sales_agent eventualmente confunde bot identity | Arch fitness test enforce separación. Doc clara `current-state/` |

## Copilot-first checklist

- [x] **¿Operable desde copilot?** — sí, ESTE PI EXTIENDE COPILOT a Telegram. El propio outcome del PI ES copilot-first
- [x] **¿Tools accesibles vía Telegram?** — subset documentado, gradual expansion
- [x] **¿HITL bidireccional sales_agent ↔ copilot?** — sí, S3
- [x] **¿Notifications surface?** — sí, S4 push proactivo

## Decisiones diferidas

| Tema | Por qué diferido | Cuándo |
|---|---|---|
| Voz/audio Telegram | MVP texto+files suficiente | Post research si user feedback |
| Cards interactivas avanzadas (multi-step forms) | "Web-only" filter cubre MVP | Si patterns claros emergen |
| Multi-user UI CRUD | Tabla preparada, UI no urgente MVP | PI futuro post 50+ tenants Telegram-active |
| Conversion analytics Telegram (funnel link → activate → retention) | Métricas básicas suficientes MVP | Post-launch 30 días |

## Aprobaciones / blockers Chris

| Item | Estado |
|---|---|
| Reservar `@nicolify_copilot_bot` en BotFather (cuenta Nicolify) | **PENDING Chris** — pre-PR-1 |
| Telegram bot token global → secrets manager (env var `COPILOT_TELEGRAM_BOT_TOKEN`) | PENDING Chris post-bot creation |
| Decisión final memory pattern (post research) | PENDING — research file llegando |

## Próximos pasos

1. ✅ Research done
2. ✅ PI.md refinado (decisiones D-PI5-001..031)
3. ✅ S1 sprint.md macro escrito (`sprints/S1-foundation-telegram-bot/sprint.md`)
4. ✅ PR-1 folder skeleton creado (`prs/PR-1-telegram-bot-foundation/`) con prompts cocidos
5. ⏳ Chris autoriza arrancar PR-1 architect → ejecutar prompt
6. ⏳ Chris reserva `@nicolify_copilot_bot` BotFather + provee token al architect cuando lo pida (no urgente — architect solo diseña, no necesita token)
