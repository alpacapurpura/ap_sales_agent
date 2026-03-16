# Phase 11: Frontend Unification & Dashboard Polish - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Unify all 8 stage detail panels into a consistent, polished dashboard experience. Wire real KPI data into stage cards (replacing hardcoded mocks), add inter-stage conversion rates, implement a deep-dive action sidebar per metric, and execute a full visual redesign maximizing shadcn components. Research best-in-class monitoring dashboards for visual inspiration. This phase builds the **command and control center** — not just visualization, but the infrastructure for users to see a problem and immediately navigate toward action.

</domain>

<decisions>
## Implementation Decisions

### Stage Card Real KPIs
- **Data sourcing**: 8 parallel per-stage API calls (existing `/metrics/{stage}` endpoints). No new summary endpoint.
- **Main KPI per card**: Use the primary metric from each stage's existing `headerKpis`:
  - ATRACCION → total visitors (sum across channels)
  - CAPTURA → totalLeads
  - NUTRICION → totalMqls
  - OPORTUNIDAD → totalSqls
  - VENTAS → totalRevenue ($)
  - ADOPCION → healthPct (%)
  - EXPANSION → netMrr ($)
  - EVANGELIZACION → kFactor
- **Secondary KPI**: Conversion rate to that stage from the previous one (see Conversion Rate section). Exception: Atraccion shows total spend (no previous stage).
- **Loading state**: Skeleton shimmer (animated gray bars) while each endpoint loads. Data appears progressively.
- **Error/no-data fallback**: Show mock values with a small "datos simulados" badge on the card. Matches existing ENABLE_MOCKS fallback pattern.
- **Fix**: EXPANSION mock has `hasDetail: false` — must change to `true` (panel exists now).

### Conversion Rate Display (UI-03)
- **Location**: Inside each card as the secondaryKpi (no arrows or extra UI between cards)
- **Formula**: Match mainKpi type — use whatever the mainKpi represents for the ratio. E.g., revenue-based for Ventas, health-based for Adopcion.
- **Atraccion exception**: First stage has no conversion rate. Secondary KPI = total spend across all paid channels.
- **Label format**: "X% conversión" — consistent across all stages

### Visual Polish — Deep Redesign
- **Design philosophy**: Act like a designer who has read "Steal Like an Artist" and "Don't Make Me Think". Data must be VERY understandable with visual weight on the most important elements.
- **Research mandate**: UI-SPEC must investigate the most impressive monitoring/control dashboards currently built. Find visually disruptive and attractive alternatives for displaying funnel metrics. Propose options.
- **Component library**: Maximize shadcn usage. Exploit every relevant shadcn component.
- **Micro-interactions**: Subtle animations — scale+shadow on hover, count-up numbers on load, fade-in panel transitions, subtle highlight on ChannelRow hover, skeleton shimmer with smooth gradient.
- **Responsive**: Full responsive — desktop, tablet, and mobile breakpoints. All layouts must work across devices.
- **Channel icons (UI-04)**: Official brand icons for all platforms (Meta, Google, TikTok, YouTube, Shopify, Mailerlite, WhatsApp, Manychat, etc.). Use react-icons or custom SVGs. Instant recognition without reading.
- **Stage colors**: Claude decides after researching best practices for monitoring dashboards. Must be very UI-friendly. Research-informed decision.
- **UI-SPEC flow**: Use `/gsd:ui-phase 11` before planning to generate a design contract with dashboard research, layout system proposal, and component breakdown.

### Panel Consistency (UI-01) — Full Pattern System
- **Panel template**: All 8 panels follow the same structural template:
  1. Header KPIs (3 primary, optional secondary row)
  2. MiniFunnel (stage N-1 → stage N = X%)
  3. Content area (groups, channels, offer cards — varies by stage type)
  4. BottleneckBanner (if applicable)
  5. Available/unconnected channels (if applicable)
