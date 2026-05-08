# T-2 Implementation Log — _pii_patterns LIFT + scan_goldens_pii.py + hook Section 9

**Story:** sales-agent-goldens-3-tenants-dataset  
**Ticket:** T-2  
**State:** pushed  
**Builder:** builder-backend Sonnet (R23 — production_code: false)  
**Date:** 2026-05-08

---

## § Skills Consulted

| Skill | Why invoked | Decision |
|---|---|---|
| `backend-expert` | Runtime quality checklist per Step 0 GATE | Anti-patterns: no `session.query()`, no `Column()`, no `print()`, no `Any`, no `git add .`. TDD RED→GREEN per layer. |
| `tessl__fastapi` | Backend implementation conventions | No new routes in T-2 (scripts-only scope). Confirmed Pydantic v2 patterns for any model usage. |
| `tessl__pytest-api-testing` | Test structure for `pytest.mark.no_eval` opt-out, fixture scoping, `tmp_path` isolation | Used `pytestmark = pytest.mark.no_eval` at module level; `pii_tmp_dir` fixture scoped per function; `subprocess.run` with `check=False` for CLI testing. |

*Note: T-2 is tooling/scripts only (`production_code: false`). No routes, no DB, no external HTTP calls. `tessl__graceful-degradation` not applicable.*

---

## § Scope Verified

CONTRACT/06-tickets.yaml T-2 scope: 7 deliverables in `backend/scripts/`, `scripts/git-hooks/`, `backend/tests/architecture/`, `backend/tests/agentic_evals/sales_agent/`, `backend/tests/scripts/`. No `modules/copilot/`, `modules/sales_agent/`, or `frontend/` touched.

---

## § Anti-Duplication Gate (Step 0)

Pre-LIFT grep evidence:
```
grep -rn "PATTERNS = " backend/scripts/ → 1 match in scan_seed_pii.py only
grep -rn "DNI_PE_GUARD_PREFIXES" backend/scripts/ → 0 matches
```
DRY threshold 2 consumers (scan_seed_pii + scan_goldens_pii) triggered LIFT per anti-duplication.md.

---

## § Default-Flip Detection (Step 0.5)

No `core/config.py` defaults touched. N/A.

---

## § CONTEXT-BRIEF.md Validation

`Validator pass:` confirmed populated (not `_pending_`). `Faithfulness flag:` not blocking.  
§11 LOW discrepancy noted: CONTEXT-BRIEF cited "8 categories" vs actual 9 in `scan_seed_pii.py`. Resolved: verified existing scanner, used 9 categories (email, phone_intl, dni_ar, cuit_ar, rut_cl, dni_pe, curp_mx, rfc_mx, url_internal_nicolify).

---

## § Implementation Summary

### Layer order (Inside-Out scripts, not DDD modules)

1. **NEW `backend/scripts/_pii_patterns.py`** — LIFT of `PATTERNS` dict + `DNI_PE_GUARD_PREFIXES` from `scan_seed_pii.py`. Exports `__all__ = ["DNI_PE_GUARD_PREFIXES", "PATTERNS"]`. `Final` typing. `# downstream-regression-na:` magic comment (scripts/ not src/shared/). 9 categories.

2. **EDIT `backend/scripts/scan_seed_pii.py`** — 1-line refactor: replaced 13-line local `PATTERNS = {...}` with `from _pii_patterns import PATTERNS  # noqa: E402`. All downstream logic preserved. Backward-compat: `_COMPILED` dict and all functions unchanged.

3. **NEW `backend/scripts/scan_goldens_pii.py`** — Standalone CLI goldens scanner. Key differences vs seed scanner: NO whitelist (D10 strict block), default path `backend/tests/agentic_evals/sales_agent/goldens/`, YAML traversal via `_yaml_strings()` returning `(yaml_path, value)` tuples, `_check_string()` with DNI_PE context guard, `_scan_file()` error handling. Exit codes 0/1/2. ruff import order fixed post-edit.

4. **EDIT `scripts/git-hooks/pre-commit`** — Section 1: added `*/agentic_evals/sales_agent/goldens/*)` to voseo path exclusion case pattern (es-AR dialect). Section 9 (appended): triggers on staged `goldens/**/*.yaml`, runs `scan_goldens_pii.py` against full goldens dir, mirrors Section 8 structure (VENV_PY guard, color codes, cat <<EOF error block). Final `exit 0` moved to end-of-file.

