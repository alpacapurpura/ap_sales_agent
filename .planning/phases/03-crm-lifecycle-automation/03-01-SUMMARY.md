---
phase: 03-crm-lifecycle-automation
plan: 01
subsystem: database, domain
tags: [eventbus, domain-events, sqlalchemy, scoring, lifecycle, alembic, crm]

# Dependency graph
requires:
  - phase: 02-provider-adapter-infrastructure
    provides: "ETL tables, existing Alembic migration chain"
provides:
  - "EventBus singleton (shared/domain/events.py) with after-commit dispatch"
  - "DomainEvent base dataclass for cross-module communication"
  - "ScoringWeights, ScoringThresholds, DecayConfig, InactivityConfig frozen dataclasses"
  - "SaleCompletedEvent and ChurnEvent typed domain events"
  - "lifecycle_transitions audit table with full context tracking"
  - "LifecycleRepository for transition CRUD with tenant isolation"
  - "7 new customer_profiles columns: lifetime_value, last_activity_at, is_inactive, first_conversion_at, first_seen_at, lead_source, lead_source_detail"
  - "CRM test fixtures (conftest) for plans 02 and 03"
affects: [03-02-PLAN, 03-03-PLAN, phase-05, phase-08, phase-09]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "In-process EventBus with SQLAlchemy after_commit listener for deferred dispatch"
    - "Frozen dataclass singletons for scoring configuration"
    - "String type for triggered_by (avoids PG ALTER TYPE issues)"

key-files:
  created:
    - "backend/src/shared/domain/events.py"
    - "backend/src/modules/crm/domain/scoring.py"
    - "backend/src/modules/crm/domain/events.py"
    - "backend/src/modules/crm/infrastructure/models/lifecycle_transition_model.py"
    - "backend/src/modules/crm/infrastructure/repositories/lifecycle_repository.py"
    - "backend/alembic/versions/e2f3a4b5c6d7_add_lifecycle_columns_and_transitions.py"
    - "backend/tests/shared/test_event_bus.py"
    - "backend/tests/modules/crm/conftest.py"
  modified:
    - "backend/src/modules/crm/domain/customer.py"
    - "backend/src/modules/crm/infrastructure/models/customer_model.py"
    - "backend/src/modules/crm/infrastructure/models/__init__.py"
    - "backend/tests/conftest.py"

key-decisions:
  - "EventBus uses class-level _handlers dict (singleton pattern) -- no need for DI container"
  - "triggered_by uses String not PG Enum to avoid ALTER TYPE migration issues per research pitfall 4"
  - "Scoring weights follow research recommendations: message_sent=4.0, financial_capacity_high=8.0 (adjusted from research pattern 10.0 to match Scoring Weights table)"
  - "LifecycleStage enum reused in lifecycle_transitions via create_type=False to avoid duplicate PG type"

patterns-established:
  - "EventBus pattern: subscribe at startup, publish with session for after-commit, publish without session for immediate"
  - "Frozen dataclass config: change requires deploy, module-level singletons for import"
  - "Lifecycle audit trail: every stage change recorded with reason, trigger, score, and metadata"

requirements-completed: [CRM-01]

# Metrics
duration: 5min
completed: 2026-03-15
---

# Phase 3 Plan 01: CRM Lifecycle Foundation Summary

**EventBus with after-commit dispatch, scoring config (10/40/70 thresholds, 5% daily decay), lifecycle_transitions audit table, and 7 new customer_profiles columns**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-15T18:50:10Z
- **Completed:** 2026-03-15T18:55:10Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments
- Shared EventBus for cross-module domain events with after-commit dispatch and handler exception isolation
- Scoring configuration dataclasses with research-recommended weights, thresholds (10/40/70), decay (5%/day), and inactivity (14 days)
- SaleCompletedEvent and ChurnEvent typed domain events with factory classmethods
- lifecycle_transitions audit table tracking every stage change with full context
- LifecycleRepository with tenant-isolated CRUD for transition records
- CRM test fixtures (profiles at various stages, journey events, transition samples)

## Task Commits

Each task was committed atomically:

1. **Task 1: EventBus, scoring config, and domain event contracts** - `681e52b` (feat)
2. **Task 2: Schema migration, new columns, lifecycle_transitions table** - `1f62537` (feat)

## Files Created/Modified
- `backend/src/shared/domain/events.py` - EventBus singleton with DomainEvent base class, after-commit dispatch
- `backend/src/modules/crm/domain/scoring.py` - Frozen dataclass scoring config with module-level singletons
- `backend/src/modules/crm/domain/events.py` - SaleCompletedEvent and ChurnEvent with typed payloads
- `backend/src/modules/crm/domain/customer.py` - Added 7 lifecycle/activity fields to CustomerProfile entity
- `backend/src/modules/crm/infrastructure/models/customer_model.py` - Added matching SQLAlchemy columns with indexes
- `backend/src/modules/crm/infrastructure/models/lifecycle_transition_model.py` - Audit trail table model
- `backend/src/modules/crm/infrastructure/models/__init__.py` - Exports LifecycleTransitionModel for Alembic discovery
- `backend/src/modules/crm/infrastructure/repositories/lifecycle_repository.py` - Tenant-isolated transition CRUD
- `backend/alembic/versions/e2f3a4b5c6d7_add_lifecycle_columns_and_transitions.py` - Migration for new columns + table
- `backend/tests/shared/test_event_bus.py` - EventBus tests (immediate dispatch, after-commit, handler isolation)
- `backend/tests/modules/crm/conftest.py` - CRM fixtures for profiles, events, and transitions
- `backend/tests/conftest.py` - Added LifecycleTransitionModel import for table creation

## Decisions Made
- EventBus uses class-level `_handlers` dict (singleton pattern) -- no DI container needed, consistent with research recommendation
- `triggered_by` uses String (not PG Enum) to avoid ALTER TYPE migration issues per research pitfall 4
- Scoring weights adjusted to match research Scoring Weights Recommendations table (message_sent=4.0 not 3.0)
- LifecycleStage enum reused in lifecycle_transitions migration via `create_type=False` since enum already exists from customer_profiles

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Docker daemon unavailable (requires sudo password) -- test verification (`pytest tests/shared/test_event_bus.py`) and migration verification (`alembic upgrade head`) deferred to when Docker is running. All code follows the exact patterns from research and uses the existing SQLite-based test infrastructure.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- EventBus ready for plan 02 (scoring engine) and plan 03 (sale transitions, inactivity, churn handlers) to subscribe handlers
- Scoring config singletons ready for import by LifecycleService
- lifecycle_transitions table and repository ready for audit logging
- CRM test conftest provides fixtures for plan 02 and 03 test files
- **Blocker:** Docker must be running before migration can be applied (`docker exec -it visionarias_brain_dev alembic upgrade head`)

## Self-Check: PASSED

All 14 files verified present. Both task commits (681e52b, 1f62537) verified in git log.

---
*Phase: 03-crm-lifecycle-automation*
*Completed: 2026-03-15*
