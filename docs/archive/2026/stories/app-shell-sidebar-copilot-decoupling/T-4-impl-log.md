# T-4 Impl Log — app-shell-sidebar-copilot-decoupling

**Ticket:** T-4 — Phase 4 Activate useShellMutex policy + remove SidebarContext inline matchMedia (Scenarios 1, 3)
**Owner:** claude-sonnet (builder-frontend)
**Assigned at:** 2026-05-08T21:00:00Z
**Estimate:** 3h
**Acceptance validators:** scenario_1_min_width_unit, scenario_3_mobile_mutex_unit, fe_typecheck, fe_lint_shell, fe_arch_fitness_full
**Depends on:** T-3 (DONE — commit f784ce75)

## Plan

Activate mutex policy. Remove SidebarContext inline matchMedia auto-collapse. Wire AppSidebar Sheet trigger to useShellMutex. CopilotSidebar backdrop+Esc dispatch mutex.

- MODIFY `frontend/src/components/shared/layout/SidebarContext.tsx` — remove inline `useEffect+matchMedia(<1279)` auto-collapse. Add `expandSidebar()` + `collapseSidebar()` imperative actions.
- MODIFY `frontend/src/components/shared/layout/DashboardShellClient.tsx` — mount `useShellMutex()` (effects fire internally now T-4).
- MODIFY `frontend/src/features/copilot/components/CopilotSidebar.tsx` — backdrop click + Esc handler dispatch `useShellMutex.closePanel()` instead of `setSidebarState('collapsed')` directly.
- MODIFY `frontend/src/components/shared/layout/AppSidebar.tsx` — remove local `isMobileOpen useState`. Wire `<Sheet open={shellMutex.activePanel === 'app-sidebar'} onOpenChange={...}>`. NOTE: Sheet primitive YA EXISTE L667-687 — refactor existing trigger, NO new Sheet (per AD8).
- TESTS: `frontend/src/components/shared/layout/__tests__/use-shell-mutex.test.ts` (mutex policy unit per breakpoint + ping-pong idempotency).

TDD RED→GREEN. Loop hasta validators GREEN o cap_reached.

## Iteration log

### Iter 1 — 2026-05-08

**RED phase** — wrote Phase 4 test suites first (21 tests, 3 RED: `collapseSidebar/expandSidebar not a function`).

**GREEN phase** — implemented in order:
1. `SidebarContext.tsx`: removed inline `useEffect+matchMedia("<1279px")` auto-collapse; added `collapseSidebar()` + `expandSidebar()` with functional updater form (no-op if already target state) and localStorage sync.
2. `ShellMutexContext.tsx` (NEW): createContext + Provider alias + `useShellMutexContext()` returning undefined gracefully outside shell.
3. `use-shell-mutex.ts`: activated viewport-aware mutex policy effect — desktop (≥1280px) no-op; tablet (768-1279px) copilot→collapseSidebar; mobile (<768px) strict mutex both directions. Added `useSidebar()` + `useCopilotStore` + `useViewport` imports.
4. `DashboardShellClient.tsx`: added `DashboardContent` inner component that mounts `useShellMutex(tenantId)` inside `SidebarProvider` boundary; wraps in `ShellMutexProvider`. Note: `useShellMutex` must be inside `SidebarProvider` (calls `useSidebar()` internally).
5. `AppSidebar.tsx`: removed `useState(false)` for `isMobileOpen`; derived from `shellMutex?.activePanel === "app-sidebar"`; added `useCallback` shim for `setIsMobileOpen` → `openPanel/closePanel`; wired Sheet `open` + `onOpenChange` to mutex.
6. `CopilotSidebar.tsx`: consumed `useShellMutexContext()`; backdrop `onClick` dispatches `shellMutex?.closePanel()` before `setSidebarState`; added `case "Escape"` with mutex dispatch.

**Results:**
- 21/21 tests PASS (Phase 1 preserved, Phase 4 added: SidebarContext expand/collapse, matchMedia removal, ping-pong idempotency, tenant isolation)
- 51/51 architecture fitness tests PASS
- `tsc --noEmit`: 0 errors (scope files; pre-existing untracked parallel-session errors excluded)
- ESLint: 0 errors, 270 warnings (all pre-existing; no new warnings from T-4 files)
- Prettier: 2 format fixes applied (AppSidebar.tsx, DashboardShellClient.tsx)

**Commit:** `6b691987` — pushed to `development`
**Files:** 7 modified/created (ShellMutexContext.tsx new + 6 modified)
