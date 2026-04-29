# Sprint S0 — Fundación Robusta y Escalable

## Meta

| Campo | Valor |
|---|---|
| Sprint ID | S0-foundation |
| PI padre | PI-1-campaigns-module |
| Estado | in-progress (PR-0 shipped 2026-04-29; plan reescrito a Opus 1M sizing) |
| Inicio | 2026-04-29 |
| Cierre estimado | 2026-05-13 (2 semanas) |
| Cierre real | — |
| Owner PM | /pm |

## Objetivo (1 línea)

Construir 5 primitivas cross-cutting (`shared/`) que TODO sprint posterior consume sin refactor: outbox global, idempotency, plan tiers + budget guard, compliance gate, observability spec — agrupadas en **2 PRs amplios cohesivos** (Opus 4.7[1M] sizing).

## Pre-handoff

Primer sprint del PI. Input desde:
- Research legacy: `docs/pm/campaigns/` (FOUNDATION.md + 5 carpetas) — migrado en PR-0 (shipped).
- Decisiones macro: `../../decisions.md` D1-D17.
- Estado actual: `current-state/campaigns.md` (módulo inexistente, primer PR sembrando).
- Audit observability: `shared/agent_observability/` ya existe → S0.6 trivial.
- Cost model billing: `research/2026-04-29-billing-tiers-cost-model.md`.
- Refactor sesión 2026-04-29 noche: PR-folder pattern + Opus 1M sprint sizing → 5 PRs chicos consolidados a 2 PRs amplios.

## Plan PRs (folders)

> **Sprint sizing Opus 4.7[1M]:** 2 PRs amplios cohesivos. Cada PR ≈ 3 ejecuciones (architect + builder + auditor) = 6 ejecuciones totales para S0.

| PR | Folder | Descripción | Agentes/skills | Esfuerzo | Estado |
|---|---|---|---|---|---|
| PR-0 | `prs/PR-0-research-migration/` | Saneamiento research legacy → opportunities/ + research synthesis + current-state update | PM solo | S | shipped 2026-04-29 |
| PR-1 | `prs/PR-1-foundation-event-driven-core/` | **Event-driven primitives:** outbox global (refactor `event_bus`, tabla `domain_event_outbox`, dispatcher) + IdempotencyStore Redis-backed + observability spec (registrar `agent_kind="campaign"` en `shared/agent_observability/`). Migrar 3 emisores existentes (sales_agent + copilot + brand) | `nicolify-architect` → `nicolify-backend` → `nicolify-backend-auditor` | L | not-started |
| PR-2 | `prs/PR-2-billing-and-compliance/` | **Billing + compliance gate:** plan_config + tenant_subscription + BudgetGuard (con reservación 50% sales_agent invariant) + OutboundRateLimiter Redis sliding window + Streamlit admin `/planes-billing` + ComplianceService (WABA-24h + opt-in + blacklist + country-block) | `nicolify-architect` → `nicolify-backend` → `nicolify-backend-auditor` | L | not-started |

PR-1 bloquea PR-2 (BudgetGuard usa outbox para event emission; ComplianceService depende de idempotency para webhook delivery).

Detalle de cada PR vive en `prs/PR-{n}-{slug}/PR.md` (creado al arrancar PR vía `cp -r process/pr-folder-template/`). Prompts pre-cocidos en `prompts/`.

## Por qué 2 PRs amplios y no 5 chicos

Plan original (pre-2026-04-29 noche): 5 PRs (PR-1 outbox, PR-2 idempotency, PR-3 plan-tiers, PR-4 compliance, PR-5 observability) = 15+ ejecuciones agente.

Plan ajustado Opus 4.7[1M]: 2 PRs amplios cohesivos = 6 ejecuciones.