5. **NEW arch gate `backend/tests/architecture/test_pii_patterns_single_source.py`** — 8 tests: module exists, exports PATTERNS+guard, both consumers import from `_pii_patterns`, no duplicate dict literals, exactly 9 categories. Empty `PATTERNS_DICT_ALLOWLIST` (shrink-only ratchet). Uses `ast.parse` for static analysis + `importlib.util.spec_from_file_location` for dynamic dict inspection.

6. **NEW `backend/tests/agentic_evals/sales_agent/test_goldens_pii_scanner.py`** — 23 tests. `pytestmark = pytest.mark.no_eval` opts out of auto-eval marker in conftest. 12 parametrized adversarial cases (email×3, phone×3, id_docs×4, url×3), plus standalone group tests, clean synthetic YAML passes, error/empty/nonexistent path tests. `# voseo-allowed` magic comment for AR dialect fixtures in docstring.

7. **EXTEND `backend/tests/scripts/test_pre_commit_hook.py`** — 3 new tests: `test_blocks_pii_in_goldens` (Section 9), `test_section_8_seed_pii_still_works_post_lift` (backward-compat), `test_voseo_excludes_goldens_path` (Section 1 path exclusion). **Also fixed** existing `test_blocks_pii_in_seed_tenants` to copy `_pii_patterns.py` alongside refactored `scan_seed_pii.py` (backward-compat regression fix).

8. **NEW `backend/tests/_pii_fixtures/__init__.py`** — empty `__init__.py` for `_pii_fixtures/` package directory.

---

## § Cross-module reads

None. T-2 is tooling-only scope (scripts + tests). No agentic module reads required.

---

## § Quality Gate Results

| Gate | Result |
|---|---|
| `ruff check` | 0 errors (all checks passed) |
| `ruff format --check` | 2412 files already formatted |
| `mypy` new files | 0 errors (types, unused-ignore fixed) |
| `tests/architecture/test_pii_patterns_single_source.py` | 8/8 PASS |
| `tests/agentic_evals/sales_agent/test_goldens_pii_scanner.py` | 23/23 PASS |
| `tests/scripts/test_pre_commit_hook.py` | 16/16 PASS (13 existing + 3 new) |
| `tests/fixtures/eval/tenants/test_seed_pii_scanner.py` | backward-compat: 7 skipped (eval-marked, not a regression) |
| Full T-2 suite combined | 47/47 PASS |

---

## § Errors Encountered and Fixed

1. **ruff `I001` import sort** in `scan_goldens_pii.py` — fixed by `ruff --fix`.
2. **ruff `RUF002/RUF003` `×` multiplication sign** in test docstring/comment — replaced with `x`.
3. **ruff `F841` unused variable** `source` in arch test `test_pii_patterns_has_nine_categories` — removed unused assignment.
4. **mypy `unused-ignore`** on `spec.loader.exec_module(mod)` and `mod.PATTERNS` — replaced `# type: ignore[union-attr]` with explicit `types.ModuleType` annotation + `assert hasattr(loader, "exec_module")`. Used direct attribute access `mod.PATTERNS` with `dict[str, Any]` annotation (no ignore needed).
5. **ruff `B009` getattr with constant** — replaced `getattr(mod, "PATTERNS")` with `mod.PATTERNS`.
6. **Backward-compat regression**: `test_blocks_pii_in_seed_tenants` in `test_pre_commit_hook.py` broke after LIFT because it copies `scan_seed_pii.py` without `_pii_patterns.py`. Fixed by adding `_pii_patterns.py` copy to the test fixture setup.

---

## § Files Modified

| File | Status |
|---|---|
| `backend/scripts/_pii_patterns.py` | NEW |
| `backend/scripts/scan_seed_pii.py` | EDIT (LIFT refactor) |
| `backend/scripts/scan_goldens_pii.py` | NEW |
| `scripts/git-hooks/pre-commit` | EDIT (Section 1 + Section 9) |
| `backend/tests/architecture/test_pii_patterns_single_source.py` | NEW |
| `backend/tests/agentic_evals/sales_agent/test_goldens_pii_scanner.py` | NEW |
| `backend/tests/scripts/test_pre_commit_hook.py` | EXTEND (3 new + 1 fix) |
| `backend/tests/_pii_fixtures/__init__.py` | NEW |
