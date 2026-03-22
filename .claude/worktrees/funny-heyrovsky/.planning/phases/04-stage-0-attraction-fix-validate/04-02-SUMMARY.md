---
phase: 04-stage-0-attraction-fix-validate
plan: 02
subsystem: api
tags: [metrics-service, multi-metric, attraction-dashboard, channel-row, stale-ux, refresh-endpoint, pydantic, react]

# Dependency graph
requires:
  - phase: 04-stage-0-attraction-fix-validate
    provides: Multi-metric DTO contracts (MetricValueDTO, ChannelMetricDTO), 6 provider adapters, STAGE_CHANNEL_MAP with metric_names
provides:
  - MetricsService multi-metric aggregation with 4 channel groups
  - POST /metrics/attraction/refresh/{channel_slug} with 15-min cooldown
  - Frontend multi-metric ChannelRow with stale indicator and refresh button
  - Frontend ChannelGroup with group-type-specific header totals
  - AttractionDetail with 4 groups and Ultima actualizacion header
  - Updated API mapper and mock data for multi-metric structure
affects: [04-03-PLAN, frontend-dashboard, metrics-api]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "4-group channel classification: organic_social, ga4_search, paid, outbound via _GROUP_MAP"
    - "Error message classification: extraction run errors mapped to user-facing Spanish strings"
    - "MetricDisplay component: renders individual metric with label, value, optional breakdown"
    - "Group totals computed as dict keyed by metric name (sum across channels)"

key-files:
  created: []
  modified:
    - backend/src/modules/analytics/application/services/metrics_service.py
    - backend/src/modules/analytics/api/metrics.py
    - frontend/src/features/marketing-studio/types/metrics.ts
    - frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/ChannelRow.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/ChannelGroup.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/AttractionDetail.tsx
    - frontend/src/features/marketing-studio/api/metrics-api.ts
    - frontend/src/features/marketing-studio/api/metrics-mock-data.ts

key-decisions:
  - "Channel grouping via _GROUP_MAP dict: social->organic_social, search/direct->ga4_search, paid->paid, outbound->outbound"
  - "Stale detection reads ExtractionRunRepository.get_latest() per provider (cached in provider_runs dict)"
  - "Error messages mapped from extraction error text to Spanish: token_expired->Token expirado, rate_limited->Reintentando, etc."
  - "Refresh endpoint routes channel_slug to provider_name via _SLUG_TO_PROVIDER map"
  - "Frontend ChannelRow renders metrics side-by-side with MetricDisplay sub-component"
  - "Available channels render only icon + name + Configurar badge (no metrics)"

patterns-established:
  - "Multi-metric rendering: MetricDisplay component reusable for any metric type"
  - "Group-type-specific summaries: buildSummary() switch on GroupType for header text"
  - "Stale UX pattern: yellow badge + last-known timestamp + refresh button with cooldown"

requirements-completed: [ATR-02, ATR-03, ATR-04, ATR-05]

# Metrics
duration: 4min
completed: 2026-03-15
---

# Phase 4 Plan 2: Multi-Metric Service Aggregation and Frontend Dashboard Redesign Summary

**MetricsService returns 4-group multi-metric DTOs with stale detection, frontend ChannelRow renders per-channel-type metric layouts with yellow desactualizado indicator and refresh button**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-15T20:36:23Z
- **Completed:** 2026-03-15T20:40:53Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- MetricsService.get_attraction_metrics() builds multi-metric ChannelMetricDTO objects grouped into organic_social, ga4_search, paid, outbound with dict-based totals
- Stale detection from ExtractionRun status with user-facing error message classification
- POST /metrics/attraction/refresh/{channel_slug} endpoint with 15-minute cooldown
- Frontend ChannelRow redesigned for multi-metric display with MetricDisplay sub-component, stale indicator, refresh button, no-data state
- ChannelGroup headers show group-specific totals (Alcance+Engagement for social, Sesiones+Usuarios for search, etc.)
- AttractionDetail renders 4 sections + available channels + Ultima actualizacion timestamp header

## Task Commits

Each task was committed atomically:

1. **Task 1: MetricsService multi-metric aggregation and API update** - `38c5a14` (feat)
2. **Task 2: Frontend multi-metric ChannelRow, ChannelGroup, and AttractionDetail redesign** - `25093cc` (feat)

## Files Created/Modified
- `backend/src/modules/analytics/application/services/metrics_service.py` - Multi-metric aggregation, 4-group classification, stale detection, error mapping
- `backend/src/modules/analytics/api/metrics.py` - Added refresh endpoint with 15-min cooldown
- `frontend/src/features/marketing-studio/types/metrics.ts` - MetricValue interface, updated ChannelMetric/TrafficGroup/AttractionDetail types
- `frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/ChannelRow.tsx` - Multi-metric layout, stale badge, refresh button, no-data state
- `frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/ChannelGroup.tsx` - Group-type-specific header totals
- `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/AttractionDetail.tsx` - 4 groups + available section + timestamp header
- `frontend/src/features/marketing-studio/api/metrics-api.ts` - Updated mapper for multi-metric response shape
- `frontend/src/features/marketing-studio/api/metrics-mock-data.ts` - Mock data with multi-metric structure

## Decisions Made
- Channel grouping uses _GROUP_MAP dict mapping channel_type strings to group keys
- Stale detection queries ExtractionRunRepository per provider with result caching to avoid repeated DB hits
- Error messages mapped from extraction error keywords to Spanish user-facing strings
- Refresh endpoint maps channel_slug to provider_name (multiple slugs can share a provider)
- Manual channels (cold-contact) cannot be refreshed via API (returns 400)
- Frontend MetricDisplay component renders label + value + optional breakdown as reusable sub-component
- Engagement breakdown shown as small text below the total (e.g., "likes 2000, comentarios 800")

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Full multi-metric pipeline from MetricsService through API to frontend dashboard is wired
- Ready for Plan 03: validation script comparing ETL output against real provider data
- Mock data updated for development without live API connections

## Self-Check: PASSED

- 8/8 files verified present
- 2/2 commits verified in git log
