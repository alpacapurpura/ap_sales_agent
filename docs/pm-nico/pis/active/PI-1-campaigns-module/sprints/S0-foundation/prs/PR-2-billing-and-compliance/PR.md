# PR-2-billing-and-compliance

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-2-billing-and-compliance |
| Sprint padre | S0-foundation |
| PI padre | PI-1-campaigns-module |
| Estado | ready (bloqueado por PR-1) |
| Tipo | infra |
| Esfuerzo | L |
| Owner PM | /pm |
| Claimed by session | — |

## Problema (user-facing)

1. Hoy Nicolify no tiene tope de gasto LLM por tenant. Cualquier tenant puede correr extracciones masivas y disparar costo a infinito (R4 PI-1 sin mitigar).
2. Copilot exhausto puede consumir budget que tenía que cubrir sales_agent → "las ventas se paran" (anti-objetivo Chris).
3. Sin compliance gate central, cada channel re-implementa WABA-24h + opt-in tracking + blacklist + country-block ad-hoc → drift garantizado, lawsuit risk.
4. Sin rate limiter outbound, tenant lanza campaña a 10K contactos sin límite → spam, ban canal.

JTBD interno: "Como builder/founder de Nicolify, cuando un tenant ejecuta agentes (copilot, sales_agent, campaigns), quiero garantía de que (a) no rompe el cap de su plan, (b) sus ventas no paran si copilot se exhauste, (c) no manda mensajes ilegales o spam, sin que cada feature reinvente la rueda."

## Outcome esperado

Cuatro primitivas en `backend/src/shared/billing/` + `shared/compliance/` que TODO consumer downstream usa via DI:

1. **Plan tiers + tenant_subscription** (5 planes editables sin migration): Free $5 / Básico $15 / Intermedio $30 / Avanzado $45 / Ultra $95. Reservación 50% sales_agent invariant.
2. **BudgetGuard** — gate proactivo pre-LLM-call. Copilot exhausto **NO** consume SA pool (test arch enforcement).
3. **OutboundRateLimiter** — Redis sliding window. Cap `max_outbound_msg_per_day` por plan.
4. **ComplianceService** — gate central por (contact, channel, campaign): WABA-24h + opt-in + blacklist + country-block.

Plus:
- **Streamlit admin `/planes-billing`** — Chris edita `plan_config` rows + ve spend ciclo per tenant + override custom_overrides.

**Métrica:**
- Test arch verde: copilot agotado (otros pool $0 restante) NO puede consumir SA pool aunque tenga $20 disponibles
- 5 planes en `plan_config` poblados via migration seed
- Cambiar Ultra $95 → $120 = 1 UPDATE row, 0 migrations
- ComplianceService.check sub-100ms p95
- Streamlit admin operable (edit row + save + verify reflejado en BudgetGuard.check)

## Walking skeleton (mínimo viable cohesivo)

PR amplio cohesivo. 4 sub-deliverables comparten dominio "policy enforcement pre-execute":

```
shared/
├── billing/
│   ├── domain/
│   │   ├── plan.py                      ← PlanConfig VO
│   │   ├── subscription.py              ← TenantSubscription
│   │   └── budget_decision.py           ← BudgetDecision (allowed/soft_warn/reason)
│   ├── infrastructure/
│   │   ├── plan_config_model.py         ← tabla plan_config
│   │   ├── tenant_subscription_model.py ← tabla tenant_subscription
│   │   ├── plan_repository.py
│   │   └── subscription_repository.py
│   └── application/
│       ├── budget_guard.py              ← BudgetGuard.check(tenant_id, agent_kind, est_cost)
│       ├── plan_service.py              ← effective plan resolver (plan_config + custom_overrides merged)
│       └── rate_limiter.py              ← OutboundRateLimiter sliding window Redis
├── compliance/
│   ├── domain/
│   │   ├── check_result.py              ← CheckResult(allowed, reason, evidence)
│   │   └── policies/                    ← WABA24hPolicy, OptInPolicy, BlacklistPolicy, CountryBlockPolicy
│   ├── infrastructure/
│   │   ├── opt_in_repository.py         ← consulta tabla opt_ins existente o nueva
│   │   └── blacklist_repository.py
│   └── application/
│       └── compliance_service.py        ← ComplianceService.check(contact, channel, campaign)

backend/src/admin_panel/modules/billing.py  ← Streamlit page (registry-based, regla admin-panel.md)

backend/migrations/versions/
└── 110_add_billing_and_compliance.py
    ├── CREATE TABLE plan_config (idempotente, seed 5 rows)
    ├── CREATE TABLE tenant_subscription (1:1 tenant)
    ├── CREATE TABLE channel_blacklist (tenant + channel + identifier + reason)
    └── (seed: poblar tenant_subscription para tenants existentes con plan default 'free')
```

