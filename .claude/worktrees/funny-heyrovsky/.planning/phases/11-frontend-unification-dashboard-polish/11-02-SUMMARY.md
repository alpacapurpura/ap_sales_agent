---
phase: 11-frontend-unification-dashboard-polish
plan: "02"
subsystem: frontend/metrics-dashboard
tags: [ui-polish, channel-icons, sidebar, micro-interactions, responsive, detail-panels]
dependency_graph:
  requires: ["11-01"]
  provides: ["channel-icons-library", "sidebar-content-adapter", "metric-click-flow"]
  affects: ["frontend/marketing-studio/metrics-dashboard", "frontend/globals.css"]
tech_stack:
  added: []
  patterns:
    - "channelIcons.ts: slug -> lucide-react icon + hex color mapping"
    - "SidebarContent: polymorphic switch(stageId) for per-stage drill-down"
    - "MetricDisplay: clickable sub-component wrapper for metric values"
    - "ChannelGroup -> ChannelRow: stageId + onMetricClick prop threading"
    - "animate-fade-in: CSS class from globals.css for panel transitions"
key_files:
  created:
    - frontend/src/features/marketing-studio/lib/channelIcons.ts
    - frontend/src/features/marketing-studio/components/metrics-dashboard/sidebar/SidebarContent.tsx
  modified:
    - frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/ChannelRow.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/ChannelGroup.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/TierGroup.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/OfferCard.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/AttractionDetail.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/CaptureDetail.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/NurtureDetail.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/OpportunityDetail.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/SalesDetail.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/AdoptionDetail.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/ExpansionDetail.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/EvangelizationDetail.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/MetricsDashboard.tsx
    - frontend/src/features/marketing-studio/components/metrics-dashboard/MetricSidebar.tsx
    - frontend/src/app/globals.css
decisions:
  - "channelIcons.ts uses lucide-react fallbacks for all channels; TikTok uses Radio (not in lucide), Meta Ads uses Zap"
  - "SidebarContent renders stage-specific context banners with brand colors per stage palette from UI-SPEC"
  - "MetricSidebar accepts children prop: SidebarContent injected from MetricsDashboard, fallback static buttons preserved"
  - "Clickable metrics: MetricDisplay wraps in <button> when onMetricClick + stageId provided"
  - "ChannelGroup/TierGroup/OfferCard each received onMetricClick threading as Rule 3 auto-fix"
  - "animate-fade-in CSS class added to globals.css; Tailwind animate-pulse retained for DetailSkeleton"
  - "Pre-existing PlaceholderDetail.tsx TypeScript errors deferred (out of scope for Plan 11-02)"
metrics:
  duration: "10 min"
  completed_date: "2026-03-16"
  tasks_completed: 6
  files_modified: 15
---

# Phase 11 Plan 02: Detail Panel Polish, Channel Icons & Sidebar Wiring Summary

Professional brand icons, consistent responsive KPI grids, metric click-to-sidebar drill-down flow, and fade-in animations across all 8 Growth Studio detail panels.

## Artifact List

### Created Files

| File | Purpose | Lines |
|------|---------|-------|
| `lib/channelIcons.ts` | Channel slug → lucide-react icon + hex color | 219 |
| `sidebar/SidebarContent.tsx` | Polymorphic content adapter per stageId | 442 |

### Modified Files

