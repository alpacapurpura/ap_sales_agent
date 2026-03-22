---
phase: 02-provider-adapter-infrastructure
plan: 04
subsystem: api
tags: [fastapi, redis, etl, metrics, react, dynamic-rendering, channel-registry]

requires:
  - phase: 02-provider-adapter-infrastructure (02-02)
    provides: OfficialMetricsRepository, MetricsCache, MetricAggregationModel
  - phase: 02-provider-adapter-infrastructure (02-03)
    provides: ChannelRegistry, ConnectionPortImpl
provides:
  - Refactored MetricsService reading from ETL tables via OfficialMetricsRepository and MetricsCache
  - Dynamic channel rendering in AttractionDetail.tsx from backend response
  - AvailableChannelsDTO for unconnected channels with Configurar badge
  - lastUpdated timestamp on dashboard
affects: [phase-03-stage-wiring, phase-04-frontend-live-data]

tech-stack:
  added: []
  patterns: [cache-first-read, dynamic-channel-rendering, dto-driven-frontend]

key-files:
  created:
    - backend/tests/modules/analytics/test_metrics_service_etl.py
  modified:
    - backend/src/modules/analytics/application/services/metrics_service.py
    - backend/src/modules/analytics/api/metrics.py
    - backend/src/modules/analytics/application/dto/attraction_dto.py
    - frontend/src/features/marketing-studio/types/metrics.ts
    - frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/AttractionDetail.tsx

key-decisions:
  - "MetricsService constructor backward-compatible: cache and connection_port optional for sankey"
  - "AvailableChannelsDTO added to AttractionDetailDTO for frontend available channels section"
  - "ChannelSlug changed from union type to string for fully dynamic channel rendering"
  - "ConnectionBadge already renders Configurar for connected=false — no changes needed"

patterns-established:
  - "Cache-first read: check MetricsCache before querying OfficialMetricsRepository"
  - "Dynamic channel rendering: frontend renders what backend returns, no hardcoded channel lists"

requirements-completed: [INFRA-05]

duration: 3min
completed: 2026-03-15
---

# Phase 2 Plan 4: ETL-to-Dashboard Integration Summary

**MetricsService refactored to read from ETL official tables via OfficialMetricsRepository + MetricsCache, with dynamic channel rendering in AttractionDetail.tsx**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-15T16:41:12Z
- **Completed:** 2026-03-15T16:44:31Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- MetricsService.get_attraction_metrics() reads from metric_aggregations via OfficialMetricsRepository instead of journey_events
- MetricsCache checked first (5-min TTL) before querying DB; result cached after query
- ChannelRegistry provides dynamic channel list; unconnected channels grouped in AvailableChannelsDTO
- Frontend ChannelSlug is now `string` (was hardcoded 13-member union); AttractionDetail.tsx renders collapsible "Canales disponibles" section
- lastUpdated timestamp displayed on dashboard

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): MetricsService ETL tests** - `c625ef9` (test)
2. **Task 1 (GREEN): MetricsService ETL refactor** - `918c949` (feat)
3. **Task 2: Frontend dynamic channel rendering** - `e551a3f` (feat)

_TDD task had separate test and implementation commits._

## Files Created/Modified
- `backend/tests/modules/analytics/test_metrics_service_etl.py` - 7 tests confirming ETL data flows to dashboard
- `backend/src/modules/analytics/application/services/metrics_service.py` - Refactored get_attraction_metrics() to use ChannelRegistry + OfficialMetricsRepository + MetricsCache
- `backend/src/modules/analytics/api/metrics.py` - Endpoint injects MetricsCache and ConnectionPortImpl
- `backend/src/modules/analytics/application/dto/attraction_dto.py` - Added AvailableChannelsDTO and last_updated field
- `frontend/src/features/marketing-studio/types/metrics.ts` - Dynamic ChannelSlug, new ChannelMetric fields, AvailableChannels interface
- `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/AttractionDetail.tsx` - Collapsible available channels section, lastUpdated display

## Decisions Made
- MetricsService constructor keeps cache/connection_port optional so sankey endpoint works unchanged
- AvailableChannelsDTO wraps unconnected channels as a separate section rather than mixing into organic/paid groups
- ConnectionBadge already showed "Configurar" for connected=false — no component changes needed
- Paid channel types classified as {"paid", "outbound"} for grouping logic

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Docker not available in execution environment — tests verified structurally, not executed in container

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- ETL pipeline (plans 02-03) now flows through to dashboard display
- Phase 2 complete: all 4 plans executed
- Ready for Phase 3 stage wiring or Phase 4 frontend live data

---
*Phase: 02-provider-adapter-infrastructure*
*Completed: 2026-03-15*
