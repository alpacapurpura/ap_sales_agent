# T-9 — Result

**Ticket**: T-9 — Integration `run_simulation` `grader_callback` hook (`asyncio.create_task` fire-and-forget) + 4 scenario tests (happy / edge / cache / adversarial) + calibration MD seeds
**Owner**: builder-agentic-opus-4.7
**State**: tests-passing
**Date**: 2026-05-09

## Summary

Wired the MAJ-EVAL grader runtime (Story E T-1..T-8) into the Story B
`run_simulation` orchestrator via an OPTIONAL `grader_callback` parameter
that fires post-completion through `asyncio.create_task` (fire-and-forget).
The 4 production-critical scenarios (happy 3 rubrics, edge variance > 0.15
triggers R2 debate, cache idempotency, adversarial prompt-injection) all
verify GREEN against deterministic mock judges. Story B existing tests
remain passing (zero ripple — `grader_callback=None` is the default).

The integration adapter `make_grader_callback` translates a
`SimulationResult` into a `RubricGradeRequest`, dispatches the rubric set
per `persona_kind` (D7 cement), and best-effort wraps the
`grade_transcript_maj_eval` invocation. Calibration MD seed files (4
rubrics in scope) ship with the Chris-fillable label skeleton + auto
baseline section + re-calibration triggers.

## Deliverables vs T-9 acceptance (06-tickets.yaml)

| AcceptanceID | Description | Verifier path | Result |
|---|---|---|---|
| A1 | Scenario 1 (happy) — 24 MajEvalScore rows persisted + cost-bucket invariant | `test_maj_eval_happy.py::test_3_rubrics_per_turn` | ✅ PASS |
| A2 | Scenario 2 (edge) — variance triggers Round 2 + convergence/unconverged | `test_maj_eval_debate.py::test_variance_triggers_round_2` + `test_round_2_convergence_or_unconverged_flag` | ✅ PASS (4 tests) |
| A3 | Scenario 3 (cache) — 100% cache hit on re-run + zero new judge calls | `test_grader_cache.py::test_cache_hit_deterministic` | ✅ PASS (zero get_judge invocations under cache HIT) |
| A4 | Scenario 4 (adversarial) — sandbox markers resist injection (judges < 0.5) | `test_maj_eval_adversarial.py::test_prompt_injection_in_transcript_no_score_1` | ✅ PASS (4 hostile variants) + `test_sandbox_markers_protect_judge_prompt` + `test_suspicious_flag_when_all_judges_score_1_with_injection` |
| A5 | Async grader callback works (fire-and-forget, no block sim loop) | `test_run_simulation_grader_hook.py` | ✅ PASS (7 tests) — incl. `test_runner_does_not_await_callback` (1.0s timeout) + `test_grader_callback_optional_default_none` |
| A6 | Cost budget Story E baseline ~$330 cold / ~$108 warm cache (hard ceiling $400) | `agentic_cost_budget_full_eval_cold_warm` shell DB query | N/A unit layer (full-cost eval is `--run-evals` CI nightly opt-in) |

## Files added/modified

### NEW (15)