| File | Change |
|------|--------|
| `channel-widgets/ChannelRow.tsx` | Brand icons, onMetricClick prop, hover bg-primary/5 |
| `channel-widgets/ChannelGroup.tsx` | stageId + onMetricClick forwarded to ChannelRow |
| `channel-widgets/TierGroup.tsx` | onOfferClick prop forwarded to OfferCard |
| `channel-widgets/OfferCard.tsx` | onRevenueClick prop with clickable button |
| `detail-panels/AttractionDetail.tsx` | Wrapper pattern, KPI grid, onMetricClick, animate-fade-in |
| `detail-panels/CaptureDetail.tsx` | Wrapper pattern, KPI grid, onMetricClick |
| `detail-panels/NurtureDetail.tsx` | Wrapper pattern, KPI grid, onMetricClick |
| `detail-panels/OpportunityDetail.tsx` | Wrapper pattern, KPI grid, onMetricClick |
| `detail-panels/SalesDetail.tsx` | Wrapper pattern, KPI grid, onMetricClick, offer-level clicks |
| `detail-panels/AdoptionDetail.tsx` | Wrapper pattern, KPI grid, onMetricClick, OfferHealthCard clickable |
| `detail-panels/ExpansionDetail.tsx` | Wrapper pattern, KPI grid, onMetricClick, KPI cards clickable |
| `detail-panels/EvangelizationDetail.tsx` | Wrapper pattern, KPI grid, onMetricClick, EvangelistCard clickable |
| `MetricsDashboard.tsx` | SidebarContent injection, handleMetricClick to all 8 panels |
| `MetricSidebar.tsx` | children prop (ReactNode), SidebarContent slot |
| `app/globals.css` | animate-fade-in, bottleneck-critical, skeleton-loading keyframes |

## UI-SPEC Implementation Checklist

### Panel Consistency (UI-01)
- [x] All 8 panels use DetailSkeleton / DetailEmpty / DetailError
- [x] All 8 panels: `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4` for header KPIs
- [x] All 8 panels: animate-fade-in on content wrapper
- [x] All 8 panels: italic timestamp `Actualizado: ...`
- [x] All 8 panels: MiniFunnel rendered (where applicable)
- [x] All 8 panels: BottleneckBanner for warning/critical severity

### Channel Icons (UI-04)
- [x] getChannelIcon(): Instagram, Facebook, Youtube, TikTok (Radio fallback), Meta (Zap), Google (Search), Shopify (ShoppingCart), Mailerlite (Mail), WhatsApp (MessageCircle), Manychat (MessageSquare), AI SDR (Bot), LinkedIn (Globe)
- [x] getChannelColor(): brand hex values (Instagram #E4405F, Facebook #1877F2, YouTube #FF0000, TikTok #010101, WhatsApp #25D366, etc.)
- [x] ChannelRow: Icon w-5 h-5 with style={{ color: iconColor }}
- [x] Icon micro-animation: group-hover:scale-110

### Action Sidebar
- [x] MetricSidebar accepts children ReactNode
- [x] SidebarContent polymorphic switch(stageId) renders 8 stage adapters
- [x] Each stage adapter: color-coded context banner + "proxima version" placeholder + 3 action CTAs
- [x] MetricsDashboard: SidebarContent injected as children of MetricSidebar
- [x] handleMetricClick passed to all 8 detail panels

## Micro-Interaction Catalog

| Animation | CSS Class / Tailwind | Duration | Applied To |
|-----------|---------------------|----------|------------|
| Panel fade-in | `.animate-fade-in` (globals.css) | 200ms ease-in | All 8 detail panel wrappers |
| Skeleton shimmer | `animate-pulse` (shadcn/Tailwind) | 1.5s | DetailSkeleton |
| Stage card scale | `hover:scale-[1.02]` + `transition-all duration-150` | 150ms | StageCard |
| Channel row hover | `hover:bg-primary/5` + `transition-all duration-100 ease-out` | 100ms | ChannelRow connected row |
| Channel icon lift | `group-hover:scale-110 transition-transform duration-100` | 100ms | Channel icon in ChannelRow |
| Metric click feedback | `hover:bg-primary/5 transition-colors duration-100` | 100ms | MetricDisplay button |
| BottleneckBanner pulse | `.bottleneck-critical` (globals.css) | 2s infinite | Critical severity banners |
| Sidebar slide-in | shadcn Sheet side="right" | 250ms | MetricSidebar |

## Responsive Breakpoint Validation

| Breakpoint | KPI Grid | Metric Spacing |
|-----------|---------|----------------|
| Mobile (<sm) | `grid-cols-1` — single column | `gap-2` |
| Tablet (sm+) | `sm:grid-cols-2` — 2 columns | `sm:gap-3` |
| Desktop (lg+) | `lg:grid-cols-3` — 3 columns | full gap-4 |

## Sidebar Content Mapping

| Stage | Sidebar Context Color | Action CTAs |
|-------|----------------------|-------------|
| ATRACCION | Blue (bg-blue-50) | "Crear campana", "Editar config", "Ver historial" |
| CAPTURA | Purple (bg-purple-50) | Same pattern |
| NUTRICION | Pink (bg-pink-50) | Same pattern |
| OPORTUNIDAD | Orange (bg-orange-50) | Same pattern |
| VENTAS | Green (bg-green-50) | Revenue + offer-level click |
| ADOPCION | Cyan (bg-cyan-50) | OfferHealthCard click |
| EXPANSION | Amber (bg-amber-50) | Net MRR KPI card click |
| EVANGELIZACION | Fuchsia (bg-fuchsia-50) | K-Factor, NPS, EvangelistCard click |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] ChannelGroup missing stageId + onMetricClick forwarding**
- **Found during:** Task 4 — AttractionDetail passes props to ChannelGroup which passes to ChannelRow
- **Issue:** ChannelGroup.tsx didn't accept or forward stageId/onMetricClick to ChannelRow
- **Fix:** Added stageId and onMetricClick to ChannelGroupProps interface; forwarded to ChannelRow
- **Files modified:** `channel-widgets/ChannelGroup.tsx`
- **Commit:** 9db198d

