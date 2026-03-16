---
phase: 08-stage-4-ventas
plan: 00
subsystem: testing
tags: [pytest, tdd, sales-metrics, wave-0]

# Dependency graph
requires:
  - phase: 07-stage-3-oportunidad
    provides: analytics module test patterns and conftest fixtures
provides:
  - 5 pytest stub files for VEN-01 through VEN-05 (RED state)
  - Shared fixtures sample_offer_id and sample_customer_id in conftest.py
affects: [08-01, 08-02]

# Tech tracking
tech-stack:
  added: []
  patterns: [lazy-import test stubs for TDD RED phase]

key-files:
  created:
    - backend/tests/modules/analytics/test_offer_read_port.py
    - backend/tests/modules/analytics/test_sales_dto.py
    - backend/tests/modules/analytics/test_sales_endpoint.py
    - backend/tests/modules/analytics/test_subscription_split.py
    - backend/tests/modules/analytics/test_cac_calculation.py
  modified:
    - backend/tests/modules/analytics/conftest.py

key-decisions:
  - "Lazy imports inside test functions to fail per-test not per-file"

patterns-established:
  - "Wave 0 test pattern: lazy imports in test bodies for RED-state stubs that fail individually"

requirements-completed: [VEN-01, VEN-02, VEN-03, VEN-04, VEN-05]

# Metrics
duration: 2min
completed: 2026-03-16
---

# Phase 8 Plan 00: Wave 0 Test Stubs Summary

**36 pytest stubs across 5 files covering sales DTOs, endpoint registration, subscription split, CAC calculation, and OfferReadPort ABC -- all RED state for TDD**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-16T15:03:46Z
- **Completed:** 2026-03-16T15:05:32Z
- **Tasks:** 1
- **Files modified:** 6

## Accomplishments
- 5 test files with 36 total tests collected via pytest --collect-only
- Shared fixtures (sample_offer_id, sample_customer_id) added to conftest.py
- All tests use lazy imports so each fails individually at the assertion level, not at collection time

## Task Commits

Each task was committed atomically:

1. **Task 1: Create 5 pytest stub files and extend conftest.py** - `f640026` (test)

## Files Created/Modified
- `backend/tests/modules/analytics/conftest.py` - Added sample_offer_id and sample_customer_id fixtures
- `backend/tests/modules/analytics/test_offer_read_port.py` - VEN-04: OfferReadPort ABC and impl tests (4 tests)
- `backend/tests/modules/analytics/test_sales_dto.py` - VEN-01: tier mapping, DTO structure, currency conversion (15 tests)
- `backend/tests/modules/analytics/test_sales_endpoint.py` - VEN-02: sales route registration, MetricsService method (4 tests)
- `backend/tests/modules/analytics/test_subscription_split.py` - VEN-03: subscription label logic (5 tests)
- `backend/tests/modules/analytics/test_cac_calculation.py` - VEN-05: StageCostService extension, repository, thresholds (6 tests)

## Decisions Made
- Lazy imports inside test functions (not at module level) so pytest collects all tests and each fails individually with clear ImportError when production code is missing

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 36 test stubs ready as RED targets for plans 08-01 (backend implementation) and 08-02 (frontend)
- Shared fixtures available for integration tests

---
*Phase: 08-stage-4-ventas*
*Completed: 2026-03-16*
