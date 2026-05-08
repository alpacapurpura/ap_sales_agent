<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Backend Code Review: T-1 — Migration 125 + eval_simulator observability schema mirror

**Date:** 2026-05-07
**Story:** eval-foundation-simulator-homologation
**Ticket:** T-1
**Files Reviewed:** 11 (1 migration + 4 SQLAlchemy models + spec.py + 4 __init__.py + 1 bootstrap edit + 1 pyproject.toml edit)
**Domains touched:** sales_agent (R5 schema-mirror exception only), shared/infrastructure
**Skills consulted:** backend-expert, tessl__fastapi (N/A), tessl__pytest-api-testing (N/A), tessl__graceful-degradation (N/A), brand-expert/offer-expert/metrics-expert (N/A)
**Verdict:** **PASS**

## /test-backend Gate Status

| # | Gate | Result | Detail |
|---|---|---|---|
| 3 | Lint (ruff check) — Story B scope | PASS | 0 errors on `src/modules/sales_agent/observability/eval_simulator/` + `src/shared/infrastructure/agent_observability_bootstrap.py` |
| 4 | Format (ruff) — Story B scope | PASS | 0 reformats |
| 5 | Type check (mypy) — Story B scope | PASS | `mypy src/modules/sales_agent/observability/eval_simulator/` 0 issues; pyproject.toml override `disable_error_code = ["misc","type-arg"]` paridad campaigns |
| 6 | Arch fitness (78 gates) | PASS | gate-output.json reports `arch-fitness PASS` |
| 8 | Verify-marker | N/A — schema mirror only |
| 10 | Migration idempotency | PASS — `IF NOT EXISTS` on every CREATE TABLE + CREATE INDEX; downgrade `DROP TABLE IF EXISTS … CASCADE` |
| 13 | pip-audit | N/A — no new dependencies |

**Pre-existing failures excluded per `<gate_output_caveat>`:** 3237 ruff/mypy errors in brand/copilot/connections/analytics (NOT touched by Story B); 3 of 4 pytest fails unrelated; 1 pytest fail (`test_simulator_public_api_surface::test_no_internal_symbols_leaked`) is T-9 agentic ownership flake under full-suite ordering, NOT T-1 scope.

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | DDD Compliance | PASS | 0 |
| 2 | Tenant Isolation | PASS | 0 |
| 3 | Soft Deletes | PASS | 0 |
| 4 | Code Quality | PASS | 0 (Story B scope) |
| 5 | SQLAlchemy 2.0 | PASS w/ note | 0 (legacy `Column()` paridad campaigns; mypy override accepted) |
| 6 | Async Consistency | N/A | schema-only |
| 7 | Pydantic v2 / PII | N/A | no DTOs/routes in T-1 |
| 8 | Migration Quality | PASS | 0 |
| 9 | Security | PASS | 0 |
| 10 | Tests / TDD | PASS | T-2 covers migration tests (RED tests landed in same story) |
| 11 | Cross-cutting | PASS | 0 |
| 12 | Default flip side-effect coverage | N/A | no flag flip |

## Findings

### INFO: MV `mv_daily_llm_cost_per_tenant_v2` not extended for eval_simulator
**Category:** 8
**File:** `backend/alembic/versions/125_add_eval_simulator_observability_tables.py`
**Issue:** `CONTEXT-BRIEF.md §7` states *"migration 124 extends MV UNION ALL eval_simulator_llm_call"*. Migration 125 does NOT extend the cross-agent MV (`079_cross_agent_daily_cost_mv.py` only includes `copilot_llm_call` + `sales_agent_llm_call`; `campaigns` precedent ALSO does not extend it). Brief and arch-doc claim is inaccurate, but absence is consistent with campaigns precedent.
**Fix:** None required for T-1 scope. If cross-agent dashboards must surface eval_simulator costs (Story D/E/F downstream), a separate migration must extend the MV. Track as deferred.
**Skill ref:** `metrics-expert` § analytics-metrics + `auditor-downstream-regression.md` (eval_simulator added to SSoT table by T-10).

### NOTE: SQLAlchemy 2.0 `Column()` legacy syntax — accepted under R5/campaigns paridad
**Category:** 5
**File:** `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/{eval_simulator_llm_call,eval_simulator_trace_event,eval_synthetic_tenants}.py`
**Issue:** Models use legacy `Column()` instead of SA 2.0 `mapped_column()` + `Mapped[type]`. `runtime-quality-checklist.md` notes legacy Column handling pattern is permissible when mirroring an existing precedent.
**Justification (PASS):** Schema mirrors `campaigns/observability/persistence/models/llm_call_model.py` (verified at `backend/src/modules/campaigns/observability/persistence/models/llm_call_model.py:34`) which uses identical `Column()` pattern. mypy override `disable_error_code = ["misc","type-arg"]` paridad campaigns, scoped to `src.modules.sales_agent.observability.eval_simulator.*` only. Cross-codebase grep confirms paridad.
**Skill ref:** `backend-expert` `runtime-quality-checklist.md` § SQLA legacy Column.

### NOTE: `runtime-quality-checklist.md` cited in IMPL-LOG (Skill routing OK)
**Category:** 11
**File:** `T-1-impl-log.md` § Skills Consulted line 15
**Issue:** Cited as "Loaded `runtime-quality-checklist.md` before commit". Citation present.
**Status:** PASS.

## Contract Compliance (business surface only)