**2. [Rule 3 - Blocking] TierGroup missing onOfferClick forwarding to OfferCard**
- **Found during:** Task 4 — SalesDetail passes onMetricClick → RevenueSection → TierGroup
- **Issue:** TierGroup didn't accept onOfferClick prop to forward to OfferCard
- **Fix:** Added onOfferClick?: (offerId, publicName, revenue) => void to TierGroupProps; forwarded to OfferCard
- **Files modified:** `channel-widgets/TierGroup.tsx`
- **Commit:** 9db198d

**3. [Rule 2 - Missing functionality] OfferCard missing clickable revenue metric**
- **Found during:** Task 4 — Plan required offer-level click for VENTAS stage sidebar trigger
- **Issue:** OfferCard had no onRevenueClick prop; revenue was static span text
- **Fix:** Added onRevenueClick?: () => void; revenue rendered as clickable button when callback provided
- **Files modified:** `channel-widgets/OfferCard.tsx`
- **Commit:** 9db198d

**4. [Rule 3 - Blocking] MetricSidebar missing children prop**
- **Found during:** Task 5 — MetricsDashboard needs to inject SidebarContent as children
- **Issue:** MetricSidebar.tsx didn't accept ReactNode children
- **Fix:** Added children?: ReactNode to MetricSidebarProps; renders children or fallback static buttons
- **Files modified:** `MetricSidebar.tsx`
- **Commit:** d3628f7

### Out-of-Scope Issues (Deferred)

- `PlaceholderDetail.tsx`: Pre-existing TypeScript error `TS2345: string | number not assignable to number` — not introduced by Plan 11-02, deferred to maintenance task.

## Self-Check: PASSED

Files verified:
- FOUND: frontend/src/features/marketing-studio/lib/channelIcons.ts
- FOUND: frontend/src/features/marketing-studio/components/metrics-dashboard/sidebar/SidebarContent.tsx
- FOUND: frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/ChannelRow.tsx (modified)
- FOUND: frontend/src/app/globals.css (modified)

Commits verified:
- a5b5322 feat(11-02): create channelIcons library
- d16f2ec feat(11-02): update ChannelRow with brand icons, onClick handlers
- 6f29f88 feat(11-02): create SidebarContent polymorphic sidebar content adapter
- 9db198d feat(11-02): update all 8 detail panels
- d3628f7 feat(11-02): wire SidebarContent into MetricsDashboard and MetricSidebar
- 95ba749 feat(11-02): add micro-interaction animations to globals.css
