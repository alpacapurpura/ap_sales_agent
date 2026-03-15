---
phase: 03-crm-lifecycle-automation
plan: 02
subsystem: api
tags: [scoring-engine, lifecycle-transitions, event-bus, domain-events, tdd]

# Dependency graph
requires:
  - phase: 03-01
    provides: EventBus, ScoringConfig, LifecycleStage enum, lifecycle_transitions table, lifecycle columns on CustomerProfileModel
provides:
  - LifecycleService scoring engine with threshold-based stage transitions
  - JourneyEventRepository.track_event as canonical event write path
  - CustomerService.track_event wiring event write -> score recalculation -> stage transition
  - SaleService event emission via EventBus (SaleCompletedEvent)
  - Event handler registration for sale_completed and churn_detected
  - PipelineService.move_stage delegation to LifecycleService.force_stage
affects: [03-crm-lifecycle-automation, growth-studio-metrics]

# Tech tracking
tech-stack:
  added: []
  patterns: [service-layer-orchestration, event-driven-lifecycle, tdd-red-green]

key-files:
  created:
    - backend/src/modules/crm/application/services/lifecycle_service.py
    - backend/src/modules/crm/application/event_handlers.py
    - backend/tests/modules/crm/test_lifecycle_scoring.py
    - backend/tests/modules/crm/test_sale_lifecycle.py
  modified:
    - backend/src/modules/crm/application/services/customer_service.py
    - backend/src/modules/crm/application/services/sale_service.py
    - backend/src/modules/crm/application/services/lead_service.py
    - backend/src/modules/crm/infrastructure/repositories/customer_repository.py
    - backend/src/modules/crm/infrastructure/models/lifecycle_transition_model.py
    - backend/src/modules/crm/infrastructure/repositories/lifecycle_repository.py
    - backend/src/main.py
    - backend/tests/conftest.py
    - backend/tests/modules/crm/conftest.py

key-decisions:
  - "Service-layer orchestration: CustomerService.track_event calls repo.track_event + LifecycleService.recalculate_score (DDD boundary respected)"
  - "Fit score applied once via computed_traits flag to prevent re-adding on subsequent recalculations"
  - "LifecycleTransitionModel.metadata renamed to transition_metadata to avoid SQLAlchemy reserved attribute conflict"
  - "SaleService imports only shared EventBus + domain events (no CRM application service coupling)"

patterns-established:
  - "Journey event write hook: all event writes go through CustomerService.track_event which auto-triggers scoring"
  - "Sale event emission: SaleService -> EventBus.publish(SaleCompletedEvent, session) -> after-commit handler"
  - "Lifecycle audit: every stage change records LifecycleTransition with triggered_by and metadata"

requirements-completed: [CRM-01, CRM-02, CRM-03]

# Metrics
duration: 6min
completed: 2026-03-15
---

# Phase 3 Plan 2: Scoring Engine & Sale-Triggered Lifecycle Summary

**LifecycleService scoring engine with threshold transitions, EventBus-driven sale lifecycle changes, and automatic score recalculation on every journey_event write**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-15T18:58:49Z
- **Completed:** 2026-03-15T19:05:00Z
- **Tasks:** 2
- **Files modified:** 13

## Accomplishments
- Scoring engine sums journey_event weights + one-time fit score, applies thresholds (10/40/70) for SUBSCRIBER->LEAD->MQL->SQL transitions including backward and skip
- CUSTOMER stage profiles exempt from scoring-driven transitions
- Sale events trigger lifecycle changes via EventBus: CONVERSION->CUSTOMER, EXPANSION->lifetime_value, CHURNED->reactivation
- Every stage transition recorded in lifecycle_transitions audit table with triggered_by and metadata
- Journey event writes automatically trigger score recalculation and stage transitions (per locked decision)
- 21 passing tests (12 scoring + 9 sale lifecycle) covering all behaviors

## Task Commits

Each task was committed atomically:

1. **Task 1: LifecycleService scoring engine with threshold transitions** - `fd26da6` (feat)
2. **Task 2: Sale-triggered lifecycle transitions via EventBus** - `734ca25` (feat)

## Files Created/Modified
- `backend/src/modules/crm/application/services/lifecycle_service.py` - Scoring engine, threshold transitions, sale handler, force_stage
- `backend/src/modules/crm/application/event_handlers.py` - EventBus handler registration for sale_completed and churn_detected
- `backend/src/modules/crm/application/services/customer_service.py` - Added track_event() wiring event write -> scoring
- `backend/src/modules/crm/application/services/sale_service.py` - Added SaleCompletedEvent emission via EventBus
- `backend/src/modules/crm/application/services/lead_service.py` - PipelineService.move_stage delegates to LifecycleService.force_stage
- `backend/src/modules/crm/infrastructure/repositories/customer_repository.py` - Added JourneyEventRepository.track_event() canonical write path
- `backend/src/modules/crm/infrastructure/models/lifecycle_transition_model.py` - Renamed metadata -> transition_metadata
- `backend/src/modules/crm/infrastructure/repositories/lifecycle_repository.py` - Updated for transition_metadata column name
- `backend/src/main.py` - Registered CRM event handlers at startup
- `backend/tests/modules/crm/test_lifecycle_scoring.py` - 12 tests for scoring engine
- `backend/tests/modules/crm/test_sale_lifecycle.py` - 9 tests for sale lifecycle transitions

## Decisions Made
- Service-layer orchestration for DDD: CustomerService.track_event orchestrates repo write + lifecycle scoring (repository handles persistence only)
- Fit score stored as computed_traits flag to ensure one-time application
- LifecycleTransitionModel column renamed from `metadata` to `transition_metadata` (Python attr name) while keeping `metadata` as the DB column name via Column("metadata", ...) for backward compatibility
- SaleService decoupled from CRM services -- imports only shared EventBus and domain event classes

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Renamed metadata column in LifecycleTransitionModel**
- **Found during:** Task 1 (initial test run)
- **Issue:** SQLAlchemy raises InvalidRequestError because `metadata` is a reserved attribute name in the Declarative API
- **Fix:** Renamed Python attribute to `transition_metadata` with Column("metadata", ...) to keep DB column name unchanged
- **Files modified:** lifecycle_transition_model.py, lifecycle_repository.py, conftest.py
- **Verification:** All tests pass, no migration needed (DB column name unchanged)
- **Committed in:** fd26da6 (Task 1 commit)

**2. [Rule 3 - Blocking] Added ProductModel and SaleModel imports to test conftest**
- **Found during:** Task 2 (sale test requiring SaleModel relationship resolution)
- **Issue:** SaleModel has a relationship to ProductModel which wasn't imported in test conftest, causing InvalidRequestError
- **Fix:** Added imports to global tests/conftest.py db_engine fixture
- **Files modified:** backend/tests/conftest.py
- **Verification:** Sale lifecycle tests pass
- **Committed in:** 734ca25 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both fixes necessary for correctness. No scope creep.

## Issues Encountered
- Docker daemon not running in environment; tests executed using local venv Python instead

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Scoring engine and lifecycle transitions complete, ready for Plan 03 (decay/inactivity/churn)
- All 21 tests passing, audit trail verified
- EventBus wiring in place for churn_detected (placeholder handler registered)

---
*Phase: 03-crm-lifecycle-automation*
*Completed: 2026-03-15*