**Compat layer:** `tenant_billing_config` legacy (copilot ya usa) → si `tenant_subscription IS NULL` → fallback al legacy hasta migración full S2.

## Soluciones consideradas

**Plan storage:**

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A — Tabla `plan_config` editable + Streamlit admin** | Cambiar quota = 1 UPDATE. Override per-tenant via `custom_overrides`. Sin migration por cambio precio | UI extra (Streamlit). Validation runtime (CHECK constraints) | **ELEGIDA** |
| B — Enum hardcoded en código + constantes | Type-safe en código | Cambiar precio = code change + deploy. No override per-tenant | descartada por friction op |
| C — Helm/k8s ConfigMap | DevOps friendly | Chris no devops. Streamlit es la UI ya conocida | descartada |

**BudgetGuard reservación:**

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A — 2 buckets separados (sales_agent / others)** | Invariante explícito en código. Test arch verifica copilot NO consume SA pool | Más código que single bucket | **ELEGIDA** (Chris invariant crítico) |
| B — Single bucket + soft alert al 50% | Más simple | Rompe invariante "ventas no paran". Defendiblee solo si trust runtime | descartada |
| C — Hard separation con cuentas billing distintas | Más estricto | Sobre-ingeniería single tenant | descartada |

**ComplianceService scope:**

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A — Service central, channels consumen via DI** | DRY. Auditable. Future voice_agent reusa | Acoplamiento → channels dependen shared/compliance | **ELEGIDA** |
| B — Cada channel implementa su check | Encapsulado por channel | Drift garantizado. WABA-24h reimplementado 3 veces | descartada |
| C — Compliance solo en orchestrator (no per-channel) | Simple | Channel directo (ej: Telegram raw send) bypassea check | descartada |

**Rate limiter backend:**

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A — Redis sliding window (sorted set ZADD/ZREMRANGEBYSCORE)** | Atómico, accurate, reusa Redis ya stack | Memory cost (1 entry per msg en window) | **ELEGIDA** |
| B — Token bucket Redis | Más smooth | Menos accurate burst | descartada (default antispam = sliding) |
| C — Postgres count query | Persiste reboot | Latencia + contención | descartada |

## Validación técnica preliminar (Technical Sanity Check)

> PM tiene cost model en `research/2026-04-29-billing-tiers-cost-model.md`. Architect debe leerlo + validar con `Explore` audit. CONTRACT formaliza schemas.

**Estado actual billing:**
- `tenant_billing_config` (legacy) usado por copilot → cuota copilot rudimentaria. Sin reservación SA invariant
- `mv_daily_llm_cost_per_tenant_v2` (MV agregada) ya existe en `shared/agent_observability/cost/` — reusable para BudgetGuard sin queries adicionales
- `copilot_llm_call` + `sales_agent_llm_call` tablas observability (existing)

**Compliance hoy:**
- WABA-24h: hardcoded en algún channel handler (architect verifica vía `Explore`)
- Opt-in tracking: tabla `lead_opt_ins`? (architect verifica)
- Blacklist: no existe centralizada (probable verifica)
- Country-block: no existe

**Modules afectados:** `shared/billing/`, `shared/compliance/` (nuevos), `admin_panel/modules/billing.py` (Streamlit) + integraciones livianas en copilot orchestrator + sales_agent supervisor (PR-2 NO migra estos consumers — solo expone API; migrar es S2).

**Tiempo estimado:** L (3 ejecuciones agente).

## Decisiones diferidas (explícitas)

