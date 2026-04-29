# PI-1-campaigns-module — Sistema de Campañas

> Primer PI formal de pm-nico. Input legacy migrado: `docs/pm/campaigns/` (FOUNDATION.md + research 5 carpetas + MASTER_TODO 13 fases).
>
> **Reframing 2026-04-29 (Chris):** prioridad absoluta = **robustez + escalabilidad como Sprint 0**. Antes de tocar dominio campaigns, construir primitivas cross-cutting que TODO sprint posterior reusa sin refactor.

## Meta

| Campo | Valor |
|---|---|
| PI ID | PI-1-campaigns-module |
| Estado | discovery → planning |
| Tema | Módulo nuevo: orquestación campañas multi-canal end-to-end |
| Alcance PI-1 | Sprint 0 (robustez) + Sprint 1 (dominio) + Sprint 2 (orchestrator) + Sprint 3 (MVP 1 Telegram) + **Sprint 4 (Mini CRM Hub lite, paralelo a S3)**. Resto = PI-2/PI-3. |
| Owner PM | /pm |
| Inicio | 2026-04-29 |
| Cierre estimado | TBD post-S0 plan |
| Cierre real | — |

## Outcome esperado (PI-1 cierre)

User puede:
1. Ver sus contactos en `/sales/contactos` (vista lite con filtros, búsqueda, detail drawer).
2. Crear segmento manual seleccionando contactos.
3. Lanzar campaña AGENT_CONVERSATION (Telegram) sobre ese segmento.
4. Sales Agent ejecuta outbound personalizado.
5. Si lead responde, conversación vive en Inbox con `campaign_id` tag.

**Toda la primitiva robusta debajo + arquitectura FE forward-compatible lista para PI-2/PI-3 sin refactor.**

- Cuantitativo: 1 campaña real lanzada por Chris a 5+ contactos Telegram desde UI, 0 mensajes duplicados, 0 leak entre tenants.
- Cualitativo: "Sé que cuando agreguemos email, retargeting, webinar, segment builder visual o CRM Hub completo, no reescribimos nada — solo agregamos."

## Hipótesis

- **H1**: Nicolify hoy tiene piezas dispersas (sales_agent + assets + connections) sin orquestación. Unificarlas = palanca enorme.
- **H2**: Tier 1 LATAM = WhatsApp + TikTok DM + retargeting + webinar. SMS irrelevante.
- **H3**: User no quiere templates fijos. Quiere instrucciones high-level + agente personaliza.
- **H4 (nueva, Chris 2026-04-29)**: Si Sprint 0 entrega primitivas robustas (outbox, idempotency, rate limit, compliance gate, observability), Sprints 1-N agregan canales/tipos sin tocar foundation. **Cero refactor entre MVPs**.

## Sprint plan PI-1

### Sprint 0 — FUNDACIÓN ROBUSTA Y ESCALABLE *(no negociable, antes de cualquier dominio campaigns)*

**Objetivo**: primitivas cross-cutting reutilizables en `backend/src/shared/`. Campaigns es primer consumer, sales_agent + voice_agent + content_agent las heredan. Bases bien definidas — Chris 2026-04-29: "para todo, debemos dejar las bases bien definidas".

**Alcance acotado**: 5 sub-sprints críticos. S0.4/S0.7/S0.8 originales descartados a Sprint 2 / regla estándar (cut Chris para priorizar profundidad sobre amplitud).

