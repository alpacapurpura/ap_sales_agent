---
phase: 03-crm-lifecycle-automation
plan: 03
subsystem: crm
tags: [inactivity-detection, score-decay, churn, lifecycle, arq, batch-processing]

# Dependency graph
requires:
  - phase: 03-01
    provides: EventBus, scoring config, lifecycle transitions model, ChurnEvent
  - phase: 03-02
    provides: LifecycleService with scoring engine, event_handlers registration
provides:
  - InactivityService with batch detection and exponential score decay
  - Churn event handler wiring (churn_detected -> CHURNED stage)
  - Manual stage override API (PUT /api/crm/pipeline/{profile_id}/stage)
  - Transition audit trail API (GET /api/crm/pipeline/{profile_id}/transitions)
  - ARQ cron job for daily inactivity detection at 4am UTC
affects: [04-funnel-analytics, growth-studio, sales-agent]

# Tech tracking
tech-stack:
  added: []
  patterns: [batch-processing-with-chunks, exponential-score-decay, idempotent-event-handlers]

key-files:
  created:
    - backend/src/modules/crm/application/services/inactivity_service.py
    - backend/tests/modules/crm/test_inactivity_detection.py
    - backend/tests/modules/crm/test_churn_detection.py
  modified:
    - backend/src/modules/crm/application/services/lifecycle_service.py
    - backend/src/modules/crm/application/event_handlers.py
    - backend/src/modules/crm/api/pipeline.py
    - backend/src/modules/analytics/workers/tasks.py
    - backend/src/modules/analytics/workers/settings.py
    - backend/tests/conftest.py

key-decisions:
  - "Score decay clamps to 0.0 when below 0.01 (exponential decay asymptotes, never reaches exact zero)"
  - "Churn handler uses event_name 'churn_detected' (matching ChurnEvent.create factory)"
  - "Pipeline API endpoints added to existing pipeline.py router (not a separate file)"
  - "Batch processing queries all profiles per tenant then filters in-memory (simpler than complex WHERE clause for both inactive and recovery)"

patterns-established:
  - "Idempotent event handling: check current state before applying transition (e.g., skip if already CHURNED)"
  - "Batch processing in chunks of 500 with flush-per-batch for memory efficiency"
  - "Score decay formula: new_score = lead_score * (1 - daily_rate)^days_inactive"

requirements-completed: [CRM-04, CRM-05]

# Metrics
duration: 5min
completed: 2026-03-15
---

# Phase 3 Plan 3: Inactivity Detection and Churn Handling Summary

**Batch inactivity detection with 5%/day exponential score decay, churn event handler for subscription cancellations, and manual stage override API with full audit trail**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-15T19:09:23Z
- **Completed:** 2026-03-15T19:14:39Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- InactivityService flags profiles inactive after 14 days with configurable threshold
- Exponential score decay (5%/day) with CUSTOMER exemption and backward stage transitions
- Churn event handler sets CHURNED stage idempotently from any lifecycle stage
- Manual override API (PUT) and transition audit trail API (GET) on pipeline router
- ARQ cron job registered for daily inactivity detection at 4am UTC
- 18 new unit tests, 39 total CRM tests passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Batch inactivity detection with score decay** - `69eedfc` (feat)
2. **Task 2: Churn detection and manual override API** - `29517e9` (feat)

_Both tasks followed TDD: RED (failing tests) -> GREEN (implementation) -> verify_

## Files Created/Modified
- `backend/src/modules/crm/application/services/inactivity_service.py` - Batch inactivity detection and score decay engine
- `backend/src/modules/crm/application/services/lifecycle_service.py` - Added handle_churn_event method
- `backend/src/modules/crm/application/event_handlers.py` - Churn handler wiring (replaced placeholder)
- `backend/src/modules/crm/api/pipeline.py` - Manual override and transitions API endpoints
- `backend/src/modules/analytics/workers/tasks.py` - run_inactivity_detection ARQ task
- `backend/src/modules/analytics/workers/settings.py` - Registered task and daily cron job
- `backend/tests/modules/crm/test_inactivity_detection.py` - 11 tests for inactivity and decay
- `backend/tests/modules/crm/test_churn_detection.py` - 7 tests for churn and manual override
- `backend/tests/conftest.py` - Fixed passlib mock for test environment

## Decisions Made
- Score decay clamps to 0.0 when below 0.01 (exponential decay asymptotically approaches but never reaches zero)
- Churn handler uses 'churn_detected' event_name matching ChurnEvent.create factory from Plan 01
- Pipeline API endpoints consolidated in existing pipeline.py (no separate router file)
- Batch processing uses offset pagination with 500-profile chunks

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed conftest.py passlib mock for test environment**
- **Found during:** Task 1 (test execution)
- **Issue:** conftest.py model imports silently failed due to missing passlib dependency, causing SQLAlchemy relationship resolution failures for ALL CRM tests
- **Fix:** Added sys.modules mock for passlib before model imports
- **Files modified:** backend/tests/conftest.py
- **Verification:** All 39 CRM tests pass
- **Committed in:** 69eedfc (Task 1 commit)

**2. [Rule 1 - Bug] Fixed score decay floor clamping**
- **Found during:** Task 1 (test_decay_clamps_to_floor)
- **Issue:** Exponential decay formula 10 * 0.95^365 produces ~7.4e-08, not exactly 0.0
- **Fix:** Added epsilon threshold (< 0.01) clamping to min_score in InactivityService
- **Files modified:** backend/src/modules/crm/application/services/inactivity_service.py
- **Verification:** test_decay_clamps_to_floor passes with exact 0.0 assertion
- **Committed in:** 69eedfc (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both fixes necessary for correctness. No scope creep.

## Issues Encountered
- Docker daemon not running in this environment; tests executed directly via python3 -m pytest (pre-existing dev environment limitation)

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- CRM lifecycle automation complete: scoring, transitions, inactivity, churn, manual override
- Phase 3 all 3 plans delivered: EventBus + scoring + lifecycle transitions + inactivity + churn
- Ready for Phase 4 (funnel analytics) which consumes CRM data for Growth Studio visualization

---
*Phase: 03-crm-lifecycle-automation*
*Completed: 2026-03-15*
