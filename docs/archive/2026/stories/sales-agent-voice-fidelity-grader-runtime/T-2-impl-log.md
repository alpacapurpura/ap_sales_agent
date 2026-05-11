# T-2 Implementation Log — SQLAlchemy 2.0 models + Pydantic v2 types

Story: sales-agent-voice-fidelity-grader-runtime
Ticket: T-2
Assigned: builder-backend-sonnet
Started: 2026-05-09
State: pushed

## Skills Consulted

- `backend-expert` — invoked per Step 0 GATE. Loaded `references/runtime-quality-checklist.md` antes commit. Decision: use `Column()` parity con precedent file `eval_simulator_llm_call.py` (R5 schema-mirror); no `Mapped[]` para estos modelos por paridad con Story B precedent. `extra="forbid"` + `frozen=True` en todos los Pydantic models. No raw `dict` returns. No `Any` en models SQLA.
- `tessl__fastapi` — invoked para Pydantic v2 patterns. Decision: `ConfigDict(extra="forbid", frozen=True)` in all 3 types (JudgeOpinion, MajEvalScore, RubricGradeRequest). `from_attributes=True` NOT needed (test-infra types, no ORM serialization). No `class Config:` inner.
- `tessl__pytest-api-testing` — invoked para fixture scoping. Decision: tests marcados `pytestmark = pytest.mark.no_eval` (pure unit, no LLM, no DB) → run default CI. Factory fixtures `_make_judge_opinion` + `_make_majeval_score` para evitar duplication.
- `tessl__graceful-degradation` — N/A (T-2 is pure types + models, no external calls).

## R24 Brief Acceptance Gate

- Validator pass: `/home/chris/AISALESHT/docs/product/stories/sales-agent-voice-fidelity-grader-runtime/CONTEXT-BRIEF-validation.md` (10.1KB, PASS verdict, 2026-05-09T01:05:00Z)
- Faithfulness flag: clean (zero discrepancies)
- R24 ACCEPTED: proceeding.

## Step 0.5 Default-Flip Detection

N/A — T-2 touches no `core/config.py` defaults. No flag flip.

## Git state at start

```
development (clean)
eb020bfe docs(eval-grader): T-1 impl-log + result + tickets state=pushed
```

## TDD Iteration Log

### Iteration 1 — RED

- Created `tests/agentic_evals/sales_agent/grader/test_pydantic_types_unit.py`
- Run: `ImportError: No module named 'tests.agentic_evals.sales_agent.grader.result'`
- RED confirmed: all tests fail (module not found).

### Iteration 2 — Implementation

1. Created `tests/agentic_evals/sales_agent/grader/__init__.py` (empty `__all__ = []` per D-AG-16 cement)
2. Created `tests/agentic_evals/sales_agent/grader/result.py` (JudgeOpinion + MajEvalScore + RubricGradeRequest)
3. Created `src/modules/sales_agent/.../persistence/models/eval_simulator_grade.py`
4. Created `src/modules/sales_agent/.../persistence/models/eval_simulator_grade_cache.py`
5. Edited `src/modules/sales_agent/.../persistence/models/__init__.py` (additive — 2 new exports)

### Iteration 2.1 — First GREEN attempt

- Tests auto-skipped by `agentic_evals/sales_agent/conftest.py` eval marker hook.
- Fix: added `pytestmark = pytest.mark.no_eval` to test file (pure unit tests, no LLM/DB).
- Run: 9 FAIL (6 `RubricGradeRequest not fully defined` + 3 MajEvalScore factory issues)

### Iteration 2.2 — Fix forward-refs in RubricGradeRequest

- Root cause 1: `list["Any"]` / `"Any"` as string in `from __future__ import annotations` context — Pydantic v2 can't resolve `Any` as forward-ref string.
- Fix: import `Any` from `typing` directly; use `list[Any]` / `Any` as direct types.
- Root cause 2: `MajEvalScore` factory missing `cache_hit_count` required field.
- Fix: added `"cache_hit_count": 0` to `_make_majeval_score` factory.
- Run: 27/27 PASS.

### Iteration 2.3 — Quality gates

- `ruff check`: 2 fixable issues → `--fix` applied: `RUF022` `__all__` sorting + `FURB157` verbose Decimal constructor.
- `ruff format --check`: 3 files to reformat → applied.
- `mypy src/...models/` → Success (3 files).
- `mypy tests/.../grader/result.py` → Success.
- `pytest tests/architecture/` → 1016 pass / 1 skip (pre-existing optional gate). GREEN.
- `pytest tests/agentic_evals/sales_agent/grader/test_pydantic_types_unit.py` → 27/27 PASS.

## Anti-duplication audit (Step 0 GATE)

```bash
find /home/chris/AISALESHT/backend/src -name "eval_simulator_grade*.py" 2>/dev/null
# Result: EMPTY before this PR — files genuinely NEW (T-2 first create)

grep -rn "class EvalSimulatorGradeModel\|class EvalSimulatorGradeCacheModel" \
  /home/chris/AISALESHT/backend/src/ 2>/dev/null
# Result: EMPTY — no pre-existing mirror classes
```

## Files created/modified this session

| File | Action | Reason |
|---|---|---|
| `tests/agentic_evals/sales_agent/grader/__init__.py` | NEW | Package init — empty `__all__` per D-AG-16 |
| `tests/agentic_evals/sales_agent/grader/result.py` | NEW | JudgeOpinion + MajEvalScore + RubricGradeRequest Pydantic v2 types |
| `tests/agentic_evals/sales_agent/grader/test_pydantic_types_unit.py` | NEW | 27 unit tests for T-2 types + ORM imports |
| `src/modules/.../persistence/models/eval_simulator_grade.py` | NEW | SQLA model — mirror Alembic 127 grade table, R5 schema-mirror |
| `src/modules/.../persistence/models/eval_simulator_grade_cache.py` | NEW | SQLA model — mirror Alembic 127 cache table, R5 schema-mirror |
| `src/modules/.../persistence/models/__init__.py` | EDIT (additive) | Register 2 new models in `__all__` |

## Validators run

| Validator | Command | Result |
|---|---|---|
| be_lint | `ruff check ... --no-cache` | PASS (after --fix RUF022 + FURB157) |
| be_format | `ruff format --check ...` | PASS (after reformat) |
| be_mypy_strict | `mypy src/...models/ tests/.../grader/result.py` | PASS (0 errors) |
| be_arch_fitness_full | `pytest tests/architecture/ -x -q` | PASS (1016/1 skip) |
| be_unit_tests | `pytest tests/.../grader/test_pydantic_types_unit.py -v` | 27/27 PASS |

## Scope compliance (R5 exception verified)

- Touched `modules/sales_agent/observability/eval_simulator/persistence/models/` — R5 schema-mirror exception applies (`.claude/rules/backend-ddd.md`).
- Zero touches to `domain/`, `application/`, `api/` of sales_agent module.
- Zero touches to `modules/copilot/` — outside T-2 scope.
- All Pydantic types live in `backend/tests/` (test-infra, `production_code: false`).
