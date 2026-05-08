# T-1 Implementation Log — Migration 124 + eval_simulator observability schema mirror

**Story:** eval-foundation-simulator-homologation
**Ticket:** T-1
**Assigned to:** claude-sonnet (builder-backend, R5 schema-mirror exception)
**Started:** 2026-05-07
**State:** tests-passing

## R24 Note

CONTEXT-BRIEF.md has `Validator pass: _pending_`. The prompt provided all deliverables explicitly via `<deliverables_literal_from_06_tickets>`, `<files_in_scope_strict>`, and `<acceptance_criteria>` — the underlying ready-package files (03-arch-be.md, 06-tickets.yaml) are the authoritative source of truth. Proceeded based on direct spec package, cited in IMPL-LOG.

## Skills Consulted

- `backend-expert` — invoked Step 0 gate. Loaded `runtime-quality-checklist.md` before commit. Guided: use `Column()` style matching campaigns precedent (paridad exact mirror). Key decision: JSONB `server_default` SQLite-incompatible — use `default=dict` only (migration has the DB-level default in raw SQL). Added mypy override per campaigns pattern (`disable_error_code = ["misc", "type-arg"]`).
- `tessl__fastapi` — invoked for Annotated deps + response_model patterns (N/A: no FastAPI endpoints in T-1). Confirmed: pure schema-mirror + migration, no routes.
- `tessl__pytest-api-testing` — invoked for fixture scoping patterns. Relevant for T-3 (fixture implementation). T-1 is schema-only, no test code written.
- `tessl__graceful-degradation` — invoked for external call timeout patterns (N/A: no external HTTP calls in T-1 schema migration).
- `brand-expert`, `offer-expert`, `metrics-expert` — N/A: T-1 touches sales_agent observability only.

## Step 0 Anti-Duplication Check

```bash
find /home/chris/AISALESHT/backend/src -name "eval_simulator*" 2>/dev/null
# → 0 results — first-time creation, no mirror risk
```

Result: No existing eval_simulator files. PASS — proceed.

## Iteration Log

### Iter 1 — Implementation + Fixes

**Files created:**
- `backend/alembic/versions/125_add_eval_simulator_observability_tables.py` — idempotent raw SQL, 3 tables + 6 indexes
- `backend/src/modules/sales_agent/observability/eval_simulator/__init__.py`
- `backend/src/modules/sales_agent/observability/eval_simulator/persistence/__init__.py`
- `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/__init__.py`
- `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_llm_call.py`
- `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_trace_event.py`
- `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_synthetic_tenants.py`
- `backend/src/modules/sales_agent/observability/eval_simulator/spec.py`

**Files edited:**
- `backend/src/shared/infrastructure/agent_observability_bootstrap.py` — 1-line import append
- `backend/pyproject.toml` — mypy override `src.modules.sales_agent.observability.eval_simulator.*` (disable_error_code ["misc", "type-arg"], paridad campaigns pattern)

**Migration revision naming:** Arch doc called for `124_add_eval_simulator_observability_tables` but `124_drop_tenant_provider_api_keys` already exists. Used `125_add_eval_simulator_observability_tables` with `down_revision = "124_drop_tenant_provider_api_keys"`.

**Bug fixed during implementation:** Initial models used `server_default=text("'{}'::jsonb")` on JSONB columns. This caused SQLite compile error in integration tests (SQLite doesn't support `'{}'::jsonb` DDL syntax). Fixed by removing `server_default=` from ORM models — the DB-level DEFAULT is already handled by migration 125 raw SQL. Pattern follows `message_model.py` precedent (`default=dict` only).

## Acceptance Criteria Verification

| # | Criterion | Result |
|---|---|---|
| A1 | Migration applies idempotent (IF NOT EXISTS) — run 2x no error | PASS: `alembic upgrade 125_...` x2 = second run no-op |
| A2 | 3 new tables exist post-upgrade | PASS: eval_simulator_llm_call, eval_simulator_trace_event, eval_synthetic_tenants via `\dt` |
| A3 | Spec registered: `get_spec('eval_simulator')` returns spec | PASS: Python import test confirmed agent_kind, tables, has_lead_id=False |

## Quality Gates

| Gate | Result |
|---|---|
| `ruff check` src files | PASS: 0 errors |
| `ruff format --check` | PASS: all formatted |
| `mypy --strict` eval_simulator/ | PASS: no errors (after pyproject.toml override) |
| `pytest tests/architecture/` (excl. pre-placed agentic test) | PASS: 827/827 |
| `pytest tests/modules/sales_agent/` | PASS: 673/673 |

### Pre-existing failing test (not caused by T-1)

`tests/architecture/test_schema_migrations_registry_complete.py` — UNTRACKED file pre-placed by architect as part of the story's ready package. Requires `tests/agentic_evals/sales_agent/simulator/_internal/schema_migrations` (T-4..T-9 AGENTIC deliverables). This failure is EXPECTED and was present before T-1 changes.

## Out-of-Scope Notes

Per T-1 spec:
- Migration test (T-2) — NOT written (T-2 scope)
- Arch fitness gate `test_eval_simulator_observability_invariants.py` (T-2) — NOT written
- Fixture `eval_tenant_seeded` (T-3) — NOT written
- Simulator internals (T-4..T-10 AGENTIC) — NOT touched
