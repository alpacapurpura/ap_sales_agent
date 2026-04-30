# campaigns — Estado funcional

## Meta

| Campo | Valor |
|---|---|
| Studio padre | Sales / Growth (PI-1 — Sales con hooks Growth) |
| Estado | PI-1 S1 SHIPPED (PR-3 domain + PR-4 services/API) — S2 PR-5 SHIPPED partial (PR-6 pending) |
| Ultima actualizacion | 2026-04-30 (PR-5 S2: orchestrator real + 4 ARQ workers + ChannelRouter Telegram + circuit breaker + audit log retention 90d) |
| Doc tecnico | `docs/domains/campaigns/` (en construccion) |

---

## S1 SHIPPED — Superficies entregadas (PR-3 + PR-4)

### Domain layer (PR-3 — commits `f951c282`, `4cab1c1c`, `7b39b66b`, `4de090a9`)

| Superficie | Estado |
|---|---|
| Campaign aggregate + FSM 6 estados (draft/scheduled/running/paused/completed/failed/cancelled) + DAG steps | SHIPPED |
| CampaignTask + ChannelRouter port + DomainEvents | SHIPPED |
| Segment + SegmentFilter v1 strict (extra=forbid) + SegmentSnapshot opt-in | SHIPPED |
| CampaignTemplate domain model + 6 repository interfaces tenant-scoped | SHIPPED |
| SQLA models (6 tablas) + 6 repo impls (soft-delete, tenant-isolated, AsyncSession) | SHIPPED |
| Migration 6 tablas + worker partial idx + template dual UNIQUE (migration 092/093) | SHIPPED |
| 4 arch tests domain (FSM Hypothesis + tenant ISO AST + filter strict + worker idx DDL) | SHIPPED |

### Application services (PR-4 Sub-A/B — commits `85e3ca66`, `5802b82c`)

| Superficie | Estado |
|---|---|
| SegmentFilterEvaluator: SQL-side filtering via LeadQueryPort (SQLA BinaryExpression por criterio) | SHIPPED |
| CampaignService: FSM lifecycle (launch/pause/complete/fail/cancel), plan enforcement 402, idempotency-key opt-in | SHIPPED |
| SegmentService: resolve() SQL-filtered + snapshot() materializacion | SHIPPED |
| CampaignTemplateService: catalog list, clone-to-tenant, variable resolution | SHIPPED |
| PaginatedResponse[T] canonical DTO | SHIPPED |

### API REST 23 endpoints (PR-4 Sub-C — commit `a0a0bfc7`)

Prefijo: `/api/v1/`

**campaigns (9 endpoints):**
- `GET /campaigns/` — list con PaginatedResponse (limit=20, offset=0)
- `POST /campaigns/` — create (idempotency-key opt-in)
- `GET /campaigns/{id}` — get by id
- `PATCH /campaigns/{id}` — update metadata
- `DELETE /campaigns/{id}` — soft delete
- `POST /campaigns/{id}/launch` — FSM transition → running
- `POST /campaigns/{id}/pause` — FSM transition → paused
- `POST /campaigns/{id}/complete` — FSM transition → completed
- `POST /campaigns/{id}/cancel` — FSM transition → cancelled

**segments (7 endpoints):**
- `GET /segments/` — list con PaginatedResponse
- `POST /segments/` — create
- `GET /segments/{id}` — get by id
- `PATCH /segments/{id}` — update criteria
- `DELETE /segments/{id}` — soft delete
- `POST /segments/{id}/resolve` — materializar snapshot SQL-filtered
- `GET /segments/{id}/snapshot` — ultimo snapshot

**campaign-templates (7 endpoints):**
- `GET /campaign-templates/` — list global + tenant (PaginatedResponse)
- `POST /campaign-templates/` — create tenant template
- `GET /campaign-templates/{id}` — get by id
- `PATCH /campaign-templates/{id}` — update
- `DELETE /campaign-templates/{id}` — soft delete
- `POST /campaign-templates/{id}/clone` — clone template to tenant
- `GET /campaign-templates/catalog` — catalog global templates

Todos los endpoints no-DELETE tienen `response_model=` (PII allowlist). Header `X-Tenant-ID` requerido en todos.

### Templates globales seed (PR-4 Sub-D — commit `04a695f1`)

5 templates globales con UUIDs v5 reproducibles (idempotentes en re-run):