| ID | Sub-sprint | Ubicación | Entregable |
|---|---|---|---|
| S0.1 | **Outbox pattern GLOBAL** | `shared/domain_events/outbox/` | Refactor `event_bus` actual: tabla `domain_event_outbox` + dispatcher worker. Exactly-once entre DB write + ARQ enqueue. **Cubre TODO el proyecto**, no solo campaigns. Migra emisores existentes (sales_agent events, copilot events, brand events). |
| S0.2 | Idempotency store | `shared/idempotency/` | Servicio `IdempotencyStore` Redis-backed. Decorator `@idempotent(key_fn, ttl)`. Usado en external API calls (ManyChat, MailerLite, Meta) + CampaignTask creation + sales_agent webhooks. TTL 24h-7d configurable. |
| S0.3 | **Plan tiers + BudgetGuard + RateLimiter** | `shared/billing/` | Tablas `plan_config` (5 planes: Free/Básico/Intermedio/Avanzado/Ultra editables sin migration) + `tenant_subscription`. `BudgetGuard.check(tenant_id, agent_kind, est_cost)` con **reservación 50% sales_agent invariant**. `OutboundRateLimiter` sliding window Redis. Streamlit admin `/planes-billing`. **Razonamiento numérico**: ver `research/2026-04-29-billing-tiers-cost-model.md`. |
| S0.5 | Compliance gate service | `shared/compliance/` | `ComplianceService.check(contact, channel, campaign)` → `CheckResult(allowed, reason)`. Encapsula WABA-24h, opt-in tracking, blacklist, country-block. Usable desde ChannelRouter (S2) + futuro voice_agent. |
| S0.6 | Campaign observability spec | `campaigns/observability/` | **NO crear módulo nuevo** — `shared/agent_observability/` ya existe (consumido por copilot + sales_agent). Solo: `CampaignLlmCallModel` (si campaigns invoca LLM en futuro), `CampaignCallbackHandler(BaseAgentCallbackHandler)`, `register_agent_observability(AgentObservabilitySpec(agent_kind="campaign", ...))`. MV `mv_daily_llm_cost_per_tenant_v2` ya cubre vía UNION-ALL. |

**Cut explícito** (movido a Sprint 2 o regla estándar):
- ~~S0.4 Circuit breaker + DLQ~~ → Sprint 2 cuando hay external API calls reales (sin uso aún = sobre-ingeniería)
- ~~S0.7 Audit trail~~ → Sprint 2 cuando hay mutaciones a auditar
- ~~S0.8 Arch tests dedicado~~ → ya regla estándar `.claude/rules/architectural-fitness.md`. Aplica auto.

**Criterio éxito S0**: 5 PRs merged con tests verdes. Zero código de dominio campaigns escrito todavía. Primitivas testables aisladamente. BudgetGuard reservación 50% probada con test (copilot exhausto NO consume SA pool).

### Sprint 1 — DOMINIO CAMPAIGNS + REPOS *(TDD strict)*

| ID | Entregable |
|---|---|
| S1.1 | `campaigns/domain/`: Campaign, CampaignStep, CampaignTask, Segment, SegmentFilter, ChannelRouter (interface), CampaignType/Status enums, events |
| S1.2 | `campaigns/infrastructure/models/` + repositories (Async SQLA 2.0) |
| S1.3 | `campaigns/application/services/`: CampaignService (CRUD + lifecycle), SegmentService (resolve + estimate_size) |
| S1.4 | API: `campaigns/api/campaigns.py` + `segments.py` + `templates.py` con response_model |
| S1.5 | Templates globales catalog: 5 templates iniciales (welcome, launch-4day, webinar, cold-reactivation, post-purchase) |

### Sprint 2 — ORCHESTRATOR + WORKERS *(usa primitivas S0)*

| ID | Entregable |
|---|---|
| S2.1 | `CampaignOrchestrator.launch()`: resolve segment → compliance gate (S0.5) → idempotent task creation (S0.2) → outbox (S0.1) → ARQ enqueue |
| S2.2 | `CampaignExecutionWorker` ARQ: fetch PENDING → BudgetGuard+RateLimiter (S0.3) → execute → circuit breaker (movido aquí desde S0.4) → trace (shared agent_observability) → audit log (movido aquí desde S0.7) |
| S2.3 | `CampaignSchedulerWorker` ARQ: activa campañas en `scheduled_at` |
| S2.4 | `SegmentRefreshWorker` ARQ (cada 15min) |
| S2.5 | ChannelRouter v1 (Telegram-only): `select_channel()` → Telegram si `lead.telegram_id` |

### Sprint 3 — MVP 1 TELEGRAM OUTBOUND *(primer end-to-end visible)*

