# Sprint S0 — Fundación Robusta y Escalable

## Meta

| Campo | Valor |
|---|---|
| Sprint ID | S0-foundation |
| PI padre | PI-1-campaigns-module |
| Estado | in-progress (PR-0 saneamiento iniciado 2026-04-29) |
| Inicio | 2026-04-29 |
| Cierre estimado | 2026-05-13 (2 semanas) |
| Cierre real | — |
| Owner PM | /pm |

## Objetivo (1 línea)

Construir 5 primitivas cross-cutting (`shared/`) que TODO sprint posterior consume sin refactor: outbox global, idempotency, plan tiers + budget guard, compliance gate, observability spec.

## Pre-handoff

Primer sprint del PI. Input desde:
- Research legacy: `docs/pm/campaigns/` (FOUNDATION.md + 5 carpetas) — migrado a opportunities/ + research/ via PR-0.
- Decisiones macro: `../../decisions.md` D1-D17.
- Estado actual: `current-state/campaigns.md` (módulo inexistente).
- Audit observability: `shared/agent_observability/` ya existe → S0.6 trivial.
- Cost model billing: `research/2026-04-29-billing-tiers-cost-model.md`.

## Plan PRs

| PR | Descripción | Agentes/skills | Esfuerzo | Estado |
|---|---|---|---|---|
| PR-0 | Saneamiento: migrar research legacy → opportunities/ + research synthesis + current-state update | PM solo (no builder) | S | shipped 2026-04-29 |
| PR-1 | S0.1 Outbox pattern global. Refactor `event_bus`. Tabla `domain_event_outbox` + dispatcher. Migra emisores existentes (sales_agent, copilot, brand) | `nicolify-architect` → `nicolify-backend` → `nicolify-backend-auditor` | L | not-started |
| PR-2 | S0.2 IdempotencyStore Redis-backed. Decorator `@idempotent`. Cobertura external API + webhooks | `nicolify-architect` → `nicolify-backend` | S | not-started |
| PR-3 | S0.3 Plan tiers + BudgetGuard + RateLimiter. Tablas `plan_config`/`tenant_subscription`. Streamlit admin `/planes-billing`. Reservación 50% sales_agent enforce | `nicolify-architect` → `nicolify-backend` (+ Streamlit page) | M-L | not-started |
| PR-4 | S0.5 ComplianceService. WABA-24h + opt-in + blacklist + country-block | `nicolify-architect` → `nicolify-backend` | S | not-started |
| PR-5 | S0.6 Campaign observability spec. Reusa `shared/agent_observability/` | `nicolify-backend` (sin architect — patrón ya existe) | XS | not-started |

PR-0 paraleliza con nada (es saneamiento PM). PR-1 bloquea PR-2/3/4/5 (todos consumen outbox). PR-2/3/4/5 paralelizables entre sí post-PR-1.

## Criterio éxito sprint

- [ ] PR-0 shipped: research migrado, opportunities/ creado, current-state actualizado.
- [ ] PR-1 shipped: outbox global con ≥3 emisores migrados (sales_agent + copilot + brand), test exactly-once verde.
- [ ] PR-2 shipped: IdempotencyStore con cobertura ≥1 webhook real (ej: Telegram).
- [ ] PR-3 shipped: 5 planes en `plan_config`, BudgetGuard con test reservación SA invariant verde, Streamlit admin operable.
- [ ] PR-4 shipped: ComplianceService con WABA-24h check funcional + tests fixtures lead pre/post 24h.
- [ ] PR-5 shipped: `mv_daily_llm_cost_per_tenant_v2` incluye `agent_kind='campaign'` ready para futuras llamadas.
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
| (append durante implementación) | | |

## Riesgos

| Riesgo | Mitigación | Owner |
|---|---|---|
| Outbox global toca emisores existentes (sales_agent, copilot) → puede romper observability | Feature flag + rollout progresivo. Test exactly-once por emisor migrado | nicolify-architect |
| Plan tiers requiere migración tenant_billing_config existente (copilot ya usa) | Compat layer: si tenant_subscription IS NULL → fallback al tenant_billing_config legacy hasta migración completa | nicolify-architect |
| Refactor event_bus cambia firma → puede romper tests existentes | Run `/test-all` antes de mergear | nicolify-backend-auditor |
| ComplianceService duplica logic existente en `connections/` | Audit primero, reusa si ya existe | `Explore` agent pre-architect |

## Cierre

Al cerrar S0:
1. Llenar `learnings.md`.
2. Llenar `handoff.md` para S1 (dominio campaigns) Y para S4 (mini CRM Hub forward-compat).
3. Agentes recomendados:
   - **S1:** `nicolify-architect` (CONTRACT.md domain models campaigns) → `nicolify-backend` (TDD).
   - **S4** (paralelo a S3 post-S0): `ux-flow-architect` (UI-SPEC desde UX session previa) + `nicolify-architect` (CONTRACT.md API contacts forward-compat) → `nicolify-backend` + `nicolify-frontend` paralelo → ambos auditors.
4. Si learnings impactan proceso global → append `process-learnings.md`.
