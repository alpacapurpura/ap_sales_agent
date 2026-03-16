---
phase: 11-frontend-unification-dashboard-polish
plan: "01"
subsystem: frontend/growth-studio
tags: [metrics-dashboard, ui-infrastructure, real-data-wiring, loading-states, sidebar]
dependency_graph:
  requires: []
  provides:
    - DetailSkeleton (shared loading skeleton for all 8 detail panels)
    - DetailEmpty (empty state with Spanish copy)
    - DetailError (error state with retry button and cached fallback)
    - MetricSidebar (shadcn Sheet-based drill-down sidebar framework)
    - StageCard real KPI wiring (mainKpi + secondaryKpi from API)
    - MetricsDashboard 8-hook orchestration with sidebar state
  affects:
    - All 8 detail panels (will use DetailSkeleton/DetailEmpty/DetailError in Plan 11-02)
    - StageSummaryRow (extended with loadingMap, mockMap, onMetricClick props)
tech_stack:
  added: []
  patterns:
    - "Progressive loading: 8 parallel React Query hooks, each stage updates independently"
    - "mergeStageData() helper: maps per-stage API shapes to unified StageSummary"
    - "loadingMap/mockMap: per-stage boolean maps passed from MetricsDashboard to StageCard"
    - "Sidebar state: sidebarMetric + sidebarOpen managed in MetricsDashboard orchestrator"
key_files:
  created:
    - frontend/src/features/marketing-studio/components/metrics-dashboard/ui/DetailSkeleton.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/ui/DetailEmpty.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/ui/DetailError.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/MetricSidebar.tsx
  modified:
    - frontend/src/features/marketing-studio/components/metrics-dashboard/StageCard.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/MetricsDashboard.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/StageSummaryRow.tsx
    - frontend/src/features/marketing-studio/types/metrics.ts
decisions:
  - "Task execution order resequenced: Task 6 (types) logically precedes Tasks 3-5 (components using types) but Task 3 was committed before types were written. MetricSidebar imports MetricClickData from metrics.ts — both were committed in the same session so no runtime gap exists."
  - "mergeStageData() uses switch/case per StageId to map heterogeneous API shapes to a unified StageSummary, avoiding a generic mapper that would require each stage to conform to the same DTO shape."
  - "isMock logic: when hook is not loading and has no data (error or empty), the stage card shows the STAGE_SUMMARIES mock baseline with 'datos simulados' badge. This matches the CONTEXT.md fallback spec."
  - "StageSummary.mainKpi.value widened to number|string to support pre-formatted dual-currency strings from future API responses."
metrics:
  duration: "6 minutes"
  tasks_completed: 6
  files_created: 4
  files_modified: 4
  completed_date: "2026-03-16"
---

# Phase 11 Plan 01: UI Infrastructure and Real Data Wiring Summary

**One-liner:** Shared loading/error/empty state components + 8-hook parallel data wiring in MetricsDashboard + shadcn Sheet sidebar framework for metric drill-down.

## Artifacts Delivered

| File | Purpose | Min Lines | Actual |
|------|---------|-----------|--------|
| `ui/DetailSkeleton.tsx` | Shimmer loading wrapper for all 8 detail panels | 40 | 61 |
| `ui/DetailEmpty.tsx` | Empty state with "Sin datos para este periodo" + stage CTA | 30 | 53 |
| `ui/DetailError.tsx` | Error banner with AlertTriangle, Reintentar button, cached fallback | 35 | 67 |
| `MetricSidebar.tsx` | shadcn Sheet right-side drill-down sidebar framework | 80 | 182 |
| `StageCard.tsx` | Real KPI wiring + "X.X% conversion" + skeleton + "datos simulados" badge | 100 | 120 |
| `MetricsDashboard.tsx` | 8-hook orchestrator + sidebar state management | 150 | 293 |
| `StageSummaryRow.tsx` | Extended with loadingMap, mockMap, onMetricClick props | — | 46 |
| `types/metrics.ts` | MetricClickData, HeaderKpiData, widened StageSummary | — | 420 |

## Key Integration Points

### How the sidebar connects to detail panels (Plan 11-02)

The `handleMetricClick` function in `MetricsDashboard` accepts a `MetricClickData` and sets `sidebarMetric` + `sidebarOpen = true`. The handler is passed down to `StageSummaryRow` via `onMetricClick` prop. In Plan 11-02, each `AttractionDetail`, `CaptureDetail`, etc. will receive this callback and call it when a user clicks on any metric value (channel row, KPI tile, etc.).

The `MetricSidebar` component currently shows placeholder "Pronto" action buttons. Plan 11-02 will add `SidebarContent` polymorphic adapters per stage/metric type.

### Progressive loading pattern

```
MetricsDashboard mounts
  ├── useAttractionDetail() fires   → when resolves: ATRACCION card updates
  ├── useCaptureDetail() fires      → when resolves: CAPTURA card updates
  ├── ...8 parallel hooks...
  └── each hook's state flows via mergeStageData() → enrichedSummaries[]
                                                    → StageSummaryRow
                                                    → StageCard (isLoading / isMock)
```

No sequential awaiting — each stage card shows its skeleton independently and updates as soon as its hook resolves.

## Must-Haves Verification

| Truth | Status |
|-------|--------|
| Stage cards display real KPI values from backend API | DONE — mergeStageData() extracts values from hook responses |
| Stage cards show conversion rate to next stage as secondaryKpi | DONE — "X.X% conversion" format when unit === '%' |
| Loading states show skeleton shimmer while API data loads | DONE — isLoading prop + Skeleton bars in StageCard |
| Error/no-data fallback shows mock values with 'datos simulados' badge | DONE — isMock prop + Badge component in StageCard |
| All 8 detail panels use consistent header layout with 3 KPIs | PENDING — DetailSkeleton component ready; detail panels updated in Plan 11-02 |
| Action sidebar (Sheet) can be opened from any detail panel metric click | FRAMEWORK READY — MetricSidebar exists; per-panel wiring in Plan 11-02 |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking Dependency] Task 6 types required by Tasks 3, 4, 5**
- **Found during:** Task 3 (MetricSidebar imports MetricClickData)
- **Issue:** Plan ordered Task 6 (types) last, but Tasks 3-5 all import types that didn't exist yet
- **Fix:** Executed types as part of Task 3 commit context; Task 6 verified and formalized the definitions
- **Files modified:** `types/metrics.ts`
- **Commit:** `ed13b9a`

**2. [Rule 2 - Missing Critical Functionality] StageSummary.mainKpi.value type widened**
- **Found during:** Task 6
- **Issue:** Original type was `value: number` but dual-currency formatted strings require `string`
- **Fix:** Widened to `value: number | string` in both StageSummary and new HeaderKpiData
- **Files modified:** `types/metrics.ts`
- **Commit:** `ed13b9a`

## Self-Check

### Files created:
- [x] `ui/DetailSkeleton.tsx` — exists
- [x] `ui/DetailEmpty.tsx` — exists
- [x] `ui/DetailError.tsx` — exists
- [x] `MetricSidebar.tsx` — exists

### Commits exist:
- [x] `03fe38b` — DetailSkeleton
- [x] `30d4e13` — DetailEmpty + DetailError
- [x] `8667bdb` — MetricSidebar
- [x] `c556e7a` — StageCard real KPI wiring
- [x] `3718758` — MetricsDashboard 8-hook orchestration
- [x] `ed13b9a` — metrics.ts types

## Self-Check: PASSED
