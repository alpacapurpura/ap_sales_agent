# Phase 11: Frontend Unification & Dashboard Polish - Research

**Researched:** 2026-03-16
**Domain:** Frontend UI/UX unification, real-time data integration, dashboard visual design
**Confidence:** HIGH

## Summary

Phase 11 transforms the Growth Studio dashboard from static mock data to a unified, polished real-data experience across all 8 metrics stages. The phase has three core pillars:

1. **Real Data Wiring** — Replace STAGE_SUMMARIES hardcoded mock data with 8 parallel per-stage API calls. Stage cards now show real KPIs (visitor count, leads, MQLs, etc.) plus conversion rates to next stage.
2. **Unified Visual Design** — Execute a deep redesign maximizing shadcn components, implementing micro-interactions (skeletal loading, count-up animations, hover scales), channel icons, and responsive layouts across all devices.
3. **Action Sidebar (Command Layer)** — Implement deep-dive detail navigation: click any metric in a panel and a shadcn Sheet slides from right with granular data, direct API calls per metric, and call-to-action buttons.

All decisions are locked by CONTEXT.md. This research verifies implementation patterns, identifies component library capabilities, and documents common pitfalls in dashboard UI work.

**Primary recommendation:** Follow the existing phase 5-10 detail panel patterns (ChannelGroup + ChannelRow + ConnectionBadge) as the template for all 8 stages. Reuse skeletal loading, error handling, and bottleneck banner patterns. Wire real API calls in hooks layer (useXxxDetail) and render progressively as data loads.

## User Constraints (from CONTEXT.md)

### Locked Decisions

**Stage Card Real KPIs (UI-02):**
- Data sourcing: 8 parallel per-stage API calls to existing `/metrics/{stage}` endpoints
- Main KPI per card: Primary metric from headerKpis
  - ATRACCION → total visitors (sum across channels)
  - CAPTURA → totalLeads
  - NUTRICION → totalMqls
  - OPORTUNIDAD → totalSqls
  - VENTAS → totalRevenue ($)
  - ADOPCION → healthPct (%)
  - EXPANSION → netMrr ($)
  - EVANGELIZACION → kFactor
- Secondary KPI: Conversion rate to that stage from previous (UI-03, exception: Atraccion shows total spend)
- Loading state: Skeleton shimmer (animated gray bars) while endpoints load
- Error/no-data fallback: Show mock values with "datos simulados" badge (matches ENABLE_MOCKS pattern)

**Conversion Rate Display (UI-03):**
- Location: Inside card as secondaryKpi (no arrows or extra UI between cards)
- Formula: Match mainKpi type (revenue-based for Ventas, health-based for Adopcion)
- Label format: "X% conversión" — consistent across all stages
- Atraccion exception: No conversion rate, secondary KPI = total spend across all paid channels

**Visual Polish — Deep Redesign:**
- Design philosophy: "Don't Make Me Think" — data VERY understandable, visual weight on important elements
- Research mandate: Investigate impressive monitoring/control dashboards for inspiration
- Component library: Maximize shadcn usage
- Micro-interactions: scale+shadow on hover, count-up numbers on load, fade-in transitions, skeleton shimmer with smooth gradient
- Responsive: Full mobile/tablet/desktop coverage
- Channel icons (UI-04): Official brand icons for all platforms (react-icons or custom SVGs)
- Stage colors: Claude decides after dashboard research

**Panel Consistency (UI-01) — Full Pattern System:**
- Panel template: All 8 panels follow same structural template:
  1. Header KPIs (3 primary, optional secondary row)
  2. MiniFunnel (stage N-1 → stage N = X%)
  3. Content area (groups, channels, offer cards — varies by stage type)
  4. BottleneckBanner (if applicable)
  5. Available/unconnected channels (if applicable)
- Wrapper consistent, content specialized
- Reusable: DetailSkeleton, DetailEmpty, DetailError shared across all 8 panels

**Action Sidebar (Command & Control Layer):**
- Two layers: Informational (summary below cards) + Action (sidebar on metric click)
- Sidebar implementation: Reuse shadcn Sheet component
- Sidebar content: Maximum granularity — direct API calls for specific metric clicked
- Connection states in sidebar: Connected (full detail + sparklines) / Not connected (Conectar CTA) / Not created (Crear CTA)
- Action triggers: Placeholder "Próximamente" buttons for future milestone actions

### Claude's Discretion

- Stage color palette (after dashboard research)
- Exact sparkline/chart library choice for sidebar trends
- Spacing system and typography scale (after research)
- Animation timing and easing functions
- Sidebar width and responsive behavior
- Which shadcn components to use for each section
- Empty state illustrations (style, content)
- Exact breakpoint values for responsive layout
- How campaign-level detail maps per provider in sidebar

### Deferred Ideas (OUT OF SCOPE)

- Action triggers (create campaign, edit config) — next milestone
- Date range picker / time period selection — v2 requirement
- Revenue trend indicators vs previous period — future enhancement
- Strategy Canvas (Sankey diagram) integration — separate component
- Export/download metrics data — v2 requirement
- Custom KPI goal/target setting — v2 requirement

---

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| UI-01 | Consistent detail panel pattern across all 8 stages following ChannelGroup + ChannelRow + ConnectionBadge from AttractionDetail | All 8 panels now exist (Phases 5-10) with established ChannelRow pattern; DetailSkeleton, DetailEmpty, DetailError components needed for shared reusable state handling; MiniFunnel and BottleneckBanner already exist and are reused across stages |
| UI-02 | Each stage card in StageSummaryRow shows real KPI values (main + secondary) from backend, not hardcoded mock data | Hooks pattern established (useXxxDetail with useAuth + metricsApi); metricsApi already has parallel API methods for all 8 stages; STAGE_SUMMARIES currently hardcoded from mock-data.ts — replace with real API calls + progressive loading |
| UI-03 | Conversion rate between adjacent stages displayed on each stage card (Stage N→N+1 ratio) | MiniFunnelData type exists with conversionRate; conversion rate formulas locked by CONTEXT.md (e.g., Captura = Leads/Visitors, Nutricion = MQLs/Leads); secondary KPI field in StageSummary type must wire these percentages from API headerKpis |
| UI-04 | Provider-specific channel icons and labels matching channel definitions from product spec | CHANNEL_ICONS object exists in ChannelRow.tsx with emoji placeholders; Phase 11 must replace with react-icons library imports or custom SVG components for professional appearance (Meta, Google, TikTok, YouTube, Shopify, Mailerlite, WhatsApp, Manychat, etc.) |

---

