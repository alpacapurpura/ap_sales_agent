# Prompt — Architect kickoff (PR-2 billing-and-compliance)

> Copy-paste este prompt en sesión Claude Code nueva, o spawn `nicolify-architect` vía Agent tool. PM pre-coció contexto.

> **PRE-REQUISITO:** PR-1 shipped (outbox + idempotency + observability spec). Architect verifica `RESULT.md` PR-1 existe antes empezar.

```
Sos `nicolify-architect`. Trabajo: producir CONTRACT.md para PR-2-billing-and-compliance (PI-1 campaigns S0 foundation).

**Lectura obligatoria (en orden):**
1. `docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S0-foundation/prs/PR-2-billing-and-compliance/PR.md` — problema + soluciones elegidas + scope
2. `docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S0-foundation/prs/PR-1-foundation-event-driven-core/RESULT.md` — qué expuso PR-1 (idempotency disponible, outbox dispatcher operable)
3. `docs/pm-nico/pis/active/PI-1-campaigns-module/PI.md` — Sprint 0 reframe + decisiones D10-D11
4. `docs/pm-nico/research/2026-04-29-billing-tiers-cost-model.md` — **lectura completa**, contiene cost model, tabla schema borrador, BudgetGuard pseudocódigo, anti-patterns
5. `docs/pm-nico/current-state/{copilot,sales_agent,iam,campaigns}.md` — capacidades vivas
6. `.claude/rules/backend-ddd.md` + `tenant-isolation.md` + `backend-migrations.md` + `architectural-fitness.md` + `master-data.md` + `currency-handling.md` + `admin-panel.md`
7. Código vivo (read-only para validar):
   - `backend/src/shared/agent_observability/cost/` (MV `mv_daily_llm_cost_per_tenant_v2`)
   - `backend/src/modules/copilot/observability/` (cost recording actual)
   - Buscar `tenant_billing_config` (legacy) — schema + dónde se consume
   - `backend/src/admin_panel/` (Streamlit registry pattern + ejemplos pages existentes)
   - Buscar `lead_opt_ins` o equivalente (compliance gap audit)
   - Buscar handlers WABA-24h hardcoded actuales (compliance gap audit)
8. Tessl skills: `tessl__fastapi`, `tessl__pytest-api-testing`, `tessl__graceful-degradation`

**Skills a invocar (durante diseño):**
- `copilot-expert` — invariantes cost recording + observability hooks. NO romper pricing snapshot logic
- `sales-agent-expert` — invariantes tier pricing 200k Kimi + DeepSeek alias. Reservación 50% pool semantics
- `metrics-expert` — `mv_daily_llm_cost_per_tenant_v2` schema + refresh frequency. BudgetGuard reuse no duplica
- `backend-expert` — Streamlit registry pattern + admin-panel rules

**Tu output: `docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S0-foundation/prs/PR-2-billing-and-compliance/CONTRACT.md`** siguiendo template.

**Decisiones arquitectónicas a tomar (responder explícito en CONTRACT):**

1. **Schema concreto `plan_config`:**
   - Columnas + types (ver borrador en research/billing-tiers-cost-model.md líneas 56-71)
   - CHECK constraints: `llm_budget_total_usd > 0`, `sales_agent_reserved_pct BETWEEN 0 AND 1`
   - Índices necesarios
   - Seed migration: 5 rows iniciales (free $5 / basic $15 / intermediate $30 / advanced $45 / ultra $95) idempotente con `ON CONFLICT DO NOTHING`

2. **Schema `tenant_subscription`:**
   - 1:1 tenant → plan_id FK
   - `custom_overrides JSONB` para per-tenant overrides
   - `cycle_anchor_day` semantics (día del mes que reinicia ciclo)
   - Compat con `tenant_billing_config` legacy: estrategia de fallback (copilot ya consume legacy)
   - **Decisión clave:** mantener `tenant_billing_config` legacy intacta + `PlanService.get_effective` cae a legacy si tenant_subscription IS NULL. PR-2 NO migra data legacy (S2)

3. **`PlanService.get_effective(tenant_id) -> PlanConfig`:**
   - Resolución: tenant_subscription.plan_id → plan_config row + apply custom_overrides JSONB merge
   - Fallback: si subscription IS NULL → leer tenant_billing_config legacy + traducir a PlanConfig in-memory (no escribir)
   - Cache: 5min TTL por tenant (evitar query DB en cada LLM call)

4. **`BudgetGuard.check(tenant_id, agent_kind, est_cost) -> BudgetDecision`:**
   - Reuse `mv_daily_llm_cost_per_tenant_v2` (existente). Verificar columnas `agent_kind` discriminator
   - Lógica: 2 buckets (sales_agent / others). Copilot exhausto NO consume SA pool
   - Soft warn @ 80% pool (no bloquea, retorna `soft_warn=True`)
   - Hard block @ 100% (`allowed=False`)
   - MV refresh stale → cache decision 5min para no re-query
   - Decisión: si MV >1h stale → graceful degradation, soft cap @ 105% (admite hasta 5% over para no perder ventas)

5. **`OutboundRateLimiter.check(tenant_id) -> bool`:**
   - Redis sliding window: ZADD + ZREMRANGEBYSCORE + ZCARD
   - Key: `rate_limit:outbound:{tenant_id}`
   - Window: 24h (configurable post-MVP)
   - `max_outbound_msg_per_day=NULL` → unlimited (subject to BudgetGuard)
   - Soft-fail Redis: si Redis unavailable → log warning + permitir (regla `tessl__graceful-degradation`)

6. **`ComplianceService.check(contact, channel, campaign) -> CheckResult`:**
   - Policy chain: WABA24hPolicy → OptInPolicy → BlacklistPolicy → CountryBlockPolicy
   - Short-circuit en primer FAIL
   - `CheckResult(allowed: bool, failed_policy: str | None, reason: str | None, evidence: dict)`
   - WABA24h: query last inbound message timestamp por contact+channel < 24h ago → allowed
   - OptIn: depends on existing `lead_opt_ins` schema (architect verifica via Explore)
   - Blacklist: tabla `channel_blacklist` (tenant + channel + identifier)
   - CountryBlock: lista vacía default. Lee `COMPLIANCE_DEFAULT_COUNTRY_BLOCK_LIST` env var

7. **Streamlit `/planes-billing` page:**
   - Path `backend/src/admin_panel/modules/billing.py` + wrapper `pages/planes_billing.py`
   - Registry-based (regla `admin-panel.md`)
   - Vistas:
     - Lista 5 planes (read + edit row inline)
     - Lista tenants con plan_id + spend ciclo actual
     - Override per-tenant (edit `custom_overrides` JSONB textarea)
   - Sin cross-import a otros admin modules

8. **Architecture fitness tests nuevos:**
   - `test_budget_reservation_invariant.py` — property-based (Hypothesis): copilot agent_kind nunca puede gastar de SA pool aunque tenga budget
   - `test_compliance_used_by_channels.py` — allowlist ratchet shrink-only (vacío inicial; future channel sender debe llamar `ComplianceService.check` antes send)
   - `test_no_hardcoded_plan_prices.py` — grep `5\.00|15\.00|30\.00|45\.00|95\.00` fuera migration seed → fail

9. **PR-1 dependency:**
   - `IdempotencyStore` (PR-1) usado por compliance opt-in webhook handler? → architect decide si scope acá o S2

**Reglas duras:**
- NO escribas código de implementación. Solo schemas + interfaces + migration plan + admin page contract + decisiones.
- SQLA 2.0 async + Pydantic v2 + structlog.
- Migrations idempotentes raw SQL `IF NOT EXISTS`.
- response_model obligatorio (no aplica esta PR — sin endpoints API; Streamlit NO tiene response_model).
- Currency-handling.md: `llm_budget_total_usd` usa `Decimal` Python + `NUMERIC` Postgres. **NO** hardcodear "USD" — todos los planes son USD por design (Chris cobra en USD), documentar en CONTRACT.
- Master-data: cycle anchor en UTC. Trial timestamps `DateTime(timezone=True)`.
- Si detectás gap funcional en PR.md → "Open questions for PM".

**Al terminar:**
1. CONTRACT.md completo con: schema 3 tablas + interfaces 5 servicios + migration outline + admin page contract + flag rollout consumers (S2) + open questions
2. Última línea respuesta:
   `<!-- @pm: CONTRACT.md ready. Próximo paso: ejecutar prompts/02-builder-start.md o ejecutar /pm "PR-2 architect done" para review. -->`
3. Brief Chris < 200 palabras: decisiones top + open questions.
```

## Cómo usar

1. PR-1 debe estar shipped antes (verificar `RESULT.md` existe)
2. Spawn architect con este prompt o copy-paste sesión nueva
3. CONTRACT.md → `prompts/02-builder-start.md`