| Item | Razón | Cuándo |
|---|---|---|
| Wire copilot orchestrator a `BudgetGuard.check` antes LLM call | PR-2 expone API, NO refactoriza consumers (mantiene blast radius bajo) | S2 |
| Wire sales_agent specialists a BudgetGuard | idem | S2 |
| Wire ChannelRouter a ComplianceService | ChannelRouter no existe hasta S2 | S2 |
| Migrar `tenant_billing_config` legacy a `tenant_subscription` para tenants existentes | Compat layer cubre transición. Migración full data S2 | S2 |
| Stripe/MercadoPago integration billing real | Out of scope PI-1. Manual override mientras tanto | post PI-1 |
| Country-block lista paises | Default permisivo (lista vacía). Chris define cuando legal lo pida | TBD |
| Trial mechanism (`trial_ends_at`) | Tabla soporta, lógica auto-expire en S2 worker dedicado | S2 |
| WABA-24h policy auto-reset cuando lead responde | Política architect decide implementación: trigger DB vs check on-demand | architect |

## Out of scope

- Billing real (Stripe/MercadoPago) — manual override
- Wiring consumers (copilot, sales_agent, channels) — solo API exposure
- Trial expiration worker
- Daily quota reset workers
- Audit log dedicado (S2)
- Circuit breaker (S2)

## Copilot-first checklist

- [x] **¿Operable conversacional desde copilot?** Default Sí, **N/A funcional**: PR-2 es infra. Copilot consume vía services downstream
- [x] **¿Qué tools nuevos requiere?** Ninguno PR-2. En S2: `inspect_my_quota`, `flag_compliance_issue`
- [x] **¿Cards/UI nueva?** Streamlit admin `/planes-billing` (NO copilot UI — es admin panel para Chris)
- [x] **Si NO copilot → razón documentada:** infra layer + admin panel para founder/superuser. Copilot consume downstream

## Agentes / skills recomendados

(Ref: `process/agent-routing-matrix.md` — fila "Pure backend infra")

| Fase | Agente/skill | Prompt pre-coce | Entregable esperado |
|---|---|---|---|
| Pre-design | `nicolify-architect` | `prompts/01-architect-start.md` | `CONTRACT.md` con schemas + interfaces + migration + admin page contract |
| UX | — | — | N/A (Streamlit ya tiene patron registry) |
| Implementation | `nicolify-backend` | `prompts/02-builder-start.md` | code + tests + migration + Streamlit page + IMPL-LOG |
| Audit | `nicolify-backend-auditor` | `prompts/03-auditor-start.md` | REVIEW.md (13 gates `/test-backend`) |
| Cierre | `/pm` | `prompts/04-pm-close.md` | `RESULT.md` + current-state updates |

**Skills módulo durante audit:** `copilot-expert` (cost model + observability hooks) + `sales-agent-expert` (reservación invariant) + `metrics-expert` (MV `mv_daily_llm_cost_per_tenant_v2` reuse). `admin-panel.md` regla automática (Streamlit registry).

## Surface impactada

| Tipo | Path / nombre | Cambio |
|---|---|---|
| Tabla DB | `plan_config` | nueva (5 rows seed) |
| Tabla DB | `tenant_subscription` | nueva (1:1 tenant) |
| Tabla DB | `channel_blacklist` | nueva |
| Module | `backend/src/shared/billing/` | nuevo (domain + infra + application) |
| Module | `backend/src/shared/compliance/` | nuevo (domain + infra + application) |
| Module | `backend/src/admin_panel/modules/billing.py` | nuevo (Streamlit page registry-based) |
| Module | `backend/src/admin_panel/pages/planes_billing.py` | nuevo (PageSpec wrapper) |
| Migration | `backend/migrations/versions/110_*.py` | idempotente raw SQL |
| Tests | `tests/shared/billing/`, `tests/shared/compliance/`, `tests/architecture/test_budget_reservation_invariant.py`, `tests/architecture/test_compliance_used_by_channels.py`, `tests/admin_panel/test_billing_page_smoke.py` | nuevos |
| Env var | `BILLING_DEFAULT_PLAN_ID` | nuevo (default `free`) |
| Env var | `COMPLIANCE_DEFAULT_COUNTRY_BLOCK_LIST` | nuevo (default empty) |
| current-state/ | `current-state/iam.md` | append capability "Plan tiers + tenant_subscription" |
| current-state/ | `current-state/copilot.md` | append "BudgetGuard API exposed (wiring S2)" |
| current-state/ | `current-state/sales_agent.md` | append "BudgetGuard reservation 50% invariant exposed (wiring S2)" |
| current-state/ | `current-state/campaigns.md` | append "ComplianceService API + RateLimiter exposed (wiring S2)" |

## Tests requeridos (TDD)

