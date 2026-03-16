---
phase: 05-stage-1-captura
plan: 02
subsystem: ui
tags: [react, nextjs, tailwind, tanstack-query, metrics-dashboard, capture-panel]

# Dependency graph
requires:
  - phase: 05-stage-1-captura-01
    provides: CaptureDetailDTO backend endpoint (/api/v1/analytics/metrics/capture)
  - phase: 04-stage-0-attraction
    provides: ChannelGroup, ChannelRow, MetricsDashboard component patterns
provides:
  - CaptureDetail panel component with MiniFunnel and CostLink widgets
  - useCaptureDetail hook for capture metrics data fetching
  - CaptureDetail types (CaptureHeaderKpis, MiniFunnelData, CaptureDetail)
  - Mock capture data for development/fallback
affects: [06-stage-2-activation, 11-polish]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Stage detail panel pattern: hook + panel + reusable channel widgets"
    - "MiniFunnel cross-stage conversion visualization"
    - "CostLink inline configuration prompt for unconfigured costs"
    - "ChannelRow secondary line for conversation volume"

key-files:
  created:
    - frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/CaptureDetail.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/MiniFunnel.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/CostLink.tsx
    - frontend/src/features/marketing-studio/hooks/useCaptureDetail.ts
  modified:
    - frontend/src/features/marketing-studio/types/metrics.ts
    - frontend/src/features/marketing-studio/api/metrics-api.ts
    - frontend/src/features/marketing-studio/api/metrics-mock-data.ts
    - frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/ChannelGroup.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/ChannelRow.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/MetricsDashboard.tsx

key-decisions:
  - "Reused TrafficGroup type for both web_infrastructure and ai_agent capture groups"
  - "CostLink defaults to /growth/settings/costs route for cost configuration"
  - "ChannelRow conversations secondary line uses 10px muted text below leads metric"

patterns-established:
  - "MiniFunnel: reusable cross-stage conversion arrow (source -> target = %)"
  - "CostLink: inline 'Configurar costo' prompt for channels without cost data"
  - "Stage detail panel lifecycle: loading skeleton -> error state -> data render"

requirements-completed: [CAP-01]

# Metrics
duration: 8min
completed: 2026-03-16
---

# Phase 5 Plan 02: Capture Detail Panel Summary

**CaptureDetail panel with MiniFunnel conversion arrow, 3 header KPIs, and channel groups for Web Infrastructure and AI Agent channels**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-16T04:10:00Z
- **Completed:** 2026-03-16T04:18:00Z
- **Tasks:** 3 (2 auto + 1 checkpoint approved)
- **Files modified:** 10

## Accomplishments
- CaptureDetail panel renders when clicking CAPTURA stage card, replacing PlaceholderDetail
- MiniFunnel shows cross-stage conversion visualization: Visitantes -> Leads = X%
- Panel header displays 3 KPIs: TOTAL LEADS, CONVERSION, COSTO POR LEAD
- Two channel groups: Infraestructura Web (landing-form, mailerlite) and Agente AI Conversacional (ig-dm, fb-messenger, tiktok-dm, whatsapp-inbound)
- AI Agent channels show "de X conversaciones" secondary line
- CostLink component shows "Configurar costo" for unconfigured cost channels

## Task Commits

Each task was committed atomically:

1. **Task 1: Types, API layer, hook, and mock data for capture** - `462e270` (feat)
2. **Task 2: CaptureDetail panel, MiniFunnel, CostLink, and ChannelGroup/Row extensions** - `a9ff4c0` (feat)
3. **Task 3: Visual verification** - checkpoint approved by user (no commit)

## Files Created/Modified
- `frontend/src/features/marketing-studio/types/metrics.ts` - Added CaptureDetail, CaptureHeaderKpis, MiniFunnelData types; extended GroupType union
- `frontend/src/features/marketing-studio/api/metrics-api.ts` - Added getCaptureDetail method and mapCaptureResponse mapper
- `frontend/src/features/marketing-studio/api/metrics-mock-data.ts` - Added MOCK_CAPTURE_DETAIL with 2 web + 4 AI agent channels; set CAPTURA hasDetail: true
- `frontend/src/features/marketing-studio/hooks/useCaptureDetail.ts` - TanStack Query hook for capture detail data
- `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/CaptureDetail.tsx` - Main capture detail panel with KPIs, MiniFunnel, and channel groups
- `frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/MiniFunnel.tsx` - Cross-stage conversion arrow visualization
- `frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/CostLink.tsx` - Inline cost configuration link
- `frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/ChannelGroup.tsx` - Extended with web_infrastructure and ai_agent summary formats
- `frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/ChannelRow.tsx` - Added capture channel icons and conversations secondary line
- `frontend/src/features/marketing-studio/components/metrics-dashboard/MetricsDashboard.tsx` - Routed CAPTURA stage to CaptureDetail component

## Decisions Made
- Reused TrafficGroup type for both capture groups (web_infrastructure and ai_agent) to avoid type duplication
- CostLink defaults to /growth/settings/costs route (will be wired when settings page is built)
- Conversations secondary line rendered at 10px muted text for visual hierarchy

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Capture detail panel complete, ready for Phase 6 (Stage 2 Activation)
- MiniFunnel and CostLink components are reusable for future stage detail panels
- ChannelRow conversation secondary line pattern available for other stages

## Self-Check: PASSED

All files verified present. All commits verified in git log.

---
*Phase: 05-stage-1-captura*
*Completed: 2026-03-16*
