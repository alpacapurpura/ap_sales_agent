# T-3 Impl Log — app-shell-sidebar-copilot-decoupling

**Ticket:** T-3 — Phase 3 Activate min-content-width floor 720px @≥1024 (Scenario 1)
**Owner:** claude-sonnet (builder-frontend)
**Assigned at:** 2026-05-08T20:30:00Z
**Estimate:** 2h
**Acceptance validators:** scenario_1_min_width_unit, fe_typecheck, fe_lint_shell
**Depends on:** T-2 (DONE — commit 0d8701c2 / 8f004bc8)

## Plan

DashboardShellClient main element gets lg:min-w-[var(--shell-content-min-width,720px)] floor + CSS var wiring at parent.

- MODIFY `frontend/src/components/shared/layout/DashboardShellClient.tsx` — apply `<main className='... lg:min-w-[var(--shell-content-min-width,720px)]'>` + parent wrapper `<div style={{ '--shell-content-min-width': '720px' }}>`
- NEW `frontend/src/components/shared/layout/__tests__/DashboardShell-min-width-floor.test.tsx` — Vitest unit (mocked viewport widths × copilot states; assert main.style.minWidth applied per breakpoint)

TDD RED→GREEN. Loop hasta validators GREEN o cap_reached.

## Iteration log

### Iteration 1 — 2026-05-08

**RED phase (TDD):**
- Created `DashboardShell-min-width-floor.test.tsx` with 11 tests covering:
  - CSS variable wiring (parent wrapper provides `--shell-content-min-width`)
  - main element class presence (`lg:min-w-[var(--shell-content-min-width,720px)]`)
  - CSS var reference and 720px fallback in class string
  - Children rendering preserved across all viewport widths
  - Structural position: wrapper is ancestor of main
- Result: 5 FAIL / 6 PASS (RED confirmed)

**GREEN phase:**
- Modified `DashboardShellClient.tsx`:
  - Added `SHELL_MIN_WIDTH_VAR` and `SHELL_MIN_WIDTH_PX` constants
  - Applied CSS var inline style to the outer `<div>` wrapper: `style={{ [SHELL_MIN_WIDTH_VAR]: SHELL_MIN_WIDTH_PX } as React.CSSProperties}`
  - Added `lg:min-w-[var(--shell-content-min-width,720px)]` class to `<main>` element
- Fixed prettier formatting (auto-fix)
- Result: 11/11 PASS (GREEN)

**Validators:**
- `scenario_1_min_width_unit`: 24/24 PASS (3 test files)
- `fe_typecheck`: PASS (0 errors in story scope; pre-existing growth-studio TS errors from parallel session unrelated)
- `fe_lint_shell`: PASS (0 errors; 8 pre-existing warnings in existing copilot components not touched)

**Files modified:**
- `frontend/src/components/shared/layout/DashboardShellClient.tsx` (MODIFY — min-width floor applied)
- `frontend/src/components/shared/layout/__tests__/DashboardShell-min-width-floor.test.tsx` (NEW — 11 Vitest tests)

**Commit:** f784ce75