**Plan + Subscription:**
- `tests/shared/billing/test_plan_config.py` — VO invariants
- `tests/shared/billing/test_plan_repository.py` — CRUD + tenant_id N/A (plan_config es global)
- `tests/shared/billing/test_subscription_repository.py` — get_by_tenant + custom_overrides merge
- `tests/shared/billing/test_plan_service.py` — effective plan resolution (plan_config + overrides)

**BudgetGuard (crítico):**
- `tests/shared/billing/test_budget_guard.py`:
  - `test_sales_agent_call_within_pool_allowed`
  - `test_sales_agent_call_exhausts_sa_pool_blocked`
  - `test_copilot_call_within_others_pool_allowed`
  - `test_copilot_call_exhausts_others_pool_blocked`
  - **`test_copilot_exhausted_cannot_consume_sa_pool`** ← CRÍTICO invariant
  - `test_soft_warn_at_80pct`
  - `test_custom_override_per_tenant_respected`

**OutboundRateLimiter:**
- `tests/shared/billing/test_rate_limiter.py`:
  - sliding window correct (msg en t=0 expira en t=24h+1)
  - max_outbound_msg_per_day=NULL → unlimited
  - concurrent inserts atómicos

**ComplianceService:**
- `tests/shared/compliance/test_waba_24h_policy.py`
- `tests/shared/compliance/test_opt_in_policy.py`
- `tests/shared/compliance/test_blacklist_policy.py`
- `tests/shared/compliance/test_country_block_policy.py`
- `tests/shared/compliance/test_compliance_service.py` — orchestration of policies

**Architecture:**
- `tests/architecture/test_budget_reservation_invariant.py` — verifica BudgetGuard.check con `agent_kind != "sales_agent"` NUNCA puede acceder a SA pool (introspect logic + property-based test)
- `tests/architecture/test_compliance_used_by_channels.py` — todo channel sender (futuro Telegram/WhatsApp) llama `ComplianceService.check` antes (allowlist ratchet shrink-only)
- `tests/architecture/test_no_hardcoded_plan_prices.py` — busca `5.00`, `15.00`, etc en código fuera de migration seed → fail

**Admin panel smoke:**
- `tests/admin_panel/test_billing_page_smoke.py` — Streamlit page loads sin error (mock contract test)

**Migration:**
- Test idempotency clone DB (regla `backend-migrations.md`)

## Aceptación

- [ ] `/test-backend` 13 gates verde
- [ ] Test crítico `test_copilot_exhausted_cannot_consume_sa_pool` verde
- [ ] Migration 110 idempotente clone DB OK
- [ ] Streamlit `/planes-billing` operable (load page + edit row + save → reflejado en BudgetGuard.check)
- [ ] 5 planes seed visibles en page
- [ ] `IMPL-LOG.md` completo
- [ ] `REVIEW.md` veredicto PASS
- [ ] `RESULT.md` escrito por `/pm`
- [ ] 4 `current-state/{m}.md` actualizados
- [ ] Decisiones registradas en `decisions.md` PI-1

## Riesgos

| Riesgo | Mitigación | Owner |
|---|---|---|
| Compat con `tenant_billing_config` legacy (copilot consume) | Service `PlanService.get_effective` cae a legacy si `tenant_subscription IS NULL`. Documentar deprecation timeline | architect |
| `mv_daily_llm_cost_per_tenant_v2` desfasado (refresh hourly) | BudgetGuard usa cycle_spend del MV + cache 5min. Si MV stale → soft cap (admite hasta 105%). Nunca pierde plata real (Kimi $0.001) | architect |
| Reservación 50% bloquea trabajo crítico copilot cuando hay budget SA disponible | Aceptado por Chris ("ventas no paran" > "copilot full feature") | — |
| Streamlit admin permite editar plan_config sin validation → quota negativa | CHECK constraints en tabla + validation Streamlit form | builder |
| ComplianceService duplica logic existente | `Explore` agent pre-architect verifica + reusa lo existente | architect |
| Migration seed planes podría romper tenants ya con `tenant_billing_config` | Migration NO toca legacy. tenant_subscription INSERT solo para tenants nuevos. Tenants existentes via backfill manual o S2 worker | builder |
| Country-block sin lista define → policy inactiva | Aceptado. Chris activa cuando legal pida | — |
| Test arch `test_budget_reservation_invariant` introspection frágil | Property-based test (Hypothesis) genera N tenants con N spend distributions, verifica invariante runtime | builder |