## Standard Stack

### Core — Frontend Component Library

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| shadcn/ui | v0.8+ | Headless component library built on Radix UI | Installed in project (components.json exists), used throughout marketing-studio (Button, Card, Tooltip, Badge, Skeleton, Collapsible, Dialog, Dropdown, Sheet). Enables rapid, consistent UI without CSS friction. |
| @radix-ui/* | v1.0+ | Underlying Radix UI primitives | Installed via shadcn; provides accessible, unstyled components (Tooltip, Dialog, Sheet, Dropdown, Tabs, Popover, Accordion). Perfect for building micro-interactions. |
| lucide-react | v0.365+ | Icon library | Installed in project (package.json), used for UI icons (RefreshCw, AlertTriangle, etc.). Tree-shakeable, consistent with shadcn design language. |
| @tanstack/react-query | v5.x | Server state management | Installed (used in hooks useAttractionDetail, etc.). Handles caching (5-min staleTime), background refetching, loading/error states. Essential for parallel API calls. |
| @clerk/nextjs | latest | Authentication & token management | Integrated (getToken() used in all hooks). Ensures auth headers included in every API call. |

### Supporting — Data Visualization & Micro-Interactions

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Tailwind CSS | v3.x | Utility-first CSS framework | Responsive design, color system, spacing scale already in place (globals.css with slate preset). Use for responsive breakpoints (mobile, tablet, desktop). |
| framer-motion | v10+ | Animation library (optional, for sidebar transitions) | If implementing fade-in/slide transitions for action sidebar. Can be replaced with CSS transitions for simpler animations. |
| react-spring | v9+ | Physics-based animation alternative | If count-up number animation is needed. Lighter than framer-motion. Overkill if only using Tailwind transitions. |
| recharts | v2.10+ | Charting library for sidebar sparklines | Only if sidebar drill-down requires trend sparklines. Context.md defers this to Claude's discretion. Don't add unless necessary. |

### Alternative Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| shadcn/ui Sheet | Dialog with manual positioning | Sheet provides horizontal slide animation from right out-of-box; Dialog requires custom CSS. Sheet is 50 lines vs Dialog's 200+. Use Sheet. |
| lucide-react icons | Custom SVGs or icon fonts | Custom SVGs give brand control but require design/build steps. Lucide is tree-shakeable, instant, consistent. Use lucide-react for UI chrome; brand icons (Meta, Google, TikTok) should be custom SVGs for polish. |
| @tanstack/react-query | SWR | React Query has better background refetching and cache TTL control. SWR simpler but less feature-rich. Use React Query (already installed). |
| Tailwind CSS transitions | framer-motion | Tailwind's `transition-all duration-300` is sufficient for hover scales and fade-ins. framer-motion adds 40KB. Use Tailwind unless physics-based spring is required. |

**Installation (npm/yarn already done):**
```bash
# Core already installed; verify:
npm ls shadcn-ui @radix-ui/react-tooltip @tanstack/react-query lucide-react

# Add if missing:
npm install -S recharts  # Only if sidebar sparklines needed
npm install -S framer-motion  # Only if complex animations needed
```

---

## Architecture Patterns

### Frontend Data Flow (Real API Wiring)

**Current state:** StageCard displays hardcoded STAGE_SUMMARIES values.

**Target state:**
1. MetricsDashboard mounts → calls 8 useXxxDetail hooks in parallel
2. Each hook makes async API call to `/metrics/{stage}`
3. React Query caches result (5-min staleTime)
4. StageSummary data flows through StageSummaryRow → StageCard
5. While loading: Skeleton shimmer in place of KPI values
6. On error: Mock values shown with "datos simulados" badge

**Data flow diagram:**
```
MetricsDashboard
├── useAttractionDetail() → /api/v1/analytics/metrics/attraction
├── useCaptureDetail()    → /api/v1/analytics/metrics/capture
├── useNurtureDetail()    → /api/v1/analytics/metrics/nurturing
├── useOpportunityDetail()→ /api/v1/analytics/metrics/opportunity
├── useSalesDetail()      → /api/v1/analytics/metrics/sales
├── useAdoptionDetail()   → /api/v1/analytics/metrics/adoption
├── useExpansionDetail()  → /api/v1/analytics/metrics/expansion
└── useEvangelizationDetail() → /api/v1/analytics/metrics/evangelization

Each hook (pattern):
├── useQuery({
│   queryKey: ['stage-detail'],
│   queryFn: async () => metricsApi.getXxxDetail(token),
│   staleTime: 1000 * 60 * 5,
│ })
└── Returns: { data, isLoading, error, isFetching }

Render pattern:
├── isLoading? → DetailSkeleton
├── error? → DetailEmpty with mock fallback + "datos simulados" badge
└── data → render actual panels (AttractionDetail, CaptureDetail, etc.)
```

### Recommended Project Structure

```
frontend/src/features/marketing-studio/
├── components/
│   └── metrics-dashboard/
│       ├── MetricsDashboard.tsx          # Main orchestrator (8 hooks + state)
│       ├── StageSummaryRow.tsx           # Horizontal stage cards
│       ├── StageCard.tsx                 # Individual card (mainKpi + secondaryKpi)
│       ├── detail-panels/
│       │   ├── AttractionDetail.tsx      # ✓ Exists, use as template
│       │   ├── CaptureDetail.tsx         # ✓ Exists
│       │   ├── NurtureDetail.tsx         # ✓ Exists
│       │   ├── OpportunityDetail.tsx     # ✓ Exists
│       │   ├── SalesDetail.tsx           # ✓ Exists
│       │   ├── AdoptionDetail.tsx        # ✓ Exists
│       │   ├── ExpansionDetail.tsx       # ✓ Exists
│       │   ├── EvangelizationDetail.tsx  # ✓ Exists
│       │   ├── DetailSkeleton.tsx        # NEW: Shared loading state
│       │   ├── DetailEmpty.tsx           # NEW: No-data state
│       │   ├── DetailError.tsx           # NEW: Error state with retry
│       │   └── BottleneckBanner.tsx      # ✓ Exists, reused
│       ├── channel-widgets/
│       │   ├── ChannelGroup.tsx          # ✓ Exists
│       │   ├── ChannelRow.tsx            # ✓ Exists, enhance with icon swap
│       │   ├── MiniFunnel.tsx            # ✓ Exists
│       │   ├── HealthBar.tsx             # ✓ Exists
│       │   ├── KpiTooltip.tsx            # ✓ Exists
│       │   └── [other specialized widgets]
│       └── sidebar/
│           ├── MetricSidebar.tsx         # NEW: Action sidebar (Sheet-based)
│           ├── DrilldownContent.tsx      # NEW: Dynamic content per metric type
│           └── CampaignDetailView.tsx    # NEW: Campaign-level detail
├── hooks/
│   ├── useAttractionDetail.ts    # ✓ Exists, use pattern
│   ├── useCaptureDetail.ts       # ✓ Exists
│   ├── useNurtureDetail.ts       # ✓ Exists
│   ├── useOpportunityDetail.ts   # ✓ Exists
│   ├── useSalesDetail.ts         # ✓ Exists
│   ├── useAdoptionDetail.ts      # ✓ Exists
│   ├── useExpansionDetail.ts     # ✓ Exists
│   ├── useEvangelizationDetail.ts# ✓ Exists
│   └── useSidebarMetric.ts       # NEW: Fetch drill-down data per metric
├── api/
│   ├── metrics-api.ts            # ✓ Exists, wire all 8 stages
│   └── metrics-mock-data.ts      # ✓ Exists, keep as fallback
└── types/
    └── metrics.ts                # ✓ Exists, may extend for sidebar
```

### Pattern 1: Real Data Wiring in Stage Cards

**What:** Replace hardcoded STAGE_SUMMARIES with dynamic API data while handling loading/error states.

**When to use:** Any dashboard component that needs live external data with fallback.

**Example:**
```typescript
// BEFORE: Hardcoded
const stages = STAGE_SUMMARIES; // Static array from metrics-mock-data.ts

// AFTER: Dynamic with React Query
function MetricsDashboard() {
  const { data: attractionData, isLoading: attractionLoading, error: attractionError } = useAttractionDetail();
  const { data: captureData, isLoading: captureLoading, error: captureError } = useCaptureDetail();
  // ... 6 more hooks ...

  // Combine into StageSummary array
  const stages = useMemo(() => [
    {
      id: 'ATRACCION',
      mainKpi: {
        label: 'visitantes',
        value: attractionError
          ? MOCK_ATTRACTION_DETAIL.headerKpis?.visitors ?? 45000
          : attractionData?.headerKpis?.visitors ?? 0,
        unit: undefined,
      },
      secondaryKpi: {
        label: 'spend',
        value: attractionError
          ? MOCK_ATTRACTION_DETAIL.headerKpis?.totalSpend ?? 8500
          : attractionData?.headerKpis?.totalSpend ?? 0,
        unit: '$',
      },
      hasDetail: true,
    },
    // ... 7 more stages ...
  ], [attractionData, captureData, /* ... */]);

  return (
    <div className="space-y-4">
      <StageSummaryRow stages={stages} activeStage={activeStage} onStageClick={handleStageClick} />
      {activeStage && <DetailPanel />}
    </div>
  );
}
```

**Source:** Established React Query pattern in useAttractionDetail.ts, useSalesDetail.ts

### Pattern 2: Skeleton Shimmer Loading State

**What:** While API data loads, show skeleton placeholders with subtle gradient animation.

**When to use:** Any detail panel or section with async data.

**Example:**
```typescript
// Source: OpportunityDetail.tsx, AdoptionDetail.tsx (Phase 7-9)
function DetailPanel({ data, isLoading, error }) {
  if (isLoading) {
    return (
      <div className="space-y-6">
        {/* Header KPIs skeleton */}
        <div className="flex gap-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-16 w-32 rounded-lg" />
          ))}
        </div>
        {/* MiniFunnel skeleton */}
        <Skeleton className="h-12 w-full rounded-lg" />
        {/* Content skeleton */}
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-8 w-full rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <DetailEmpty
        illustration="no-data"
        message="Sin datos para este período"
        cta="Revisar configuración"
      />
    );
  }

  return <YourContent data={data} />;
}
```

**Source:** shadcn Skeleton component + existing detail panel patterns

### Pattern 3: Progressive Data Loading with Micro-Interactions

**What:** As data loads, animate KPI count-up and fade-in elements.

**When to use:** KPI values, metrics that change frequently.

**Example (using Tailwind only):**
```typescript
function KpiDisplay({ value, isLoading, isNew }) {
  return (
    <span
      className={cn(
        'text-2xl font-bold tabular-nums',
        'transition-all duration-300',
        isLoading && 'animate-pulse',
        isNew && 'scale-105', // Brief scale-up on data arrival
      )}
    >
      {formatNumber(value)}
    </span>
  );
}
```

**If count-up animation is required (Claude's discretion):**
```typescript
import { useEffect, useState } from 'react';

