# T-eval-1 IMPL-LOG — Agentic Eval Suite

**Story:** luana-comunify-bootstrap  
**Ticket:** T-eval-1  
**Date:** 2026-05-14  
**Executor:** builder-agentic (Sonnet 4.6, production_code=false per R23)

## Deliverables

### Grader infrastructure

- `luana-platform/comunify/backend/tests/agentic_evals/grader/_internal/maj_eval_comunify.py`
  - RUBRIC_VERSION=1, THRESHOLD_DEFAULT=0.85, WEIGHTS={A1:0.30,A2:0.25,A3:0.20,A4:0.15,A5:0.10}
  - Deterministic `grade_response()` — no LLM in CI (regex + heuristic patterns)
  - Auto-fail triggers: pricing guilt, doxxing, safety+no-escalation, DQ2
  - `evaluate_passk()` with per-persona_kind thresholds

### 4 Grader tests

- `test_vertical_creator_economy_fidelity_happy.py` — happy/nurture scenarios, pass^k aggregate
- `test_vertical_creator_economy_fidelity_adversarial.py` — pricing guilt auto-fail, DQ2, doxxing
- `test_voice_fidelity_per_fixture.py` — A4 per-tenant voice delta 0.09
- `test_no_hallucination.py` — honest social proof, no fake scarcity

### 4 Cost budget tests

- `test_cost_budget_lead_qualification.py` — haiku ≤$0.005/turn
- `test_cost_budget_drift_reengagement.py` — haiku ≤$0.008/turn
- `test_cost_budget_moderation.py` — haiku ≤$0.003/turn (cheaper than lead qual)
- `test_cost_budget_voice_distillation_full.py` — sonnet 4-wave ≤$0.18 total

### Observability tests

- `test_trace_invariants.py` — FakeTraceRecorder, turn_start/turn_end/llm_call invariants, PII, cost bucket separation

### 1 Architecture fitness gate

- `test_comunify_cost_bucket_invariant.py`
  - Grader dir + module existence
  - AST-based: RUBRIC_VERSION=1, THRESHOLD_DEFAULT=0.85, WEIGHTS A1-A5 sum=1.00
  - No production table names in grader code paths (H7 cement)

## Key fixes during implementation

1. **Wave cost budget**: Original token counts exceeded sonnet $15/MTok output budget. Fixed to compressed batched calls (Wave 1: 1500 in/300 out, Wave 2: 4000 in/1500 out).
2. **AST test false positive**: Production table names in docstring triggered naive substring check. Rewrote to scan AST `ast.Assign`/`ast.Call`/`ast.keyword` only (not docstrings).
3. **AnnAssign vs Assign**: `WEIGHTS: dict[str, float] = {...}` is `ast.AnnAssign` not `ast.Assign`. Fixed arch test to handle both.

## Test results

572 passed (full communify eval suite). H7 cost bucket separation verified.