**Cohesión por PR:**
- **PR-1 (event-driven core):** outbox + idempotency + observability comparten dominio (todo es event-driven infra). Builder en una ejecución implementa los 3 con TDD por sub-deliverable. Migración de 3 emisores existentes (sales_agent/copilot/brand) hace sentido en una sola sesión con todo el contexto cargado.
- **PR-2 (billing-compliance):** plan tiers + budget guard + rate limiter + compliance gate comparten dominio (todo es "policy enforcement" antes ejecución cara). BudgetGuard.check + ComplianceService.check son llamados en mismo punto del código (Orchestrator pre-execute hook) — diseñarlos juntos = menos drift.

**Cuándo no consolidar:** si hay multi-dominio (ej: PR mezcla brand + analytics + scheduling) o multi-blast-radius (ej: refactor afecta 5+ módulos críticos). Aplica criterio cohesión, no contexto.

## Criterio éxito sprint

- [x] PR-0 shipped: research migrado, opportunities/ creado, current-state actualizado, RESULT.md cerrado.
- [ ] PR-1 shipped: outbox global con ≥3 emisores migrados (sales_agent + copilot + brand), test exactly-once verde, IdempotencyStore con cobertura ≥1 webhook real (Telegram), observability spec registrado. RESULT.md + current-state update.
- [ ] PR-2 shipped: 5 planes en `plan_config`, BudgetGuard con test reservación SA invariant verde, OutboundRateLimiter test sliding window, ComplianceService con WABA-24h check funcional + Streamlit admin operable. RESULT.md + current-state update.
- [ ] Cero código de dominio campaigns escrito.
- [ ] Arch test: BudgetGuard reservación verde.

## Out of scope S0 (movido a S2)

| Item | Razón | Sprint destino |
|---|---|---|
| Circuit breaker + DLQ | Sin external API calls reales aún = sobre-ingeniería | S2 |
| Audit log dedicado | Sin mutaciones a auditar aún | S2 |
| Arch tests dedicados | Ya regla estándar `architectural-fitness.md` | regla CI |

## Decisiones a tomar durante sprint

| Fecha | Decisión | PR |
|---|---|---|
| 2026-04-29 noche | Plan 5 PRs chicos → 2 PRs amplios cohesivos (Opus 1M sizing) | sprint plan |
| (append durante implementación) | | |

## Riesgos

| Riesgo | Mitigación | Owner |
|---|---|---|
| PR-1 toca emisores existentes (sales_agent, copilot) → puede romper observability | Feature flag + rollout progresivo. Test exactly-once por emisor migrado | nicolify-architect |
| PR-2 plan tiers requiere migración tenant_billing_config existente (copilot ya usa) | Compat layer: si tenant_subscription IS NULL → fallback al tenant_billing_config legacy hasta migración completa | nicolify-architect |
| PR-1 refactor event_bus cambia firma → puede romper tests existentes | Run `/test-all` antes de mergear PR-1 | nicolify-backend-auditor |
| ComplianceService duplica logic existente en `connections/` | Audit primero, reusa si ya existe | `Explore` agent pre-architect |
| PR amplio = blast radius grande. Bug en outbox afecta sales_agent + copilot + brand simultáneo | TDD por sub-deliverable. Auditor con foco DDD/tenant. Rollback plan: feature flag por emisor migrado | nicolify-backend-auditor |

## Cierre

Al cerrar S0:
1. Llenar `learnings.md`.
2. Llenar `handoff.md` para S1 (dominio campaigns) Y para S4 (mini CRM Hub forward-compat).
3. Verificar `prs/PR-0/RESULT.md` + `prs/PR-1/RESULT.md` + `prs/PR-2/RESULT.md` escritos.
4. Verificar `current-state/campaigns.md` actualizado con capabilities lineage de S0.
5. Agentes recomendados:
   - **S1:** `nicolify-architect` (CONTRACT.md domain models campaigns) → `nicolify-backend` (TDD).
   - **S4** (paralelo a S3 post-S0): `ux-flow-architect` + `nicolify-architect` → `nicolify-backend` + `nicolify-frontend` paralelo → ambos auditors.
6. Si learnings impactan proceso global → append `process-learnings.md`.
