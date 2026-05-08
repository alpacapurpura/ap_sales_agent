# T-10 Impl Log — Smoke + property concurrency + schema regression + R3 SSoT update

> Owner: builder-agentic Opus 4.7 (R23 — production_code=false test infra; Opus needed for T-10 final invariant cement permanente + scenario coverage end-to-end)
> Phase: BUILD_GREEN_T-10
> Started: 2026-05-08 (Step 0 captured: 2026-05-08 UTC)
> Inputs: CONTEXT-BRIEF.md (faithfulness flag _pending_ — proceed under documented justification; T-1..T-9 all closed against same brief = high confidence), 06-tickets.yaml T-10, 03-arch-agentic.md §10+§13, T-1..T-9 result.md.

## R24 brief acceptance gate

CONTEXT-BRIEF.md header shows `Validator pass: _pending_` and `Faithfulness flag: _pending_`. Per rule §11 "Faithfulness gaps + validator findings": pre-validator state, all artifacts read completely. T-1 through T-9 all closed successfully against this same brief. Proceeding under the same documented justification used in T-9 (high confidence — all 9 prior tickets succeeded; brief content has not been mutated since 2026-05-07T17:37Z).

## Step 0 GATE — Skills consulted

| Skill | Why invoked | Decision captured |
|---|---|---|
| `copilot-expert` | T-10 builds smoke tests that exercise observability flow (callback handler → `eval_simulator_llm_call` rows), and the rule-cardinal "Trazas primero" applies (DB query asserts before declaring symptom). Also the §0 anti-duplication cardinal applies. | Followed §0 anti-duplication: no new file in `observability/` `recording/` `cost/` `channels/`. T-10 is pure pytest under `tests/agentic_evals/sales_agent/simulator/`. Trazas-first principle: smoke tests query `eval_simulator_llm_call` + `eval_simulator_trace_event` rows AFTER `run_simulation` to assert observability invariants (H5 6-key metadata, sanitize_payload heredado, tenant isolation). |
| `sales-agent-expert` | T-10 touches sales_agent eval test infrastructure — must respect §3 protected surfaces + voseo policy + voice constraints. Also §0 anti-duplication cardinal applies. | §3 verified — T-10 touches ZERO production files (`closer_studio.py`, `SmartBufferService`, `OutputManager`, `enrollment_*`, webhook adapters, `follow_up_engine`, `PromptVersionModel`, `model_pricing_snapshot`, `tool_call_dedup.py`). Voseo policy: jailbreak persona uses `es-AR` dialect (magic comment escape applied). Voice: agent runtime respects compiled `personality_profiles.system_instruction` (heredado via T-7 agent_bridge — T-10 doesn't override). |
| `tessl__langgraph` | run_simulation invokes a LangGraph; smoke tests exercise it real (not stubbed) for happy scenarios. | NO `from __future__ import annotations` cement applied to ALL new test files (story-wide invariant per T-4..T-9). Patterns referenced: "Basic Agent Graph" + "Conditional Branching" + always-have-exit-conditions (max_turns + termination registry — already enforced by graph topology T-8). Reducer pattern `Annotated[list, operator.add]` for transcript heredado from T-4. |
| `tessl__graceful-degradation` | T-10 monkeypatches LLM router for adversarial sub-case A (empty response) — must align with H7 taxonomy + Rule 2 (every timeout needs fallback). | Rule 2 honored: monkeypatched `MultiRoleLLMRouter.generate_response` returns "" for `agent_kind=sales_agent` turn 1 → agent_bridge maps to `EMPTY_RESPONSE` subtype (H7) → graph terminates AGENT_ERROR cleanly without bubble. Rule 5 honored: customer LLM failure ≠ agent failure (separate node paths). Rule 6: structlog `simulator.agent_empty_response` emitted with simulation_id + turn breadcrumb. |
| `tessl__pytest-api-testing` | New conftest.py + 4 new test files. | Function-scoped fixtures default. AsyncMock for ainvoke patches. `monkeypatch` (not unittest.mock) for module attribute swaps. parametrize for 5-archetype matrix. `@pytest.mark.eval` auto-applied by parent conftest (NOT redeclared). Smoke tests integration-env-aware: skip gracefully if Postgres + LLM keys missing (per parent conftest pattern). |
| `tessl__fastapi` | NOT applicable — T-10 is pure pytest test infra; no FastAPI routes touched. | N/A — declared upfront so audit trail shows skill considered + ruled out. |

## Step 0.5 — Default flip detection

T-10 touches NO `core/config.py` defaults. Reviewing `.claude/rules/anti-default-flip-audit.md` inventory: no flag flips proposed (`USE_OUTBOX_PATTERN_*`, `LITELLM_PROXY_ENABLED`, `USE_DEEPAGENTS_*` untouched). Step 0.5 not applicable.

## Step 0 — Anti-duplication grep evidence

```bash
grep -rn "test_simulator_smoke\|test_concurrency_property\|test_schema_migration_regression" backend/tests/ 2>&1 | grep -v __pycache__
# → 2 docstring matches (test_schema_migrations_registry_complete.py:244 + golden_v1_simulation_result.yaml:3); ZERO actual file collisions.
```

T-9 already mentions `test_schema_migration_regression.py` in docstring as the upcoming T-10 deliverable. Clean — no mirror creation.

## Cross-module audit (NO-NEW-LAYER)

| Layer probed | Result | Decision |
|---|---|---|
| `backend/src/core/` settings/factories | NOT touched (test infra only) | N/A |
| `backend/src/shared/agent_observability/` | NOT touched (T-10 consumes existing observability subclass via T-5 factory through T-7 agent_bridge) | NO-NEW-LAYER respected |
| Existing `tests/agentic_evals/sales_agent/conftest.py` parent | Provides `--run-evals` flag + `pytest.mark.eval` | EXTEND via simulator/conftest.py (re-exports + adds simulator-specific fixtures) |
| `tests/agentic_evals/sales_agent/simulator/fixtures/tenant_seeded.py` | T-3 fixture exists | CONSUME via re-export in simulator/conftest.py |
| `tests/agentic_evals/sales_agent/simulator/fixtures/actor_profiles.py` | T-9 fixtures exist | CONSUME via re-export in simulator/conftest.py |

No new infrastructure layer introduced. T-10 is pure pytest test files under `tests/`.

## Implementation order (TDD per layer)

1. **conftest.py** (foundation — wires all fixtures + run_id + markers).
2. **test_simulator_smoke.py** (9 cases — 5-archetype × happy + 1 negative + 2 edge + 2 adversarial).
3. **test_concurrency_property.py** (H3+H4 N=10 paralelas property-based).
4. **test_schema_migration_regression.py** (H1+H10 frozen golden v1 deserialization + registry exhaustive).
5. **test_termination_registry.py EXTEND** (T-4 base + 3 new tests for register_custom_policy + idempotency cleanup).
6. **Update `.claude/rules/auditor-downstream-regression.md`** (append eval_simulator entry to SSoT table).
7. **Update `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml`** (append eval simulator fields).

## Iteration log

### 2026-05-08T20:00Z — Implementation complete

**Files created:**
- `backend/tests/agentic_evals/sales_agent/simulator/conftest.py` — fixtures wiring (run_id, eval_tenant_seeded re-export, ActorProfile re-exports as pytest fixtures)
- `backend/tests/agentic_evals/sales_agent/simulator/test_simulator_smoke.py` — 9 tests covering 4 spec scenarios (5 archetype parametrize + 1 negative + 2 edge + 2 adversarial)
- `backend/tests/agentic_evals/sales_agent/simulator/test_concurrency_property.py` — 3 property-based tests (N=10 parallel + semaphore cap + cost split)
- `backend/tests/agentic_evals/sales_agent/simulator/test_schema_migration_regression.py` — 10 tests (frozen golden v1 + registry exhaustive + idempotency probes + nested model round-trips)

**Files modified:**
- `backend/tests/agentic_evals/sales_agent/simulator/test_termination_registry.py` — APPENDED 5 tests (cleanup_test_policies fixture, register_custom_policy, idempotent_no_duplicate, cleanup_teardown, default_policies_present_after)
- `.claude/rules/auditor-downstream-regression.md` — APPENDED `modules/sales_agent/observability/eval_simulator/` SSoT entry (R3 update)
- `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` — APPENDED eval simulator fields (simulator_path, dual_llm_pattern, schema_versions, observability_table flags, archetypes_supported, simulator_test_coverage list)

**Quality gates run native WSL:**

| Gate | Result | Detail |
|---|---|---|
| `ruff check` | PASS | 5 files clean after fixes (RUF002 multiplication-sign x4, RUF100 unused noqa x6, FURB157 Decimal verbose, N812 mixed case, ASYNC240 pathlib in async — fixed with `noqa` where pragmatic) |
| `ruff format --check` | PASS | 5 files (2 reformatted by ruff format on first pass) |
| `mypy --strict --ignore-missing-imports` | PASS | 5 files clean (3 fixes: `dict[str, Any] = dict(initial_state.model_dump())` typed coercion x4 occurrences in test_simulator_smoke.py + 2x in test_concurrency_property.py; `import yaml  # type: ignore[import-untyped]`) |
| `pytest tests/agentic_evals/sales_agent/simulator/test_termination_registry.py + test_schema_migration_regression.py + test_concurrency_property.py` | PASS 23/23 | After fix to `test_synthetic_v1_to_v2_migrator_round_trips` (replaced bogus `monkeypatch.setattr(dict, '__getitem__', ...)` with `monkeypatch.setitem(...)` + manual SCHEMA_MIGRATIONS pop teardown) |
| `pytest tests/agentic_evals/sales_agent/simulator/test_simulator_smoke.py` (no --run-evals) | PASS 4 + 7 skipped | 4 no_eval tests pass; 7 eval-marked auto-skip per parent conftest |
| `pytest tests/agentic_evals/sales_agent/simulator/test_simulator_smoke.py --run-evals` | PASS 6 + 5 skipped | 5 archetype parametrize iterations skip on Postgres-unreachable (graceful per parent conftest pattern); 5 no_eval tests + suite_cost_total_cap pass |
| `pytest tests/agentic_evals/sales_agent/simulator/` | PASS 160/160 + 12 DB-required skipped | Full simulator suite — no regression |
| `pytest tests/architecture/ -m "not eval"` | PASS 939/939 | Full architecture fitness — no regression vs T-9 baseline |
| `pytest tests/modules/sales_agent/observability/` (R3 downstream regression) | PASS 33/33 | sales_agent observability — no regression from R3 SSoT update |
| `grep -q 'eval_simulator' .claude/rules/auditor-downstream-regression.md` | PASS | A4 verifier |
| `grep -q 'simulator_path' docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` | PASS | A5 verifier |
| D6 preservation gate (`git status --short -- client_simulator/`) | PASS | Cero changes |

**Issues encountered + fixes:**

1. **N812** lowercase imported as non-lowercase (conftest.py): swapped from `actor_profile_X as _ACTOR_PROFILE_X` to `from .fixtures import actor_profiles as _actor_profiles_module` + access via `_actor_profiles_module.actor_profile_X`.

2. **RUF002** ambiguous multiplication sign in docstrings (test_simulator_smoke.py 4x): replaced `×` with `x` (paridad with stub-mode test_max_turns_cap pattern).

3. **RUF100** unused `# noqa: SLF001` directives (4x — codebase project does not have SLF lint enabled): removed.

4. **FURB157** `Decimal("0")` verbose: replaced with `Decimal(0)`.

5. **ASYNC240** `pathlib.Path.iterdir()` in async function (test_simulator_smoke.py:380): added per-line `# noqa: ASYNC240 — local tmp_path I/O is non-blocking; pytest test scope acceptable`.

6. **mypy `Returning Any from function declared to return dict[str, Any]`** (4x in test_simulator_smoke.py + 2x in test_concurrency_property.py): explicit typed coercion `snapshot: dict[str, Any] = dict(initial_state.model_dump())`.

7. **mypy `Library stubs not installed for "yaml"`**: added `# type: ignore[import-untyped]` (paridad with project pattern — types-PyYAML not in dev deps).

8. **Test failure `dict object attribute __getitem__ is read-only`** (test_synthetic_v1_to_v2_migrator_round_trips_via_apply_migrations): the original implementation tried `monkeypatch.setattr(CURRENT_SCHEMA_VERSIONS, "__getitem__", ...)` which is invalid for built-in dict. Replaced with simpler approach: just `monkeypatch.setitem(CURRENT_SCHEMA_VERSIONS, test_model, 2)` (auto-restore on teardown) + manual `SCHEMA_MIGRATIONS.pop(...)` in `finally` block.

### Native ticket tests breakdown

```
tests/agentic_evals/sales_agent/simulator/test_termination_registry.py:                10 PASS / 0 FAIL
tests/agentic_evals/sales_agent/simulator/test_schema_migration_regression.py:         10 PASS / 0 FAIL
tests/agentic_evals/sales_agent/simulator/test_concurrency_property.py:                 3 PASS / 0 FAIL
tests/agentic_evals/sales_agent/simulator/test_simulator_smoke.py (no --run-evals):     4 PASS / 7 SKIP (eval-gated)
tests/agentic_evals/sales_agent/simulator/test_simulator_smoke.py (--run-evals, no DB): 6 PASS / 5 SKIP (Postgres-skipped)
                                                                  T-10 SUITE TOTAL:   33 PASS  (excluding integration-env-required skip paths)
```

### Anti-mirror grep evidence (Step 0 cement)

```bash
grep -rn "test_simulator_smoke\|test_concurrency_property\|test_schema_migration_regression" backend/tests/ 2>&1 | grep -v __pycache__
# → 2 docstring matches pre-create (in T-9 docs); ZERO actual file collisions.
```

### Integration env caveats per spec/result.md

- Real LLM smoke tests skip when Postgres unreachable (parent conftest pattern + per-test `_get_db_session()` probe).
- D9 cost cap baseline (`agentic_cost_budget_baseline` validator from 04-validators.yaml) tests the DB-side rollup; current run cannot execute that command since Postgres is unreachable in the WSL native environment. The cost cap **logic** is implemented:
  - Per-test individual cap assertion `result.cost_summary.total_cost_usd < COST_CAP_INDIVIDUAL` (line 268 test_simulator_smoke.py).
  - Suite-total cap assertion in `test_suite_cost_total_cap` (line 305).
  - Both will execute when integration env (Postgres + LLM keys) is available.
- Full integration verifier (DB-driven `agentic_cost_budget_baseline` + 5 archetype real LLM e2e) deferred to gate-runner spawn with full integration env (auditor-agentic Step downstream_regression_scope).


