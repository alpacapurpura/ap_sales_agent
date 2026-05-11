# T-2 Result — SQLAlchemy 2.0 models + Pydantic v2 types

Story: sales-agent-voice-fidelity-grader-runtime
Ticket: T-2
State: pushed
Builder: builder-backend-sonnet
Completed: 2026-05-09

## Deliverables status

| Deliverable | Status | File |
|---|---|---|
| `EvalSimulatorGradeModel` (SQLA 2.0) | DONE | `src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_grade.py` |
| `EvalSimulatorGradeCacheModel` (SQLA 2.0) | DONE | `src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_grade_cache.py` |
| `__init__.py` additive edit (2 new models registered) | DONE | `src/modules/sales_agent/observability/eval_simulator/persistence/models/__init__.py` |
| `JudgeOpinion` Pydantic v2 frozen=True extra=forbid | DONE | `tests/agentic_evals/sales_agent/grader/result.py` |
| `MajEvalScore` Pydantic v2 schema_version Literal[1] | DONE | `tests/agentic_evals/sales_agent/grader/result.py` |
| `RubricGradeRequest` Pydantic v2 frozen=True | DONE | `tests/agentic_evals/sales_agent/grader/result.py` |
| `grader/__init__.py` (package init, empty __all__) | DONE | `tests/agentic_evals/sales_agent/grader/__init__.py` |
| 27 unit tests (5 test classes per 06-tickets.yaml) | DONE | `tests/agentic_evals/sales_agent/grader/test_pydantic_types_unit.py` |

## Acceptance criteria

| Criterion | Status | Evidence |
|---|---|---|
| A1: Pydantic v2 frozen=True + extra='forbid' invariants verified | PASS | 27/27 tests pass |
| A2: SQLAlchemy 2.0 models register + ORM columns match migration 127 | PASS | `test_orm_round_trip_minimal` (6 tests) pass |
| be_lint | PASS | ruff check 0 errors |
| be_format | PASS | ruff format 0 files to reformat |
| be_mypy_strict | PASS | mypy 0 errors |
| be_arch_fitness_full | PASS | 1016/1 skip (pre-existing optional) |
| jscpd_no_duplication | N/A pre-commit (gate runs globally) | Per anti-duplication audit: zero mirrors |

## Decisions implemented

- **D-BE-3** (schema-mirror R5): SQLA models use `Column()` parity with `eval_simulator_llm_call.py` precedent (Story B). R5 exception applied.
- **D-BE-4** (MajEvalScore v1 cement): `schema_version: Literal[1] = 1` — cannot be bumped without SCHEMA_MIGRATIONS registry entry.
- **D-BE-5** (Pydantic frozen extra forbid): all 3 types have `ConfigDict(extra="forbid", frozen=True)`.
- **D-AG-16** (grader package zero re-exports): `grader/__init__.py` has `__all__ = []` — surface controlled via `simulator/__init__.py` H9 expand (T-8).
- **D2** (judge weights cement): `JudgeOpinion.judge_id Literal["sonnet", "gpt4o", "kimi"]` + weight ge=0.0 le=1.0.
- **D15** (judge models pinned): validated via `test_judge_id_literal_validated`.

## Blocking dependencies for downstream tickets

- T-4 (`judge_registry.py`) — imports `JudgeOpinion` from `result.py` ✅ unblocked
- T-5 (`maj_eval.py`) — imports `MajEvalScore`, `RubricGradeRequest` ✅ unblocked
- T-6 (`cache.py`) — imports `MajEvalScore` ✅ unblocked
- T-7 (`judge_prompts.py`) — imports `RubricGradeRequest` ✅ unblocked
- T-9 (integration) — imports both SQLA models via session ✅ unblocked

## Scope compliance (R5 exception)

Only touched:
- `modules/sales_agent/observability/eval_simulator/persistence/models/` (R5 schema-mirror — allowed)
- `tests/agentic_evals/sales_agent/grader/` (new test-infra package)
- Zero touches: copilot/, sales_agent domain/application/api/, frontend/

## Notes for auditor-backend

- SQLA models use legacy `Column()` (not `Mapped[]`) intentionally — parity with Story B precedent `eval_simulator_llm_call.py`. R5 schema-mirror exception justifies this in this specific context.
- `RubricGradeRequest.transcript: list[Any]` and `tenant_voice_profile: Any` are intentional — avoids circular imports with Story D `GoldenTurnModel` and Story A `PersonalityProfile` in test-infra layer. `extra="forbid"` still enforces no unknown fields.
- Test file uses `pytestmark = pytest.mark.no_eval` — pure unit tests (no LLM, no DB), run in default CI.
