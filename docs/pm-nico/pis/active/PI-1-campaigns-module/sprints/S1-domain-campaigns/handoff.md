# S1 Handoff — Domain Campaigns → S2 Orchestrator

> Owner: PM. Cierre sprint S1, input para S2.

## Sprint cerrado

| Campo | Valor |
|---|---|
| Sprint ID | S1-domain-campaigns |
| Estado | done |
| Cierre real | 2026-04-29 |
| PRs shipped | PR-3 (PASS) + PR-4 (PASS post-fix) |
| Commits totales | 12 (PR-3) + 9 (PR-4) = 21 |

## Surface disponible post-S1 (consumible por S2)

### Domain entities
- `Campaign` — aggregate root + FSM 6 estados (draft → scheduled → running ↔ paused → completed/canceled)
- `CampaignStep` — DAG branching `next_step_ids: list[UUID]`
- `CampaignTask` — unit ejecución per (campaign_id, lead_id, step_id) + worker queue partial idx CRITICAL 1000 clientes
- `Segment` — lazy filter + opt-in `SegmentSnapshot` materialization
- `SegmentFilter` — Pydantic v2 strict (extra=forbid) v1 minimal
- `CampaignTemplate` — global vs tenant-scoped dual UNIQUE PARTIAL
- `ChannelRouter` Protocol port (S2 implementa Telegram/WhatsApp/Email)
- 11 DomainEvents heredan shared S0 outbox base

### Application services
- `CampaignService` — CRUD + FSM transitions (delegate `Campaign.transition_*`) + cache TTL 30s + Redis pub/sub invalidation + plan enforcement (`max_campaigns_active` → 402)
- `SegmentService` — CRUD + `resolve()` SQL-side filtering JOIN customer_profiles + `estimate_size` cache 5min + `snapshot` opt-in
- `CampaignTemplateService` — CRUD + `list_available()` (global + tenant) cache 5min + `clone_to_campaign` transactional
- `SegmentFilterEvaluator` — pure function `evaluate(filter, lead) -> bool` + `to_sql_select(filter, *, tenant_id) -> Select` para escalabilidad

### API surface (23 endpoints REST)
- `/api/v1/campaigns/*` — CRUD + 6 FSM transitions (schedule/launch[stub]/pause/resume/complete/cancel) + steps CRUD
- `/api/v1/segments/*` — CRUD + resolve + snapshot
- `/api/v1/campaign-templates/*` — list_available + clone
- TODOS endpoints: `response_model=` + `Depends(get_tenant_context)` + AsyncSession + pagination max 100

### DB surface (PR-3 + PR-4 migrations)
- Tablas: `campaign`, `campaign_step`, `campaign_task`, `segment`, `segment_snapshot`, `campaign_template`
- ENUMs: campaign_type, campaign_status, step_type, task_status, segment_type
- ALTER `leads.country` (PR-2 deuda cerrada PR-4 mapping)
- Worker queue partial idx `WHERE status IN ('pending','scheduled')` — CRITICAL performance 1000 clientes
- Template dual UNIQUE PARTIAL (global vs tenant)
- Seed 5 templates globales reproducibles uuid5: welcome / launch-4day / webinar / cold-reactivation / post-purchase

## Decisiones architect tomadas (framing 1000 clientes)

| # | Decisión | Razón |
|---|---|---|
| 1 | FSM SSoT en domain entity (no service duplica) | Cero deuda — service delegate `Campaign.transition_*` |
| 2 | DAG `next_step_ids: list[UUID]` (no linked-list) | Branching real welcome 4-step + launch 4-day desde día 1 |
| 3 | Segment lazy + opt-in SegmentSnapshot | NO materialización masiva, audience locked solo running |
| 4 | SegmentFilter v1 minimal Pydantic strict + abstract base extensible | v1 cubre 100% catálogo FOUNDATION, vNext sin migration breaking |
| 5 | Worker queue partial idx `WHERE status IN ('pending','scheduled')` | Performance crítica 1000 clientes con campaign_task batches |
| 6 | Template dual UNIQUE PARTIAL (global vs tenant) | NULL distinct semantics correcta día 1 |
| 7 | AsyncSession en código nuevo (no Session legacy) | Regla `backend-ddd.md` migrate incrementally |
| 8 | SQL-side filtering JOIN customer_profiles | Escalable 1000 clientes sin Python loop |
| 9 | Cache TTL 30s + Redis pub/sub invalidation | Multi-pod ready día 1 |
| 10 | Plan enforcement `max_campaigns_active` → 402 | BudgetGuard wired en API layer |
| 11 | Idempotency-Key opt-in POST campaigns + clone | Production-grade dedup con S0 primitives |
| 12 | Templates seed uuid5(NAMESPACE_DNS, slug) reproducible | Idempotente cross-env (dev/staging/prod) |

