---
phase: 05-stage-1-captura
plan: 01
subsystem: api, database
tags: [fastapi, sqlalchemy, pydantic, alembic, eventbus, crm, analytics, capture-metrics]

# Dependency graph
requires:
  - phase: 04-stage-0-attraction
    provides: MetricsService pattern, ChannelRegistry, attraction DTOs, MetricAggregationModel
  - phase: 03-crm-lifecycle-automation
    provides: EventBus, DomainEvent pattern, SaleCompletedEvent template, CustomerService.identify()
  - phase: 02-provider-adapter-infrastructure
    provides: ETL pipeline, OfficialMetricsRepository, MetricsCache, ConnectionPort
provides:
  - GET /metrics/capture endpoint returning CaptureDetailDTO
  - CaptureMetricsRepository for CRM-based lead count aggregation
  - ChannelCostSettingModel table for per-tenant cost configuration
  - CaptureCostService with CAL calculation and agency cost proration
  - LeadCapturedEvent domain event emitted from ChatOrchestrator
  - CHANNEL_TYPE_TO_CAPTURE_SLUG mapping for connections->analytics bridge
  - IdentityService.get_or_create_customer returns (profile, was_created) tuple
affects: [05-02-frontend-capture-panel, 08-stage-4-conversion, cost-tracking]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "CRM-based lead count via CaptureMetricsRepository (cross-module query pattern)"
    - "ChannelCostSettingModel for per-tenant cost configuration (reusable by all stages)"
    - "_CAPTURE_GROUP_MAP for channel type to group assignment"
    - "IdentityService returns (profile, was_created) tuple for event-conditional logic"

key-files:
  created:
    - backend/src/modules/analytics/application/dto/capture_dto.py
    - backend/src/modules/analytics/infrastructure/models/channel_cost_model.py
    - backend/src/modules/analytics/infrastructure/repositories/capture_repository.py
    - backend/src/modules/analytics/application/services/capture_cost_service.py
    - backend/alembic/versions/f5a6b7c8d9e0_add_channel_cost_settings.py
    - backend/tests/modules/analytics/test_capture_metrics.py
    - backend/tests/modules/analytics/test_lead_captured_event.py
    - backend/tests/modules/analytics/test_capture_cost.py
    - backend/tests/modules/analytics/test_cal_calculation.py
  modified:
    - backend/src/modules/analytics/application/services/metrics_service.py
    - backend/src/modules/analytics/api/metrics.py
    - backend/src/modules/analytics/infrastructure/models/__init__.py
    - backend/src/modules/crm/domain/events.py
    - backend/src/modules/crm/application/event_handlers.py
    - backend/src/modules/crm/application/services/identity_service.py
    - backend/src/modules/crm/infrastructure/repositories/customer_repository.py
    - backend/src/modules/sales_agent/application/orchestrator/chat.py
    - backend/src/tests/test_telegram_flow.py

key-decisions:
  - "IdentityService.get_or_create_customer changed to return (profile, was_created) tuple for conditional LeadCapturedEvent emission"
  - "CaptureMetricsRepository uses distinct profile_id as conversation approximation (JourneyEventModel lacks session_id)"
  - "Alembic migration created manually due to pre-existing duplicate revision ID issue (a1b2c3d4e5f6)"
  - "Agency cost proration distributes by category: organic_management, paid_management, video, full_service"

patterns-established:
  - "CRM-query repository in analytics module: wraps cross-module queries at infrastructure layer"
  - "Cost configuration model: per-tenant, per-channel, multiple cost types with proration support"
  - "_CAPTURE_GROUP_MAP pattern: channel_type -> group_key for 2-group capture structure"

requirements-completed: [CAP-02, CAP-03, CAP-04, CAP-05]

# Metrics
duration: 7min
completed: 2026-03-16
---

# Phase 5 Plan 01: Capture Backend Summary

**CRM-based lead count aggregation, cost configuration model with CAL calculation, LeadCapturedEvent emission from ChatOrchestrator, and GET /metrics/capture endpoint**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-16T03:54:31Z
- **Completed:** 2026-03-16T04:01:40Z
- **Tasks:** 3
- **Files modified:** 18

## Accomplishments
- GET /metrics/capture endpoint returns CaptureDetailDTO with web_infrastructure and ai_agent channel groups
- ChatOrchestrator emits LeadCapturedEvent only for NEW profiles with correct channel slug mapping
- ChannelCostSettingModel table created with per-tenant cost configuration and agency proration
- CAL (Cost per Lead) calculation with zero-division safety and configurable costs
- Mini funnel data (Visitors -> Leads) with Stage 0 visitor aggregation

## Task Commits

Each task was committed atomically:

