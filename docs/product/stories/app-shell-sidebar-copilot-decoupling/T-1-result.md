# T-1 Result — Phase 1 Skeleton DashboardShell + SSoT modules + hooks

**Story:** app-shell-sidebar-copilot-decoupling
**Ticket:** T-1
**State:** pushed
**Builder:** claude-sonnet (builder-frontend)
**Date:** 2026-05-07

## Diff summary

7 new files + 1 modified file + 2 new test files:

| File | Status | Description |
|---|---|---|
| `frontend/src/lib/tokens/z-index.ts` | NEW | Z_INDEX + Z_INDEX_CLASSES SSoT. AD5 z-index scale (40/50/60/70/80/85/90/100). |
| `frontend/src/features/copilot/lib/copilot-shell-widths.ts` | NEW | COPILOT_WIDTHS SSoT (collapsed:60 rail:280 chat:400 expanded:460 max:680). Fixes drift. |
| `frontend/src/hooks/use-viewport.ts` | NEW | SSR-safe matchMedia wrapper. Lazy useState init. Breakpoints: mobile<768, tablet 768-1023, desktop≥1024. |
| `frontend/src/stores/shell-mutex-store.ts` | NEW | Vanilla zustand store factory. Tenant-namespaced localStorage persistence. State: activePanel(app-sidebar\|copilot\|null). |
| `frontend/src/hooks/use-shell-mutex.ts` | NEW | React hook wrapping store. useMemo per tenantId. Phase 1 useEffect no-op reserved for T-4. |
| `frontend/src/components/shared/layout/DashboardShell.tsx` | NEW | Server Component passthrough → DashboardShellClient. |
| `frontend/src/components/shared/layout/DashboardShellClient.tsx` | NEW | "use client". Identical JSX to DashboardLayoutClient (no behavior change Phase 1). |
| `frontend/src/app/(main)/[tenantId]/(dashboard)/layout.tsx` | MODIFIED | Replaced DashboardLayoutClient with DashboardShell. DashboardLayoutClient.tsx kept on disk for rollback (Phase 8 deletes). |
| `frontend/src/hooks/__tests__/use-viewport.test.ts` | NEW | 5 tests: SSR null, mobile/tablet/desktop detection, transition. |
| `frontend/src/components/shared/layout/__tests__/use-shell-mutex.test.tsx` | NEW | 8 tests: store actions, tenant isolation, DashboardShell smoke. |

## Validator outputs

| Validator | Result | Detail |
|---|---|---|
| `fe_typecheck` | PASS | `tsc --noEmit` — 0 errors |
| `fe_lint_shell` | PASS | ESLint 10 T-1 files `--max-warnings=0` — 0 errors, 0 warnings |
| `fe_arch_fitness_full` | PASS | 25 arch test files, 51/51 tests pass |
| Vitest full suite | PASS | 1996/1996 tests, 269 test files |
| Coverage | PASS | 32%/27%/29%/33% (all ≥ 20% threshold) |

## Out-of-scope (Phase 1 boundary confirmed)

- No mutex enforcement (T-4)
- No min-width floor on sidebar (T-2)
- No copilot drawer width consumption (T-3)
- No z-index token consumption in existing components (T-5..T-9)
- No DashboardLayoutClient.tsx deletion (T-8 / Phase 8)

## Commit SHA

(populated post-push)
