---
phase: 07-stage-3-oportunidad
plan: 01
subsystem: api
tags: [fastapi, sqlalchemy, shopify, eventbus, bottleneck-detection, metrics]

# Dependency graph
requires:
  - phase: 03-crm-lifecycle-automation
    provides: EventBus, LifecycleService, scoring weights, lifecycle_transitions
  - phase: 06-stage-2-nutricion
    provides: NurtureMetricsRepository pattern, StageCostService, STAGE_CHANNEL_MAP, MetricsService
provides:
  - GET /metrics/opportunity endpoint with OpportunityDetailDTO
  - OpportunityMetricsRepository for SQL pipeline counting
  - Shopify webhook handler with identity resolution and idempotency
  - AppointmentEvent domain event and EventBus bridge
  - CRM appointment event handlers (meeting_booked/completed/no_show)
  - PATCH /agenda/{id}/status endpoint for appointment status updates
  - Bottleneck detection for abandoned cart and meeting no-show rates
  - Channel registry entries for opportunity stage (5 channels, 3 groups)
affects: [07-02-frontend, 08-stage-4-ventas]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Bottleneck detection with configurable thresholds and severity levels"
    - "Shopify webhook tenant resolution via connections table with module-level cache"
    - "jsonb_extract_path_text for JSONB property queries (avoids getitem operator issues)"

key-files:
  created:
    - backend/src/modules/analytics/application/dto/opportunity_dto.py
    - backend/src/modules/analytics/infrastructure/repositories/opportunity_repository.py
    - backend/tests/modules/connections/test_shopify_webhook.py
    - backend/tests/modules/scheduling/test_appointment_events.py
    - backend/tests/modules/analytics/test_opportunity_metrics.py
  modified:
    - backend/src/modules/connections/api/marketing_webhooks.py
    - backend/src/modules/crm/domain/events.py
    - backend/src/modules/crm/application/event_handlers.py
    - backend/src/modules/scheduling/api/agenda.py
    - backend/src/modules/analytics/application/services/metrics_service.py
    - backend/src/modules/analytics/application/services/channel_registry.py
    - backend/src/modules/analytics/api/metrics.py

key-decisions:
  - "jsonb_extract_path_text used for JSONB property queries instead of getitem operator (SQLAlchemy JSONB operator compatibility with test environments)"
  - "Appointment event handlers create own SessionLocal (follows existing sale_completed handler pattern)"
  - "PATCH /agenda/{id}/status added for appointment status updates since no existing status-change endpoint existed"
  - "Abandoned cart detection deferred to background task (not in webhook handler per research recommendation)"

patterns-established:
  - "Bottleneck detection: threshold-based severity (normal/warning/critical) with Spanish-language tips"
  - "Shopify webhook handler: always return 200 OK, idempotency via checkout_token, tenant resolution from shop_domain"

requirements-completed: [OPO-02, OPO-03, OPO-04, OPO-05]

# Metrics
duration: 11min
completed: 2026-03-16
---

# Phase 7 Plan 1: Stage 3 Opportunity Backend Summary

**Shopify webhook event processing, scheduling EventBus bridge, OpportunityMetricsRepository, and GET /metrics/opportunity endpoint with bottleneck detection for abandoned cart and meeting no-show rates**

## Performance

- **Duration:** 11 min
- **Started:** 2026-03-16T09:15:05Z
- **Completed:** 2026-03-16T09:26:05Z
- **Tasks:** 3
- **Files modified:** 12

## Accomplishments
- Shopify webhook upgraded from stub to full event processing with identity resolution, idempotency, and scoring recalculation
- Scheduling module now publishes appointment events via EventBus; CRM creates meeting_booked/completed/no_show journey_events
- GET /metrics/opportunity returns OpportunityDetailDTO with 3 channel groups (checkout, payment_links, qualification) and bottleneck flags
- 17 tests passing across 3 test files covering webhook handlers, appointment events, and bottleneck threshold logic

## Task Commits

Each task was committed atomically:

1. **Task 1: Domain contracts, Shopify webhook handler, and Shopify webhook tests** - `54009e6` (feat)
2. **Task 2: Scheduling EventBus bridge, CRM listeners, appointment event tests** - `2793ce7` (feat)
3. **Task 3: OpportunityMetricsRepository, MetricsService method, API endpoint, channel registry** - `8f8873e` (feat)

## Files Created/Modified
- `backend/src/modules/analytics/application/dto/opportunity_dto.py` - OpportunityDetailDTO, BottleneckDTO, OpportunityHeaderKpisDTO
- `backend/src/modules/analytics/infrastructure/repositories/opportunity_repository.py` - SQL pipeline counting from journey_events and lifecycle_transitions
- `backend/src/modules/analytics/application/services/metrics_service.py` - get_opportunity_metrics method with bottleneck detection
- `backend/src/modules/analytics/application/services/channel_registry.py` - Opportunity stage entries in STAGE_CHANNEL_MAP
- `backend/src/modules/analytics/api/metrics.py` - GET /metrics/opportunity endpoint
- `backend/src/modules/connections/api/marketing_webhooks.py` - Shopify webhook handler with checkout/order event processing
- `backend/src/modules/crm/domain/events.py` - AppointmentEvent domain event class
- `backend/src/modules/crm/application/event_handlers.py` - Appointment event handlers and EventBus registration
- `backend/src/modules/scheduling/api/agenda.py` - PATCH /{id}/status endpoint with EventBus publishing
- `backend/tests/modules/connections/test_shopify_webhook.py` - 5 tests for Shopify webhook handler
- `backend/tests/modules/scheduling/test_appointment_events.py` - 4 tests for appointment EventBus bridge
- `backend/tests/modules/analytics/test_opportunity_metrics.py` - 8 tests for DTO construction and bottleneck thresholds

## Decisions Made
- Used `func.jsonb_extract_path_text` instead of JSONB `[]` operator for idempotency queries (avoids SQLAlchemy operator compatibility issues in test environments)
- Added PATCH /agenda/{id}/status endpoint since no appointment status-change endpoint existed
- Appointment event handlers follow existing sale_completed handler pattern: create own SessionLocal, commit, close
- Abandoned cart detection left as TODO for background task (per research: 1h detection window requires periodic check, not synchronous webhook processing)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed JSONB operator compatibility in idempotency queries**
- **Found during:** Task 1 (Shopify webhook handler)
- **Issue:** `JourneyEventModel.properties["checkout_token"].as_string()` and `cast(properties["checkout_token"], String)` both failed with "Operator 'getitem' is not supported" in test environment
- **Fix:** Used `func.jsonb_extract_path_text(JourneyEventModel.properties, "checkout_token")` which works reliably across all environments
- **Files modified:** backend/src/modules/connections/api/marketing_webhooks.py
- **Verification:** All 5 Shopify webhook tests pass
- **Committed in:** 54009e6 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Fix was necessary for test correctness. No scope creep.

## Issues Encountered
- SQLAlchemy model mapper initialization required pre-importing all related models (TenantModel, LeadModel, MessageModel, etc.) in test files to avoid lazy relationship resolution errors -- resolved by adding model imports at top of test files

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Backend endpoint fully functional, ready for frontend OpportunityDetail panel (Plan 02)
- All 3 channel groups populated with real CRM data
- Bottleneck detection tested with 8 threshold cases
- Shopify webhook ready for real traffic once dev store is configured

## Self-Check: PASSED

- All 6 key files verified present on disk
- All 3 task commits (54009e6, 2793ce7, 8f8873e) verified in git log

---
*Phase: 07-stage-3-oportunidad*
*Completed: 2026-03-16*