1. **Task 0: Wave 0 test stubs** - `210043c` (test)
2. **Task 1: Domain contracts, cost model, CRM repository, Alembic migration** - `f6f0b3e` (feat)
3. **Task 2: MetricsService capture method, API endpoint, ChatOrchestrator event, EventBus handler** - `f70e993` (feat)

## Files Created/Modified
- `backend/src/modules/analytics/application/dto/capture_dto.py` - CaptureDetailDTO, CaptureHeaderKpisDTO, MiniFunnelDTO
- `backend/src/modules/analytics/infrastructure/models/channel_cost_model.py` - ChannelCostSettingModel with UniqueConstraint
- `backend/src/modules/analytics/infrastructure/repositories/capture_repository.py` - CRM lead count and conversation aggregation
- `backend/src/modules/analytics/application/services/capture_cost_service.py` - Cost retrieval, proration, CAL calculation
- `backend/src/modules/analytics/application/services/metrics_service.py` - Added get_capture_metrics() method
- `backend/src/modules/analytics/api/metrics.py` - Added GET /metrics/capture endpoint
- `backend/src/modules/crm/domain/events.py` - Added LeadCapturedEvent and CHANNEL_TYPE_TO_CAPTURE_SLUG
- `backend/src/modules/crm/application/event_handlers.py` - Added lead_captured handler registration
- `backend/src/modules/crm/application/services/identity_service.py` - get_or_create_customer returns (profile, was_created)
- `backend/src/modules/crm/infrastructure/repositories/customer_repository.py` - create_with_identity accepts lead_source, sets first_seen_at
- `backend/src/modules/sales_agent/application/orchestrator/chat.py` - Emits LeadCapturedEvent on new profile creation
- `backend/alembic/versions/f5a6b7c8d9e0_add_channel_cost_settings.py` - Migration for channel_cost_settings table

## Decisions Made
- **IdentityService tuple return:** Changed `get_or_create_customer` to return `(profile, was_created)` tuple so ChatOrchestrator can conditionally emit LeadCapturedEvent only for new profiles (avoiding double-counting)
- **Conversation approximation:** Used `distinct(profile_id)` as conversation count since JourneyEventModel lacks `session_id`. Added TODO for future session tracking.
- **Manual Alembic migration:** Created migration file manually instead of autogenerate due to pre-existing duplicate revision ID (a1b2c3d4e5f6) causing multiple heads. Stamped DB to correct revision before applying.
- **Agency proration categories:** Implemented 4 categories (organic_management, paid_management, video, full_service) with even distribution across connected channels per category.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] IdentityService return type change propagated to tests**
- **Found during:** Task 2 (ChatOrchestrator event emission)
- **Issue:** Changing `get_or_create_customer` to return a tuple broke all callers in `test_telegram_flow.py`
- **Fix:** Updated all 8 call sites in test file to destructure tuple with `customer, _ = ...`
- **Files modified:** `backend/src/tests/test_telegram_flow.py`
- **Verification:** All imports resolve without errors
- **Committed in:** f70e993 (Task 2 commit)

**2. [Rule 3 - Blocking] Pre-existing Alembic multiple heads prevented autogenerate**
- **Found during:** Task 1 (Alembic migration)
- **Issue:** Duplicate revision ID `a1b2c3d4e5f6` in two migration files caused multiple heads. `alembic upgrade head` and `alembic revision --autogenerate` both failed.
- **Fix:** Created migration manually with explicit revision chain. Stamped DB to correct head before applying new migration.
- **Files modified:** `backend/alembic/versions/f5a6b7c8d9e0_add_channel_cost_settings.py`
- **Verification:** `alembic upgrade f5a6b7c8d9e0` succeeded
- **Committed in:** f6f0b3e (Task 1 commit)

**3. [Rule 1 - Bug] Unused variable `latest_updated` in get_capture_metrics**
- **Found during:** Task 2 (ruff lint)
- **Issue:** Declared `latest_updated` variable following attraction pattern but capture uses `now.isoformat()` directly
- **Fix:** Removed unused variable
- **Files modified:** `backend/src/modules/analytics/application/services/metrics_service.py`
- **Committed in:** f70e993 (Task 2 commit)

---

**Total deviations:** 3 auto-fixed (2 bugs, 1 blocking)
**Impact on plan:** All fixes necessary for correctness and build success. No scope creep.

## Issues Encountered
- Pre-existing Alembic duplicate revision ID (`a1b2c3d4e5f6` used by both `add_etl_infrastructure` and `add_offer_value_level` migrations). Resolved by stamping DB and creating manual migration. Logged to deferred items.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Backend capture endpoint complete and ready for frontend CaptureDetail panel (Plan 02)
- Cost configuration model ready for settings UI (future plan)
- LeadCapturedEvent wiring complete -- new profiles will be tracked with lead_source from first contact

---
*Phase: 05-stage-1-captura*
*Completed: 2026-03-16*
