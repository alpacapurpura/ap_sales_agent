# T-9 — Implementation Log

**Ticket**: T-9 — Integration `run_simulation` grader_callback hook (`asyncio.create_task`) + 4 scenario tests (happy/edge/cache/adversarial) + calibration MD seed
**Owner**: builder-agentic-opus-4.7
**State**: in-progress → tests-passing
**Date**: 2026-05-09

## Skills Consulted

| Skill | Why invoked | Decision cited |
|---|---|---|
| `backend-expert` | runtime-quality-checklist + DDD inside-out + tenant isolation | runtime-quality-checklist.md scanned for FastAPI Annotated/JSONResponse 501 stubs/datetime/SQLA legacy patterns — N/A Story E (no FastAPI routes; SQLA 2.0 already used) |
| `tessl__pytest-api-testing` | factory fixtures + httpx.AsyncClient guidance + parametrize edge cases | conftest.py with `mock_judge_factory` factory (function-scope), `parametrize` Scenarios 1-4 hostile content variants, autouse cleanup pattern N/A (no DB at unit layer) |
| `tessl__graceful-degradation` | Rule 2 fallback per dependency — fire-and-forget callback | grader_callback wraps invocation in try/except + structlog warn; never propagates to sim loop (preserves Story B determinism cement) |
| `tessl__fastapi` | Pydantic v2 frozen=True + extra="forbid" patterns | `RubricGradeRequest` already cements both — `make_grader_callback` returns Callable matching contract |
| `sales-agent-expert` | §3 personality_profile.system_instruction READ-ONLY + voice creep guard | judge prompts consume Slot 3 verbatim; integration adapter NEVER mutates voice; calibration MD frontmatter cites SSoT §3 |
| `copilot-expert` | observability writes best-effort try/except + structlog warning | Same pattern in `make_grader_callback` — callback failure = log warn, sim continues |

## Iteration Log

### Iter 1 — RED: scaffold conftest + 4 scenario tests + integration tests + calibration MD seeds (failing)

**Files added/modified:**

- NEW `backend/tests/agentic_evals/sales_agent/grader/integration.py` — `make_grader_callback` factory
- EDIT `backend/tests/agentic_evals/sales_agent/simulator/_internal/runner.py` — additive `grader_callback: Callable | None = None` param + per-turn `asyncio.create_task` fire-and-forget
- NEW `backend/tests/agentic_evals/sales_agent/grader/conftest.py` — `mock_judge_factory` + `grader_session` fixtures
- NEW `backend/tests/agentic_evals/sales_agent/grader/test_run_simulation_grader_hook.py` — A5 hook unit tests (5 tests)
- NEW `backend/tests/agentic_evals/sales_agent/grader/scenarios/__init__.py`
- NEW `backend/tests/agentic_evals/sales_agent/grader/scenarios/test_scenario_1_happy_multi_judge.py` — Scenario 1 happy path
- NEW `backend/tests/agentic_evals/sales_agent/grader/scenarios/test_scenario_2_edge_round_2_debate.py` — Scenario 2 variance > 0.15 → R2
- NEW `backend/tests/agentic_evals/sales_agent/grader/scenarios/test_scenario_3_cache_idempotency.py` — Scenario 3 idempotent re-run cache hit
- NEW `backend/tests/agentic_evals/sales_agent/grader/scenarios/test_scenario_4_adversarial_prompt_injection.py` — Scenario 4 prompt-injection sandbox
- NEW `backend/tests/agentic_evals/sales_agent/grader/test_judge_no_system_leak.py` — leak assertion contract reuse
- NEW `backend/tests/agentic_evals/sales_agent/grader/test_unconverged_fallback.py` — DQ8 unconverged semantics
- NEW `backend/tests/agentic_evals/sales_agent/grader/test_maj_eval_happy.py` — Scenario 1 entry alias (validator path)
- NEW `backend/tests/agentic_evals/sales_agent/grader/test_maj_eval_debate.py` — Scenarios 2 + r2_partial entry aliases (validator paths)
- NEW `backend/tests/agentic_evals/sales_agent/grader/test_maj_eval_adversarial.py` — Scenario 4 entry aliases (validator paths)
- NEW `backend/tests/agentic_evals/sales_agent/grader/calibration/__init__.py` (placeholder)
- NEW `backend/tests/agentic_evals/sales_agent/grader/calibration/voice_fidelity_calibration.md` — Chris seed labels skeleton + auto-baseline section + re-calibration triggers
- NEW `backend/tests/agentic_evals/sales_agent/grader/calibration/qualification_accuracy_calibration.md` — same structure
- NEW `backend/tests/agentic_evals/sales_agent/grader/calibration/no_overpromise_calibration.md` — same structure
- NEW `backend/tests/agentic_evals/sales_agent/grader/calibration/no_hallucination_calibration.md` — same structure

