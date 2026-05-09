# T-1 Result — GoldenScenarioModel v1 schema + parallel migrations registry

Story: sales-agent-goldens-3-tenants-dataset
Ticket: T-1
Commit SHA: a6c058b2
State: pushed
Date: 2026-05-08

## Deliverables (6 files)

| File | Status |
|---|---|
| `backend/tests/agentic_evals/sales_agent/goldens/__init__.py` | NEW ✅ |
| `backend/tests/agentic_evals/sales_agent/goldens/_schema.py` | NEW ✅ |
| `backend/tests/agentic_evals/sales_agent/goldens/_schema_migrations.py` | NEW ✅ |
| `backend/tests/agentic_evals/sales_agent/test_goldens_schema.py` | NEW ✅ |
| `backend/tests/architecture/test_goldens_schema_completeness.py` | NEW ✅ |
| `backend/tests/architecture/test_goldens_no_mirror_simulator_schema.py` | NEW ✅ |

## Validator output (verbatim)

```
be_lint: ruff check — All checks passed! (0 errors)
be_format: ruff format --check — 6 files already formatted (0 to reformat)
be_mypy_strict: mypy --strict goldens/ — Success: no issues found in 3 source files
scenario_1_goldens_schema_validation:
  tests/agentic_evals/sales_agent/test_goldens_schema.py → 37 passed
arch_ratchet_5_new_gates:
  tests/architecture/test_goldens_schema_completeness.py → 15 passed
  tests/architecture/test_goldens_no_mirror_simulator_schema.py → 7 passed
legacy_simulator_invariants_intact:
  tests/architecture/test_simulator_public_api_surface.py → 7 passed
  tests/architecture/test_simulator_no_mirrors_shared.py → 23 passed
  tests/architecture/test_schema_migrations_registry_complete.py → 17 passed

Total: 106 passed, 1 warning (PydanticDeprecatedSince20 on core/config.py — pre-existing)
```

## Acceptance criteria status

| Criteria | Status |
|---|---|
| A1: GoldenScenarioModel + GoldenTurnModel + GoldenMetadataModel round-trip | ✅ PASS |
| A2: Arch fitness gates green | ✅ PASS |
| A3: Story B simulator invariants intact | ✅ PASS |

## Key design decisions implemented

- **D6 cement**: `schema_version: Literal[1] = 1` — immutable v1 spec
- **D7 cement**: `actor_profile_schema_version: Literal[2] = 2` — frozen at curation time
- **D3 scope**: `GoldenPersonaKind` 3 values only (happy/nurture/unqualified). `adversarial` → Story I
- **D-A-1**: All 3 models: `ConfigDict(extra='forbid', frozen=True)`
- **D-A-2**: `GOLDEN_SCHEMA_MIGRATIONS` is a distinct parallel registry. Zero imports from `simulator/_internal/schema_migrations.py`
- **D-A-13**: No migrations — data-migration pattern (not Alembic)

## Parallel safety note

T-2 builder concurrent session files (`scan_seed_pii.py`, `pre-commit`, `test_pre_commit_hook.py`,
`_pii_patterns.py`, `scan_goldens_pii.py`, `test_pii_patterns_single_source.py`) are untouched per M8.