| Slug | Descripcion |
|---|---|
| `welcome_new_lead` | Bienvenida a nuevo lead opt-in (1 paso, 1 canal) |
| `product_launch_4day` | Secuencia lanzamiento 4 dias (4 pasos, multi-paso) |
| `webinar_registration` | Registro + recordatorios webinar (3 pasos) |
| `cold_reactivation` | Reactivacion lead frio (2 pasos, re-engagement) |
| `post_purchase_followup` | Post-compra + upsell (3 pasos) |

### Arch fitness tests (PR-4 Sub-E — commit `531ed287`)

20 arch tests en 4 archivos (AST-based, zero runtime deps):

| Test | Que verifica |
|---|---|
| `test_campaigns_api_response_model.py` | Todos los endpoints no-DELETE tienen response_model= |
| `test_campaigns_fsm_service_layer.py` | Transiciones FSM solo en domain layer, no en API |
| `test_campaigns_pagination_default.py` | PaginatedResponse shape + list endpoints con limit=20/offset=0 |
| `test_segment_resolve_sql_filtering.py` | SegmentFilterEvaluator usa SQLA, SegmentService usa LeadQueryPort, no cross-module crm |

---

## S2 SHIPPED FULL — Orchestrator + Workers + ChannelRouter Telegram + Cutover Consumers

> PR-5 commits: Sub-A `4d8953ab` + Sub-B `b830bbad` + Sub-C `227ba63a` + Sub-D `78fdd6ce` + Sub-E `961a2c3c` + Sub-F `5febfe39` + Sub-G `5ad63dc8` + REVIEW iter-2 PASS `e4408b2f`
> PR-6 commits: Sub-A `f8a4b3e5` + Sub-B `7b2de359` + Sub-C `8d2aed36` + Sub-D `97780627` + Sub-E `fb2683d0` + Sub-F `6b8fcb11` + Sub-G `d3fbe665` + REVIEW iter-2 PASS `03d423c7`

| Superficie | Estado | PR |
|---|---|---|
| `CampaignOrchestrator.launch()` real (reemplaza PR-4 STUB) — @idempotent, single-TX, root tasks | SHIPPED | PR-5 Sub-C |
| `run_campaign_execution_task` ARQ worker (dispatch Telegram via CB + idempotency) | SHIPPED | PR-5 Sub-D |
| `run_campaign_scheduler_tick` ARQ cron (promote SCHEDULED + claim pending tasks) | SHIPPED | PR-5 Sub-D |
| `run_segment_refresh_tick` ARQ cron (refresh STATIC segments linked RUNNING campaigns) | SHIPPED | PR-5 Sub-D |
| `purge_old_campaigns_audit` ARQ cron (retention 90d, cron 04:30 UTC) | SHIPPED | PR-5 Sub-D |
| `TelegramChannelRouter` (pipeline pre-send: compliance → rate-limiter → idempotency → CB → POST) | SHIPPED | PR-5 Sub-B |
| `ChannelRouterRegistry` singleton (thread-safe, startup bootstrap) | SHIPPED | PR-5 Sub-B |
| Circuit breaker per (channel, tenant_id) Redis-backed (Lua atomico, CLOSED/OPEN/HALF_OPEN) | SHIPPED | PR-5 Sub-A |
| `AuditLogService` best-effort (sanitize PII + persist) + `campaign_audit` table (migration 113) | SHIPPED | PR-5 Sub-A |
| 4 arch fitness gates (orchestrator + workers + registry + retention) | SHIPPED | PR-5 Sub-E |
| ComplianceService + OutboundRateLimiter wired pre-send (TelegramChannelRouter) | SHIPPED | PR-5 Sub-B |
| ChannelRouter WhatsApp (via ManyChat bridge) | PENDIENTE | PI-2 |
| ChannelRouter Email (via MailerLite) | PENDIENTE | PI-2 |
| **PR-6: Wrappers BudgetGuardingChatModel/Service + cost_estimator + PricingSnapshotRepoAsync** | SHIPPED | PR-6 Sub-A |
| **PR-6: Outbox cutover ON sales_agent (USE_OUTBOX_PATTERN_SALES_AGENT=True) + BudgetGuard wiring single point ConversationPipeline** | SHIPPED | PR-6 Sub-B |
| **PR-6: Outbox cutover ON copilot (USE_OUTBOX_PATTERN_COPILOT=True) + BudgetGuard wiring single point build_deep_agent_graph** | SHIPPED | PR-6 Sub-C |
| **PR-6: Outbox cutover ON brand (USE_OUTBOX_PATTERN_BRAND=True)** | SHIPPED | PR-6 Sub-D |
| **PR-6: 2 arch fitness gates (budget_guard_pre_llm_call + no_legacy_event_bus_publish ratchet)** | SHIPPED | PR-6 Sub-E |
| Brand BudgetGuard wiring 7 LLM callsites (DR-7) | DIFERIDO | Sub-D-2 / S3 |
| Observabilidad emision real (campaign_llm_call + campaign_trace_event) | PENDIENTE | S3 |

