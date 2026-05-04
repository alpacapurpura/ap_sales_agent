# Frontend Performance Refactor - Design Spec

**Date:** 2026-04-08
**Problem:** App hangs on Growth Studio entry; 60+ performance anti-patterns across frontend
**Approach:** Full refactor (Enfoque B) - 6 parallel workstreams

## Root Causes

### RC1: useSearchParams() in GrowthStudioContext (CRITICAL)
- **File:** `features/growth-studio/components/metrics-dashboard/context/GrowthStudioContext.tsx`
- `useSearchParams()` returns new object every render
- Used in dependency arrays of `handleChannelClick` and `handleChannelSidebarClose` callbacks
- Callbacks recreate → context `useMemo` invalidates → 38+ consumers re-render → infinite cascade

### RC2: React Query no global defaults (CRITICAL)
- **File:** `app/providers.tsx`
- `QueryClient` initialized with NO options
- Default `staleTime: 0` → all queries instantly stale
- Default `refetchOnWindowFocus: true` → tab switch = cascade refetch
- 16 of 21 useQuery hooks in growth-studio missing `gcTime`
- 6+ concurrent queries fire on Growth Studio mount

### RC3: force-dynamic + "use client" in layouts (HIGH)
- **Files:** `app/layout.tsx:5`, `app/(main)/layout.tsx:4`, `app/(main)/[tenantId]/(dashboard)/layout.tsx:1`
- Root + main layouts: `export const dynamic = "force-dynamic"` → all caching disabled
- Dashboard layout: `"use client"` → 50+ child routes lose SSR benefits
- 6x sequential `getToken()` calls before content renders

### RC4: Copilot render loops (HIGH)
- **File:** `features/copilot/components/WithCopilot.tsx`
- `getValue` prop passed as inline arrow → new ref every render → useEffect re-runs
- `copilot:collect-values` event triggers all WithCopilot instances → store updates → re-render loop
- **File:** `features/copilot/hooks/useCopilotNavigator.ts:86`
- useEffect deps include `pendingUIActions` (array) + `executeAction` → unstable references

## Tech Stack Context

- Next.js 16.2.1, React 19.2.3, React Query 5.90.19, Zustand 5.0.12
- `useShallow` available from zustand (not currently used)
- `react-window` / `@tanstack/react-virtual` NOT installed
- All recharts usage through `components/ui/chart.tsx` wrapper (no direct imports)

## Workstreams

### WS1: GrowthStudioContext + Shell
**Files:** `GrowthStudioContext.tsx`, `growth-studio/layout.tsx`
- Replace `useSearchParams()` dependency with `useRef` + read inside callbacks
- Split context into `GrowthStudioStateContext` (reactive) + `GrowthStudioActionsContext` (stable)
- `React.memo()` on `GrowthStudioShell`
- Memoize `metaAdsDashboardOpen` separately

### WS2: React Query Defaults
**Files:** `app/providers.tsx`, 21 hooks in `features/growth-studio/hooks/` and `features/growth-studio/api/`
- Global defaults: `staleTime: 5min`, `gcTime: 10min`, `refetchOnWindowFocus: false`, `retry: 1`
- Add `gcTime: 30 * 60 * 1000` to all 16 hooks missing it
- Add `enabled` guards to stage detail hooks (only fetch when stage is active)

### WS3: Layouts - force-dynamic + server/client split
**Files:** `app/layout.tsx`, `app/(main)/layout.tsx`, `app/(main)/[tenantId]/(dashboard)/layout.tsx`
- Remove `force-dynamic` from root and main layouts
- Dashboard layout: extract `DashboardClientShell` component with "use client", keep layout as server component
- Move `CopilotPanel` and `SidebarProvider` into client shell

### WS4: Copilot Render Loops
**Files:** `WithCopilot.tsx`, `CopilotChat.tsx`, `useCopilotNavigator.ts`, `useCopilotChat.ts`, `copilot-store.ts`
- `WithCopilot`: accept `getValue` as stable ref (document requirement); use `useRef` internally to track latest value
- `useCopilotNavigator`: stabilize `executeAction` with proper deps; use functional update for queue
- `CopilotChat`: wrap with `React.memo()`
- Store selectors: use `useShallow` from zustand where selectors return objects/arrays

### WS5: Heavy Components + Code Splitting
**Files:** `chart.tsx`, `CampaignsTab.tsx`, `meta-view.tsx`, `SidebarContent.tsx`, `app-sidebar.tsx`
- `chart.tsx`: wrap in `next/dynamic` with `ssr: false`
- `CampaignsTab.tsx`: paginate campaign list (show 20 + "load more"), no new dependency needed
- Large components (meta-view, SidebarContent): split into sub-components with `React.memo()`
- `app-sidebar.tsx`: memoize `NavContent` to prevent re-render on navigation

### WS6: Memoization + Inline Handlers
**Scope:** Top 20 heaviest components across features/
- Add `React.memo()` to leaf components that receive props from re-rendering parents
- Replace inline `onClick={() => fn(arg)}` with `useCallback` in components with memoized children
- Zustand: `useShallow` for multi-field selectors across copilot consumers

## Testing Strategy
- Each workstream must pass: `ruff check` + `tsc --noEmit` + `vitest run` + `eslint`
- Manual verification: Growth Studio loads without hanging
- No new dependencies except potentially `@tanstack/react-virtual` if pagination isn't enough

## Out of Scope
- Backend API changes
- New E2E tests (existing smoke tests cover Growth Studio)
- Styling changes
