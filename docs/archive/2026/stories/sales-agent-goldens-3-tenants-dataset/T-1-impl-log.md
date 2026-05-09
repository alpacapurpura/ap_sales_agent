# T-1 Implementation Log — GoldenScenarioModel v1 schema + parallel migrations registry

Story: sales-agent-goldens-3-tenants-dataset
Ticket: T-1
Owner: builder-backend-sonnet (R23 production_code:false)
Date: 2026-05-08
State: pushed

## Skills Consulted

- `backend-expert` — Invoked per Step 0 GATE. Loaded `references/runtime-quality-checklist.md` before commit. Key decision: Pydantic v2 `ConfigDict(extra='forbid', frozen=True)` on all 3 model classes; `pytest.raises((ValidationError, TypeError))` for frozen tests (not bare Exception per B017 lint rule).
- `tessl__fastapi` — Invoked per mandatory skill list. Decision: no FastAPI routes in T-1 (schema-only ticket), but Annotated + response_model patterns noted for downstream T-3.
- `tessl__pytest-api-testing` — Invoked per mandatory skill list. Decision: factory fixture pattern `_make_valid_golden(**overrides)` for parametrized edge case tests; no async fixtures needed (pure Pydantic validation tests).
- `tessl__graceful-degradation` — N/A for T-1 (no external calls). Noted for T-3 generation script.
- `brand-expert` — N/A (no brand module touch).
- `offer-expert` — N/A (no offer module touch).
- `metrics-expert` — N/A (no analytics module touch).

## Step 0 — Anti-duplication gate

```bash
grep -rn "class GoldenScenarioModel" /home/chris/AISALESHT/backend/ → ZERO matches
grep -rn "GOLDEN_SCHEMA_MIGRATIONS" /home/chris/AISALESHT/backend/ → ZERO matches
```

Both greps returned zero — NEW justified (no golden YAML schema precedent in codebase).

## Step 0.5 — Default flip detection

N/A — T-1 touches no `core/config.py` defaults. Zero flag flips.

## Step 0.5b — Context-brief R24 gate

CONTEXT-BRIEF.md: Validator pass: PARTIAL (faithfulness flag: partial, 1 LOW discrepancy: "8 regex categories" vs 9 actual — irrelevant to T-1). Proceeding per R24 rules (partial flag + §11 entries cited below).

§11 gaps noted: Faithfulness discrepancy is in PII scanner regex count (T-2 territory). Zero impact on T-1 schema deliverables.

## TDD iterations

### Iteration 1 — RED phase

Wrote test files first:
- `backend/tests/agentic_evals/sales_agent/test_goldens_schema.py` (unit tests, schema-only)
- `backend/tests/architecture/test_goldens_schema_completeness.py` (arch fitness gate)
- `backend/tests/architecture/test_goldens_no_mirror_simulator_schema.py` (parallel registry gate)

RED confirmed: `ModuleNotFoundError: No module named 'tests.agentic_evals.sales_agent.goldens._schema'`

### Iteration 2 — GREEN phase

Implemented deliverables:
1. `backend/tests/agentic_evals/sales_agent/goldens/__init__.py` — empty placeholder
2. `backend/tests/agentic_evals/sales_agent/goldens/_schema.py` — GoldenScenarioModel v1
3. `backend/tests/agentic_evals/sales_agent/goldens/_schema_migrations.py` — parallel registry

Result: 59/59 tests pass.

### Iteration 3 — Lint/format fixes

Fixed lint errors:
- ERA001: Removed commented-out example code from `_schema_migrations.py` (docstring explains pattern instead)
- B017: Changed `pytest.raises(Exception)` to `pytest.raises((ValidationError, TypeError))` for frozen mutation tests
- SIM102: Combined nested `if` in arch gate AST import scanner
- RUF100: Removed unused `# noqa: F401` directives from arch completeness test
- mypy: Removed stale `# type: ignore[index]` comment on Final dict write (unused ignore error)

Result: ruff check clean, ruff format clean, mypy strict clean on goldens/ files.

### Iteration 4 — Story B regression verification

Ran Story B tests:
- `test_simulator_public_api_surface.py` → 7/7 PASS
- `test_simulator_no_mirrors_shared.py` → 23/23 PASS
- `test_schema_migrations_registry_complete.py` → 17/17 PASS

Zero regressions introduced.

## Final test count

Total tests passing: 106/106
- test_goldens_schema.py: 37 tests
- test_goldens_schema_completeness.py: 15 tests  
- test_goldens_no_mirror_simulator_schema.py: 7 tests
- Story B regression: 47 tests

## Quality gates status

| Gate | Status |
|---|---|
| ruff check | PASS (0 errors) |
| ruff format --check | PASS (0 files to reformat) |
| mypy strict on goldens/ | PASS (0 errors) |
| scenario_1_goldens_schema_validation | PASS (37 unit tests) |
| arch_ratchet_5_new_gates | PASS (2 new gates, 22 assertions) |
| legacy_simulator_invariants_intact | PASS (47 Story B tests) |

## Files created (T-1 scope only)

| File | Type | LOC |
|---|---|---|
| `backend/tests/agentic_evals/sales_agent/goldens/__init__.py` | NEW | 6 |
| `backend/tests/agentic_evals/sales_agent/goldens/_schema.py` | NEW | 107 |
| `backend/tests/agentic_evals/sales_agent/goldens/_schema_migrations.py` | NEW | 119 |
| `backend/tests/architecture/test_goldens_schema_completeness.py` | NEW | 174 |
| `backend/tests/architecture/test_goldens_no_mirror_simulator_schema.py` | NEW | 196 |
| `backend/tests/agentic_evals/sales_agent/test_goldens_schema.py` | NEW | 342 |

Total new LOC: ~944

## Key design decisions (D6, D7, D-A-1, D-A-2)

- **D6** — `schema_version: Literal[1] = 1` cement. NEVER mutate v1 fields.
- **D7** — `actor_profile_schema_version: Literal[2] = 2` frozen at curation time (immune Story C v3+ bumps).
- **D3** — `GoldenPersonaKind` is 3 values only (`happy/nurture/unqualified`). `adversarial` excluded (Story I scope).
- **D-A-1** — All 3 model classes: `ConfigDict(extra='forbid', frozen=True)`.
- **D-A-2** — `GOLDEN_SCHEMA_MIGRATIONS` is a distinct parallel registry. Does NOT import from `simulator/_internal/schema_migrations.py`. Different namespace, different lifecycle.
- **D-A-13** — No arch gate for migrations (goldens is data-migration pattern, not Alembic).

## Cross-module reads

- Read `backend/tests/agentic_evals/sales_agent/simulator/_internal/schema_migrations.py` (read-only, pattern reference for parallel registry)
- Read `backend/tests/agentic_evals/sales_agent/simulator/actor_profile.py` (read-only, Pydantic ConfigDict pattern reference per 06-tickets.yaml inputs)
