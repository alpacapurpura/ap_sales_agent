---
phase: 08-stage-4-ventas
plan: 01
subsystem: api
tags: [fastapi, sqlalchemy, pydantic, ddd, cross-module-port, cac, revenue-aggregation]

# Dependency graph
requires:
  - phase: 07-stage-3-oportunidad
    provides: OpportunityDetailDTO, BottleneckDTO, MetricsService pattern, StageCostService
provides:
  - OfferReadPort ABC and OfferReadPortImpl for cross-module offer data access
  - SalesMetricsRepository for CRM sales aggregation
  - SalesDetailDTO with CONVERSION/EXPANSION grouping, tier sub-groups, subscription split
  - GET /metrics/sales endpoint with full revenue pipeline
  - CAC calculation from stages 0-3 investment
  - Bottleneck detection for low conversion and high CAC ratio
affects: [08-stage-4-ventas, frontend-sales-detail]

# Tech tracking
tech-stack:
  added: []
  patterns: [OfferReadPort cross-module ABC pattern, value_level tier mapping, subscription split logic]

key-files:
  created:
    - backend/src/modules/analytics/application/dto/sales_dto.py
    - backend/src/modules/analytics/infrastructure/repositories/sales_metrics_repository.py
    - backend/src/modules/offer/application/services/offer_read_port_impl.py
    - backend/tests/modules/analytics/test_sales_endpoint.py
    - backend/tests/modules/analytics/test_cac_calculation.py
  modified:
    - backend/src/modules/analytics/domain/ports.py
    - backend/src/modules/analytics/application/services/metrics_service.py
    - backend/src/modules/analytics/application/services/stage_cost_service.py
    - backend/src/modules/analytics/api/metrics.py

key-decisions:
  - "OfferReadPort follows exact ConnectionPort ABC pattern: defined in analytics.domain.ports, implemented in offer module"
  - "SaleStage enum values (CONVERSION/EXPANSION) used directly for stage filtering (PG enum column)"
  - "LifecycleTransitionModel.profile_id used for SQL count (not customer_id as plan draft suggested)"
  - "Docstring reference to db.query() removed to satisfy DDD boundary test assertion"

patterns-established:
  - "OfferReadPort: cross-module data access via ABC + DTO projection (no ORM joins across modules)"
  - "VALUE_LEVEL_TO_TIER: 7 OfferValueLevel values mapped to 4 display tiers in backend only"
  - "Subscription split: CONVERSION + recurring pricing = new subscription, EXPANSION = renewal"
  - "CAC = get_total_funnel_investment(stages 0-3) / CONVERSION customer count"

requirements-completed: [VEN-01, VEN-02, VEN-03, VEN-04, VEN-05]

# Metrics
duration: 6min
completed: 2026-03-16
---

# Phase 08 Plan 01: Sales Backend Summary

**GET /metrics/sales endpoint with OfferReadPort cross-module integration, CONVERSION/EXPANSION revenue grouping, tier mapping, subscription split, CAC from stages 0-3, and bottleneck detection**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-16T15:04:08Z
- **Completed:** 2026-03-16T15:10:08Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- OfferReadPort ABC + OfferReadPortImpl bridges analytics and offer modules without DDD boundary violation
- SalesDetailDTO with complete data contract: header KPIs, mini funnel, CONVERSION/EXPANSION groups, tier sub-groups, per-offer cards with source breakdown and subscription split
- GET /metrics/sales endpoint with full pipeline: sales aggregation, offer enrichment, tier grouping, CAC calculation, bottleneck detection, Redis caching
- All 42 Wave 0 tests pass across 5 test files (VEN-01 through VEN-05)

## Task Commits

Each task was committed atomically:

1. **Task 1: OfferReadPort ABC, OfferReadPortImpl, and SalesDetailDTO contracts** - `9b1f8f0` (feat)
2. **Task 2: SalesMetricsRepository, StageCostService CAC extension, MetricsService.get_sales_metrics(), GET /metrics/sales** - `68514bd` (feat)

## Files Created/Modified
- `backend/src/modules/analytics/domain/ports.py` - Added OfferReadPort ABC and OfferReadDTO
- `backend/src/modules/offer/application/services/offer_read_port_impl.py` - OfferReadPortImpl querying ProductModel
- `backend/src/modules/analytics/application/dto/sales_dto.py` - All DTOs, tier mapping, exchange rates, subscription labels, bottleneck thresholds
- `backend/src/modules/analytics/infrastructure/repositories/sales_metrics_repository.py` - Sales aggregation queries (SQLAlchemy 2.0)
- `backend/src/modules/analytics/application/services/stage_cost_service.py` - Extended with get_total_funnel_investment
- `backend/src/modules/analytics/application/services/metrics_service.py` - Added get_sales_metrics with full pipeline
- `backend/src/modules/analytics/api/metrics.py` - Added GET /metrics/sales endpoint
- `backend/tests/modules/analytics/test_sales_endpoint.py` - Endpoint and repository tests
- `backend/tests/modules/analytics/test_cac_calculation.py` - CAC and bottleneck threshold tests

## Decisions Made
- OfferReadPort follows ConnectionPort ABC pattern exactly: defined in analytics.domain.ports, implemented in offer module
- SaleStatus.COMPLETED and SaleStage.CONVERSION/EXPANSION PG enum members used directly (not string comparisons)
- LifecycleTransitionModel.profile_id used for SQL count (model uses profile_id, not customer_id)
- Tenant display currency determined by most common Sale.currency (fallback USD)
- Free tier offers (level_0) excluded from sales panel entirely
- Unsold offers from catalog appear in adquisicion group with $0 revenue

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed LifecycleTransitionModel column reference**
- **Found during:** Task 2 (SalesMetricsRepository.get_total_sql_count)
- **Issue:** Plan referenced `LifecycleTransitionModel.customer_id` and `transitioned_at` but actual model uses `profile_id` and `occurred_at`
- **Fix:** Used correct column names from actual model
- **Files modified:** backend/src/modules/analytics/infrastructure/repositories/sales_metrics_repository.py
- **Verification:** Code references verified against LifecycleTransitionModel source
- **Committed in:** 68514bd (Task 2 commit)

**2. [Rule 1 - Bug] Fixed docstring triggering DDD boundary test**
- **Found during:** Task 2 (test_repository_uses_select_syntax test failure)
- **Issue:** Repository docstring contained "NOT db.query()" text which matched test assertion for forbidden pattern
- **Fix:** Rewrote docstring to avoid the literal string
- **Files modified:** backend/src/modules/analytics/infrastructure/repositories/sales_metrics_repository.py
- **Verification:** All 42 tests pass
- **Committed in:** 68514bd (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both auto-fixes necessary for correctness. No scope creep.

## Issues Encountered
None beyond the deviations documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Backend complete for Stage 4 Sales panel
- GET /metrics/sales returns SalesDetailDTO with all required groupings
- Frontend plan (08-02) can consume this endpoint directly
- OfferReadPort pattern established for any future cross-module data needs

---
*Phase: 08-stage-4-ventas*
*Completed: 2026-03-16*
