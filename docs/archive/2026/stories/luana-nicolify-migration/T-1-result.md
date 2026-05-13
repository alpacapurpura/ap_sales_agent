# T-1 Result — Baseline capture + codemod scripts + arch tests

## Status: DONE

All 4 acceptance criteria GREEN. T-1 closed. T-2..T-14 unblocked.

## Deliverables

| Deliverable | Status | Path |
|---|---|---|
| `baseline-be-tests.json` | ✓ DONE | `docs/product/stories/luana-nicolify-migration/baseline-be-tests.json` |
| `baseline-fe-tests.json` | ✓ DONE | `docs/product/stories/luana-nicolify-migration/baseline-fe-tests.json` |
| `scripts/codemod_be_imports.py` | ✓ DONE | `scripts/codemod_be_imports.py` |
| `scripts/codemod_fe_imports.ts` | ✓ DONE (template — T-8 completes) | `scripts/codemod_fe_imports.ts` |
| `scripts/test_delta_check.py` | ✓ DONE | `scripts/test_delta_check.py` |
| `test_no_legacy_src_paths.py` | ✓ DONE (SKIP until post-Story-10) | `backend/tests/architecture/` |
| `test_no_legacy_src_mock_paths.py` | ✓ DONE (1 PASS now, 1 SKIP) | `backend/tests/architecture/` |
| `test_consolidated_migration_idempotent.py` | ✓ DONE (SKIP until T-10) | `backend/tests/architecture/` |
| `test_delta_zero_enforcement.py` | ✓ DONE (5 PASS now) | `backend/tests/architecture/` |
| Visual baselines (5 PNGs) | ⚠ DEFERRED to T-11 | See rationale in T-1-impl-log.md §3 |
| `T-1-impl-log.md` | ✓ DONE | `docs/product/stories/luana-nicolify-migration/T-1-impl-log.md` |

## Acceptance Criteria

| ID | Description | Result |
|---|---|---|
| A1 | baseline-be-tests.json + baseline-fe-tests.json exist + parseable `.summary.failed` | ✓ PASS — BE: failed=8, FE: failed=0 |
| A2 | `python scripts/codemod_be_imports.py --dry-run --self-check` passes | ✓ PASS — "Self-check PASSED — all assertions green (idempotency + rewrites + stay-local)" |
| A3 | 4 new arch fitness tests exist + collectable (11 tests collected, skip GREEN by default) | ✓ PASS — 11 tests collected, 6 pass, 5 skip (correctly) |
| A4 | Existing arch fitness GREEN (no regression from new files) | ✓ PASS — 1069 passed, 6 skipped, 0 failures |

## Baseline counters

**BE (pytest-json-report):**
- Total collected: 10184 (12 deselected)
- Passed: 10018
- Failed: 8 (pre-existing, documented in T-1-impl-log.md §1)
- Skipped: 148

**FE (vitest --reporter=json):**
- Total: 2164
- Passed: 2164
- Failed: 0

## Halt triggers assessment

- Trigger #1 (MAPPING references missing luana-core package): NOT triggered. All 26 luana-core-* packages verified present in `/home/chris/luana-platform/core/`.
- Trigger #5 (unexpected new BE failures): NOT triggered. 8 failures < 100 threshold.
- Trigger #11 (stale mock path with no luana-core equivalent): NOT triggered in T-1. Baseline grep `patch('src.')` = 0.

## Decisions honored

- D5 (cap delta=0): baseline captured, delta scripts authored
- D1 (full big-bang scope): MAPPING covers all 18 modules + 11 shared
- D10 (Session 5 pre-auth): T-1 is tooling only, no production code touched

## Blockers / Escalations

None. T-2..T-14 unblocked.

## Next tickets

T-2 (brand + offer BE imports rewrite — Opus 4.7 per 05-guidelines.md §0) can now be spawned.
