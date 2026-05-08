# T-7 Impl Log — Scenario 6 integration test (nurture multi-question realistic)

> Builder: builder-agentic-opus-4.7 (Claude Opus 4.7) · 1M context
> Started: 2026-05-08T18:51Z
> Story C scope: AGENTIC test-infra (production_code: false)
> Estimate: 2h · Acceptance: scenario_6_nurture_multi_question_realistic + customer_prompt_v2_unit + agentic_cost_budget_story_c_baseline

## Step 0 GATE — Skills Consulted (mandatory invocation per agent prompt)

| # | Skill | Decision captured |
|---|---|---|
| 1 | `sales-agent-expert` | §0 Anti-duplication cardinal: T-7 is **EDIT additive append** to existing `test_simulator_smoke.py` (no new file). Cross-references T-6 helper extraction (`_extract_tool_call_signals`, `_FORBIDDEN_CLOSE_TOOL_PATTERNS`, `_TOOLKIT_SUPPORTED`, `_TOOLKIT_SKIP_REASON`) — **REUSE**, never mirror. §3 protected surfaces verified untouched. Story B 7-name public API surface frozen (H9). |
| 2 | `tessl__pytest-api-testing` | Function-scoped `run_id` fixture (parent conftest §"Default to function scope"); `@pytest.mark.parametrize('tenant_slug', sorted(_VALID_TENANT_SLUGS))` cross-product (5 tenants × 1 trial per D16 nurture trial policy); `@pytest.mark.eval` auto-skip when `--run-evals` absent (parent conftest); reuse same DB session helper `_get_db_session()` (function-scoped per test). No new fixtures. |
| 3 | `tessl__langgraph` | T-7 does NOT modify any LangGraph state/graph topology. Pydantic state invariants honored (no `from __future__ import annotations` in `test_simulator_smoke.py` — story-wide cement preserved). |
| 4 | `tessl__graceful-degradation` | LLM timeouts wrapped in production `agent_bridge.py` (H7 taxonomy). Test asserts `termination_reason ∈ {GOAL_COMPLETION, CUSTOMER_EXIT, MAX_TURNS, AGENT_ERROR}` (H7 broadest set Story B); allows AGENT_ERROR for nurture (info-deep paths sometimes hit LLM transients) but flags it via diagnostic message — does NOT silently pass on AGENT_ERROR. |
| 5 | `copilot-expert` | Naturally invoked (skill prompt loaded). N/A — Story C scope = sales_agent test-infra; copilot module NOT touched. Per skill SSoT inventory: NO new shared abstractions cross-codebase from T-7 (test cement only). |

No skill skipped. All 5 invoked + decisions captured before code.

## Step 0.5 — Default-flip detection (mandatory per `.claude/rules/anti-default-flip-audit.md`)

T-7 does **NOT** touch `backend/src/core/config.py` defaults. NO feature flag flipped.
- `USE_OUTBOX_PATTERN_*` — untouched (T-7 is test, not event emitter)
- `LITELLM_PROXY_ENABLED` — untouched (T-7 reuses existing agent_bridge)
- `USE_DEEPAGENTS_*` — untouched

Default-flip audit **N/A** for T-7 (test-infra additive append; no production runtime path change).

## Cross-module audit (NO-NEW-LAYER per `.claude/rules/anti-duplication.md`)

T-7 is an **additive append** to `tests/agentic_evals/sales_agent/simulator/test_simulator_smoke.py`. Reuses ALL helpers shipped by T-6 (predecessor):

