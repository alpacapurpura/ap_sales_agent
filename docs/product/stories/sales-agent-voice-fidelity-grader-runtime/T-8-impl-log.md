# T-8 — Implementation Log

**Ticket**: T-8 — `simulator/__init__.py` H9 expand 7→8 (`grade_transcript_maj_eval`) + arch fitness re-freeze + 4 NEW grader gates
**Owner**: builder-agentic-opus-4.7
**State transitions**: draft → developing → tests-passing
**Started**: 2026-05-09
**Completed**: 2026-05-09

## Skills Consulted

| Skill | Reason invoked | Decision cited |
|---|---|---|
| `backend-expert` (`runtime-quality-checklist.md`) | Static AST gate authoring + Pydantic v2 invariants | Pattern: `tests/architecture/` arch fitness — pure static analysis, NO DB queries, `pytestmark = pytest.mark.no_eval`. Anti-pattern: avoid runtime invocation in arch tests. |
| `tessl__pytest-api-testing` | pytest fixture scoping + parametrize | Used `@pytest.mark.parametrize` for forbidden table/class names; function-scope default; no DB fixtures (static AST only). |
| `sales-agent-expert` § D-AG-15 / D-AG-16 cement | H9 expand 7→8 single addition `grade_transcript_maj_eval`; grader package cero re-exports | Implementation honors §3 protected SSoT (no touch to `personality_profiles.system_instruction`). |
| `tessl__fastapi` | N/A (no FastAPI surface) | Confirmed not applicable |
| `tessl__graceful-degradation` | N/A (static AST gates, no external calls) | Confirmed not applicable |

**Step 0.5 — Default-flip detection:** N/A. T-8 doesn't touch `core/config.py`, doesn't flip flags. No `USE_*_PATTERN_*` / `LITELLM_PROXY_ENABLED` / `USE_DEEPAGENTS_*` / `ENABLE_*` modifications.

## Pre-existing arch fitness gates inventory (verified pre-implementation)

```bash
ls backend/tests/architecture/test_grader_*.py
```
- `test_grader_no_mirrors_shared.py` ✅ (T-7 already shipped — reuses `validator agentic_no_grader_in_modules_imports`)
- `test_grader_pii_sanitize_pre_judge.py` ✅ (T-5/T-7 already shipped)
- `test_grader_round_2_no_self_reasoning.py` ✅ (T-7 already shipped)
- `test_grader_sandbox_markers_enforced.py` ✅ (T-7 already shipped)

Pre-existing simulator gates also confirmed GREEN baseline pre-T-8.

T-8 NEW gates needed (not yet shipped):
- `test_grader_public_api_surface.py` (NEW)
- `test_grader_writes_eval_only_bucket.py` (NEW)

T-8 EDIT gates:
- `test_simulator_public_api_surface.py` (allowlist 7→8)

T-8 EDIT files:
- `tests/agentic_evals/sales_agent/simulator/__init__.py` (H9 expand 7→8)

T-8 NEW files NOT needed:
- `grader/__init__.py` (already exists with `__all__: list[str] = []`)
- `grader/_internal/__init__.py` (already exists with `__all__: list[str] = []`)

## TDD timeline

### RED phase

1. Wrote `tests/architecture/test_grader_public_api_surface.py` (8 tests):
   - `test_grader_dunder_all_is_empty_list`
   - `test_grader_dunder_all_length_is_zero`
   - `test_grader_internal_dunder_all_is_empty_list`
   - `test_grade_transcript_maj_eval_accessible_via_simulator`
   - `test_grade_transcript_maj_eval_in_simulator_dunder_all`
   - `test_grade_transcript_maj_eval_not_re_exported_from_grader_package`
   - `test_no_internal_symbols_leaked_on_grader`
   - `test_internal_subpackage_not_reexported_on_grader`

2. Wrote `tests/architecture/test_grader_writes_eval_only_bucket.py` (9 tests via parametrize):
   - `test_grader_root_exists`
   - `test_grader_has_python_files`
   - `test_no_forbidden_orm_class_imported[CopilotLlmCallModel]`
   - `test_no_forbidden_orm_class_imported[SalesAgentLlmCallModel]`
   - `test_no_forbidden_orm_class_imported[CampaignLlmCallModel]`
   - `test_no_forbidden_table_literal_in_executable_code[copilot_llm_call]`
   - `test_no_forbidden_table_literal_in_executable_code[sales_agent_llm_call]`
   - `test_no_forbidden_table_literal_in_executable_code[campaign_llm_call]`
   - `test_grader_references_canonical_eval_write_path`

