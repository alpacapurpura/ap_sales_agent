# T-5 Implementation Log — maj_eval.py MAJ-EVAL state machine

**Ticket**: T-5 (Opus 4.7 mandatory — ★ critical complexity)
**State**: developing → tests-passing
**Owner**: builder-agentic (Opus 4.7)
**Started**: 2026-05-08

## Skills Consulted

| Skill | Why invoked | Decision cited |
|---|---|---|
| `backend-expert` | Always; loaded `runtime-quality-checklist.md` for SQLA 2.0 + Pydantic v2 + tenant isolation patterns | SQLA 2.0 `select(...).where(...)` with AsyncSession; Pydantic v2 `model_validate` for cache reconstruction; structlog only |
| `tessl__fastapi` | Always | N/A — pure async test-infra, no FastAPI surface (state machine is internal) |
| `tessl__pytest-api-testing` | Always | Function-scoped fixtures; `AsyncMock` for `judge.grade()`; `MagicMock` for AsyncSession; `pytest.mark.asyncio`/`no_eval` markers |
| `tessl__graceful-degradation` | maj_eval.py wraps DB persist + cache lookup → Rule 2 mandatory | try/except around persist + cache_persist (already inside cache.py); structlog warn fallback "re-grade" |
| `sales-agent-expert` | Touches `personality_profile.system_instruction` SSoT (read via tenant_voice_profile in RubricGradeRequest) | §3 Protected surfaces — READ-ONLY consume; NO mutation, NO mirror, NO fine-tune |
| `copilot-expert` | Cost recording pattern via `cost_recorder.pop_cost(litellm_call_id)` | Already wired by Story B `EvalSimulatorCallbackHandler` — judge LLM calls write `eval_simulator_llm_call` ONLY (H7 cement) |

## Step 0.5 — Default-Flip Detection

N/A — T-5 introduces NEW state machine, NOT a flag flip. No `core/config.py` defaults touched.

## Iteration log

### iter-1 (2026-05-08T22:30Z) — RED tests + skeleton
- Wrote `test_maj_eval_unit.py` with 14 tests covering all T-5 acceptance points
- Tests fail with `ModuleNotFoundError: tests.agentic_evals.sales_agent.grader._internal.maj_eval`
- Confirmed RED before implementing.

### iter-2 — Implement maj_eval.py
- Created `_internal/maj_eval.py` per 03-arch.md §4.3 verbatim pseudocode
- Constants: VARIANCE_R1_THRESHOLD=0.15, VARIANCE_R2_TARGET=0.10, JUDGE_CONCURRENCY=20
- Pure functions: `_weighted_average`, `_variance` (max-min, NOT statistical)
- State machine: Round 1 parallel via asyncio.gather + Semaphore; Round 2 conditional with peer-only filtering
- Fallbacks: unconverged (R2 var ≥0.10), r2_partial (judge fail R2 → R1 score), suspicious (all 1.0 + injection), <2 valid judges
- Best-effort persist + cache via try/except wrappers
- PII sanitize defense-in-depth: `sanitize_payload({"content": turn.content})` per turn

### iter-3 — Validators

(filled at runtime)