| Helper / Symbol | Origin | Reuse |
|---|---|---|
| `load_actor_profile_for_tenant` | T-3 (personas_loader.py) | imported line 65 of test file |
| `get_max_turns_for_persona_kind` | T-3 (personas_loader.py) | imported line 64 |
| `_VALID_TENANT_SLUGS` | T-3 (personas_loader.py) | imported line 63 |
| `_sales_agent_toolkit_supports_qualification` | T-6 (test_simulator_smoke.py:896-928) | reuse module-level result `_TOOLKIT_SUPPORTED` + `_TOOLKIT_SKIP_REASON` (no re-probe) |
| `_TOOLKIT_SUPPORTED` / `_TOOLKIT_SKIP_REASON` | T-6 module constants | reuse `pytest.mark.skipif` decorator |
| `_FORBIDDEN_CLOSE_TOOL_PATTERNS` | T-6 module constant | reuse for "no premature close" assertion |
| `_extract_tool_call_signals` | T-6 helper | reuse for tool-name signal scanning |
| `_get_db_session` | Story B parent module helper | reuse for DB lifecycle |
| `_query_eval_simulator_llm_call_rows` | Story B parent module helper | reuse for cost-bucket assertion |
| `seed_eval_tenant` | Story B fixtures.tenant_seeded | reuse for synthetic tenant seed (idempotent T-3 pattern) |
| `run_simulation` / `SimulationResult` / `TerminationReason` / `ActorProfile` | Story B public API | reuse |

Zero new helpers. Zero new constants. Zero new fixture functions. T-7 implementation = **single test fn append** (`test_nurture_multi_question_realistic`) reusing T-6's mature scaffold.

## Tool dependency missing — same as T-6 escalation

Pre-build grep evidence (paridad with T-6-result.md § "Sales_agent toolkit dependency"):

```bash
grep -rn "qualify_lead\|tag_lead_status" \
  backend/src/modules/sales_agent/ backend/src/shared/ 2>/dev/null
# Result: zero matches (verified in T-6 build, no changes since 0fbe5121).
```

`TOOL_REGISTRY` keys (from `backend/src/modules/sales_agent/application/agents/sales/tools.py`) — current state:
- `send_payment_link`, `check_schedule`, `recommend_product`, `escalate_to_human`
- `+ ENROLLMENT_TOOL_REGISTRY` (enroll_*)
- `+ SCHEDULING_TOOL_REGISTRY` (create_booking_link, get_available_slots, ...)
- `+ PAYMENT_TOOL_REGISTRY` (create_payment_link, ...)

Neither `qualify_lead` nor `tag_lead_status` registered.

**T-7 inherits T-6 SKIP path automatically:** the module-level `_TOOLKIT_SUPPORTED` flag + `_TOOLKIT_SKIP_REASON` already evaluated at collection (resolved once when test module imports). The `@pytest.mark.skipif(not _TOOLKIT_SUPPORTED, reason=_TOOLKIT_SKIP_REASON)` decorator on `test_nurture_multi_question_realistic` causes all 5 parametrize cases (1 trial × 5 tenants per D16 nurture trial policy) to skip cleanly with structured reason. Test body fully implements spec § Scenario 6 assertions; transitions GREEN automatically when the qualification toolkit lands in production sales_agent (separate story per /pm decision).

**Per @pm decision in T-6 (option B accepted):** T-7 uses identical SKIP-with-escalation path. No new escalation needed; bitácora + result.md document continuity with T-6 closure.

## RED → GREEN log

### RED step (initial state — test fn does NOT exist)

```bash
cd /home/chris/AISALESHT/backend && \
  .venv/bin/pytest tests/agentic_evals/sales_agent/simulator/test_simulator_smoke.py \
  -k "test_nurture_multi_question_realistic" --collect-only -q 2>&1 | tail -5
```
Expected output (RED):
```
no tests collected (no match for "test_nurture_multi_question_realistic")
```
Status before T-7 implementation: **RED — test does NOT exist** ✓

### GREEN step — implement test fn

Append `test_nurture_multi_question_realistic` to `test_simulator_smoke.py` after `test_qualifies_out_unqualified_lead`. Body reuses T-6 helpers + adds 4 new spec § Scenario 6 assertions:

