# Prompt — Builder kickoff (PR-2 billing-and-compliance)

> Copy-paste en sesión Claude Code nueva, o spawn `nicolify-backend` vía Agent tool.

```
Sos `nicolify-backend`. Trabajo: implementar PR-2-billing-and-compliance siguiendo CONTRACT.md.

**Lectura obligatoria (en orden):**
1. `docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S0-foundation/prs/PR-2-billing-and-compliance/PR.md`
2. `docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S0-foundation/prs/PR-2-billing-and-compliance/CONTRACT.md` (SSoT)
3. `docs/pm-nico/research/2026-04-29-billing-tiers-cost-model.md` (cost model + ejemplos)
4. `docs/pm-nico/current-state/{copilot,sales_agent,iam,campaigns}.md`
5. `.claude/rules/backend-ddd.md` + `tenant-isolation.md` + `tdd-mandatory.md` + `backend-migrations.md` + `architectural-fitness.md` + `master-data.md` + `currency-handling.md` + `admin-panel.md`
6. `CLAUDE.md` (root)

**Skills:**
- `copilot-expert` — antes tocar cost recording / wiring future
- `sales-agent-expert` — invariantes pool sales_agent
- `metrics-expert` — MV `mv_daily_llm_cost_per_tenant_v2` reuse correcto
- `backend-expert` — Streamlit registry pattern (regla `admin-panel.md`)
- `tessl__fastapi` + `tessl__pytest-api-testing` + `tessl__graceful-degradation`

**Workflow TDD strict:**

**Sub-deliverable 1: Plan + Subscription (DDD Inside-Out)**
1. Domain VO: `tests/shared/billing/test_plan_config.py` → `shared/billing/domain/plan.py` + `subscription.py` + `budget_decision.py`
2. Infra:
   - `tests/shared/billing/test_plan_repository.py` → `infrastructure/plan_config_model.py` + `plan_repository.py`
   - `tests/shared/billing/test_subscription_repository.py` → `tenant_subscription_model.py` + `subscription_repository.py`
   - Migration `110_*.py` raw SQL idempotente con seed 5 planes (`ON CONFLICT DO NOTHING`)
3. Application:
   - `tests/shared/billing/test_plan_service.py` (effective resolution + custom_overrides merge + legacy fallback) → `application/plan_service.py`

**Sub-deliverable 2: BudgetGuard (CRÍTICO)**
1. Tests primero (orden RED por test):
   - `test_sales_agent_call_within_pool_allowed`
   - `test_copilot_call_within_others_pool_allowed`
   - `test_sales_agent_exhausts_sa_pool_blocked`
   - `test_copilot_exhausts_others_pool_blocked`
   - **`test_copilot_exhausted_cannot_consume_sa_pool`** ← INVARIANT TOP
   - `test_soft_warn_at_80pct`
   - `test_custom_override_per_tenant_respected`
   - `test_mv_stale_graceful_soft_cap_105pct`
2. GREEN: `shared/billing/application/budget_guard.py`
3. Integración con MV: query `mv_daily_llm_cost_per_tenant_v2` por (tenant_id, agent_kind, cycle_start)
4. Cache 5min en memoria (`functools.lru_cache` con TTL via `cachetools`)

**Sub-deliverable 3: OutboundRateLimiter**
1. RED: `tests/shared/billing/test_rate_limiter.py` (sliding window + soft-fail Redis)
2. GREEN: `shared/billing/application/rate_limiter.py` (Redis sorted set ZADD/ZREMRANGEBYSCORE/ZCARD)
3. Soft-fail si Redis unavailable → log warning + return True

**Sub-deliverable 4: ComplianceService**
1. Domain: `tests/shared/compliance/test_check_result.py` → `domain/check_result.py`
2. Per-policy:
   - `test_waba_24h_policy.py` → `domain/policies/waba_24h.py`
   - `test_opt_in_policy.py` → `policies/opt_in.py` (consume `lead_opt_ins` schema o crear si no existe — verificar CONTRACT)
   - `test_blacklist_policy.py` → `policies/blacklist.py` + `infrastructure/blacklist_repository.py` + tabla `channel_blacklist`
   - `test_country_block_policy.py` → `policies/country_block.py`
3. Service: `test_compliance_service.py` (orchestration chain) → `application/compliance_service.py`
4. Short-circuit primer FAIL

**Sub-deliverable 5: Streamlit admin page**
1. `tests/admin_panel/test_billing_page_smoke.py` (Streamlit page loads sin error)
2. `backend/src/admin_panel/modules/billing.py` con `render_billing_admin()`
3. `backend/src/admin_panel/pages/planes_billing.py` wrapper (PageSpec + render_billing_admin call)
4. Registrar en navigation registry (regla `admin-panel.md`)

**Sub-deliverable 6: Architecture fitness tests**
1. `tests/architecture/test_budget_reservation_invariant.py` (Hypothesis property-based)
2. `tests/architecture/test_compliance_used_by_channels.py` (allowlist shrink-only, vacío inicial)
3. `tests/architecture/test_no_hardcoded_plan_prices.py` (regex grep)

**Quality gates NATIVE WSL:**
- `cd backend && .venv/bin/ruff check . --fix && .venv/bin/ruff format .`
- `cd backend && .venv/bin/mypy src/shared/billing src/shared/compliance src/admin_panel/modules/billing.py`
- `cd backend && .venv/bin/pytest tests/shared/billing tests/shared/compliance tests/admin_panel -v`
- `cd backend && .venv/bin/pytest tests/architecture -v`
- `cd backend && .venv/bin/pytest tests/{copilot,sales_agent} -v` (regression — wiring NO se hace en PR-2 pero verificar imports no rompen)
- Migration test: clone DB siguiendo `.claude/rules/backend-migrations.md`
- Streamlit smoke: `cd backend && PYTHONPATH=src .venv/bin/python -c "from admin_panel.modules import billing; billing.render_billing_admin"` (import success)
- Final: `/test-backend` 13 gates

**Bloqueado:** STOP + IMPL-LOG sección "Bloqueadores" + marker `@pm`. NO inventes solución.

**Outputs:**
- Code + tests + migration + Streamlit page
- IMPL-LOG.md siguiendo template
- Commits conventional:
  - `feat(shared/billing): plan_config + tenant_subscription + BudgetGuard`
  - `feat(shared/billing): OutboundRateLimiter Redis sliding window`
  - `feat(shared/compliance): policy chain (WABA24h + OptIn + Blacklist + CountryBlock)`
  - `feat(admin_panel): planes-billing Streamlit page`
  - `test(architecture): budget reservation invariant + compliance allowlist + no hardcoded prices`
  - PROHIBIDO `git add .|-A|-u`. Stage por nombre. `git pull origin development` antes cada commit (M5).

**Al terminar:**
1. IMPL-LOG.md completo
2. Update `current-state/{iam,copilot,sales_agent,campaigns}.md` con capabilities API exposed (wiring marked S2)
3. Última línea:
   `<!-- @pm: implementación done. Próximo paso: ejecutar prompts/03-auditor-start.md o ejecutar /pm "PR-2 builder done". -->`
4. Brief Chris < 250 palabras: sub-deliverables shipped + tests verdes + commit hashes + wiring pendiente S2.
```

## Notas

- BE-only PR (admin_panel Streamlit es BE Python).
- Wiring consumers (copilot orchestrator + sales_agent supervisor + ChannelRouter) explicitly out of scope. PR-2 expone API + tests; cutover S2.