| ID | Entregable |
|---|---|
| S3.1 | Sales Agent: `OutboundOrchestrator` paralelo a ChatOrchestrator (non-breaking) |
| S3.2 | AgentState: campos opcionales `campaign_id`, `campaign_instructions`, `outbound_mode` |
| S3.3 | `compose.py`: nuevo slot `CAMPAIGN_CONTEXT` |
| S3.4 | Supervisor routing: `outbound_mode=True` → skip qualifier para score≥40 |
| S3.5 | `campaigns/infrastructure/external/sales_agent_adapter.py`: bridge CampaignTask → OutboundOrchestrator |
| S3.6 | Inbound reply recognition: ChatOrchestrator busca CampaignTask SENT últimas 24h → inyecta `campaign_id` en AgentState |
| S3.7 | Inbox UI: tag "campaña: {name}" en conversaciones |
| S3.8 | Campaign analytics endpoint: GET /campaigns/{id}/stats (SENT/RESPONDED/CONVERTED) |
| S3.9 | E2E test: crear campaign → launch → verificar Telegram messages |
| S3.10 | Test manual: Chris envía a 5+ contactos reales (UI desde S4 ya disponible) |

### Sprint 4 — MINI CRM HUB LITE *(paralelo a S3, forward-compatible architecture)*

> **Principio:** API contracts FINALES desde día 1. UI lite hoy. PI-3 expande por agregación, no por reescritura. Detalle en `sprints/S4-crm-hub-lite/sprint.md`.

| ID | Entregable |
|---|---|
| S4.1 | CRM contacts API forward-compatible: GET /contacts (paginated + ALL filters supported in schema) + GET /contacts/{id} + endpoint stubs documentados (`/journey`, `/campaigns` deferred PI-3) |
| S4.2 | UX session refinement: cargar `ux-sessions/2026-04-29-crm-module-proposal/` → UI-SPEC mini view (subset documentado) |
| S4.3 | FE primitives: `features/crm-hub/` con DataTable wrapper (en `components/shared/data-table/`), ContactFiltersPanel, ContactDetailContent (reusable drawer + página futura), IdentityList, ScoreBadge, LifecycleStageChip, SelectedContactsBar (slot pattern para PI-3 bulk actions) |
| S4.4 | `/sales/contactos` page: Server Component + ContactsPageClient con tabla + filtros + búsqueda + paginación + drawer detail + selección múltiple |
| S4.5 | Segment manual creation: SelectedContactsBar → "Crear segmento" → POST /segments STATIC |
| S4.6 | Wire S4 ↔ S3: botón "lanzar campaña Telegram" desde segment lite |

**Forward-compat invariantes (test arch):**
- `FilterParams` Pydantic schema soporta TODOS los filters PI-3 desde S4.1; lite UI expone subset.
- `ContactDetailContent` component aislado, drawer hoy + página completa PI-3 lo reusan.
- `Segment` domain ya soporta STATIC + DYNAMIC desde S1; S4 lite crea STATIC, PI-3 builder visual crea DYNAMIC.
- `DataTable` primitive en `components/shared/`, no en `features/crm-hub/` (reusable por campañas + segmentos PI-3).

## Out of scope PI-1 *(va a PI-2 / PI-3)*

| Item | PI futuro |
|---|---|
| Copilot subagent commercial_director (NL → campaign creation) | PI-2 |
| ManyChat bridge (WhatsApp via ManyChat) | PI-2 |
| MailerLite EMAIL_DRIP integration | PI-2 |
| EVENT_TRIGGER (webinar/launch multi-step) | PI-3 |
| CRM Hub completo (Segment Builder Visual + Campaign Dashboard + página detail completa + bulk actions avanzadas) | PI-3 — **agrega sobre lite S4, no reescribe** |
| Timeline rico journey events (endpoint + UI) | PI-3 |
| Retargeting Meta Ads | PI-3 |
| OneSignal Push | PI-4 |
| Referral / Afiliados | PI-4 |
| AI Voice Vapi | TBD (deferred) |

## Decisiones clave (heredadas legacy + nuevas)