**Existing arch fitness gates already cover** (no new gates needed in T-9):
- `test_grader_pii_sanitize_pre_judge.py` (T-5)
- `test_grader_sandbox_markers_enforced.py` (T-7)
- `test_grader_round_2_no_self_reasoning.py` (T-7)
- `test_grader_no_mirrors_shared.py` (T-7)
- `test_grader_writes_eval_only_bucket.py` (T-8)
- `test_grader_public_api_surface.py` (T-8)
- `test_simulator_public_api_surface.py` (T-8)

**Story B cement preserved:**
- `runner.py` `grader_callback` param ADDITIVE (default `None`) — Story B existing tests pass `None` → zero ripple. Verified via `pytest tests/agentic_evals/sales_agent/simulator/` post-edit.
- `asyncio.create_task` fire-and-forget — does NOT await callback completion → preserves Story B determinism (latency budget intact).
- Try/except wraps `asyncio.create_task` invocation — exception during callback creation logged + swallowed.

### Iter 2 — GREEN per validators

**Validator results native WSL** (T-9 ticket scope only):

| Validator | Command | Result |
|---|---|---|
| `be_lint` | `cd backend && .venv/bin/ruff check tests/agentic_evals/sales_agent/grader/ tests/agentic_evals/sales_agent/simulator/_internal/runner.py --no-cache` | ✅ All checks passed |
| `be_format` | `.venv/bin/ruff format --check tests/agentic_evals/sales_agent/grader/ tests/agentic_evals/sales_agent/simulator/_internal/runner.py` | ✅ 28 files formatted clean |
| `be_mypy_strict` | `.venv/bin/mypy tests/agentic_evals/sales_agent/grader/integration.py tests/agentic_evals/sales_agent/simulator/_internal/runner.py` | ✅ Success: no issues found in 2 source files |
| `tests/agentic_evals/sales_agent/grader/` | `.venv/bin/pytest tests/agentic_evals/sales_agent/grader/ -q` | ✅ **151 passed**, 1 warning |
| Story B regression | `.venv/bin/pytest tests/agentic_evals/sales_agent/simulator/ --deselect ::test_db_session_propagated_to_agent_bridge_via_contextvar` | ✅ **213 passed**, 36 skipped (eval-gated), 1 deselected (pre-existing flaky requires redis+LLM real) |
| `be_arch_fitness_full` | `.venv/bin/pytest tests/architecture/ -x -q --override-ini="addopts="` | ✅ **1063 passed**, 1 skipped (env-gated) |

**T-9 acceptance criteria mapping (06-tickets.yaml):**

| AcceptanceID | Validator | Test Path | Result |
|---|---|---|---|
| A1 | `scenario_1_maj_eval_multi_judge_happy` | `test_maj_eval_happy.py::test_3_rubrics_per_turn` | ✅ PASS — 24 grades persisted (8 turns x 3 rubrics), debate_triggered=False |
| A2 | `scenario_2_judge_disagreement_triggers_debate` | `test_maj_eval_debate.py::test_variance_triggers_round_2` | ✅ PASS — variance > 0.15 triggers R2; converges below 0.10 |
| A3 | `scenario_3_cache_hit_deterministic` | `test_grader_cache.py::test_cache_hit_deterministic` | ✅ PASS — cache HIT path zero judge calls |
| A4 | `scenario_4_prompt_injection_via_transcript` | `test_maj_eval_adversarial.py::test_prompt_injection_in_transcript_no_score_1` | ✅ PASS — 4 hostile injection variants resisted; suspicious flag wired DQ8 |
| A5 | `agentic_observability_extended_metadata_grader` + `legacy_simulator_invariants_intact` | `test_run_simulation_grader_hook.py` | ✅ PASS — 7 hook tests including fire-and-forget non-blocking + zero ripple None default |
| A6 | `agentic_cost_budget_full_eval_cold_warm` | shell — DB query ceiling $400 | N/A unit layer (full-cost eval is `--run-evals` CI nightly) |

