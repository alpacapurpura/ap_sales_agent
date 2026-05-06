# Sprint S2 — Orchestrator + Workers

## Meta

| Campo | Valor |
|---|---|
| Sprint ID | S2-orchestrator |
| PI padre | PI-1-campaigns-module |
| Estado | done |
| Inicio | 2026-04-30 |
| Cierre estimado | +1 semana después de S1 cierre |
| Cierre real | 2026-04-30 (mismo día — Opus 4.7[1M] sprint compresion) |
| Owner PM | /pm |

## Objetivo (1 línea)

Construir CampaignOrchestrator + 3 workers ARQ + ChannelRouter v1 (Telegram-only) + circuit breaker + audit log + wiring real consumers (copilot/sales_agent) a primitivas S0 — backend completamente funcional, falta solo OutboundOrchestrator sales_agent (S3) para end-to-end.

## Pre-handoff (input desde S1)

- **Decisiones tomadas S1:** link a `../S1-domain-campaigns/handoff.md`
- **Surface disponible post-S1:**
  - Domain campaigns: Campaign, CampaignStep, CampaignTask, Segment, SegmentFilter, ChannelRouter interface, enums, events
  - Repos + services CRUD (CampaignService, SegmentService)
  - API endpoints `/campaigns`, `/segments`, `/templates`
  - 5 templates globales seed
- **Surface S0 (consume aquí real):**
  - OutboxService.enqueue (transactional task creation)
  - `@idempotent` decorator (CampaignTask creation deduplicada)
  - BudgetGuard.check (gate pre-LLM call sales_agent)
  - ComplianceService.check (gate pre-send per channel)
  - OutboundRateLimiter.check (cap por plan)
- **Riesgos abiertos:**
  - Wiring copilot/sales_agent a BudgetGuard pendiente — S2 hace cutover por flag
  - 20 emisores legacy → cutover progressivo S2

## Plan PRs (folders) — DESCOMPONER POST-S1 HANDOFF

| PR (tentativo) | Scope | Esfuerzo | Estado |
|---|---|---|---|
| PR-5-orchestrator-and-workers | CampaignOrchestrator.launch() + 4 ARQ workers (Execution / Scheduler / SegmentRefresh / AuditRetention) + ChannelRouter v1 (Telegram) + circuit breaker custom asyncio Redis-backed + audit log `campaign_audit` retention 90d | L | shipped (8 commits + Sub-G fix iter-2 PASS) |
| PR-6-consumers-cutover | Wrappers BudgetGuardingChatModel/Service + 3 flags USE_OUTBOX_PATTERN_* default ON + wiring single point sales_agent + copilot (brand BudgetGuard wiring DR-7 deferred) + 2 arch tests ratchet | M | shipped (6 commits + Sub-G fix iter-2 PASS) |

**Cohesión PR-5:** workers + orchestrator + router comparten dominio "execution pipeline".
**Cohesión PR-6:** wiring real cross-module — separado para blast radius bajo (rollback simple si bug en cutover).

## Criterio éxito sprint

- [ ] PR-5 + PR-6 shipped con RESULT.md
- [ ] `/test-backend` 13 gates verde
- [ ] CampaignOrchestrator.launch() funcional end-to-end stub (sin OutboundOrchestrator sales_agent — S3)
- [ ] 3 ARQ workers ejecutan sin error (smoke test)
- [ ] ChannelRouter Telegram select_channel funcional (test integration)
- [ ] Flag rollout: USE_OUTBOX_PATTERN_{SALES_AGENT,COPILOT,BRAND} = `true` en dev (verificar tests verdes con flag ON)
- [ ] BudgetGuard.check llamada en cada copilot/sales_agent LLM call (audit verifica callsites)
- [ ] ComplianceService.check llamada en ChannelRouter pre-send (test arch shrink-only)
- [ ] `current-state/{campaigns,sales_agent,copilot,connections}.md` con lineage cutover

## Out of scope

| Item | Razón | Sprint destino |
|---|---|---|
| OutboundOrchestrator sales_agent + AgentState campaign_id | S3 implementa primer end-to-end visible Telegram | S3 |
| FE `/sales/contactos` mini CRM Hub | paralelo a S3 | S4 |
| WhatsApp/Email channel routing | PI-2 | PI-2 |
| Webinar/Event campaign types | PI-3 | PI-3 |

## Decisiones a tomar durante sprint

| Fecha | Decisión | PR |
|---|---|---|
| TBD | Circuit breaker library (resilience4j-py / py-breaker / custom) | PR-5 |
| TBD | Audit log retention (90d default? mismo que copilot_trace?) | PR-5 |
| TBD | ARQ worker concurrency limits per worker | PR-5 |
| TBD | Cutover order: sales_agent → copilot → brand vs paralelo | PR-6 |

## Riesgos

| Riesgo | Mitigación | Owner |
|---|---|---|
| Cutover flag flip rompe sales_agent en prod | Rollout staging primero. Test ON+OFF en CI. Rollback = flag flip OFF | builder |
| ARQ worker contention con copilot workers existentes | Worker pool dedicado para campaigns. Verificar en `pyproject.toml` ARQ config | architect |
| Circuit breaker config mal calibrado → falsos positivos | Default tolerante (5 fail / 60s open). Tunable via env | architect |
| ChannelRouter v1 Telegram-only crea acoplamiento | Interface clean. WhatsApp/Email PI-2 = nuevo implementación + register | architect |
| Audit log inflación tabla | TTL retention worker (90d) en S2 mismo o S3 | builder |

## Cierre

1. Llenar `learnings.md`
2. Llenar `handoff.md` para S3 (mvp-telegram) — surface orchestrator + router + cutover status
3. Marcar `done`
4. Verificar `RESULT.md` PRs
5. Skills S3: `sales-agent-expert` (OutboundOrchestrator + AgentState extension) + `nicolify-agentic` (LangGraph supervisor routing) + `nicolify-frontend` (Inbox tag UI) + `chrome-devtools-verify` (E2E browser) + auditors