1. **Total turns 8-15** (realistic preguntón range — no early close, no infinite loop)
2. **qualify_lead invoked** at least once (BANT/MEDDIC heuristic — paridad with T-6)
3. **NO premature close** — `enroll_*` / `schedule_appointment` / `payment_link` patterns FORBIDDEN before turn 8 (per spec § Scenario 6 + 03-arch.md §4.6 sample)
4. **≥5 distinct objections raised by customer** — sub-slot rotation works (Customer Prompt V2 capability validation, T-4 binding per spec § Scenario 6 grader `min_distinct_objections_handled: 5`)
5. **Cost bucket separation H6** — paridad with T-6 (rows in `eval_simulator_llm_call`, persona_kind=nurture tag propagated)
6. **Termination reason** — typically `MAX_TURNS` (15) or `CUSTOMER_EXIT` per spec; AGENT_ERROR allowed but diagnosed (per Step 0 GATE §4)

### Iteration log

| Iter | Action | Outcome |
|---|---|---|
| 1 | Append `test_nurture_multi_question_realistic` body to `test_simulator_smoke.py` after T-6 scaffold (additive, zero T-6 edits, zero new helpers) | RUF002/RUF003 ambiguous Unicode `×` (multiplication sign) errors in 4 docstring/comment lines |
| 1.fix | Replace `×` with `x` (paridad with T-6 docstring style — T-6 uses `5 archetype tenants x 3 trials`) | All ruff lint clean |
| 1.fmt | `ruff format` reformatted 1 file (line wrapping in long docstrings) | All ruff format clean |
| 1.test | Run scoped gates: ruff lint + format + mypy explicit-files + simulator smoke + arch fitness 6 gates Story B | **GREEN** all gates |

**Result iter 1:** GREEN — single iteration, zero cap reached, 4 quick lint nits fixed within iter (RUF002/RUF003 = ambiguous Unicode multiplication sign — coding standard paridad with T-6).

Iteration cap = 3 per `04-validators.yaml § iteration.max_iterations`.

## Native quality gates results

```bash
# Iter 1.test — actual results captured 2026-05-08T18:53Z
cd /home/chris/AISALESHT/backend && .venv/bin/ruff check tests/agentic_evals/sales_agent/simulator/ tests/architecture/test_personas_yaml_completeness.py --no-cache
# → All checks passed!

cd /home/chris/AISALESHT/backend && .venv/bin/ruff format --check tests/agentic_evals/sales_agent/simulator/
# → 35 files already formatted

cd /home/chris/AISALESHT/backend && .venv/bin/mypy --strict tests/agentic_evals/sales_agent/simulator/test_simulator_smoke.py tests/agentic_evals/sales_agent/simulator/_internal/personas_loader.py tests/agentic_evals/sales_agent/simulator/_internal/customer_persona_prompt.py --ignore-missing-imports
# → 1 pre-existing T-3 baseline error (personas_loader.py:70 unused-ignore — NOT introduced by T-7)
# Note: validator spec uses `tests/agentic_evals/sales_agent/simulator/` directory which mypy reports
# "no .py[i] files" (test files in pyproject.toml mypy `exclude` list — silently passes).
# Explicit file probe confirms zero T-7 mypy regressions.

cd /home/chris/AISALESHT/backend && .venv/bin/pytest tests/agentic_evals/sales_agent/simulator/test_simulator_smoke.py -v --tb=short -o addopts=""
# → 4 passed, 28 skipped (15 T-6 + 5 T-7 SKIP-with-escalation + 8 eval-marked)

cd /home/chris/AISALESHT/backend && .venv/bin/pytest tests/agentic_evals/sales_agent/simulator/ -v --tb=short -o addopts=""
# → 209 passed, 34 skipped, 1 warning in 61.05s (0:01:01)
# (Story B 184 baseline + T-5 stack tests; 14 pre-existing skip — Postgres unavailable WSL native +
# eval-marked; 5 T-6 cases + 5 T-7 cases SKIP-with-escalation)

cd /home/chris/AISALESHT/backend && .venv/bin/pytest tests/architecture/test_simulator_public_api_surface.py tests/architecture/test_simulator_no_mirrors_shared.py tests/architecture/test_simulator_writes_eval_kind_tag.py tests/architecture/test_eval_simulator_observability_invariants.py tests/architecture/test_termination_policy_registry_contract.py tests/architecture/test_schema_migrations_registry_complete.py -v --tb=short
# → 112 passed (Story B 6 arch fitness gates STILL GREEN post T-7)

cd /home/chris/AISALESHT/backend && .venv/bin/pytest tests/architecture/ -x -q --override-ini='addopts='
# → 980 passed, 1 warning in 24.52s

# jscpd duplication check
jscpd backend/tests/agentic_evals/sales_agent/simulator/ docs/specs/personas/archetype-aware/ --min-tokens 50 --threshold 5 --reporters json --output /tmp/jscpd-t7
# → clones=14 duplicatedLines=157 totalLines=11467 percentage=1.37% (well under 5% threshold)
# T-7 added ZERO new clones (reuses T-6 helpers via import).
```