**Files added/modified summary:**

- **Added (15 NEW)**:
  - `backend/tests/agentic_evals/sales_agent/grader/integration.py`
  - `backend/tests/agentic_evals/sales_agent/grader/conftest.py`
  - `backend/tests/agentic_evals/sales_agent/grader/test_run_simulation_grader_hook.py`
  - `backend/tests/agentic_evals/sales_agent/grader/test_judge_no_system_leak.py`
  - `backend/tests/agentic_evals/sales_agent/grader/test_unconverged_fallback.py`
  - `backend/tests/agentic_evals/sales_agent/grader/test_grader_cache.py`
  - `backend/tests/agentic_evals/sales_agent/grader/test_maj_eval_happy.py` (validator alias)
  - `backend/tests/agentic_evals/sales_agent/grader/test_maj_eval_debate.py` (validator alias)
  - `backend/tests/agentic_evals/sales_agent/grader/test_maj_eval_adversarial.py` (validator alias)
  - `backend/tests/agentic_evals/sales_agent/grader/scenarios/__init__.py`
  - `backend/tests/agentic_evals/sales_agent/grader/scenarios/test_scenario_1_happy_multi_judge.py`
  - `backend/tests/agentic_evals/sales_agent/grader/scenarios/test_scenario_2_edge_round_2_debate.py`
  - `backend/tests/agentic_evals/sales_agent/grader/scenarios/test_scenario_3_cache_idempotency.py`
  - `backend/tests/agentic_evals/sales_agent/grader/scenarios/test_scenario_4_adversarial_prompt_injection.py`
  - `backend/tests/agentic_evals/sales_agent/grader/calibration/__init__.py`
  - `backend/tests/agentic_evals/sales_agent/grader/calibration/voice_fidelity_calibration.md`
  - `backend/tests/agentic_evals/sales_agent/grader/calibration/qualification_accuracy_calibration.md`
  - `backend/tests/agentic_evals/sales_agent/grader/calibration/no_overpromise_calibration.md`
  - `backend/tests/agentic_evals/sales_agent/grader/calibration/no_hallucination_calibration.md`

- **Modified (1 EDIT additive minimal)**:
  - `backend/tests/agentic_evals/sales_agent/simulator/_internal/runner.py` — `grader_callback: Callable | None = None` parameter + per-completion `asyncio.create_task` fire-and-forget hook (D17 / DQ5 cement)

**Cement intact:**
- Story B determinism — runner does NOT await callback; runner returns immediately post completion
- Story B existing tests pass `None` → zero ripple (verified 213 tests pass)
- D17 / DQ5 fire-and-forget cement
- D-AG-10 best-effort try/except + structlog warn (verified A5.3 test)
- D7 rubric dispatch by persona_kind (verified Scenario 1 happy=3 rubrics)
- D14 / DQ2 sandbox markers literal in slot 5 (verified Scenario 4)
- DQ3 anti-anchoring R2 peer-only (verified Scenario 2 spy test)
- DQ8 unconverged → R1 fallback + structlog warn, NOT auto-block (verified test_unconverged_fallback.py)
- DQ8 suspicious flag — all-1.0 + injection_attempt → flag (verified Scenario 4)
- D-AG-9 injection_attempt_detected propagation from ANY judge (verified Scenario 4 test)
- H7 cost-bucket invariant — eval_simulator_grade rows ONLY (verified arch fitness 1063 pass)
- H9 public API surface 8 names — `grade_transcript_maj_eval` accessible (verified arch fitness)

**State transition:** in-progress → tests-passing.