| Path | Purpose |
|---|---|
| `backend/tests/agentic_evals/sales_agent/grader/integration.py` | `make_grader_callback` factory wrapping `grade_transcript_maj_eval` for run_simulation hook |
| `backend/tests/agentic_evals/sales_agent/grader/conftest.py` | `mock_judge_factory` + `grader_session` factory fixtures + `_FakeTurn` / `_FakeVoiceProfile` / `_build_obs_context_stub` helpers |
| `backend/tests/agentic_evals/sales_agent/grader/test_run_simulation_grader_hook.py` | A5 hook integration — 7 tests (None default, explicit None, invocation-once, runner-non-blocking, callback-failure-swallowed, eval_metadata extended keys, simulation_id determinism) |
| `backend/tests/agentic_evals/sales_agent/grader/test_judge_no_system_leak.py` | Story B FORBIDDEN_LEAK_STRINGS pattern reuse — judge prompts + reasoning |
| `backend/tests/agentic_evals/sales_agent/grader/test_unconverged_fallback.py` | DQ8 unconverged semantics — R1 fallback + structlog warn + non-blocking |
| `backend/tests/agentic_evals/sales_agent/grader/test_grader_cache.py` | Validator-canonical path — `test_compute_cache_key_deterministic`, `test_cache_invalidates_on_*`, `test_judge_set_hash_invalidation`, `test_cache_hit_deterministic` (re-export from scenarios) |
| `backend/tests/agentic_evals/sales_agent/grader/test_maj_eval_happy.py` | Validator-alias re-export (Scenario 1 entries) |
| `backend/tests/agentic_evals/sales_agent/grader/test_maj_eval_debate.py` | Validator-alias re-export (Scenario 2 entries) |
| `backend/tests/agentic_evals/sales_agent/grader/test_maj_eval_adversarial.py` | Validator-alias re-export (Scenario 4 entries) |
| `backend/tests/agentic_evals/sales_agent/grader/scenarios/__init__.py` | Scenarios package marker |
| `backend/tests/agentic_evals/sales_agent/grader/scenarios/test_scenario_1_happy_multi_judge.py` | Scenario 1 — happy 3-rubric Round 1 converged path |
| `backend/tests/agentic_evals/sales_agent/grader/scenarios/test_scenario_2_edge_round_2_debate.py` | Scenario 2 — variance > 0.15 → R2 + DQ3 anti-anchoring + DQ6 r2_partial |
| `backend/tests/agentic_evals/sales_agent/grader/scenarios/test_scenario_3_cache_idempotency.py` | Scenario 3 — cache HIT zero judge calls + cache MISS persist |
| `backend/tests/agentic_evals/sales_agent/grader/scenarios/test_scenario_4_adversarial_prompt_injection.py` | Scenario 4 — 4 hostile injection variants + sandbox markers + DQ8 suspicious flag |
| `backend/tests/agentic_evals/sales_agent/grader/calibration/__init__.py` | Calibration package marker |
| `backend/tests/agentic_evals/sales_agent/grader/calibration/voice_fidelity_calibration.md` | Chris seed labels skeleton + auto baseline + re-calibration triggers (rubric voice-fidelity) |
| `backend/tests/agentic_evals/sales_agent/grader/calibration/qualification_accuracy_calibration.md` | Same structure (rubric qualification-accuracy threshold 0.75) |
| `backend/tests/agentic_evals/sales_agent/grader/calibration/no_overpromise_calibration.md` | Same structure (rubric no-overpromise threshold 0.7) |
| `backend/tests/agentic_evals/sales_agent/grader/calibration/no_hallucination_calibration.md` | Same structure (rubric no-hallucination threshold 0.85) |

### EDIT (1 — additive minimal)

| Path | Edit |
|---|---|
| `backend/tests/agentic_evals/sales_agent/simulator/_internal/runner.py` | Added `grader_callback: Callable[..., Any] \| None = None` parameter to `run_simulation`. Inserted Step 11b (post-artifact, pre-final-log): `asyncio.create_task(grader_callback(result))` wrapped in `try/except + structlog.warning` + `noqa: RUF006 — fire-and-forget per D17 cement`. Story B existing tests pass `None` → zero ripple. |

## Key decisions verified by tests