| Fecha | Decisión | Razón |
|---|---|---|
| 2026-04-29 | Crear PI-1 separado de advertising/social_media | Campaigns = orquestación cross-channel, no plataforma única |
| 2026-04-29 | SMS descartado | WhatsApp domina LATAM |
| 2026-04-29 | Tier 1: WhatsApp + TikTok DM + retargeting + webinar | Chris priorizó |
| 2026-04-29 | D1-D9 confirmadas (legacy MASTER_TODO) | Multi-canal outbound, Sales Agent personaliza siempre, foundation-first, Commercial Director = Copilot subagent, Sales Agent B2C only, campaigns/ módulo independiente, Copilot único punto contacto, ManyChat bridge transitorio, Telegram canal pruebas |
| **2026-04-29** | **Sprint 0 = Robustez y Escalabilidad cross-cutting ANTES dominio** | **Chris reframing: cero refactor entre MVPs. Foundation-first deep.** |
| **2026-04-29** | **PI-1 cierra con MVP 1 (Telegram). Multi-canal/email/event a PI-2/3** | **Reduce scope creep. Retro temprana.** |
| **2026-04-29** | **Primitivas S0 viven en `shared/` (no en `campaigns/`)** | **Reuso futuro: sales_agent outbound, voice_agent, content_agent** |

## Restricciones / Riesgos

- **R1** (técnico): orquestación cross-channel = state machine compleja. Mitigación: outbox + idempotency keys (S0.1+S0.2).
- **R2** (producto): muchas opciones abruman user. Mitigación: copilot-first guía (PI-2).
- **R3** (compliance): WABA 24h + opt-in. Mitigación: ComplianceService gate central (S0.5).
- **R4** (cost runaway): tenant lanza campaña a 10K contactos sin límite. Mitigación: rate limiter + quotas (S0.3).
- **R5** (observability gap): tarea fallida sin rastro = bug invisible. Mitigación: trace events + audit log (S0.6+S0.7).
- **R6** (vendor lock-in): ManyChat/MailerLite/Meta APIs cambian. Mitigación: circuit breaker + adapter pattern (S0.4).

## Métricas seguimiento

| Métrica | Baseline | Target PI-1 | Cierre real |
|---|---|---|---|
| Campañas lanzadas Chris testing | 0 | 1+ | — |
| Mensajes Telegram entregados S3 | 0 | 5+ | — |
| Mensajes duplicados | n/a | 0 | — |
| Leak cross-tenant en tests | n/a | 0 | — |
| Trace events por campaign launch | n/a | ≥3 (launch / task_created / task_sent) | — |
| Sprint 0 PRs merged sin refactor en S1+ | n/a | 100% | — |

## Discovery tasks pendientes (responder antes Sprint 0 PR-1)

Ver sección "Preguntas abiertas a Chris" abajo. 7 preguntas críticas.

## Opportunities atendidas

A formalizar en `opportunities/` (PR-0 esta sesión):
- `outbound-conversational.md` (Tier 1A)
- `source-aware-treatment.md` (Tier 1B)
- `email-drip-mailerlite.md` (Tier 1D — PI-2)
- `event-campaign-orchestration.md` (Tier 1E — PI-3)
- `retargeting-meta-ads.md` (Tier 1F — PI-3)
- `tiktok-dm-automation.md` (Tier 1G — PI-2/3)

## Inputs externos

- `docs/pm/campaigns/00-framework/` — taxonomía + arquitectura Strategy+Command
- `docs/pm/campaigns/01-conversacional/` — research WABA, ManyChat, Respond.io
- `docs/pm/campaigns/02-email-marketing/` — MailerLite deep dive
- `docs/pm/campaigns/03-otros-tipos/` — webinar/retargeting/push/referral/voice
- `docs/pm/campaigns/04-integracion-nicolify/` — connections map
- `docs/pm/campaigns/05-arquitectura-agente/FOUNDATION.md` — pre-código architectural foundation
- `docs/pm/campaigns/MASTER_TODO.md` — 13 fases legacy (input, no canónico)

Migración legacy → pm-nico: PR-0 esta sesión.

## Cierre / Retro

Pendiente.