- **Wrapper consistent, content specialized**: Same container, header, spacing, loading pattern across all panels. Inner content uses specialized components per stage type:
  - Pre-venta (0-4): ChannelGroup + ChannelRow
  - Adopcion: HealthBar + OfferHealthCard
  - Expansion: ExpansionGroup + ExpansionOfferRow
  - Evangelizacion: NpsSummaryCard + EvangelistCard + CandidatosBanner
- **Shared state components**: Build reusable DetailSkeleton, DetailEmpty, and DetailError components used by all 8 panels:
  - DetailSkeleton: Shimmer KPIs + shimmer bar + shimmer rows
  - DetailEmpty: Illustration + "Sin datos para este período" + contextual CTA
  - DetailError: Subtle red banner + retry button + last cached data if available

### Action Sidebar (Command & Control Layer)
- **Design principle**: Dashboard is a command center. See problem → click metric → deep detail → path to action.
- **Two interaction layers**:
  1. **Informational** (below cards): Summary panel with stage overview — current behavior, improved
  2. **Action** (sidebar): Click specific metric/channel within a panel → shadcn Sheet slides in from right with granular detail
- **Sidebar implementation**: Reuse shadcn Sheet component (already in project)
- **Sidebar content**: Maximum granularity — direct API calls for the specific metric clicked. If granularity is by campaign, show all campaign details enabling immediate decision-making. Per-metric detail, not just per-channel summary.
- **Connection states in sidebar**:
  - Connected → full detail data + sparklines + breakdown
  - Not connected → "Conectar" CTA linking to connections config
  - Not created → "Crear" CTA linking to relevant creation flow
- **Action triggers**: Placeholder "Próximamente" buttons for future milestone actions (create campaign, edit config, etc.)
- **Research mandate**: UI-SPEC must determine exact sidebar content per metric type after investigating best dashboard drill-down patterns

### Claude's Discretion
- Stage color palette (after dashboard research)
- Exact sparkline/chart library choice for sidebar trends
- Spacing system and typography scale (after research)
- Animation timing and easing functions
- Sidebar width and responsive behavior
- Which shadcn components to use for each dashboard section
- Empty state illustrations (style, content)
- Exact breakpoint values for responsive layout
- How campaign-level detail maps per provider in sidebar

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Frontend Components (Current State)
- `frontend/src/features/marketing-studio/components/metrics-dashboard/MetricsDashboard.tsx` — Main dashboard with stage routing (all 8 stages wired)
- `frontend/src/features/marketing-studio/components/metrics-dashboard/StageSummaryRow.tsx` — Stage card row (horizontal scroll)
- `frontend/src/features/marketing-studio/components/metrics-dashboard/StageCard.tsx` — Individual stage card (currently uses mock data)
- `frontend/src/features/marketing-studio/types/metrics.ts` — All TypeScript types for 8 stages
- `frontend/src/features/marketing-studio/api/metrics-mock-data.ts` — STAGE_SUMMARIES mock data (must be replaced with real API calls)
- `frontend/src/features/marketing-studio/api/metrics-api.ts` — API client with mock fallback pattern

### Detail Panels (All 8)
- `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/AttractionDetail.tsx` — Stage 0 (user said "se ve horrible" — needs most polish)
- `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/CaptureDetail.tsx` — Stage 1
- `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/NurtureDetail.tsx` — Stage 2
- `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/OpportunityDetail.tsx` — Stage 3
- `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/SalesDetail.tsx` — Stage 4 (most comprehensive, good reference)
- `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/AdoptionDetail.tsx` — Stage 5
- `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/ExpansionDetail.tsx` — Stage 6
- `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/EvangelizationDetail.tsx` — Stage 7

### Shared Widgets
- `frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/ChannelGroup.tsx` — Group container
- `frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/ChannelRow.tsx` — Multi-metric channel row
- `frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/ConnectionBadge.tsx` — Connected/Configurar status
- `frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/MiniFunnel.tsx` — Stage-to-stage funnel
- `frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/HealthBar.tsx` — CSS proportional bar
- `frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/KpiTooltip.tsx` — Plain-Spanish KPI hints
- `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/BottleneckBanner.tsx` — Shared bottleneck alert

