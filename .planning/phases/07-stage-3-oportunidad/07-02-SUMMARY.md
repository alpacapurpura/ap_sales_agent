---
phase: 07-stage-3-oportunidad
plan: 02
subsystem: ui
tags: [react, nextjs, tailwind, tanstack-query, bottleneck-detection, metrics-dashboard]

# Dependency graph
requires:
  - phase: 07-stage-3-oportunidad
    plan: 01
    provides: GET /metrics/opportunity endpoint, OpportunityDetailDTO, bottleneck detection
  - phase: 06-stage-2-nutricion
    plan: 02
    provides: NurtureDetail panel pattern, ChannelGroup/ChannelRow components, MiniFunnel component
provides:
  - OpportunityDetail panel component with header KPIs, MiniFunnel, bottleneck banners
  - BottleneckBanner component with warning/critical severity rendering
  - MetricsDashboard OPORTUNIDAD stage routing
  - useOpportunityDetail React Query hook
  - Opportunity types (OpportunityDetail, BottleneckData, OpportunityHeaderKpis)
  - Mock data for opportunity stage (MOCK_OPPORTUNITY_DETAIL)
  - Channel widget extensions (icons, labels, Proximamente badges, inline bottleneck badges)
affects: [08-stage-4-ventas]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "BottleneckBanner: severity-based color system (yellow warning, red critical) with role=alert"
    - "Inline bottleneck badges on ChannelRow with threshold-based severity detection"
    - "Proximamente badge pattern extended to checkout-lp and link-enviado channels"

key-files:
  created:
    - frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/OpportunityDetail.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/BottleneckBanner.tsx
    - frontend/src/features/marketing-studio/hooks/useOpportunityDetail.ts
  modified:
    - frontend/src/features/marketing-studio/types/metrics.ts
    - frontend/src/features/marketing-studio/api/metrics-api.ts
    - frontend/src/features/marketing-studio/api/metrics-mock-data.ts
    - frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/ChannelGroup.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/ChannelRow.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/MetricsDashboard.tsx

key-decisions:
  - "Followed NurtureDetail layout exactly: flex items-center gap-6 for KPIs, space-y-2 for panel"
  - "Proximamente badge shows sourceLabel below channel name for context (not just icon + name)"
  - "Inline bottleneck badges computed per-row from metric values (abandonment_rate > 30, no_show/booked > 0.20)"

patterns-established:
  - "BottleneckBanner: reusable severity alert component for any threshold violation"
  - "Inline bottleneck badge detection pattern: compute severity from channel metrics in ChannelRow"

requirements-completed: [OPO-01, OPO-05]

# Metrics
duration: 4min
completed: 2026-03-16
---

# Phase 7 Plan 2: Stage 3 Opportunity Frontend Summary

**OpportunityDetail panel with 3 channel groups (Checkout, Links de Pago, Calificacion), header KPIs, MiniFunnel, bottleneck banners, and inline severity badges on abandoned-cart and meeting no-show rows**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-16T09:31:57Z
- **Completed:** 2026-03-16T09:35:57Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- OpportunityDetail panel renders 3 channel groups with header KPIs (Total SQLs, Conversion, Costo por SQL) and MiniFunnel (MQLs -> SQLs)
- BottleneckBanner component shows yellow warning or red critical alerts with AlertTriangle icon and actionable tips
- Inline bottleneck badges appear on abandoned-cart (abandonment rate > 30%) and meeting-booked (no-show rate > 20%) channel rows
- checkout-lp and link-enviado show Proximamente badge; MetricsDashboard routes OPORTUNIDAD to OpportunityDetail

## Task Commits

Each task was committed atomically:

1. **Task 1: Types, API client, mock data, hook, ChannelGroup/ChannelRow modifications** - `3065787` (feat)
2. **Task 2: OpportunityDetail panel, BottleneckBanner component, MetricsDashboard wiring** - `3b8adf6` (feat)

## Files Created/Modified
- `frontend/src/features/marketing-studio/types/metrics.ts` - Added OpportunityDetail, BottleneckData, OpportunityHeaderKpis types; extended GroupType
- `frontend/src/features/marketing-studio/api/metrics-api.ts` - Added getOpportunityDetail with mapOpportunityResponse
- `frontend/src/features/marketing-studio/api/metrics-mock-data.ts` - Added MOCK_OPPORTUNITY_DETAIL; set OPORTUNIDAD hasDetail=true
- `frontend/src/features/marketing-studio/hooks/useOpportunityDetail.ts` - React Query hook for opportunity data
- `frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/ChannelGroup.tsx` - Added checkout, payment_links, qualification buildSummary cases
- `frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/ChannelRow.tsx` - Added channel icons, metric labels, Proximamente badges, inline bottleneck badges
- `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/OpportunityDetail.tsx` - Main panel with KPIs, MiniFunnel, bottleneck banners, 3 channel groups
- `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/BottleneckBanner.tsx` - Warning/critical alert banner component
- `frontend/src/features/marketing-studio/components/metrics-dashboard/MetricsDashboard.tsx` - Added OPORTUNIDAD routing to OpportunityDetail

## Decisions Made
- Matched NurtureDetail layout exactly (flex items-center gap-6 for header KPIs, space-y-4 p-4 for loading skeleton) for visual consistency
- Extended Proximamente badge to show sourceLabel below channel name for better context
- Inline bottleneck badges are computed directly from metric values in ChannelRow (no prop drilling needed)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Stage 3 Opportunity fully functional with mock data, ready for backend API integration
- All 4 stages (Atraccion, Captura, Nutricion, Oportunidad) now have working detail panels
- Next phase (Stage 4 Ventas) can follow the same pattern established here

---
*Phase: 07-stage-3-oportunidad*
*Completed: 2026-03-16*