| Decision | Test path | Mechanism |
|---|---|---|
| D17 / DQ5 — fire-and-forget `asyncio.create_task` | `test_runner_does_not_await_callback` | Slow callback (`await callback_release.wait()`) runs under `asyncio.wait_for(timeout=1.0)`; runner returns successfully even though callback is still waiting |
| D7 — rubric dispatch per persona_kind | `test_3_rubrics_per_turn` (happy=3) + `_rubrics_for_persona_kind` factory | Direct factory unit + Scenario 1 integration |
| D-AG-9 — injection_attempt_detected propagation from ANY judge | `test_injection_attempt_detected_flag_propagated` | Only sonnet flags injection; MajEvalScore.injection_attempt_detected=True |
| DQ3 — Round 2 peer-only (anti-anchoring) | `test_round_2_peer_reasoning_excludes_self` | Spy on `build_judge_prompt` call args; assert peer_reasoning entries never include self judge_id |
| DQ6 — R2 partial fallback | `test_r2_partial_fallback_judge_fail` | gpt4o R2 score=None; r2_partial=True; judges JSONB has 6 entries with R2 gpt4o.score=None |
| DQ8 — unconverged R1 fallback + structlog warn (NOT block) | `test_unconverged_logs_structlog_warning` + `test_unconverged_does_not_raise_or_block` | Spy on `me.logger.warning`; assert `maj_eval_unconverged` event with simulation_id + variance_r2 + fallback="round_1_weighted_avg"; no exceptions raised |
| DQ8 — suspicious flag (all-1.0 + injection) | `test_suspicious_flag_when_all_judges_score_1_with_injection` | All judges return score=1.0 + injection_attempt_detected=True; MajEvalScore.suspicious=True |
| D14 / DQ2 — sandbox markers literal slot 5 | `test_sandbox_markers_protect_judge_prompt` | Spy on `build_judge_prompt` returns; assert TRANSCRIPT_MARKER_BEGIN < forbidden_idx < TRANSCRIPT_MARKER_END in slot 5 |
| H7 — cost-bucket invariant (eval_simulator_grade rows ONLY) | arch fitness `test_grader_writes_eval_only_bucket.py` | Already shipped via T-8; preserved post T-9 |
| H9 — public API surface 8 names | arch fitness `test_simulator_public_api_surface.py` | Already shipped via T-8; preserved post T-9 |
| Story B determinism — `grader_callback=None` zero ripple | 213/213 simulator tests pass (1 deselected pre-existing flaky redis test) | Default behavior unchanged; only opt-in additive |

## Validators GREEN

| Validator | Result |
|---|---|
| `be_lint` | ✅ All checks passed (28 files) |
| `be_format` | ✅ 28 files clean |
| `be_mypy_strict` (integration.py + runner.py) | ✅ No issues found |
| `be_arch_fitness_full` (1063 tests) | ✅ All passed |
| Grader suite (`tests/agentic_evals/sales_agent/grader/`) | ✅ 151/151 passed |
| Story B regression (`tests/agentic_evals/sales_agent/simulator/`) | ✅ 213 passed, 36 eval-skipped, 1 deselected (pre-existing flaky redis dep) |

## Cement preserved (anti-creep)

- ✅ Story B `simulator/__init__.py` 8-name H9 surface intact (no further additions)
- ✅ `simulator/_internal/runner.py` edit is purely additive (parameter + 5-line block); no behavior change when `grader_callback=None`
- ✅ Zero edits to Story C personas / Story D goldens YAML
- ✅ Zero edits to `personality_profiles.system_instruction` SSoT (sales-agent-expert §3 protected)
- ✅ Zero new arch fitness gates needed (T-9 leverages T-5/T-7/T-8 gates intact)
- ✅ `make_grader_callback` factory consumes `grade_transcript_maj_eval` — no mirror layer
- ✅ `RubricGradeRequest` consumed verbatim from Story E T-2 — no shape change

## Out of scope (downstream stories)

- ❌ Story F — pass^k aggregator over `eval_simulator_grade` rows
- ❌ Story G — CI gate enforcement (consumes `MajEvalScore.final_score` average per rubric × tenant)
- ❌ Story H — cost budget cap full eval cold/warm
- ❌ Story I — adversarial-jailbreak-suite (extends with `toxicity-control` rubric)
- ❌ Real-LLM full eval scenarios (`--run-evals` CI nightly)
- ❌ Chris filling 40 calibration labels (T-10 documentation reconciliation)

## Trace links

- Spec: `docs/product/stories/sales-agent-voice-fidelity-grader-runtime/01-spec.md` (Q1-Q9 ratified, 4 scenarios)
- Design: `02-design-agentic.md` (DQ1-DQ8 ratified)
- Architecture: `03-arch.md` §4.3 (state machine), §4.8 (async callback), §4.11 (calibration MD seed)
- Validators: `04-validators.yaml` (28 validators; A1-A5 covered, A6 CI nightly)
- Guidelines: `05-guidelines.md` (patterns required + forbidden + files in/out scope)
- Tickets: `06-tickets.yaml` T-9 deliverables verbatim

done -> docs/product/stories/sales-agent-voice-fidelity-grader-runtime/T-9-result.md
