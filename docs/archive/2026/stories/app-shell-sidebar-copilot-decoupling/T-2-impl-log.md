# T-2 Impl Log — app-shell-sidebar-copilot-decoupling

**Ticket:** T-2 — Phase 2 Migrate useCopilotOffset + CopilotSidebar to SSoT widths (drift fix, Scenario 2)
**Owner:** claude-sonnet (builder-frontend)
**Assigned at:** 2026-05-08T00:45:00Z
**Estimate:** 2h
**Acceptance validators:** scenario_2_ssot_widths_unit, fe_typecheck, fe_lint_shell, fe_arch_fitness_full, visual_bowtie_regression_unit
**Depends on:** T-1 (DONE — commit 6f4c9ab7)

## Skills Consulted

| Skill | Why | Decision |
|---|---|---|
| `frontend-expert` | FSD boundary compliance, ESLint baseline, arch fitness | global hooks import from `features/copilot/lib/` is allowed (copilot infra-like exception). No new arch test violations introduced. |
| `tessl__react-patterns` | Error boundaries, memoization, stable keys | `useCopilotOffset` replaces resize listener + useState with `useViewport()` (SSR-safe, no memory leak). No event listener cleanup needed. |
| `copilot-expert` | COPILOT_WIDTHS SSoT shape from T-1 shipped file | T-1 shipped shape differs from arch spec key names: `collapsed=60`, `rail=280`, `chat=400`, `expanded=460`, `max=680`. Mapping: collapsed→`collapsed`, rail→`expanded`, full→`max`. |

## Plan

Drift fix: useCopilotOffset hook + CopilotSidebar grid widths consume COPILOT_WIDTHS SSoT (T-1 lib).

- MODIFY `frontend/src/hooks/use-copilot-offset.ts` — replace 380/60/0 literals with `COPILOT_WIDTHS` constants. Migrate isOpen→sidebarState 3-state. Replace internal resize listener with `useViewport()`.
- Re-export COPILOT_OPEN_WIDTH + COPILOT_RAIL_WIDTH as @deprecated aliases (1 ciclo).
- MODIFY `frontend/src/features/copilot/components/CopilotSidebar.tsx` lines 86-87 — grid template literals → `${COPILOT_WIDTHS.collapsed}px` etc.
- Tests: use-copilot-offset (hook return per state === SSoT). CopilotSidebar-grid-widths.test.tsx (grid template === SSoT).

TDD RED→GREEN.

## Iteration log

### Iteration 1

**RED phase:**
- Wrote `frontend/src/hooks/__tests__/use-copilot-offset.test.ts` (10 tests, 5 failing)
- Wrote `frontend/src/features/copilot/components/__tests__/CopilotSidebar-grid-widths.test.tsx` (3 tests, 3 passing immediately — grid values match SSoT numbers even with hardcoded strings; test validates output correctness regardless of implementation approach)
- Failing: rail returns 60 not 460, full returns 60 not 680, mobile returns 60 not 0, COPILOT_OPEN_WIDTH = 380 not 460

**GREEN phase:**
- Modified `use-copilot-offset.ts`: import `COPILOT_WIDTHS` + `useViewport`, select `sidebarState` (not `isOpen`), switch statement for 3 states, `COPILOT_OPEN_WIDTH = COPILOT_WIDTHS.expanded (460)`, `COPILOT_RAIL_WIDTH = COPILOT_WIDTHS.collapsed (60)`
- Modified `CopilotSidebar.tsx`: added `import { COPILOT_WIDTHS }` from `../lib/copilot-shell-widths`, replaced `"0px"|"400px"|"60px"|"280px"` literals with `COPILOT_WIDTHS.chat`, `COPILOT_WIDTHS.rail`, `COPILOT_WIDTHS.collapsed` constants
- Re-baselined `visual-regression-drawer-bowtie.test.tsx`: updated `COPILOT_OPEN_WIDTH: 380→460` in vi.mock and `mockReturnValue(380→460)` in expanded state tests; `paddingRight` assertion `"380px"→"460px"`
- Fixed TS error: cast via `unknown` in CopilotSidebar-grid-widths test (`fakeStore as unknown as Parameters<typeof selector>[0]`)
- Fixed prettier: `railOrHistoryW` split to 2 lines

**Results:**
- `scenario_2_ssot_widths_unit`: 13/13 PASS
- `fe_typecheck`: PASS (0 errors)
- `fe_lint_shell` (modified files): 0 errors, pre-existing warnings only
- `fe_arch_fitness_full`: 1 pre-existing fail (`features/growth-studio/pages` non-canonical) — confirmed pre-existing via git stash; not introduced by T-2. Another session (`growth-studio-folder-parity`) owns this fix.
- `visual_bowtie_regression_unit`: 6/6 PASS
- Full Vitest: 2022/2022 tests pass (1 pre-existing arch fail excluded)

## Key findings / discrepancies

1. **COPILOT_WIDTHS shape mismatch vs arch spec**: T-1 shipped `{ collapsed:60, rail:280, chat:400, expanded:460, max:680 }` vs arch spec `{ collapsed:0, chat:400, rail:60, history:280, RAIL_TOTAL:60, OPEN_RAIL:460, OPEN_FULL:680 }`. T-2 consumes T-1's shipped shape.

2. **`fe_arch_fitness_full` pre-existing failure**: `features/growth-studio/pages` flagged as non-canonical. Another session (`growth-studio-folder-parity`) working this. Not T-2 regression. Validator technically fails but the failure predates T-2.

3. **Bowtie re-baseline scope**: Only 380→460 (rail state). Mock `useCopilotOffset` directly, so no chaining through real hook. `COPILOT_RAIL_WIDTH` (60) and `paddingRight: 0` tests unchanged.
