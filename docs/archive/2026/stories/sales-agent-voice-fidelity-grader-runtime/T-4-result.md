# T-4 Result — judge_registry.py 3 judges + LiteLLM Proxy adapter

**Status:** tests-passing (awaiting auditor verdict)
**Owner:** builder-agentic Opus 4.7
**Story:** sales-agent-voice-fidelity-grader-runtime
**Date:** 2026-05-08
**Estimate:** 2h actual ~1.5h

## Deliverables shipped

### NEW files

1. **`backend/tests/agentic_evals/sales_agent/grader/_internal/judge_registry.py`** (T-4 implementation)
   - `JUDGE_WEIGHTS: Final[dict[str, float]] = {"sonnet": 0.4, "gpt4o": 0.4, "kimi": 0.2}` — D2 cement
   - `JUDGE_MODELS: Final[dict[str, str]] = {"sonnet": "claude-sonnet-4-6", "gpt4o": "gpt-4o-2024-11-20", "kimi": "kimi-k2.6"}` — D15 cement
   - `JUDGE_IDS: Final[tuple[str, ...]] = ("sonnet", "gpt4o", "kimi")` — convenience iteration
   - `_JudgeAdapter` class (registry pattern, NOT hierarchy):
     - `.grade(prompt, *, weight, round_n, obs_context, rubric_id, rubric_version, cache_hit=False) -> JudgeOpinion`
     - Dispatches via `LiteLLMService.get_client(role=ModelRole.AGENT).ainvoke(messages, config=...)` (D-AG-17 cement)
     - Extended `eval_metadata` with 5 NEW Story E keys (grader/rubric_id/rubric_version/judge_id/round_n/cache_hit/injection_attempt_detected)
     - `model_override` propagated to LiteLLM Proxy via metadata
     - `obs_context.langchain_config()` callbacks chain merged → cost_recorder bridge fires automatically (Story B canonical pattern)
     - Best-effort try/except → returns `JudgeOpinion(score=None, ...)` on failure
   - `_get_llm_service()` — process-scoped lazy LiteLLMService singleton
   - `get_judge(judge_id) -> _JudgeAdapter` — process-scoped factory + cached adapters; raises `KeyError` on unknown
   - `_parse_judge_response(raw: str) -> dict` — defensive JSON parse with score clamping `[0.0, 1.0]`, fallback to `score=None` on malformed JSON

2. **`backend/tests/agentic_evals/sales_agent/grader/test_judge_registry_unit.py`** (T-4 unit tests)
   - 7 tests, all `@pytest.mark.no_eval` (default CI without `--run-evals`)
   - Tests:
     1. `test_judge_set_full_3_returns_3_judges` — 3 judges loaded
     2. `test_weights_sum_to_1_0` — D2 cement (0.4 + 0.4 + 0.2)
     3. `test_litellm_proxy_routing_only` — AST scan; ZERO direct openai/anthropic SDK imports + LiteLLMService import present (validator `agentic_litellm_proxy_dispatch_only` parity)
     4. `test_judge_models_pinned` — D15 cement exact pinned values
     5. `test_get_judge_keyerror_on_unknown` — KeyError on unknown judge_id
     6. `test_get_judge_returns_adapter_with_correct_model` — adapter.model matches JUDGE_MODELS[id]
     7. `test_get_judge_returns_same_instance_per_judge_id` — process-scoped factory idempotent

## Quality gates — all GREEN

| Gate | Status | Cmd |
|---|---|---|
| be_lint (ruff check) | ✅ All checks passed | `cd backend && .venv/bin/ruff check tests/agentic_evals/sales_agent/grader/_internal/judge_registry.py tests/agentic_evals/sales_agent/grader/test_judge_registry_unit.py --no-cache` |
| be_format (ruff format --check) | ✅ 2 files already formatted | `cd backend && .venv/bin/ruff format --check ...` |
| be_mypy_strict | ✅ Success: no issues | `cd backend && .venv/bin/mypy tests/agentic_evals/sales_agent/grader/_internal/judge_registry.py tests/agentic_evals/sales_agent/grader/test_judge_registry_unit.py` |
| judge_registry_3_judges_loaded | ✅ 7/7 PASS | `cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/grader/test_judge_registry_unit.py -v` |
| agentic_litellm_proxy_dispatch_only | ✅ exit=0 OK | `! grep -rn "from openai import\|from anthropic import\|import openai\|import anthropic" tests/agentic_evals/sales_agent/grader/ && grep -q "from src.shared.infrastructure.llm.providers.litellm import" tests/agentic_evals/sales_agent/grader/_internal/judge_registry.py` |
| arch fitness regression | ✅ 189 passed, 3 skipped (T-5 placeholders) | `cd backend && .venv/bin/pytest tests/architecture/ -q -k "simulator or eval or schema_migrations"` |

