---
phase: 09-stages-5-6-adoption-expansion
plan: 02
subsystem: api, ui
tags: [fastapi, react, expansion, churn, mrr, ltv, crm, metrics]

# Dependency graph
requires:
  - phase: 08-stage-4-ventas
    provides: SalesMetricsRepository pattern, OfferReadPort, convert_to_usd, BottleneckDTO, MiniFunnelDTO
  - phase: 03-crm-lifecycle-automation
    provides: LifecycleTransitionModel, LifecycleStage.CHURNED, CustomerProfileModel
provides:
  - GET /metrics/expansion endpoint returning ExpansionDetailDTO
  - ExpansionMetricsRepository with renewal/upsell classification via JSONB metadata
  - ExpansionDetail frontend panel with tooltipped KPIs and three color-coded groups
  - KpiTooltip reusable component for future stages
  - MOCK_EXPANSION_DETAIL for dev-mode rendering
affects: [10-stage-7-evangelization, 11-ui-polish]

# Tech tracking
tech-stack:
  added: []
  patterns: [jsonb_extract_path_text for renewal classification, tiered bottleneck detection, KpiTooltip with shadcn Tooltip]

key-files:
  created:
    - backend/src/modules/analytics/application/dto/expansion_dto.py
    - backend/src/modules/analytics/infrastructure/repositories/expansion_repository.py
    - frontend/src/features/marketing-studio/hooks/useExpansionDetail.ts
    - frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/KpiTooltip.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/ExpansionGroup.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/ExpansionOfferRow.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/ExpansionDetail.tsx
  modified:
    - backend/src/modules/analytics/application/services/metrics_service.py
    - backend/src/modules/analytics/application/services/channel_registry.py
    - backend/src/modules/analytics/api/metrics.py
    - frontend/src/features/marketing-studio/types/metrics.ts
    - frontend/src/features/marketing-studio/api/metrics-api.ts
    - frontend/src/features/marketing-studio/api/metrics-mock-data.ts
    - frontend/src/features/marketing-studio/components/metrics-dashboard/MetricsDashboard.tsx

key-decisions:
  - "Renewal classification via jsonb_extract_path_text(metadata_info, 'event_name') = 'subscription_cycle'"
  - "Churn lost revenue estimated from last EXPANSION sale per churned customer using window function"
  - "BottleneckBanner reused from OpportunityDetail via BottleneckData type casting"
  - "KpiTooltip as standalone reusable component (not inlined) for future stage panels"

patterns-established:
  - "Expansion group pattern: colored groups with per-offer breakdown rows and aggregate totals"
  - "KpiTooltip pattern: shadcn Tooltip with Info icon for plain-Spanish metric explanations"

requirements-completed: [EXP-01, EXP-02, EXP-03, EXP-04]

# Metrics
duration: 8min
completed: 2026-03-16
---

# Phase 9 Plan 02: Expansion Panel Summary

**Expansion (Stage 6) panel with Net MRR / LTV / Churn KPIs, three revenue groups (Retencion, Crecimiento, Cancelaciones), JSONB-based renewal classification, and tiered churn bottleneck detection**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-16T17:13:48Z
- **Completed:** 2026-03-16T17:22:40Z
- **Tasks:** 2
- **Files modified:** 14

## Accomplishments
- GET /metrics/expansion endpoint with ExpansionMetricsRepository classifying renewals vs upsells from SaleModel.metadata_info JSONB
- Churn data sourced from LifecycleTransitionModel (to_stage=CHURNED) joined with last EXPANSION sale for lost revenue estimation
- Header KPIs: Net MRR (retained + expansion - lost), Avg LTV from CustomerProfileModel, Churn Rate with tiered thresholds (3% warning, 5% critical)
- ExpansionDetail frontend panel with KpiTooltip (plain-Spanish hints), MiniFunnel, three color-coded groups, and BottleneckBanner integration
- Red visual treatment on Cancelaciones group (border-l-2 border-red-200) with negative revenue prefix

## Task Commits

Each task was committed atomically:

1. **Task 1: Expansion backend -- DTOs, repository, MetricsService method, channel registry, API endpoint** - `179c7f8` (feat)
2. **Task 2: Expansion frontend -- types, API, mock data, hooks, components, MetricsDashboard routing** - `6609d1b` (feat)

## Files Created/Modified
- `backend/src/modules/analytics/application/dto/expansion_dto.py` - ExpansionDetailDTO, ExpansionHeaderKpisDTO, ExpansionGroupDTO, ExpansionOfferDTO
- `backend/src/modules/analytics/infrastructure/repositories/expansion_repository.py` - CRM queries for renewals, upsells, churn, LTV, active customers
- `backend/src/modules/analytics/application/services/metrics_service.py` - get_expansion_metrics method with cache-first pattern
- `backend/src/modules/analytics/application/services/channel_registry.py` - expansion channels in STAGE_CHANNEL_MAP
- `backend/src/modules/analytics/api/metrics.py` - GET /expansion endpoint
- `frontend/src/features/marketing-studio/types/metrics.ts` - Expansion type interfaces
- `frontend/src/features/marketing-studio/api/metrics-api.ts` - mapExpansionResponse, getExpansionDetail
- `frontend/src/features/marketing-studio/api/metrics-mock-data.ts` - MOCK_EXPANSION_DETAIL
- `frontend/src/features/marketing-studio/hooks/useExpansionDetail.ts` - react-query hook
- `frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/KpiTooltip.tsx` - Reusable tooltip KPI label
- `frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/ExpansionGroup.tsx` - Group with aggregate + offer rows
- `frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/ExpansionOfferRow.tsx` - Per-offer row with dual currency
- `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/ExpansionDetail.tsx` - Full expansion panel
- `frontend/src/features/marketing-studio/components/metrics-dashboard/MetricsDashboard.tsx` - EXPANSION routing

## Decisions Made
- Renewal vs upsell classification done via `jsonb_extract_path_text(metadata_info, 'event_name')` -- subscription_cycle = renewal, everything else = upsell
- Churn lost revenue calculated from last EXPANSION sale amount per churned customer using SQL window function (row_number over partition by customer_id)
- KpiTooltip created as standalone reusable component rather than inline, anticipating reuse in future panels
- BottleneckBanner from OpportunityDetail reused via type casting for expansion bottlenecks

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Stages 5 and 6 panels complete, dashboard now covers attraction through expansion
- Stage 7 (Evangelization) can proceed when Phase 10 planning begins
- KpiTooltip component available for any future panel needing tooltipped KPIs

---
*Phase: 09-stages-5-6-adoption-expansion*
*Completed: 2026-03-16*
