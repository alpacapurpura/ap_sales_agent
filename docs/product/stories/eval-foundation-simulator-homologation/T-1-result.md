# T-1 Result — Migration 125 + eval_simulator observability schema mirror

**Story:** eval-foundation-simulator-homologation
**Ticket:** T-1
**State:** tests-passing
**Owner:** claude-sonnet (builder-backend, R5 schema-mirror exception)

## Deliverables Shipped

| # | Deliverable | Status |
|---|---|---|
| 1 | Migration `backend/alembic/versions/125_add_eval_simulator_observability_tables.py` — 3 tables + 6 indexes | DONE |
| 2 | `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_llm_call.py` | DONE |
| 3 | `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_trace_event.py` | DONE |
| 4 | `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_synthetic_tenants.py` | DONE |
| 5 | `backend/src/modules/sales_agent/observability/eval_simulator/spec.py` | DONE |
| 6 | Bootstrap 1-line edit `backend/src/shared/infrastructure/agent_observability_bootstrap.py` | DONE |
| 7 | `__init__.py` cascading (4 files) | DONE |

**Extra (required):**
- `backend/pyproject.toml` — mypy override `src.modules.sales_agent.observability.eval_simulator.*` (paridad campaigns pattern)

## Migration Note

Arch doc called for `124_add_eval_simulator_observability_tables`. Since `124_drop_tenant_provider_api_keys` already existed, used `125_add_eval_simulator_observability_tables` with `down_revision = "124_drop_tenant_provider_api_keys"`.

## Acceptance Criteria

| # | Description | Result |
|---|---|---|
| A1 | Migration applies idempotent (run 2x no error) | PASS |
| A2 | 3 tables exist post-upgrade | PASS |
| A3 | `get_spec('eval_simulator')` returns spec | PASS |

## Diff Summary

```
backend/alembic/versions/125_add_eval_simulator_observability_tables.py (+148 lines NEW)
backend/src/modules/sales_agent/observability/eval_simulator/__init__.py (+18 lines NEW)
backend/src/modules/sales_agent/observability/eval_simulator/persistence/__init__.py (+10 lines NEW)
backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/__init__.py (+28 lines NEW)
backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_llm_call.py (+91 lines NEW)
backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_trace_event.py (+74 lines NEW)
backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_synthetic_tenants.py (+55 lines NEW)
backend/src/modules/sales_agent/observability/eval_simulator/spec.py (+36 lines NEW)
backend/src/shared/infrastructure/agent_observability_bootstrap.py (+1 line EDIT)
backend/pyproject.toml (+5 lines EDIT - mypy override)
```

## Quality Gates Output

| Gate | Result |
|---|---|
| `ruff check` | 0 errors |
| `ruff format --check` | 0 files to reformat |
| `mypy --strict eval_simulator/` | 0 errors |
| `pytest tests/architecture/` (827 tests, excl. pre-placed agentic gate) | 827/827 PASS |
| `pytest tests/modules/sales_agent/` (673 tests) | 673/673 PASS |

### Pre-existing failure

`tests/architecture/test_schema_migrations_registry_complete.py` — UNTRACKED pre-placed arch gate for T-4..T-9 (AGENTIC). Requires `simulator/_internal/schema_migrations` (builder-agentic deliverable). Not caused by T-1.

## Commit SHA

`9c541ed5`