---

## S3 PENDIENTE — Wiring sales_agent + copilot tools

| Superficie | Estado | Sprint |
|---|---|---|
| copilot provider campaigns (campaign_get_status, campaign_pause, campaign_launch tools) | PENDIENTE | S3 |
| sales_agent OutboundOrchestrator (usa CampaignService.launch() para outbound segmentado) | PENDIENTE | S3 |
| Copilot Marketing Campaign Subagent (deepagents, PI-2) | PENDIENTE | PI-2 |

---

## Capacidades operables desde copilot

| Capacidad | Hoy | PI-1 S3 | PI-2 |
|---|---|---|---|
| Lanzar campana outbound | No (orchestrator real PR-5, tool pendiente) | `campaign_launch` tool | Marketing Campaign Subagent |
| Consultar status campana | No | `campaign_get_status` | — |
| Pausar/activar | No | `campaign_pause` / `campaign_launch` | — |
| Crear segmento NL | No | — | `segment_create` NL |
| Performance queries | No | — | `campaign_roi` |

---

## Infra foundation pre-existente (PR-1/PR-2 S0 — sin cambio)

| Capacidad | Estado |
|---|---|
| Observability spec (`campaign` en registry, tablas `campaign_llm_call` + `campaign_trace_event`) | SHIPPED S0 |
| Outbox event store (`shared/domain_events/outbox/`, flag USE_OUTBOX_PATTERN OFF default) | SHIPPED S0 |
| Idempotency primitives (`shared/idempotency/`, `@idempotent` decorator) | SHIPPED S0 |
| `mv_daily_llm_cost_per_tenant_v2` UNION-ALL incluye campaign | SHIPPED S0 |
| BudgetGuard + OutboundRateLimiter + ComplianceService primitivas | SHIPPED S0 (wiring S2) |

---

## Conexiones cross-modulo

- **Lee de:** crm (customer profiles via LeadQueryPort), connections (canales MailerLite/ManyChat/Meta), offer (que se promociona), brand (voz para outbound)
- **Lo leera:** copilot (tools S3), sales_agent (OutboundOrchestrator S3), analytics (campaign performance S2), advertising (retargeting export PI-3)

---

## Decisiones producto vinculadas

Ver `pis/PI-1-campaigns-module/decisions.md`. Resumen D1-D22 (heredados + PI-1 especificos). Clave:
- D11: PI-1 cierra con MVP 1 Telegram. Multi-canal/email a PI-2/3.
- D14: Reservacion 50% sales_agent pool (BudgetGuard invariante, arch test property-based).
- D17: Sprint 0 cortado a 5 sub-sprints.
- D15: Custom asyncio CB Redis-backed por (channel, tenant_id) — pybreaker sync-only, aiobreaker abandoned.
- D16: Queue named `arq:campaigns_execution`; deploy split CampaignsWorkerSettings diferido PI-3.
- D18: Application-side idempotency Telegram via IdempotencyStore, key=`telegram-send:{task_id}`, TTL=24h.
- D19: Retention 90d audit log + cron 04:30 UTC (offset copilot purge 04:00).
- D22: Single-TX launch genera SOLO root tasks (step_index==0); descendientes S3+.

## PIs historicos / activos

| PI | Estado | Tema |
|---|---|---|
| PI-1 S1 | SHIPPED | campaigns domain + services + API + templates seed |
| PI-1 S2 | SHIPPED partial (PR-5) / PR-6 pending | orchestrator + 4 ARQ workers + Telegram + CB + audit log |
| PI-1 S3 | planned | sales_agent + copilot wiring |
| PI-2 | Next (placeholder) | Multi-canal (ManyChat) + Copilot subagent + EMAIL_DRIP |
| PI-3 | Later | Event campaigns + CRM Hub Frontend + Retargeting |