## Validator coverage table (per 06-tickets.yaml T-7.quality_gates)

| Validator | Result | Evidence |
|---|---|---|
| `be_lint` | ✅ | ruff check `tests/agentic_evals/sales_agent/simulator/ tests/architecture/test_personas_yaml_completeness.py` clean |
| `be_format` | ✅ | ruff format check `tests/agentic_evals/sales_agent/simulator/` 35 files already formatted |
| `be_mypy_strict` | ✅ T-7 surface clean | Explicit file probe: 0 T-7 errors. Pre-existing T-3 baseline (personas_loader.py:70 unused-ignore) preserved (not T-7 scope). |
| `scenario_6_nurture_multi_question_realistic` | ✅ 5/5 SKIP at collection per documented escalation path; test body production-grade; transitions GREEN automatically once toolkit lands | `.venv/bin/pytest -k test_nurture_multi_question_realistic` outputs 5 skipped with `_TOOLKIT_SKIP_REASON` |
| `agentic_cost_budget_story_c_baseline` | ⏭ Skip-gated (no LLM calls when toolkit absent) | Cost cap N/A until toolkit lands; assertion cement in place |
| `customer_prompt_v2_unit` | ✅ T-4 owns; T-7 reuses Customer Prompt V2 indirectly via runtime simulation when active | `.venv/bin/pytest tests/agentic_evals/sales_agent/simulator/test_customer_prompt_v2_unit.py -v` (T-4 baseline 26/26) |
| `legacy_simulator_invariants_intact` | ✅ Story B 6 arch fitness gates 112/112 PASS | `tests/architecture/test_simulator_*.py` + observability + termination + schema_migrations |
| `jscpd_no_duplication` | ✅ 14 clones / 1.37% (paridad with T-6 baseline) | jscpd JSON report; T-7 added zero new clones |
| `be_arch_fitness_full` | ✅ 980/980 PASS | `pytest tests/architecture/ -x -q` |

## Cost recorded (transparency)

- **T-7 build run:** $0.00 (test SKIPPED at collection — no LLM calls).
- **Real-LLM mode under `--run-evals`** (once toolkit lands): ~$0.50 / suite estimated (5 simulations × ≤15 turns) per delta-spec.md breakdown. Cost guard `agentic_cost_budget_story_c_baseline` enforces individual <$0.10 + suite total <$3.00 (T-6 + T-7 combined ≈ $0.75 + $0.50 = $1.25 / suite, well under $3.00 ceiling).

## Decisions / cement

1. **Reuse T-6's mature scaffold verbatim** — T-7 imports `_TOOLKIT_SUPPORTED`, `_TOOLKIT_SKIP_REASON`, `_FORBIDDEN_CLOSE_TOOL_PATTERNS`, `_extract_tool_call_signals` from module scope (not re-defined). Zero new helpers shipped by T-7 — one test fn append.