3. Initial RED run:
   ```
   tests/architecture/test_grader_public_api_surface.py 3 failed, 5 passed
   tests/architecture/test_grader_writes_eval_only_bucket.py 9 passed
   ```
   - 3 expected failures in `test_grader_public_api_surface.py`:
     - `test_grade_transcript_maj_eval_in_simulator_dunder_all` FAIL (simulator __all__ still 7 names) ✅ EXPECTED
     - `test_grade_transcript_maj_eval_accessible_via_simulator` FAIL (ImportError) ✅ EXPECTED
     - `test_no_internal_symbols_leaked_on_grader` FAIL (`__annotations__` was missing from ALLOWED_DUNDERS — Python sets it implicitly when `__all__: list[str] = []` has type annotation)

### Fix iteration #1 (legitimate Python machinery)

`__annotations__` is a Python-managed dunder, not a leak. Added to `_ALLOWED_DUNDERS` frozenset with explanatory comment.

### GREEN phase

1. EDIT `tests/agentic_evals/sales_agent/simulator/__init__.py`:
   - Added import: `from tests.agentic_evals.sales_agent.grader._internal.maj_eval import grade_transcript_maj_eval`
   - Added `"grade_transcript_maj_eval"` to `__all__` (alphabetical sort preserved — new total 8 names)
   - Updated module docstring: H9 cement extended to "8 names post Story E (T-8)" with downstream consumer note + reference to `test_grader_public_api_surface.py` + `03-arch.md §3.6 / §4.10` ratification cycle.

2. EDIT `tests/architecture/test_simulator_public_api_surface.py`:
   - Updated `_EXPECTED_PUBLIC_NAMES` frozenset 7→8 (added `"grade_transcript_maj_eval"`)
   - Renamed `test_simulator_dunder_all_exact_seven_names` → `test_simulator_dunder_all_exact_eight_names`
   - Renamed `test_simulator_dunder_all_length_is_seven` → `test_simulator_dunder_all_length_is_eight`
   - Updated literal `7` → `8` in length cement assertion
   - Added NEW test `test_grade_transcript_maj_eval_is_callable` (verifies the H9 expand entrypoint is callable)
   - Updated module docstring: Story E (T-8) cement reference, "EXACTLY 8 names", H9 expand 7→8 single addition note, downstream consumers Stories F/G/H/I.

### Validators sequential

```
$ cd backend && .venv/bin/ruff check tests/architecture/test_grader_public_api_surface.py tests/architecture/test_grader_writes_eval_only_bucket.py tests/architecture/test_simulator_public_api_surface.py tests/agentic_evals/sales_agent/simulator/__init__.py --no-cache
All checks passed!

$ cd backend && .venv/bin/ruff format --check ...
4 files already formatted

$ cd backend && .venv/bin/mypy tests/architecture/test_grader_public_api_surface.py tests/architecture/test_grader_writes_eval_only_bucket.py tests/architecture/test_simulator_public_api_surface.py
Success: no issues found in 3 source files

$ cd backend && .venv/bin/pytest tests/architecture/test_grader_public_api_surface.py tests/architecture/test_grader_writes_eval_only_bucket.py tests/architecture/test_simulator_public_api_surface.py -v --tb=short --override-ini="addopts="
======================== 34 passed, 1 warning in 11.07s ========================

$ cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short --override-ini="addopts="
1063 passed, 1 skipped, 1 warning in 26.16s
```

### Downstream regression scope (legacy_simulator_invariants_intact validator + grader gates)

Per validator definition `legacy_simulator_invariants_intact`:

```
$ cd backend && .venv/bin/pytest \
    tests/architecture/test_simulator_no_mirrors_shared.py \
    tests/architecture/test_simulator_writes_eval_kind_tag.py \
    tests/architecture/test_eval_simulator_observability_invariants.py \
    tests/architecture/test_termination_policy_registry_contract.py \
    tests/architecture/test_schema_migrations_registry_complete.py \
    tests/architecture/test_personas_yaml_completeness.py \
    tests/architecture/test_grader_no_mirrors_shared.py \
    tests/architecture/test_grader_pii_sanitize_pre_judge.py \
    tests/architecture/test_grader_round_2_no_self_reasoning.py \
    tests/architecture/test_grader_sandbox_markers_enforced.py \
    -v --tb=short --override-ini="addopts="
======================= 144 passed, 1 warning in 11.38s ========================
```

All Story B (5) + Story C (1) + Story E pre-T-8 (4) gates GREEN — no regression.