## Decisions applied (06-tickets.yaml T-4 → decisions_applicable)

| Decision | How applied |
|---|---|
| **D2** — Judge weights 0.4/0.4/0.2 | `JUDGE_WEIGHTS` dict with Final type annotation. Test asserts sum=1.0 within float tolerance. |
| **D15** — Judge models pinned (NOT auto-tracking) | `JUDGE_MODELS` dict pinned to exact strings: `claude-sonnet-4-6`, `gpt-4o-2024-11-20`, `kimi-k2.6`. Test asserts each pin. |
| **D-AG-2** — Weights | Same as D2 above (decisions_applicable cross-ref). |
| **D-AG-17** — LiteLLM Proxy ONLY | Single import `from src.shared.infrastructure.llm.providers.litellm import LiteLLMService`. AST scan in test enforces. Validator `agentic_litellm_proxy_dispatch_only` shell-side enforcement. |

## Hardening invariants preserved

- **H7 cost-bucket separation**: judge calls dispatch via LiteLLM Proxy → `eval_metadata['grader'] = 'maj_eval'` → Story B's `EvalSimulatorCallbackHandler` writes to `eval_simulator_llm_call` ONLY. Cost-bucket invariant verification (T-8 scope `test_grader_writes_eval_only_bucket.py`) inherits from this wiring.
- **Anti-duplication §0**: REUSE shared `LiteLLMService` + `cost_recorder` + `EvalSimulatorObservabilityContext` (Story B). NO mirror created.
- **Voice cement READ-ONLY**: T-4 does NOT touch `personality_profile.system_instruction`. Voice handling is T-7 scope (judge_prompts.py Slot 3).

## Out of scope (per 06-tickets.yaml T-4 out_of_scope)

- ❌ MAJ-EVAL state machine (T-5)
- ❌ cache.py (T-6)
- ❌ judge_prompts.py 6-slot builder (T-7)
- ❌ Integration scenarios (T-9)
- ❌ Cost-bucket arch fitness gate test_grader_writes_eval_only_bucket.py (T-8)

## Validators expected to be exercised by sub-auditor

T-4 quality gates (must_pass=true):
- `be_lint` ✅
- `be_format` ✅
- `be_mypy_strict` ✅
- `judge_registry_3_judges_loaded` ✅
- `agentic_litellm_proxy_dispatch_only` ✅
- `agentic_no_grader_in_modules_imports` (depends on T-7 arch gate `test_grader_no_mirrors_shared.py` — not yet shipped; this validator will run on full PR review post-T-7 ship)

## Files NOT TOUCHED (per parallel-safety)

- `backend/tests/agentic_evals/sales_agent/grader/_internal/cache.py` (T-6 in progress, sibling session)
- `backend/tests/agentic_evals/sales_agent/grader/_internal/judge_prompts.py` (T-7 in progress)
- `backend/tests/agentic_evals/sales_agent/grader/test_judge_prompts.py` (T-7)
- `backend/tests/agentic_evals/sales_agent/grader/result.py` (T-2 — already shipped, READ-ONLY)
- `backend/tests/agentic_evals/sales_agent/grader/test_pydantic_types_unit.py` (T-2 shipped)
- `backend/tests/agentic_evals/sales_agent/simulator/__init__.py` (T-8 H9 expand 7→8 — out of T-4 scope)
- `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/*.py` (T-2 shipped)

## Commit info

Commit message: `feat(eval-grader): T-4 judge_registry.py — 3 judges + LiteLLM Proxy`

Files staged:
- `backend/tests/agentic_evals/sales_agent/grader/_internal/judge_registry.py`
- `backend/tests/agentic_evals/sales_agent/grader/test_judge_registry_unit.py`
- `docs/product/stories/sales-agent-voice-fidelity-grader-runtime/T-4-impl-log.md`
- `docs/product/stories/sales-agent-voice-fidelity-grader-runtime/T-4-result.md`
- `docs/product/stories/sales-agent-voice-fidelity-grader-runtime/06-tickets.yaml` (T-4 entry only — state=pushed, transitions appended)
