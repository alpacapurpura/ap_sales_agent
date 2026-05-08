# T-3 Run-Evals Smoke Findings (2026-05-08)

Executed by `/dev-team` post-build per Chris approval (~$0.60 cost auth). All 3 env-gated tests FAIL with REAL bugs (not env config issues — unit tests pass because they mock these dependencies).

## Bugs found

### Bug 1 — simulation_id non-deterministic with same seed (D8/D-A-15 violation)

**Test:** `test_generate_golden_candidates.py::TestReproducibilitySmoke::test_same_seed_produces_same_simulation_id`
**Result:** FAIL

```
AssertionError: simulation_id debe ser determinístico con mismo seed
- 50862489-0689-5a83-9795-9085fa00a31c
+ a183b5b5-38a9-563e-a373-9c02bd1fd0fd
```

Seed propagation broken — same `--seed-base 42` + same tenant + same persona_kind + same trial_n produces different UUIDs across runs. Per D13 (`simulation_id_uuid5`) and D-A-15 (deterministic seeding), simulation_id should be uuid5 derived from deterministic inputs.

### Bug 2 — SQLA session injection broken (`SessionUnavailable`)

Captured stderr (both runs):
```
simulator.agent_invalid_state error='Runner failed to inject SQLAlchemy session for simulation' error_class=SessionUnavailable
simulator.simulation_completed error_subtype=invalid_state termination_reason=agent_error total_turns=1
```

Real `run_simulation` invocation fails to inject DB session → agent crashes turn 0 → total cost $0.00 (no LLM fired). Either:
- generate_golden_candidates.py async context missing session lifecycle
- Story B `run_simulation` requires session bridge that T-3 generation script doesn't provide

### Bug 3 — `test_e2e_smoke` uses non-existent `module.__import__`

**Test:** `test_promote_golden.py::TestE2ESmoke::test_generate_and_promote_cycle`
**Result:** FAIL

```
AttributeError: module 'promote_golden' has no attribute '__import__'
```

Line 532 of test_promote_golden.py uses `_promo.__import__("generate_golden_candidates")._main_async(...)`. Should be `importlib.import_module("generate_golden_candidates")` or import at module top.

### Bug 4 — `settings.DATABASE_URL` doesn't exist

**Test:** `test_goldens_cost_bucket_invariant.py::TestGoldensCostBucketInvariant::test_generation_writes_only_to_eval_bucket`
**Result:** ERROR (setup phase)

```
AttributeError: 'Settings' object has no attribute 'DATABASE_URL'
```

Line 52 references `settings.DATABASE_URL` — actual attribute is likely `database_url` (snake_case Pydantic v2) or different name. Setup fails before any DB query, so cost-bucket invariant never verified.

## Recommendation

These are scope of `/auditor` Conv 3 to flag as CHANGES_REQUESTED for T-3 follow-up ticket (T-3.bis hot-fix). Per `.claude/rules/hotfix-repro-mandatory.md` R26, the failing test outputs above ARE the repro evidence — the auditor / next builder can cite them directly.

Real LLM cost incurred this session: **$0.00** (agent crashed before LLM fire on Bug 2).

## Status

Build state: `developed` (preserved — unit tests passed, env-gated tests are CI-nightly opt-in per D14 `run_evals_flag`). Auditor decides whether to ESCALATE these as blockers or CHANGES_REQUESTED with T-3.bis hot-fix follow-up.
