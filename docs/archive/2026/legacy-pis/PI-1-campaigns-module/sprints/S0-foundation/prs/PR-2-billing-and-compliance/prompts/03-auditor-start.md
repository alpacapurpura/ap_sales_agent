# Prompt — Auditor kickoff (PR-2 billing-and-compliance)

> Copy-paste en sesión Claude Code nueva, o spawn `nicolify-backend-auditor` vía Agent tool.

```
Sos `nicolify-backend-auditor`. Trabajo: review READ-ONLY del PR-2-billing-and-compliance. NO modificás código.

**Lectura obligatoria:**
1. `docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S0-foundation/prs/PR-2-billing-and-compliance/PR.md`
2. `docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S0-foundation/prs/PR-2-billing-and-compliance/CONTRACT.md`
3. `docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S0-foundation/prs/PR-2-billing-and-compliance/IMPL-LOG.md`
4. `git diff main..HEAD`
5. `.claude/rules/backend-ddd.md` + `tenant-isolation.md` + `backend-migrations.md` + `architectural-fitness.md` + `backend-quality.md` + `master-data.md` + `currency-handling.md` + `admin-panel.md`

**Tu output:** `docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S0-foundation/prs/PR-2-billing-and-compliance/REVIEW.md`

**Verdict gate canónico:** correr `/test-backend` (13 gates). FAIL gates 3-7,11-13 → veredicto FAIL.

**Categorías review (12 cat):**

1. **DDD compliance** — billing + compliance siguen Inside-Out. `policies/` no importa de `infrastructure/` directamente
2. **Tenant isolation** — TODA query `plan_config` (global, sin tenant_id) vs `tenant_subscription` (siempre con tenant_id). Verifica explícito en repos. `channel_blacklist` filtra tenant_id
3. **Soft deletes** — `plan_config.is_active` flag (no DELETE). `tenant_subscription` activated_at vs deactivated_at
4. **Code quality** — gates 3/4/5/11/12
5. **SQLAlchemy 2.0** — async, `select().where()`, `Mapped[T]`
6. **Async consistency** — todos services async. PlanService cache safe en async context
7. **Pydantic v2 / PII** — `BudgetDecision` DTO usa `model_config = ConfigDict(...)`. Sin PII en logs (tenant_id sí, email no)
8. **Migration quality** — 110_*.py idempotente raw SQL `IF NOT EXISTS`. Seed con `ON CONFLICT DO NOTHING`. Test clone DB en IMPL-LOG
9. **Security:**
   - BudgetGuard NO tiene bypass (verifica `agent_kind` enum strict)
   - Streamlit `/planes-billing` requiere auth admin (registry-based + role check)
   - `custom_overrides` JSONB validado (no inyección arbitraria — Pydantic schema)
   - ComplianceService NO loguea PII contact identifier
10. **Tests / TDD** — RED commits ANTES GREEN. Test crítico `test_copilot_exhausted_cannot_consume_sa_pool` verde. Property-based test invariant Hypothesis verde
11. **Agentic hygiene** — N/A (sin LangGraph)
12. **Cross-cutting:**
    - **Currency**: `llm_budget_total_usd` usa `Decimal` Python + `NUMERIC` Postgres. NO hardcoded "USD" string en DTO (regla `currency-handling.md`). Documentado en CONTRACT que all plans son USD by design
    - **Master-data**: `cycle_anchor_day` semantics UTC. Timestamps `DateTime(timezone=True)`. Sin `datetime.utcnow()`
    - **Spanish neutro**: Streamlit page strings en español neutro (sin voseo) — verifica labels page
    - **Native-First**: gates corren WSL nativo, no `docker exec`
    - **Admin panel** (regla `admin-panel.md`): Streamlit page registry-based, lógica en `modules/`, wrapper en `pages/`, sin cross-module import

**Domain skill routing obligatorio:**
- `copilot-expert` — verifica BudgetGuard NO rompe cost recording actual + invariantes pricing snapshot
- `sales-agent-expert` — verifica reservación 50% pool semantics matchea expectativa SA + protected surfaces no rotas
- `metrics-expert` — verifica `mv_daily_llm_cost_per_tenant_v2` reuse correcto, no duplicate query patterns
- `backend-expert` — verifica admin panel sigue pattern registry + smoke test

**Findings + verdict mecánico:**

`FAIL` automático:
- `test_copilot_exhausted_cannot_consume_sa_pool` rojo
- Tenant leak en `tenant_subscription` query
- Migration no idempotente
- Hardcoded plan prices fuera migration seed (test arch rojo)
- Allowlist `test_compliance_used_by_channels` creció sin justificación
- Hardcoded "USD" en BudgetGuard return DTO
- `datetime.utcnow()` en cycle logic
- Voseo en Streamlit page strings
- `/test-backend` gates 3-7,11-13 fallan
- Streamlit page sin auth admin
- BudgetGuard no usa MV (re-query directo `*_llm_call` tablas)

`WARN`:
- Soft-fail Redis sin log warning
- Tests sub-deliverable < 80% coverage
- IMPL-LOG sin documentar wiring rollout S2
- ComplianceService policy chain orden mal documentado
- `custom_overrides` JSONB sin Pydantic schema validation

`info`:
- Naming `plan_config` vs `tenant_subscription` consistencia
- Streamlit form validation messages

**Verdict math:**
- FAIL en cat 1/2/8/9/11 → overall FAIL
- Allowlist crece sin justificación → FAIL
- Gates 3-7,11-13 FAIL → FAIL
- ≥2 cat WARN → overall WARN
- Otherwise PASS

**Al terminar:**
1. REVIEW.md con tabla 13 gates + tabla 12 cat + findings file:line + verdict + admin panel smoke status + invariant property-based test status
2. Última línea:
   `<!-- @pm: REVIEW.md ready (PASS|WARN|FAIL). Próximo paso: ejecutar prompts/04-pm-close.md o /pm "PR-2 auditor done". -->`
3. Brief Chris < 200 palabras: veredicto + 3 findings top + invariant test status + admin panel operable.
```