### Native ticket tests grader/ + simulator/

```
$ cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/grader/ tests/agentic_evals/sales_agent/simulator/ -v --tb=short --override-ini="addopts=" -p no:randomly --timeout=60
============ 315 passed, 36 skipped, 1 warning in 113.38s (0:01:53) ============
```

- 315/315 PASS
- 36 skipped (intentional — sales_agent toolkit dependency `qualify_lead` / `tag_lead_status` belongs to separate sales_agent toolkit story per `personas-instrumented-runtime/05-guidelines.md`)

## Files touched (T-8 scope only)

| Path | Change | Loc count Δ |
|---|---|---|
| `backend/tests/agentic_evals/sales_agent/simulator/__init__.py` | EDIT — added 1 import + 1 entry to `__all__` (8 names total) + docstring cement update | +29 / -10 |
| `backend/tests/architecture/test_simulator_public_api_surface.py` | EDIT — `_EXPECTED_PUBLIC_NAMES` 7→8 + length 7→8 + 1 NEW `test_grade_transcript_maj_eval_is_callable` + docstring cement update | +24 / -10 |
| `backend/tests/architecture/test_grader_public_api_surface.py` | NEW — D-AG-16 cement, 8 tests | +200 |
| `backend/tests/architecture/test_grader_writes_eval_only_bucket.py` | NEW — H7 cement, 9 tests parametrized | +250 |

## Decisions applied (per 06-tickets.yaml T-8 `decisions_applicable`)

- **D10** — H9 expand 7→8 with single addition `grade_transcript_maj_eval` (cement preserved alphabetical sort).
- **D-AG-15** — H9 expand semantics: simulator/__init__.py is the canonical surface controller; grader/__init__.py is private namespace.
- **D-AG-16** — `grader/__init__.py.__all__ == []` cement enforced via NEW `test_grader_public_api_surface.py`. Asserts: empty list, length zero, no `grade_transcript_maj_eval` re-export from grader package.

## Hardening invariants preserved/added

- **H7 cost-bucket separation** — NEW `test_grader_writes_eval_only_bucket.py` static-analysis gate. Forbids: imports of `CopilotLlmCallModel`, `SalesAgentLlmCallModel`, `CampaignLlmCallModel`; string literals of `copilot_llm_call`, `sales_agent_llm_call`, `campaign_llm_call` outside docstrings (citations allowed via docstring-walk exemption). Sanity probe: at least one grader file references `eval_simulator_llm_call` / `EvalSimulatorLlmCallModel` / canonical write path.
- **H9 public API surface re-freeze** — simulator/__init__.py exports EXACTLY 8 names post Story E. Re-frozen at 8 via updated frozenset in `test_simulator_public_api_surface.py`. Future expansion requires explicit ratification cycle.
- **H10 frozen golden v1 byte-equal** — Story E NO toca `_fixtures/golden_v1_simulation_result.yaml`. Affirmative non-touch.

## Anti-duplication audit (per `.claude/rules/anti-duplication.md` Step 0)

- ✅ NO mirror of shared abstractions in T-8 changes (gates are pure static AST, no shared callbacks/observability/cost_recorder copies).
- ✅ NO new file under `grader/` introduces basename collision with `shared/agent_observability/*` (verified by pre-existing `test_grader_no_mirrors_shared.py` GREEN post-T-8).
- ✅ T-8 changes touch only test infrastructure (test-infra `production_code: false`); zero edits to `modules/copilot/`, `modules/sales_agent/`, `frontend/`, `shared/`.

## Cross-module reads

- READ-ONLY consume (no edit):
  - `backend/tests/agentic_evals/sales_agent/grader/_internal/maj_eval.py` — verifying `grade_transcript_maj_eval` is exported (callable async def). T-5 deliverable.
  - `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_llm_call.py` — verifying `__tablename__ = "eval_simulator_llm_call"`. R5 schema-mirror Story B.

## Spanish neutro audit

T-8 files contain ONLY English code + docstrings + comments + `voseo-allowed` magic comment for arch fitness reglas reference dialect strict (per `.claude/rules/spanish-text.md` § Magic comment escape — cited per Story B/C precedent).

No user-facing Spanish strings in scope. Compliance: PASS.

## Cementing summary

Post T-8, public API surface frozen at 8 names; arch fitness ratchet pattern enforces shrink-only. Story E will leverage T-9 (integration grader callback hook in `run_simulation`) consuming the 8-name surface as canonical entrypoint.

Final state: **tests-passing**.
