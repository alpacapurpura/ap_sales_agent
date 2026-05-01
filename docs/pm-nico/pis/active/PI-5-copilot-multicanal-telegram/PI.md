# PI-5-copilot-multicanal-telegram — Copilot Multicanal: Telegram MVP

## Meta

| Campo | Valor |
|---|---|
| PI ID | PI-5-copilot-multicanal-telegram |
| Estado | discovery (research in progress) |
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

## Decisiones de arquitectura clave (preliminares — refinar post research)

| Decisión | Propuesta | Razón |
|---|---|---|
| **Bot identity** | Global único Nicolify (`@nicolify_copilot_bot`, 1 token) | Cero costo per-tenant. Pattern Linear/Notion. Escalable 1000+ |
| **Sales_agent bot futuro** | Per-tenant (cada uno crea en BotFather) | Voz marca tenant + grupos venta = require identity propia |
| **Routing webhook** | `/webhooks/telegram/copilot` (single, global) vs `/webhooks/telegram/sales-agent/{tenant_id}` (per-tenant futuro) | Separación física en URL — no decision runtime |
| **Tabla canal** | `copilot_channel_link` (no compartida con sales_agent) | Cero FK cruzada. Schema separado |
| **Conversation memory** | Hybrid (recent N + summary + vector Qdrant retrieval) | Cost-aware + UX permanente. Detalle research file |
| **HITL pattern** | LangGraph `interrupt()` + checkpointer + wakeup callback | LangChain recomendado pattern, Nicolify ya usa LangGraph |
| **Tool subset** | Decorator `@available_in("web", "telegram")` en tool registry | Single source of truth. Auto-doc |
| **Open vs closed bot** | Open + auth in-message | Discovery + CTA signup. Sin link = sin leak |

## Research dependencies

| File | Estado |
|---|---|
| `docs/pm-nico/research/2026-04-30-telegram-bot-copilot-patterns.md` | **in progress** (general-purpose subagent) — cubre conversation memory, HITL, multi-user roles, magic link, tool subset, escalabilidad 1000 tenants, anti-patterns |

PI.md se refina con findings concretos cuando research vuelva (tabla decisiones, tradeoffs, recomendación final por sección).

## Sprints (preliminar — refinar post research)

| Sprint | Tema | PRs estimados | Estado |
|---|---|---|---|
| **S1** | Foundation Telegram bot + linking | PR-1 webhook + bot adapter, PR-2 magic link onboarding flow, PR-3 tool subset registry + capability map | discovery |
| **S2** | Conversation memory + cost-aware context | PR-4 hybrid memory pattern (recent + summary + vector retrieval) | discovery |
| **S3** | HITL escalation sales_agent ↔ copilot | PR-5 LangGraph interrupt scaffold, PR-6 sales_agent HITL trigger, PR-7 timeout/resume handling | discovery |
| **S4** | Notificaciones proactivas + encargos | PR-8 push notifications engine, PR-9 encargos table + in-app inbox surface, PR-10 reminders cycle | discovery |
| **S5** | Multi-user roles prep + arch fitness | PR-11 `copilot_channel_link` table + role enum extensible, PR-12 arch tests + docs | discovery |

Sprint sizing target: 2-3 PRs/sprint. Total preliminar 12 PRs — refinar post research (puede shrink/expand).

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

1. ⏳ Esperar research file (`2026-04-30-telegram-bot-copilot-patterns.md`)
2. PM refina PI.md decisiones con findings concretos
3. PM redacta `sprints/S1-foundation-telegram-bot/sprint.md` macro
4. PM crea PR-1 folder skeleton (`prs/PR-1-telegram-webhook-bot-adapter/`) + prompts
5. Chris reserva username Telegram + provee token cuando esté listo PR-1 architect