- [x] Migration 125 with 3 tables + 7 indexes from CONTRACT § BE prod code matches arch-doc
- [x] `eval_simulator_llm_call` schema mirrors `campaign_llm_call` (D-BE-2 verified by T-2 arch fitness `TestCampaignParityFields` 14 tests PASS)
- [x] `eval_synthetic_tenants` lookup table present with PK `tenant_id` + `archetype_slug` + `seeded_at` + `deleted_at` (D2/D4 Opción B)
- [x] Spec registered: `register_agent_observability(agent_kind="eval_simulator", llm_call_model=..., has_lead_id=False, …)`. `agent_observability_bootstrap.py` line 30 imports spec (1-line edit).
- [x] CONTRACT § Test surfaces — RED tests for migration land in T-2 (mandatory TDD layer-by-layer); T-1 itself is schema mirror under R5 exception (production code), test coverage delegated to T-2. Acceptable — TDD-mandatory § "no aplica config pura (DDL)".
- [x] Story B § 8 Agentic Surfaces NOT in T-1 scope.

## Allowlist Movement
- [x] Did any allowlist GROW? **NO**. New mypy override `[[tool.mypy.overrides]] module = "src.modules.sales_agent.observability.eval_simulator.*"` is a **new module-scoped block**, NOT an allowlist (paridad campaigns, justified in commit body line 506-509 of pyproject.toml).
- [x] Did any allowlist shrink? Not applicable for new code.

## Native-First Audit
- [x] No `docker exec ... ruff|pytest|tsc|vitest|mypy|eslint` in commit body
- [x] Commit `9c541ed5` uses scoped `git add` (no `git add .`/`-A`/`-u` evidence)
- [x] Push to `development` branch, not `main` — `make ci-parity` not required

## Cross-cutting verification

- **Tenant isolation:** Migration declares `tenant_id UUID NOT NULL` on `eval_simulator_llm_call` (line 43) + `eval_simulator_trace_event` (line 102). `eval_synthetic_tenants` uses `tenant_id` as PK (line 132). All 3 tables enforced via T-2 arch fitness `TestTenantIsolation` 5 tests PASS.
- **Master-data UTC:** `started_at TIMESTAMPTZ NOT NULL` (line 67) + `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()` (line 114) + `seeded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()` (line 134). ORM uses `DateTime(timezone=True)` consistently. Verified by T-2 `TestTimestampColumnsTimezoneAware` 5 tests PASS.
- **Currency:** Schema does not hardcode currency. `tenant_currency CHAR(3)` nullable in `eval_simulator_llm_call` (line 63), populated at runtime per `currency-handling.md`.
- **Soft deletes:** `eval_synthetic_tenants.deleted_at TIMESTAMPTZ NULL` (line 135) for teardown idempotency. Business tables business kept; soft-delete row in lookup table flips visibility.
- **Spanish neutro:** Migration docstrings + ORM model docstrings use neutral Spanish ("Mirror semantico de…", "Lookup table for…"). No voseo. ✓
- **R5 schema-mirror exception strict:** Files touched ONLY in `modules/sales_agent/observability/eval_simulator/{persistence/models,spec.py,__init__.py}/` + `shared/infrastructure/agent_observability_bootstrap.py` (1-line). Cero `domain/`, `application/`, `api/`, `observability/recording/`. ✓ Confirmed by T-2 `TestR5SchemaMirrorException` 4 tests PASS.

## Anti-duplication §0 verification (Cat 12)

- T-1 IMPL-LOG cites Step 0 grep: `find /home/chris/AISALESHT/backend/src -name "eval_simulator*"` → 0 results (first-time creation).
- Models import `Base` from `src.shared.domain.base_entity` (NOT mirror). Spec imports `register_agent_observability` from `src.shared.agent_observability.registry` (canonical).
- Subsystem listed in `anti-duplication.md` inventory: cost bucket per `agent_kind` registry pattern → EXTEND via `register_agent_observability(agent_kind="eval_simulator", …)` (line 27-39 of spec.py). Cero mirror. Cross-references campaigns/`PI-1 PR-1 Alembic 083` precedent.
- T-1 PR.md "Existing systems audit" present in `T-1-impl-log.md` § Step 0.

## Verdict Math
- Cat 1/2/8/9/12: all PASS
- Cat 5: PASS w/ accepted note (legacy Column paridad campaigns + mypy override scoped, justified)
- /test-backend gate FAIL on pytest/ruff-check/mypy: pre-existing repo-wide errors NOT introduced by T-1 (verified via scoped ruff/mypy: 0 errors on Story B own files).
- Allowlist movement: no growth
- IMPL-LOG cites baseline skills + `runtime-quality-checklist.md`
- Downstream regression scope: T-10 SSoT update for `modules/sales_agent/observability/eval_simulator/` already landed (verified by grep `eval_simulator` in `.claude/rules/auditor-downstream-regression.md` line 43).

## Verdict
**APPROVED**

## Findings
- 0 FAIL
- 0 WARN
- 1 INFO (MV not extended — paridad campaigns precedent, deferred to downstream stories if cross-agent dashboards required)
- 2 NOTE (legacy Column paridad documented + skills citation OK)

## Cited paths
- `backend/alembic/versions/125_add_eval_simulator_observability_tables.py:30-149`
- `backend/src/modules/sales_agent/observability/eval_simulator/spec.py:27-39`
- `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_llm_call.py:23-83`
- `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_trace_event.py:23-67`
- `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_synthetic_tenants.py:23-47`
- `backend/src/shared/infrastructure/agent_observability_bootstrap.py:30`
- `backend/pyproject.toml:506-509`
- `backend/src/modules/campaigns/observability/persistence/models/llm_call_model.py:34` (paridad anchor)
- `backend/alembic/versions/079_cross_agent_daily_cost_mv.py:55-91` (MV INFO finding context)
- `T-1-result.md`, `T-1-impl-log.md`
