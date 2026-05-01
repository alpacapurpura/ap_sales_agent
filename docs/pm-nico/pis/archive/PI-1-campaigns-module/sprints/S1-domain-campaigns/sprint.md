# Sprint S1 — Dominio Campaigns + Repos

## Meta

| Campo | Valor |
|---|---|
| Sprint ID | S1-domain-campaigns |
| PI padre | PI-1-campaigns-module |
| Estado | done |
| Inicio | 2026-04-29 |
| Cierre estimado | +1 semana después de S0 cierre |
| Cierre real | 2026-04-29 (mismo día — Opus 1M autonomous) |
| Owner PM | /pm |

## Objetivo (1 línea)

Construir dominio campaigns completo (entities + repos + services + endpoints + 5 templates globales) sobre primitivas S0 (outbox, idempotency, BudgetGuard, ComplianceService, RateLimiter), sin orquestación todavía — eso es S2.

## Pre-handoff (input desde S0)

- **Decisiones tomadas S0:** link a `../S0-foundation/handoff.md`
- **Surface disponible post-S0:**
  - `shared/domain_events/outbox/` (OutboxService.enqueue + dispatcher)
  - `shared/idempotency/` (`@idempotent` decorator + IdempotencyStore)
  - `shared/billing/` (PlanService, BudgetGuard, OutboundRateLimiter)
  - `shared/compliance/` (ComplianceService policy chain)
  - `shared/agent_observability/` registrado `agent_kind="campaign"` + tablas `campaign_*`
- **Riesgos abiertos S0:**
  - Wiring consumers (copilot/sales_agent/ChannelRouter) pendiente — S1+S2 hace primer wiring real para campaigns
  - 20 emisores legacy en in-memory path — fuera scope S1, sigue pending S2
- **Skills/agentes recomendados:** `nicolify-architect` (CONTRACT campaign domain) → `nicolify-backend` (TDD strict)

## Plan PRs (folders) — DESCOMPONER POST-S0 HANDOFF

> **NO refinar PRs concretos hasta cerrar S0.** Output real S0 puede cambiar firmas API y descubrir gaps. Refinar en bootstrap PI siguiente sesión.

**Plan macro tentativo (1-2 PRs amplios cohesivos, Opus 1M sizing):**

| PR (tentativo) | Scope | Esfuerzo | Estado |
|---|---|---|---|
| PR-3-campaigns-domain-and-repos | Domain entities (Campaign, CampaignStep, CampaignTask, Segment, SegmentFilter, ChannelRouter interface, CampaignType/Status enums, events) + SQLA models + repositories + Alembic migration | L | not-started |
| PR-4-campaigns-application-and-api | CampaignService (CRUD + lifecycle FSM) + SegmentService (resolve + estimate_size) + API endpoints (`/campaigns`, `/segments`, `/templates`) con response_model + 5 templates globales seed (welcome, launch-4day, webinar, cold-reactivation, post-purchase) | L | not-started |

**Cohesión:**
- PR-3 = data plane (domain + storage). Self-contained.
- PR-4 = application + exposure. Consume PR-3.
- PR-3 bloquea PR-4. Si scope crece → split PR-4 en `application` + `api`.

**Detalle PRs:** `prs/PR-N-{slug}/PR.md` se crea en bootstrap S1 cuando S0 cierre y handoff dicte firmas concretas.

## Criterio éxito sprint

- [ ] PR-3 + PR-4 shipped con RESULT.md
- [ ] `/test-backend` 13 gates verde
- [ ] 5 templates globales seed visibles via API GET `/templates` (read-only)
- [ ] Domain consume primitivas S0 (BudgetGuard.check, ComplianceService.check, OutboxService.enqueue) en stub minimal — wiring real S2
- [ ] `current-state/campaigns.md` con capabilities Campaign/Segment/Template lineage S1
- [ ] Cero código orchestrator (es S2)
- [ ] Cero código sales_agent OutboundOrchestrator (es S3)

## Out of scope

| Item | Razón | Sprint destino |
|---|---|---|
| CampaignOrchestrator.launch() | Necesita ChannelRouter + workers | S2 |
| ARQ workers (CampaignExecutionWorker, CampaignSchedulerWorker, SegmentRefreshWorker) | S2 |
| ChannelRouter implementación (Telegram/WhatsApp/Email) | S2 |
| OutboundOrchestrator sales_agent | S3 |
| FE `/campañas/*` UI (futuro post PI-1) | post PI-1 |
| Mini CRM Hub `/sales/contactos` | S4 (paralelo a S3) |

## Decisiones a tomar durante sprint

(append durante implementación)

| Fecha | Decisión | PR |
|---|---|---|
| TBD | Campaign FSM states (`draft`/`scheduled`/`running`/`paused`/`completed`/`canceled`) | PR-3 |
| TBD | SegmentFilter DSL (JSON schema) — minimal vs expressive | PR-3 |
| TBD | Templates como rows DB vs JSON files vs combo | PR-4 |

## Riesgos

| Riesgo | Mitigación | Owner |
|---|---|---|
| Domain entities over-engineered (DDD purity vs pragma) | Sprint TDD por capa. Architect documenta solo entities con use case real S2/S3 | architect |
| SegmentFilter DSL escapa scope | Empezar minimal (campos predefinidos: lifecycle_stage, score_range, source). Expressive DSL = post PI-1 | architect |
| Templates rigid lock-in si arquitectura schema mal | Templates como rows DB editable + JSON template_body. No hardcode templates en código | builder |
| Acoplamiento prematuro a copilot subagent (commercial_director PI-2) | NO crear hooks copilot en S1. Domain agnostic | architect |

## Cierre

1. Llenar `learnings.md`
2. Llenar `handoff.md` para S2 (orchestrator) — surface domain entities + service APIs disponibles
3. Marcar `done`
4. Verificar `RESULT.md` PRs escritos
5. Skills S2: `nicolify-architect` (CONTRACT orchestrator + workers) → `nicolify-agentic` (LangGraph integration sales_agent OutboundOrchestrator) → `nicolify-backend-auditor` + `sales-agent-expert` durante audit