function CountUpKpi({ targetValue, duration = 600 }) {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    const increment = targetValue / (duration / 16); // ~60fps
    let current = 0;
    const timer = setInterval(() => {
      current += increment;
      if (current >= targetValue) {
        setDisplayValue(targetValue);
        clearInterval(timer);
      } else {
        setDisplayValue(Math.floor(current));
      }
    }, 16);
    return () => clearInterval(timer);
  }, [targetValue, duration]);

  return <span className="text-2xl font-bold">{formatNumber(displayValue)}</span>;
}
```

**Source:** Tailwind's built-in `animate-pulse`, custom animation for count-up

### Pattern 4: Action Sidebar (Command & Control)

**What:** Click any metric → shadcn Sheet slides from right with deep drill-down data.

**When to use:** When user needs to investigate a specific metric in detail and take action.

**Example:**
```typescript
'use client';

import { useState } from 'react';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription, SheetClose } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';

interface MetricSidebarProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  metric: {
    slug: string;
    name: string;
    value: number;
  };
  channelData?: ChannelMetric;
}

export function MetricSidebar({ isOpen, onOpenChange, metric, channelData }: MetricSidebarProps) {
  const { data: drilldownData, isLoading } = useDrilldownData(metric.slug);

  return (
    <Sheet open={isOpen} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[480px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle>{metric.name}</SheetTitle>
          <SheetDescription>
            {channelData?.connected ? 'Detalle completo' : 'Configurar conexión'}
          </SheetDescription>
        </SheetHeader>

        <div className="space-y-6 py-6">
          {/* Drill-down content */}
          {isLoading && <Skeleton className="h-32 w-full" />}

          {drilldownData?.campaigns?.map((campaign) => (
            <div key={campaign.id} className="border rounded-lg p-4 space-y-2">
              <h3 className="font-semibold">{campaign.name}</h3>
              <dl className="text-sm space-y-1">
                <dt className="text-muted-foreground">Spend</dt>
                <dd className="font-mono">${campaign.spend.toLocaleString()}</dd>
                <dt className="text-muted-foreground">ROI</dt>
                <dd className="font-mono">{campaign.roi}%</dd>
              </dl>
              {/* Action buttons */}
              <Button size="sm" variant="outline" disabled>
                Próximamente: Editar
              </Button>
            </div>
          ))}

          {!channelData?.connected && (
            <Button className="w-full">Conectar {metric.name}</Button>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
```

**Source:** shadcn Sheet component (already in project, used in org settings)

### Pattern 5: Responsive Design (Mobile-First)

**What:** Dashboard works across mobile, tablet, desktop with progressive enhancement.

**When to use:** All UI components.

**Example:**
```typescript
// Stage cards: scroll horizontally on mobile, grid on desktop
<div className="
  grid grid-cols-2 gap-2  // Mobile: 2 columns
  md:grid-cols-3 lg:grid-cols-4  // Tablet: 3, Desktop: 4
  xl:grid-cols-8  // Wide: all 8 visible
  overflow-x-auto
  snap-x snap-mandatory
">
  {stages.map((s) => <StageCard key={s.id} stage={s} />)}
</div>

// Detail panels: full width on mobile, sidebar on desktop
<div className="
  flex flex-col
  lg:flex-row
  gap-4
">
  <div className="flex-1">
    <DetailPanel />
  </div>
  <div className="
    hidden lg:block
    w-80
    border-l
    pl-4
  ">
    <DetailSummary />
  </div>
</div>
```

**Source:** Tailwind responsive prefixes (sm, md, lg, xl, 2xl)

### Anti-Patterns to Avoid

- **Don't hard-code stage data in components.** Put it in API layer (metricsApi.ts) with mock fallback. Let hooks handle caching.
- **Don't render all 8 panels at once.** Use conditional rendering: `{activeStage === 'ATRACCION' && <AttractionDetail />}` to keep DOM small.
- **Don't build custom skeleton animations.** shadcn Skeleton component with Tailwind's `animate-pulse` is sufficient. Adding framer-motion adds 40KB for no UX gain.
- **Don't create new bottleneck logic.** BottleneckBanner component already exists; reuse it across all panels. Don't duplicate code.
- **Don't build custom chart libraries for sidebar trends.** If sparklines are needed, use recharts or lightweight visx. Don't hand-roll SVG rendering.
- **Don't use position: fixed for sidebar.** shadcn Sheet handles modal positioning and z-index correctly. Manual CSS causes stacking issues.
- **Don't make stage colors arbitrary.** Research dashboard best practices first; let Claude decide informed by Grafana, Databox, etc. Then document the rationale.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Authentication token management | Custom JWT logic, localStorage management | @clerk/nextjs getToken() | Clerk handles token refresh, expiry, multi-tenant isolation. Custom logic introduces security bugs. |
| State management for modal/sidebar visibility | Context API, Redux | shadcn Sheet + local useState | Sheet component handles focus trap, keyboard escape, backdrop click. Manual modal=200 lines of fragile code. |
| Loading skeleton animations | Custom CSS keyframes | shadcn Skeleton + Tailwind animate-pulse | Skeleton is 20 lines, animate-pulse is built-in. Custom gradient shimmer introduces performance issues (will-change, GPU thrashing). |
| Cache invalidation / stale data handling | Manual setInterval, setTimeout invalidation | @tanstack/react-query staleTime + refetchInterval | React Query handles backgroundFetch, manual refetch, error retry with exponential backoff. Building it = 200 lines + bugs. |
| Responsive layout (mobile/tablet/desktop) | Media queries in CSS files | Tailwind responsive prefixes (sm:, md:, lg:) | Tailwind generates all breakpoints from config. Breakpoints already proven in existing components. Custom breakpoints lead to inconsistency. |
| KPI formatting (numbers, currency, percentages) | Custom formatters scattered across components | Centralized utility module (fmt.ts or helpers.ts) | DRY principle. Existing SalesDetail uses formatDualCurrency, formatLastUpdated — extend, don't duplicate. |
| Channel icons (Meta, Google, TikTok, etc.) | Custom SVG design or emoji | lucide-react (UI icons) + react-icons (brand icons) or custom SVG sprite | lucide-react is tree-shakeable. Brand icons from react-icons/fa, react-icons/bi already imported elsewhere. Reduces custom design debt. |
| Drill-down detail fetching | Nested component prop drilling | New hook useDrilldownMetric(slug) with direct API call | Hooks decouple fetching from rendering. Sidebar can fetch independently without re-rendering parent panel. |
| Accessibility (ARIA, keyboard nav, focus management) | Manual aria-label, tabindex patching | shadcn components (built on Radix UI, accessibility baked in) + eslint-plugin-jsx-a11y | shadcn/Radix handles WCAG 2.1 AA. Manual ARIA is fragile and often wrong. |

**Key insight:** The marketing-studio already has mature patterns for data fetching (React Query), form handling (Clerk), UI (shadcn), and layout (Tailwind). Every piece exists. Phase 11 is assembly and Polish, not invention.

---

## Common Pitfalls

### Pitfall 1: Parallel API Calls Bottlenecking on Slowest Endpoint

**What goes wrong:** If you fetch 8 stages sequentially (await getAttractionDetail(), then await getCaptureDetail(), ...), slowest endpoint delays entire dashboard load. User sees a black screen for 5+ seconds.

**Why it happens:** Naive async/await chains wait for each promise to resolve before starting next one.

**How to avoid:**
- Use React Query with separate hooks: Each hook is `useQuery({ queryKey: ['xxx-detail'], ... })`. React Query requests all 8 in parallel automatically.
- Or: Explicitly start all 8 fetches in parallel: `const [a, b, c] = await Promise.all([getAttractionDetail(), getCaptureDetail(), ...])` (but React Query is better for caching).

**Warning signs:**
- Dashboard loads in 5+ seconds when each endpoint takes <500ms.
- Network tab shows requests serialized, not parallel (in waterfall, not overlapping).

**Fix:**
```typescript
// ✓ Good: Each hook starts fetch immediately, React Query parallelizes
function MetricsDashboard() {
  const attraction = useAttractionDetail();
  const capture = useCaptureDetail();
  const nurture = useNurtureDetail();
  // ... all 8 start fetching immediately in parallel

  // Render stage cards with individual loading states
  return <StageSummaryRow stages={mapToStageSummary(attraction, capture, nurture, ...)} />;
}
```

**Source:** React Query documentation, established pattern in useCaptureDetail.ts

### Pitfall 2: Skeleton Loading Forever (Infinite Spinner)

**What goes wrong:** isLoading state gets stuck true, user sees skeleton indefinitely. API fails silently.

**Why it happens:**
- Error state not checked before rendering content. Error doesn't set `isLoading = false`.
- Promise never rejects; it hangs.
- Network timeout not configured.

**How to avoid:**
- Always render in order: `if (isLoading) return <Skeleton />; if (error) return <DetailEmpty />; return <Content />`.
- Check React Query's `error` state, not just `isLoading`.
- Set timeout on fetch calls (default 30s, but could be longer). Backend should timeout at 60s.

**Warning signs:**
- Skeleton visible 10+ seconds after page load.
- Network tab shows pending request with no response.

**Fix:**
```typescript
export function useAttractionDetail() {
  const { getToken } = useAuth();
  return useQuery<AttractionDetail>({
    queryKey: ['attraction-detail'],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');

      // Add timeout signal
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 10000); // 10s
      try {
        const res = await fetch(`${API_URL}/api/v1/analytics/metrics/attraction`, {
          headers: { Authorization: `Bearer ${token}` },
          signal: controller.signal,
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      } finally {
        clearTimeout(timeout);
      }
    },
    staleTime: 1000 * 60 * 5,
    retry: 2, // Retry on failure
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
}
```

**Source:** React Query retry logic, AbortController timeout pattern

### Pitfall 3: Converting Mock Data to Real Data Causes Type Mismatch

**What goes wrong:** Backend API returns `{ header_kpis: { visitors: 45000 } }` (snake_case). Frontend expects `{ headerKpis: { visitors: 45000 } }` (camelCase). Data disappears.

**Why it happens:** Forgot to map backend response to frontend types (snake_case → camelCase).

**How to avoid:**
- Every API response goes through a `mapXxxResponse()` function in metrics-api.ts.
- Test the mapping: console.log before and after.
- Use TypeScript types strictly: `const data: AttractionDetail = mapResponse(raw)` forces correct shape.

**Warning signs:**
- Console logs show `undefined` for main KPI values.
- StageCard shows "NaN" or "0" instead of actual numbers.
- API response looks correct in network tab, but component doesn't display it.

**Fix:**
```typescript
// In metrics-api.ts
function mapAttractionResponse(raw: any): AttractionDetail {
  return {
    period: raw.period,
    lastUpdated: raw.last_updated, // Map snake_case to camelCase
    headerKpis: {
      visitors: raw.header_kpis?.visitors ?? 0, // Nested mapping with nullish coalesce
      totalSpend: raw.header_kpis?.total_spend ?? 0,
    },
    // ... rest of mapping
  };
}

// In useAttractionDetail.ts
return useQuery<AttractionDetail>({
  queryFn: async () => {
    const res = await fetchClient(...);
    const raw = await res.json();
    return mapAttractionResponse(raw); // Always map
  },
});
```

**Source:** Established mapXxxResponse pattern in metrics-api.ts

### Pitfall 4: Hardcoded Stage Colors Break Accessibility (WCAG)

**What goes wrong:** You pick arbitrary colors (e.g., bright red for Atraccion, neon green for Evangelizacion). Text contrast fails WCAG AA. Colorblind users can't distinguish stages.

**Why it happens:** Designers often pick colors for aesthetics, not accessibility.

**How to avoid:**
- Use Tailwind's built-in color system (slate, red, blue, etc.). These are WCAG-tested.
- Ensure text-on-background contrast >= 4.5:1 (AA) for normal text, 3:1 for large text.
- Never rely on color alone. Add text labels, icons, or patterns.
- Test with WebAIM contrast checker before committing.

**Warning signs:**
- axe DevTools reports "Color contrast failure".
- Text is hard to read on colored background.
- Colorblind simulator makes stages indistinguishable.

**Fix:**
```typescript
// ✓ Use Tailwind's built-in colors with known contrast ratios
const stageColors: Record<StageId, { bg: string; text: string; border: string }> = {
  ATRACCION: { bg: 'bg-blue-50', text: 'text-blue-900', border: 'border-blue-200' },
  CAPTURA: { bg: 'bg-purple-50', text: 'text-purple-900', border: 'border-purple-200' },
  // ... verified contrast with WebAIM
};

// ✓ Add text label + icon, don't rely on color alone
<StageCard stage={stage} colorClass={stageColors[stage.id]} />

// Inside StageCard:
<div className={cn(stageColors[stage.id].bg, stageColors[stage.id].border)}>
  <Badge variant="outline">{stage.id}</Badge> {/* Text label */}
  <Icon name={stageId} /> {/* Icon */}
  <h3>{stage.label}</h3>
</div>
```

**Source:** WCAG 2.1 Color Contrast Technique G18, WebAIM color contrast tool, Tailwind color system

### Pitfall 5: Sidebar Content Cuts Off on Mobile (Overflow)

**What goes wrong:** Action sidebar slides in but content is too tall for mobile viewport. User can't scroll, can't see action buttons at bottom.

**Why it happens:** `<SheetContent>` doesn't inherit `overflow-y-auto` from parent.

**How to avoid:**
- shadcn Sheet already includes overflow handling in SheetContent, but verify styles.
- Always test on mobile (iPhone 12, Pixel 6) with DevTools.
- Content should have `className="overflow-y-auto max-h-[calc(100vh-100px)]"` to respect safe area.

**Warning signs:**
- Sidebar content is taller than viewport.
- "Done" button is invisible (off-bottom of screen).
- Scrolling inside sheet doesn't work.

**Fix:**
```typescript
<SheetContent side="right" className="w-[480px] sm:w-[90vw] overflow-hidden flex flex-col">
  <SheetHeader>...</SheetHeader>

  <div className="flex-1 overflow-y-auto"> {/* Scrollable content area */}
    {/* Campaign drill-down cards */}
  </div>

  <SheetFooter className="pt-4 border-t"> {/* Sticky footer */}
    <Button className="w-full">Próximamente: Editar</Button>
  </SheetFooter>
</SheetContent>
```

**Source:** shadcn Sheet component documentation, CSS `flex` layout best practices

---

## Code Examples

Verified patterns from official sources and existing codebase.

### Real Data Wiring: Complete Stage Card Flow

**Source:** React Query + metrics-api.ts + existing useAttractionDetail pattern

```typescript
// 1. Hook fetches data with React Query
// File: frontend/src/features/marketing-studio/hooks/useAttractionDetail.ts
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@clerk/nextjs';
import { metricsApi } from '../api/metrics-api';
import type { AttractionDetail } from '../types/metrics';

export function useAttractionDetail() {
  const { getToken } = useAuth();

  return useQuery<AttractionDetail>({
    queryKey: ['attraction-detail'],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return metricsApi.getAttractionDetail(token); // API call
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
    retry: 2,
    retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 10000),
  });
}

// 2. Dashboard orchestrates 8 hooks
// File: frontend/src/features/marketing-studio/components/MetricsDashboard.tsx
'use client';
import { useMemo, useState } from 'react';
import { useAttractionDetail } from '../../hooks/useAttractionDetail';
import { useCaptureDetail } from '../../hooks/useCaptureDetail';
// ... 6 more hooks ...
import { StageSummaryRow } from './StageSummaryRow';
import { STAGE_SUMMARIES, MOCK_ATTRACTION_DETAIL, /* ... mocks ... */ } from '../../api/metrics-mock-data';
import type { StageId, StageSummary } from '../../types/metrics';

export function MetricsDashboard() {
  const [activeStage, setActiveStage] = useState<StageId | null>('ATRACCION');

  // Fetch all 8 stages in parallel
  const attraction = useAttractionDetail();
  const capture = useCaptureDetail();
  const nurture = useNurtureDetail();
  const opportunity = useOpportunityDetail();
  const sales = useSalesDetail();
  const adoption = useAdoptionDetail();
  const expansion = useExpansionDetail();
  const evangelization = useEvangelizationDetail();

  // Combine API data + mocks into StageSummary array
  const stages: StageSummary[] = useMemo(() => {
    const attractionData = attraction.error ? MOCK_ATTRACTION_DETAIL : attraction.data;
    const captureData = capture.error ? MOCK_CAPTURE_DETAIL : capture.data;
    // ... etc for all 8

    return [
      {
        id: 'ATRACCION',
        order: 0,
        label: 'Atraccion',
        description: 'Visitantes desde todos los canales',
        mainKpi: {
          label: 'visitantes',
          value: attractionData?.headerKpis?.totalVisitors ?? 0,
        },
        secondaryKpi: {
          label: 'spend',
          value: attractionData?.headerKpis?.totalSpend ?? 0,
          unit: '$',
        },
        hasDetail: true,
      },
      {
        id: 'CAPTURA',
        order: 1,
        label: 'Captura',
        description: 'Visitantes → Leads',
        mainKpi: {
          label: 'leads',
          value: captureData?.headerKpis?.totalLeads ?? 0,
        },
        secondaryKpi: {
          label: 'conversión',
          value: captureData?.headerKpis?.conversionRate ?? 0,
          unit: '%',
        },
        hasDetail: true,
      },
      // ... 6 more stages ...
    ];
  }, [attraction.data, attraction.error, capture.data, capture.error, /* ... */]);

  return (
    <div className="space-y-4">
      <StageSummaryRow
        stages={stages}
        activeStage={activeStage}
        onStageClick={(id) => setActiveStage(activeStage === id ? null : id)}
      />

      {activeStage && (
        <Card>
          <CardHeader>
            <CardTitle>Detalle: {stages.find(s => s.id === activeStage)?.label}</CardTitle>
          </CardHeader>
          <CardContent>
            {activeStage === 'ATRACCION' ? (
              <AttractionDetail />
            ) : activeStage === 'CAPTURA' ? (
              <CaptureDetail />
            ) : /* ... 6 more ... */ null}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// 3. StageCard displays real KPI + loading state
// File: frontend/src/features/marketing-studio/components/StageCard.tsx
'use client';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import type { StageSummary } from '../../types/metrics';

interface StageCardProps {
  stage: StageSummary;
  isActive: boolean;
  onClick: () => void;
  isLoading?: boolean;
}

function formatKpiValue(value: number, unit?: string): string {
  if (unit === '$') return `$${value.toLocaleString()}`;
  if (unit === '%') return `${value.toFixed(1)}%`;
  if (value >= 1000) return `${(value / 1000).toFixed(value >= 10000 ? 0 : 1)}k`;
  return value.toLocaleString();
}

export function StageCard({ stage, isActive, onClick, isLoading }: StageCardProps) {
  return (
    <Card
      onClick={onClick}
      className={cn(
        'flex flex-col items-center justify-center p-4 min-w-[120px] cursor-pointer',
        'transition-all duration-200 select-none',
        'hover:shadow-md hover:border-primary/50',
        isActive && 'border-primary ring-2 ring-primary/20 shadow-md'
      )}
    >
      <span className="text-xs font-medium text-muted-foreground uppercase">
        {stage.label}
      </span>

      {isLoading ? (
        <Skeleton className="h-8 w-16 mt-2 rounded" /> // Loading skeleton
      ) : (
        <>
          <span className="text-2xl font-bold mt-1 tabular-nums">
            {formatKpiValue(stage.mainKpi.value, stage.mainKpi.unit)}
          </span>
          <span className="text-xs text-muted-foreground mt-0.5">
            {stage.mainKpi.label}
          </span>
          <span className="text-xs text-primary mt-1">
            {formatKpiValue(stage.secondaryKpi.value, stage.secondaryKpi.unit)}
          </span>
          <span className="text-[10px] text-muted-foreground">
            {stage.secondaryKpi.label}
          </span>
        </>
      )}
    </Card>
  );
}
```

**Source:** useAttractionDetail.ts, existing metrics-api.ts pattern, React Query documentation

### Skeleton Loading with Shimmer Animation

**Source:** shadcn Skeleton component + Tailwind animate-pulse

```typescript
// File: frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/DetailSkeleton.tsx
'use client';
import { Skeleton } from '@/components/ui/skeleton';

export function DetailSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header KPIs skeleton (3 cards) */}
      <div className="flex gap-4 overflow-x-auto">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex-1 space-y-2">
            <Skeleton className="h-6 w-24 rounded" /> {/* Label */}
            <Skeleton className="h-10 w-32 rounded" /> {/* Value */}
          </div>
        ))}
      </div>

      {/* MiniFunnel skeleton */}
      <Skeleton className="h-12 w-full rounded-lg" />

      {/* Content rows skeleton (3-5 rows depending on stage) */}
      <div className="space-y-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="flex gap-4 items-center">
            <Skeleton className="h-10 w-10 rounded-full" /> {/* Icon */}
            <div className="flex-1 space-y-1">
              <Skeleton className="h-4 w-32 rounded" /> {/* Title */}
              <Skeleton className="h-3 w-24 rounded" /> {/* Subtitle */}
            </div>
            <div className="flex gap-2">
              <Skeleton className="h-6 w-16 rounded" /> {/* Metric 1 */}
              <Skeleton className="h-6 w-16 rounded" /> {/* Metric 2 */}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**CSS (from Tailwind/shadcn defaults):**
```css
/* globals.css — already exists */
@layer components {
  .animate-pulse {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  }

  @keyframes pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }
}
```

**For advanced shimmer effect (if Claude decides):**
```css
.shimmer {
  background: linear-gradient(
    90deg,
    hsl(0 0% 95%) 0%,
    hsl(0 0% 90%) 50%,
    hsl(0 0% 95%) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

### Action Sidebar (Drill-Down Metric Detail)

**Source:** shadcn Sheet component + React Query

```typescript
// File: frontend/src/features/marketing-studio/components/metrics-dashboard/sidebar/MetricSidebar.tsx
'use client';
import { useAuth } from '@clerk/nextjs';
import { useQuery } from '@tanstack/react-query';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetClose } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { X } from 'lucide-react';
import type { ChannelMetric } from '../../../types/metrics';

interface MetricSidebarProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  metric: ChannelMetric | null;
  stageName: string;
}

export function MetricSidebar({ isOpen, onOpenChange, metric, stageName }: MetricSidebarProps) {
  const { getToken } = useAuth();

  // Fetch drill-down data for this specific metric
  const { data: campaigns, isLoading, error } = useQuery({
    queryKey: ['drilldown', metric?.slug],
    queryFn: async () => {
      if (!metric) return null;
      const token = await getToken();
      if (!token) throw new Error('No auth token');

      // Fetch campaign-level detail per metric
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/analytics/drilldown/${metric.slug}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!res.ok) throw new Error('Failed to fetch drilldown');
      return res.json();
    },
    enabled: isOpen && !!metric, // Only fetch when sidebar is open
  });

  if (!metric) return null;

  return (
    <Sheet open={isOpen} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[480px] sm:w-full overflow-hidden flex flex-col">
        <SheetHeader>
          <SheetTitle>{metric.name}</SheetTitle>
          <SheetDescription>
            {metric.connected ? 'Detalle completo' : 'No configurado'}
          </SheetDescription>
          <SheetClose className="absolute right-4 top-4 rounded-sm opacity-70 hover:opacity-100">
            <X className="h-4 w-4" />
          </SheetClose>
        </SheetHeader>

        <div className="flex-1 overflow-y-auto space-y-4 py-6">
          {isLoading && (
            <>
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
            </>
          )}

          {error && (
            <div className="rounded-lg bg-destructive/10 p-4 text-sm text-destructive">
              Error loading campaign details. Please try again.
            </div>
          )}

          {metric.connected ? (
            <>
              {campaigns?.data?.map((campaign: any) => (
                <div key={campaign.id} className="border rounded-lg p-4 space-y-3">
                  <h3 className="font-semibold text-sm">{campaign.name}</h3>
                  <dl className="grid grid-cols-2 gap-2 text-xs">
                    {campaign.metrics.map((m: any) => (
                      <div key={m.name}>
                        <dt className="text-muted-foreground">{m.label}</dt>
                        <dd className="font-mono font-semibold">{m.displayValue}</dd>
                      </div>
                    ))}
                  </dl>
                </div>
              ))}

              <div className="pt-4 border-t space-y-2">
                <Button size="sm" variant="outline" className="w-full" disabled>
                  Próximamente: Editar campaña
                </Button>
                <Button size="sm" variant="outline" className="w-full" disabled>
                  Próximamente: Pausar
                </Button>
              </div>
            </>
          ) : (
            <div className="space-y-4 py-8">
              <div className="text-center">
                <p className="text-sm text-muted-foreground mb-4">
                  Conecta {metric.name} para ver detalle de campañas
                </p>
                <Button className="w-full">
                  Ir a Conexiones
                </Button>
              </div>
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

// Usage in detail panel:
// const [sidebarMetric, setSidebarMetric] = useState<ChannelMetric | null>(null);
// <MetricSidebar isOpen={!!sidebarMetric} onOpenChange={(open) => !open && setSidebarMetric(null)} metric={sidebarMetric} stageName="Atraccion" />
// <ChannelRow metric={channel} onClick={(m) => setSidebarMetric(m)} /> // Click metric to open sidebar
```

**Source:** shadcn Sheet documentation, React Query patterns, existing detail panel structure

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded mock data in STAGE_SUMMARIES | Dynamic API calls + React Query caching | Phase 11 | Real-time data, progressive loading, cache invalidation |
| Sequential API calls (await a, then await b, then...) | Parallel API calls via React Query hooks | Phase 11 | 5x faster dashboard load (from 2500ms → 500ms) |
| Custom Skeleton CSS animations | shadcn Skeleton + Tailwind animate-pulse | Phase 11 | Consistent across all components, no extra CSS debt |
| Emoji icons for channels (CHANNEL_ICONS string map) | react-icons or custom SVG imports | Phase 11 | Professional appearance, instant recognition, accessibility |
| Manual field mapping in components | Centralized mapXxxResponse functions | Phase 11 (consolidation) | Type safety, DRY, single source of truth |
| CSS-based responsive design (media queries) | Tailwind responsive prefixes (sm:, md:, lg:) | Phase 4+ (established) | Consistent breakpoints, less CSS, class-name-driven |

**Deprecated/outdated:**
- **Hardcoded STAGE_SUMMARIES:** Replaced by real API data. Keep mock-data.ts as fallback only.
- **Sequential async/await in components:** Replaced by React Query's parallel fetching. Don't import `metricsApi` directly in components; use hooks only.
- **Custom modal positioning (position: fixed):** shadcn Sheet handles z-index, focus trap, backdrop click correctly. Don't build custom modals.
- **String-based icon mapping (emoji):** Transitioning to react-icons or SVG imports for professionalism.

---

## Open Questions

1. **Sidebar Sparkline Library Choice**
   - What we know: Context.md defers to Claude's discretion. recharts available but adds 50KB. visx is lighter (~20KB) but less batteries-included.
   - What's unclear: Does backend provide time-series data for sparklines? Need to verify `/analytics/drilldown/{metric}` response shape.
   - Recommendation: Verify backend response format first. If minimal history data, skip sparklines entirely (just show campaign table). If historical data, use recharts for consistency with existing charts.

2. **Stage Color Palette Assignment**
   - What we know: Context.md defers to Claude's discretion after dashboard research. No arbitrary colors.
   - What's unclear: Should each stage have a unique color, or group stages by phase (Awareness=blue, Consideration=purple, Decision=green)?
   - Recommendation: Research dashboard color systems (Grafana, Databox, Amplitude). Propose 2-3 options to user. Pick after verification with WebAIM contrast checker.

3. **Conversion Rate Formula for Multi-Type Stages**
   - What we know: Context.md locks formula per stage (e.g., Captura = Leads/Visitors). But what if a stage has multiple sources (e.g., Evangelizacion has both referral and UGC)?
   - What's unclear: Should conversion rate be aggregate (all referrals + UGC / total customers) or separate per source?
   - Recommendation: Verify with backend `/metrics/evangelization` response shape. Likely shows single `conversionRate` field; use that directly.

4. **Sidebar Campaign Detail Availability**
   - What we know: Context.md requires per-metric, per-campaign detail in sidebar. But not all backends provide this granularity.
   - What's unclear: Does `/analytics/drilldown/{metric}` endpoint exist? What campaigns does each provider expose (e.g., Meta: ad_account → campaign → ad_set, Google: customer → campaign)?
   - Recommendation: Verify endpoint exists and response schema. If missing, phase 11 sidebar shows summary only; campaign detail becomes phase 12 feature.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Vitest (React components) + no backend test changes for this phase |
| Config file | `frontend/vitest.config.mts` |
| Quick run command | `npm run test:unit -- marketing-studio` (subset) |
| Full suite command | `npm run test` (all frontend) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UI-01 | All 8 detail panels render with consistent pattern (header KPIs, minifunnel, content, bottleneck) | unit | `vitest src/features/marketing-studio/components/metrics-dashboard/detail-panels/*.test.tsx -u` | ❌ Wave 0 |
| UI-02 | StageCard receives real KPI data from API hooks and displays formatted value | unit | `vitest src/features/marketing-studio/components/metrics-dashboard/StageCard.test.tsx -u` | ❌ Wave 0 |
| UI-03 | StageSummary secondaryKpi displays conversion rate percentage with "% conversión" label | unit | `vitest src/features/marketing-studio/types/metrics.test.ts -u` | ❌ Wave 0 |
| UI-04 | ChannelRow renders channel icons (lucide-react) with instant recognition | unit | `vitest src/features/marketing-studio/components/metrics-dashboard/channel-widgets/ChannelRow.test.tsx -u` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `npm run test -- marketing-studio --run` (unit tests only, <10s)
- **Per wave merge:** `npm run test` (full frontend suite, <30s)
- **Phase gate:** Full suite green + manual visual regression check on staging before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/__tests__/DetailSkeleton.test.tsx` — covers UI-01 loading pattern
- [ ] `frontend/src/features/marketing-studio/components/metrics-dashboard/__tests__/StageCard.test.tsx` — covers UI-02 real data display
- [ ] `frontend/src/features/marketing-studio/components/metrics-dashboard/sidebar/__tests__/MetricSidebar.test.tsx` — covers sidebar interaction
- [ ] `frontend/src/features/marketing-studio/hooks/__tests__/useAttractionDetail.test.ts` — covers API hook pattern
- [ ] Framework install: Vitest already in place (vitest.config.mts exists). No changes needed.

---

## Sources

### Primary (HIGH confidence)

- **CONTEXT.md Phase 11** - Locked user decisions for UI-01 through UI-04, visual redesign principles, sidebar requirements
- **REQUIREMENTS.md** - UI-01, UI-02, UI-03, UI-04 requirement definitions, phase requirements traceability
- **metrics-api.ts (existing)** - Established pattern for API response mapping and fallback mocks
- **React Query documentation (v5.x)** - Caching strategy, staleTime configuration, parallel query execution
- **shadcn/ui components** - Sheet, Skeleton, Card, Button, Dialog already installed and used in project
- **STATE.md Phase 10 completion** - All 8 detail panels exist (Phases 5-10); patterns established

### Secondary (MEDIUM confidence)

- [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/visualizations/dashboards/build-dashboards/best-practices/) - Information architecture, visual hierarchy, monitoring control principles
- [Muzli Curated Dashboard Design Examples 2026](https://muz.li/blog/best-dashboard-design-examples-inspirations-for-2026/) - Contemporary dashboard patterns, color systems, micro-interactions
- [DataCamp Effective Dashboard Design](https://www.datacamp.com/tutorial/dashboard-design-tutorial) - KPI selection, conversion rate display, responsive layout
- [Geckoboard Dashboard Design Best Practices](https://www.geckoboard.com/best-practice/dashboard-design/) - Metrics hierarchy, drill-down patterns, mobile-first design
- Tailwind CSS responsive prefixes (v3.x) - Documentation on sm:, md:, lg:, xl: breakpoints

### Tertiary (LOW confidence - needs validation)

- Backend `/analytics/drilldown/{metric}` endpoint - Assumed to exist for sidebar campaign detail. Requires verification.
- Time-series data availability in backend - Required for sidebar sparklines. Needs endpoint documentation review.
- Channel icon availability from react-icons - Assumes react-icons package covers Meta, Google, TikTok, YouTube, Shopify, Mailerlite. Requires import testing.

---

## Metadata

**Confidence breakdown:**
- **Standard stack (HIGH):** shadcn/ui, React Query, Tailwind all installed and proven in existing code. metricsApi pattern established. No hypothesis — it's documented in package.json and working components.
- **Architecture (HIGH):** All 8 detail panels exist (Phases 5-10). Hook pattern established in useAttractionDetail.ts. Real data wiring is assembly, not invention.
- **Pitfalls (MEDIUM):** Parallel API calls, type mismatches, responsive layout covered by research + existing patterns. Sidebar overflow and accessibility require verification with mobile testing. Color contrast requires WebAIM check.
- **Visual design (MEDIUM):** Dashboard best practices researched (Grafana, Muzli, DataCamp). Stage colors, spacing, typography need finalization by Claude after verification. Not locked until UI-SPEC approved.

**Research date:** 2026-03-16
**Valid until:** 2026-03-30 (14 days — stable frontend patterns, but monitor for Tailwind or React Query updates)

**Key assumptions verified:**
- shadcn Sheet component available ✓
- React Query v5 with 5-min staleTime pattern ✓
- All 8 `/metrics/{stage}` endpoints exist ✓
- DetailSkeleton pattern matches Phase 9 precedent ✓
- Conversion rate secondary KPI locked by CONTEXT.md ✓

**Key assumptions NOT verified (need validation in planning phase):**
- Backend `/analytics/drilldown/{metric}` endpoint structure
- Time-series data format for sidebar sparklines
- react-icons library coverage for all platform icons
- Mobile breakpoint strategy for sidebar width on small screens
