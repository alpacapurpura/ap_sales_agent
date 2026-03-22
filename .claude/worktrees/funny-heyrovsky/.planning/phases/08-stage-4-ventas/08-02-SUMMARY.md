---
phase: 08-stage-4-ventas
plan: 02
subsystem: ui
tags: [react, next.js, sales, offers, revenue, accordion, shadcn, react-query]

# Dependency graph
requires:
  - phase: 08-stage-4-ventas/08-01
    provides: SalesDetailDTO backend endpoint (GET /metrics/sales), OfferReadPort, SalesMetricsRepo
provides:
  - SalesDetail frontend panel with offer cards grouped by revenue type and tier
  - OfferCard, TierGroup, RevenueGroupHeader reusable components
  - useSalesDetail React Query hook
  - getSalesDetail API client with mock fallback
  - SalesDetail, OfferSaleData, RevenueGroupData, TierGroupData, SalesHeaderKpis, SalesBottleneck types
affects: [08-stage-4-ventas/08-03, frontend-testing, growth-studio-ui-polish]

# Tech tracking
tech-stack:
  added: []
  patterns: [offer-card-component, tier-accordion-grouping, revenue-group-header, sales-bottleneck-banner]

key-files:
  created:
    - frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/OfferCard.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/TierGroup.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/RevenueGroupHeader.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/SalesDetail.tsx
    - frontend/src/features/marketing-studio/hooks/useSalesDetail.ts
  modified:
    - frontend/src/features/marketing-studio/types/metrics.ts
    - frontend/src/features/marketing-studio/api/metrics-api.ts
    - frontend/src/features/marketing-studio/api/metrics-mock-data.ts
    - frontend/src/features/marketing-studio/components/metrics-dashboard/MetricsDashboard.tsx

key-decisions:
  - "SalesBottleneck uses separate type from BottleneckData (different shape: message/tip vs metricLabel/currentRate/threshold)"
  - "useSalesDetail follows useAuth+metricsApi pattern (matches existing hooks, not tenantId prop pattern from plan)"
  - "Dual currency formatting via Intl.NumberFormat with es-MX locale for MXN and en-US for USD"

patterns-established:
  - "OfferCard: tier indicator + name + sales count | revenue pattern for product-level metrics"
  - "TierGroup: Accordion wrapper for grouping offers by value tier"
  - "RevenueGroupHeader: summary header for Adquisicion/Expansion revenue groups"

requirements-completed: [VEN-01, VEN-02, VEN-03]

# Metrics
duration: 4min
completed: 2026-03-16
---

# Phase 08 Plan 02: Sales Frontend Summary

**SalesDetail panel with offer cards grouped by Adquisicion/Expansion revenue groups, tier accordions, dual-currency KPIs, MiniFunnel, and bottleneck banners**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-16T15:13:59Z
- **Completed:** 2026-03-16T15:18:21Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Full data layer: SalesDetail types, mapSalesResponse snake->camelCase mapper, getSalesDetail API with mock fallback, useSalesDetail React Query hook
- Component hierarchy: OfferCard (tier indicator, dual currency, source breakdown, conditional subscription split) -> TierGroup (accordion) -> RevenueGroupHeader -> SalesDetail panel
- Header KPIs with Revenue Total (dual currency), Nuevos Clientes, and CAC (with incomplete indicator)
- Empty state linking to Offer Studio, loading skeleton, and error state
- MetricsDashboard VENTAS routing wired to SalesDetail

## Task Commits

Each task was committed atomically:

1. **Task 1: Types, API client, mock data, and React Query hook** - `d69eb67` (feat)
2. **Task 2: OfferCard, TierGroup, RevenueGroupHeader, SalesDetail panel, and MetricsDashboard wiring** - `6d9aa88` (feat)

## Files Created/Modified
- `frontend/src/features/marketing-studio/types/metrics.ts` - Added Sales types (OfferSaleData, TierGroupData, RevenueGroupData, SalesHeaderKpis, SalesBottleneck, SalesDetail)
- `frontend/src/features/marketing-studio/api/metrics-api.ts` - Added mapSalesResponse mapper and getSalesDetail API method
- `frontend/src/features/marketing-studio/api/metrics-mock-data.ts` - Added MOCK_SALES_DETAIL, set VENTAS hasDetail: true
- `frontend/src/features/marketing-studio/hooks/useSalesDetail.ts` - React Query hook for sales data
- `frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/OfferCard.tsx` - Single offer card with tier indicator, dual currency, source breakdown, subscription split
- `frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/TierGroup.tsx` - Accordion wrapper for tier grouping
- `frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/RevenueGroupHeader.tsx` - Revenue group header (Adquisicion/Expansion)
- `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/SalesDetail.tsx` - Top-level sales detail panel with KPIs, MiniFunnel, bottleneck banners, revenue groups
- `frontend/src/features/marketing-studio/components/metrics-dashboard/MetricsDashboard.tsx` - Added VENTAS routing to SalesDetail

## Decisions Made
- SalesBottleneck uses a separate type from BottleneckData because the backend Sales DTO returns a different shape (type/severity/message/tip) vs the Opportunity BottleneckData (type/metricLabel/currentRate/severity/threshold/tip). Created SalesBottleneckBanner inline in SalesDetail.
- useSalesDetail follows the existing useAuth + metricsApi pattern (matching useOpportunityDetail) rather than the tenantId prop pattern from the plan, maintaining consistency with the codebase.
- Dual currency formatting uses Intl.NumberFormat with es-MX locale for MXN and en-US for USD display.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Adapted MiniFunnelData field names to match existing type**
- **Found during:** Task 1 (API mapper)
- **Issue:** Plan referenced sourceCount/targetCount but existing MiniFunnelData uses sourceValue/targetValue
- **Fix:** Mapped backend source_count/target_count to frontend sourceValue/targetValue
- **Files modified:** frontend/src/features/marketing-studio/api/metrics-api.ts
- **Committed in:** d69eb67 (Task 1 commit)

**2. [Rule 1 - Bug] Adapted hook pattern to match existing codebase**
- **Found during:** Task 1 (Hook creation)
- **Issue:** Plan specified tenantId prop pattern but existing hooks use useAuth + metricsApi.method(token) pattern
- **Fix:** Created useSalesDetail following useOpportunityDetail pattern exactly (useAuth, getToken, metricsApi.getSalesDetail)
- **Files modified:** frontend/src/features/marketing-studio/hooks/useSalesDetail.ts
- **Committed in:** d69eb67 (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (2 bugs - matching existing codebase patterns)
**Impact on plan:** Both fixes necessary for codebase consistency. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- SalesDetail panel fully functional with mock data
- Ready for 08-03 (Wave 0 tests or integration testing)
- Backend endpoint from 08-01 will serve real data when connected

---
*Phase: 08-stage-4-ventas*
*Completed: 2026-03-16*