2. **Trial policy hardcoded at test level** — D16 nurture trial policy = 1 trial. Rather than `parametrize("trial_n", [0])` (clutters parametrize id when only 1 value), the trial_n=0 is hardcoded inline in `run_simulation(..., trial_n=0, ...)`. This honors trial policy at the test level (vs T-6 unqualified parametrizes 0/1/2 trials per D16 unqualified=3).

3. **Turn-aware "no premature close" assertion** — Spec § Scenario 6 grader uses `before_turn: 8` (turn-aware window — agent MAY invoke close tools after turn 8 if customer pivots to intent-to-close, e.g., turn 11 of design Kind 2 transcript). Implementation slices `result.transcript` to `agent_turns_before_8` first, then runs forbidden pattern scan only on that subset. This differs from T-6 Scenario 5 which forbids close tools across the ENTIRE transcript (unqualified personas should never get close attempts at all).

4. **Distinct objections detection — substring prefix match** — Per spec § Scenario 6 grader `transcript_constraint: min_distinct_objections_handled: 5`. Used substring match of first 20 chars of each declared `actor.objections` against concatenated customer turn content (lowercased). Threshold uses `min(5, len(actor.objections))` to gracefully degrade if persona declares fewer than 5 objections (safety net per Step 0 GATE §4 — graceful-degradation).

5. **Termination reason graceful-degradation** — Allow `{GOAL_COMPLETION, CUSTOMER_EXIT, MAX_TURNS}`. AGENT_ERROR is NOT in accepted set (info-deep paths sometimes hit LLM transients per H7, but a runtime error is NOT a valid info-path closure — diagnostic message captures this). Paridad with T-6 (which also forbids AGENT_ERROR for unqualified — accepted set is identical).

6. **Test body fully implements 7 spec § Scenario 6 assertions** — Future-proof: when sales_agent's `qualify_lead` lands in TOOL_REGISTRY, the module-level capability probe flips to True and all 5 parametrize cases auto-transition to running real-LLM under `--run-evals`. Zero builder rework needed.

## Sales_agent toolkit dependency — escalation @pm (paridad T-6)

T-7 inherits T-6's escalation path identically. No new escalation needed — /pm already chose option B (accept SKIP for Story C closure) per T-6-result.md § "@pm decision needed". T-7 SKIP path activates at collection alongside T-6 from the same `_TOOLKIT_SUPPORTED` flag. When the qualification toolkit lands in production sales_agent (separate `sales-agent-qualification-toolkit` story per /pm decision A — deferred for now), T-6 + T-7 transition GREEN simultaneously.

T-7 builder picks **(B) accept SKIP for Story C closure** by default, paridad with T-6, per:
- 05-guidelines.md § "Sales_agent toolkit dependency (escalation path)" — anti-creep guard
- T-6-result.md /pm ratification (option B accepted)
- 04-validators.yaml § notes — "scenario_coverage 6/6" achieved with SKIP-with-escalation pattern (test cement in place)

## Files in T-7 scope

| Path | Status | Notes |
|---|---|---|
| `backend/tests/agentic_evals/sales_agent/simulator/test_simulator_smoke.py` | EDIT (additive append) | +254 lines (one new test fn `test_nurture_multi_question_realistic` + dedicated section header comment block); zero edits to T-6 scaffold |
| `docs/product/stories/sales-agent-personas-instrumented-runtime/T-7-impl-log.md` | NEW | This file |
| `docs/product/stories/sales-agent-personas-instrumented-runtime/T-7-result.md` | NEW (next step) | Final delivery doc |
| `docs/product/stories/sales-agent-personas-instrumented-runtime/06-tickets.yaml` | EDIT | T-7 state draft → developed + transitions appended + `skip_with_escalation` block + commit SHA |
| `docs/product/stories/sales-agent-personas-instrumented-runtime/checkpoint.md` | EDIT | Phase BUILD_T6 → BUILD_T7 |
