# T-1 Impl Log — app-shell-sidebar-copilot-decoupling

**Ticket:** T-1 — Phase 1 Skeleton DashboardShell + SSoT modules + hooks (no behavior change)
**Owner:** claude-sonnet (builder-frontend)
**Assigned at:** 2026-05-07T22:35:00Z
**Estimate:** 3h
**Acceptance validators:** fe_typecheck, fe_lint_shell, fe_arch_fitness_full

## Skills Consulted

| Skill | Why invoked | Decision |
|---|---|---|
| `frontend-expert` | Always-on: FSD-Lite boundaries, ESLint config, form-runtime defaults | Confirmed boundary matrix: `components/shared/layout/` + `hooks/` + `stores/` + `lib/tokens/` all valid |
| `tessl__react-patterns` | Always-on: error boundaries, loading/empty/error states, accessible markup | SSR-safe `useState(getInitialState)` lazy initializer pattern; `useLayoutEffect` for subscription-only |
| `tessl__nextjs-app-router-modularization` | Page mixes Server+Client concerns | Split: `DashboardShell.tsx` (Server passthrough) + `DashboardShellClient.tsx` ("use client") |
| `tessl__shadcn-ui` | Component selection | Reused `SidebarProvider` from existing Shadcn setup — no recreation |
| `tessl__tailwind` | Utility classes + tokens | `cn()` used in DashboardShellClient; `Z_INDEX_CLASSES` for Tailwind arbitrary values |
| `tessl__vitest` | TDD RED-first hook + component tests | Vitest + @testing-library/react; custom matchMedia mock factory |
| `tessl__zod` | N/A — no forms in T-1 | Not invoked |

## Plan

Phase 1 = skeleton + SSoT modules NO behavior change. Files:
- NEW SSoT: `frontend/src/lib/tokens/z-index.ts`, `frontend/src/features/copilot/lib/copilot-shell-widths.ts`
- NEW hooks: `frontend/src/hooks/use-viewport.ts`, `frontend/src/hooks/use-shell-mutex.ts`
- NEW store: `frontend/src/stores/shell-mutex-store.ts`
- NEW components: `frontend/src/components/shared/layout/DashboardShell.tsx` (Server) + `DashboardShellClient.tsx` (Client passthrough — same JSX as DashboardLayoutClient)
- MODIFY: `frontend/src/app/(main)/[tenantId]/(dashboard)/layout.tsx` — render `<DashboardShell>` (keep DashboardLayoutClient.tsx unused for rollback)
- Tests: use-viewport / use-shell-mutex (no-op state Phase 1) / DashboardShell render snapshot

TDD RED → GREEN → REFACTOR. Loop hasta validators GREEN o cap_reached (10 iter).

## Iteration log

### iter-1 (2026-05-07)

**TDD RED:** Created test files first.
- `src/hooks/__tests__/use-viewport.test.ts` — 5 tests (SSR null, mobile/tablet/desktop detection, transition)
- `src/components/shared/layout/__tests__/use-shell-mutex.test.tsx` — 8 tests (store actions, tenant isolation, DashboardShell smoke)

Both fail with import errors (files don't exist) → RED confirmed.

**GREEN:** Implemented all 7 new files + modified layout.tsx.

Key decisions:
- `useViewport`: lazy `useState(getInitialState)` initializer (reads DOM synchronously; SSR returns `SSR_INITIAL`). `useLayoutEffect` for subscriptions only (avoids `react-hooks/set-state-in-effect` ESLint error).
- `shell-mutex-store`: vanilla zustand `createStore` factory (not React `create`) for tenant-namespacing. localStorage persistence per-tenant.
- `useShellMutex`: `useMemo` for stable store per tenantId (no `useRef` write during render — avoids `react-hooks/refs` ESLint error).
- `DashboardShell`: Server Component passthrough. `DashboardShellClient`: `"use client"`, identical JSX to `DashboardLayoutClient` (no behavior change Phase 1).
- `layout.tsx`: removed `DashboardLayoutClient` import (sonarjs rule), kept file on disk for Phase 8 rollback.

**ESLint fixes applied:**
1. `react-hooks/refs` — removed stale `storeRef.current` write inside `useMemo`
2. `react-hooks/set-state-in-effect` — switched from `useEffect(setState...)` to lazy `useState(getInitialState)` initializer
3. `prettier/prettier` — reformatted `useMemo` call to single line
4. Stale `eslint-disable-next-line react-hooks/exhaustive-deps` removed (no longer needed after `useMemo` refactor)
5. `sonarjs/no-duplicate-string` — test constants extracted (`PANEL_SIDEBAR`, `PANEL_COPILOT`, `TEST_TENANT`)

**Viewport transition test fix:** `window.innerWidth` must be updated BEFORE calling `fireChange()` since `handleChange()` reads `window.innerWidth` directly.

### Validator results

| Validator | Result |
|---|---|
| `fe_typecheck` (`tsc --noEmit`) | PASS — 0 errors |
| `fe_lint_shell` (`eslint` 10 T-1 files `--max-warnings=0`) | PASS — 0 errors, 0 warnings |
| `fe_arch_fitness_full` (25 arch test files, 51 tests) | PASS — 51/51 |
| Full Vitest suite | PASS — 1996/1996 tests, 269 test files |
| Coverage | 32% statements / 27% branches / 29% functions / 33% lines (all ≥ 20% threshold) |
