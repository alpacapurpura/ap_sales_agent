# T-5 Result — Phase 5 CopilotFAB + AppSidebar mobile aria-labels

**Story:** app-shell-sidebar-copilot-decoupling
**Ticket:** T-5
**Builder:** claude-sonnet
**Completed:** 2026-05-08
**State:** pushed
**Commit:** 3010787e

## Verdict: PASS

All acceptance validators GREEN.

## Validators

| Validator | Result | Detail |
|---|---|---|
| `scenario_3_mobile_mutex_unit` | PASS | 14/14 tests (10 CopilotFAB + 4 AppSidebar mobile drawer) |
| `fe_typecheck` | PASS | 0 TypeScript errors (tsc --noEmit) |
| `fe_lint_shell` | PASS | 0 ESLint errors, 0 new warnings |
| Architecture fitness | PASS | 25 files, 51 tests |

## Deliverables

### NEW: `frontend/src/features/copilot/components/CopilotFAB.tsx`
Mobile-only Floating Action Button to reopen Copilot sidebar.
- Returns null on desktop/tablet (viewport >= md)
- Returns null when copilot sidebarState !== 'collapsed'
- `aria-label="Abrir asistente"` (Spanish neutro)
- `z-[70]` via `Z_INDEX_CLASSES.FAB` (no hardcoded z-NN)
- `onClick` → `shellMutex?.openPanel("copilot")`
- Graceful when ShellMutex is undefined (optional chaining)

### MODIFY: `frontend/src/components/shared/layout/DashboardShellClient.tsx`
Mounted `<CopilotFAB />` after `<CopilotSidebar />` in DashboardContent. Component self-guards.

### MODIFY: `frontend/src/components/shared/layout/AppSidebar.tsx`
- `role="status" aria-live="polite"` region in Sheet content — announces "Menú principal abierto/cerrado" to screen readers
- `<SheetClose aria-label="Cerrar menú principal">` — accessible close, visually hidden (sr-only), exposed on keyboard focus
- Note: `aria-label="Abrir menú principal"` on hamburger was already added in T-4

### NEW: `frontend/src/features/copilot/components/__tests__/CopilotFAB.test.tsx`
10 tests: visibility conditions, aria-label, z-index class, mutex dispatch, graceful undefined

### NEW: `frontend/src/components/shared/layout/__tests__/AppSidebar-mobile-drawer.test.tsx`
4 tests: hamburger aria-label, Sheet trigger interactivity, SheetClose aria-label, aria-live region

## Notable implementation decisions

1. **Radix Portal test fix**: `document.querySelector` required (not `container.querySelector`) because Radix Sheet renders via Portal outside the React test container.

2. **SheetClose aria-label strategy**: Shadcn's internal SheetContent already renders an English "Close" button. Added a separate `<SheetClose aria-label="Cerrar menú principal" className="sr-only focus:not-sr-only ...">` — screen-reader accessible without visual duplication.

3. **Graceful mutex**: `shellMutex?.openPanel("copilot")` handles undefined context without crash — tested in "works when shellMutex is undefined" case.

## Blocks unblocked

T-6 (Phase 6 — Z-index migration to tokens) is now unblocked.