## Riesgos abiertos S1 (input S2)

| Riesgo | Mitigación S2 | Owner |
|---|---|---|
| `launch()` STUB — no ejecuta envío real | S2 wirea `CampaignOrchestrator` consume `CampaignLaunched` event → genera CampaignTasks via DAG steps + dispatch ChannelRouter | architect S2 |
| Outbox path consumers FSM events (`USE_OUTBOX_PATTERN_CAMPAIGNS=false` default) | Flip flag tras smoke S2 | builder S2 cutover PR |
| ChannelRouter port sin impl | S2 implementa TelegramSender/WhatsAppSender/EmailSender + register en `ChannelRouterRegistry` | architect + agentic S2 |
| ARQ workers no existen | S2 crea `CampaignExecutionWorker` (consume CampaignTask scheduled_at), `CampaignSchedulerWorker` (cron tick), `SegmentRefreshWorker` (snapshot batch) | builder S2 |
| Mocks AsyncMock pueden ocultar bugs reales (F-2 atrapado por integration test) | S2 mantiene política "1 integration test sin mocks por feature crítico" | builder + auditor |

## Commits PR-3 (5)

- `f951c282` — Sub-A+B domain entities + repos interfaces
- `4cab1c1c` — Sub-C SQLA models + repo impls
- `7b39b66b` — Migration 6 tables + worker queue idx + template dual UNIQUE
- `4de090a9` — Sub-D arch tests (tenant isolation + FSM + filter validation + worker idx)
- `8a0f0429` — Sub-F IMPL-LOG + current-state caps domain
- (Post-review) `1c64935e` — F-1 mypy override campaigns

## Commits PR-4 (12)

- `284433fa` — PR.md + CONTRACT.md + prompts (architect autonomous, 0 open Qs)
- `ddb6a220` — LeadModel.country mapping (PR-2 deuda cerrada)
- `85e3ca66` — Sub-A SegmentFilterEvaluator (runtime + SQL JOIN customer_profiles)
- `5802b82c` — Sub-B Services (CampaignService + SegmentService + TemplateService)
- `a0a0bfc7` — Sub-C API endpoints registered (23 routes)
- `04a695f1` — Sub-D 5 templates seed (uuid5 idempotent)
- `531ed287` — Sub-E arch tests (response_model + pagination + FSM service + SQL filtering)
- `2743ad70` — Sub-F IMPL-LOG + current-state shipped
- `bc65c994` — Fix F-2/F-3/F-4/F-5 (REVIEW findings)
- `aeffa210` — Integration test sin mocks (F-7)
- `fff7f538` — REVIEW.md FAIL→PASS

## Recommended skills S2

- `nicolify-architect` — CONTRACT orchestrator + workers + ChannelRouter impls
- `nicolify-agentic` — LangGraph integration sales_agent OutboundOrchestrator (S3 wiring)
- `nicolify-backend-auditor` — audit cada cutover flag flip
- `manychat-expert` — channel registry context (cuando ChannelRouter wire ManyChat → IG/FB DM)
- `sales-agent-expert` — invariants pool + voz brand mantenidas durante outbound consumption

## Quality summary

- **Tests:** ~309 verde scope campaigns + 711 arch tests verde global (711 pre-fix + 28 nuevos PR-3/4 = ~740)
- **Mypy:** 0 errors scope campaigns post-fixes
- **Ruff:** clean
- **Migration:** idempotente verificado Docker
- **Auditor verdicts:** PR-3 PASS, PR-4 FAIL→PASS post-fixes
- **Cero deuda técnica:** F-1 (PR-3) + F-2/F-3/F-4/F-5/F-7 (PR-4) todos resueltos antes ship

## Próximo sprint

S2-orchestrator inicio post-handoff. Prerequisito: bootstrap `prs/PR-N-{slug}/` folders cuando architect dicte firmas concretas (siguiendo paradigma S0/S1).