### Hooks (Data Fetching Pattern)
- `frontend/src/features/marketing-studio/hooks/` — All useXxxDetail hooks follow useAuth + metricsApi pattern

### Backend Endpoints (Existing — All 8 stages)
- `backend/src/modules/analytics/api/metrics.py` — All `/metrics/{stage}` endpoints
- `backend/src/modules/analytics/application/services/metrics_service.py` — MetricsService with cache

### Prior Design Decisions
- `docs/domains/INDEX.md` — Business domain index (anti-hallucination)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `shadcn Sheet component`: Already in project — reuse for action sidebar
- `ChannelGroup + ChannelRow + ConnectionBadge`: Core pattern for pre-venta stages
- `BottleneckBanner`: Shared across multiple panels
- `KpiTooltip`: Reusable tooltip component for plain-Spanish metric hints
- `MiniFunnel`: Stage-to-stage conversion funnel
- `HealthBar`: CSS proportional bar (adoption)
- `metrics-api.ts`: API client with ENABLE_MOCKS fallback pattern
- All 8 detail hooks: Follow consistent useAuth + metricsApi pattern

### Established Patterns
- 3 header KPIs per panel (Phases 5-10)
- MiniFunnel at panel top (Phases 5-10)
- Bottleneck banners with severity thresholds and context-aware tips (Phase 7-10)
- ENABLE_MOCKS fallback in frontend API layer
- React Query with 5-min staleTime for dashboard hooks
- Dual currency formatting via Intl.NumberFormat (Phase 8)
- CSS proportional bars without chart library (Phase 9)
- Inline bottleneck badges computed from metric values (Phase 7)

### Integration Points
- `STAGE_SUMMARIES` in `metrics-mock-data.ts`: Replace with real API-driven data
- `StageCard.tsx`: Wire to real KPI data + add conversion rate as secondaryKpi
- `MetricsDashboard.tsx`: Add sidebar state management + metric click handlers
- Each detail panel: Add onClick handlers on ChannelRow/OfferCard to trigger sidebar
- New shared components needed: DetailSkeleton, DetailEmpty, DetailError, MetricSidebar

</code_context>

<specifics>
## Specific Ideas

- "Toma en consideración que usamos shadcn, explótalo al máximo" — every UI element should leverage shadcn components where possible
- "Revisa los tableros más impresionantes actualmente construidos para sistemas de monitoreo y control" — UI-SPEC must research real-world dashboards for inspiration
- "Los datos deben ser muy pero muy entendibles, brindándole el peso visual a los elementos más importantes" — visual hierarchy is critical, most important data must be visually dominant
- "Actuar como un buen diseñador que ha leído 'El arte de robar' y 'No me dejes pensar'" — steal best patterns from the best dashboards, make everything self-explanatory
- "Busca en internet problemas similares y dame alternativas visualmente muy disruptivas y atractivas" — the UI-SPEC research must find and propose multiple visual alternatives
- "Cuando yo haga click en una métrica específica, debe aparecer un sidebar con mucha más información, llamados directos a la API para ver el detalle del detalle" — sidebar shows maximum granularity, direct API data, campaign-level detail
- "Debo poder hacer click y trabajar en ello" — the dashboard must guide users toward action, not just show data. Every metric is a potential action entry point.
- "El nivel de acción posible más granular" — per-metric, per-campaign detail. If the user clicks Meta retargeting, they see every campaign with enough detail to make decisions.

</specifics>

<deferred>
## Deferred Ideas

- Action triggers in sidebar (create campaign, edit config, launch automation) — next milestone
- Date range picker / time period selection — v2 requirement (UX-01)
- Revenue trend indicators vs previous period — future enhancement
- Strategy Canvas (Sankey diagram) integration — separate component, not this milestone
- Export/download metrics data — v2 requirement (UX-04)
- Custom KPI goal/target setting — v2 requirement (UX-03)

</deferred>

---

*Phase: 11-frontend-unification-dashboard-polish*
*Context gathered: 2026-03-16*
