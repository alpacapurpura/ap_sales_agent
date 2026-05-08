# T-2 Result — Phase 2 Migrate useCopilotOffset + CopilotSidebar to SSoT widths

**Story:** app-shell-sidebar-copilot-decoupling
**Ticket:** T-2
**State:** pushed
**Builder:** claude-sonnet (builder-frontend)
**Date:** 2026-05-08

## Diff summary

5 modified files + 2 new test files:

| File | Status | Description |
|---|---|---|
| `frontend/src/hooks/use-copilot-offset.ts` | MODIFIED | Replace 380/60 literals with COPILOT_WIDTHS SSoT. Migrate `isOpen: boolean` → `sidebarState: 'collapsed' | 'rail' | 'full'` 3-state. Replace resize listener + useState with `useViewport().isMobile`. `COPILOT_OPEN_WIDTH` updated 380→460, `COPILOT_RAIL_WIDTH` stays 60 (both as @deprecated aliases). |
| `frontend/src/features/copilot/components/CopilotSidebar.tsx` | MODIFIED | Import `COPILOT_WIDTHS`, replace `"0px"/"400px"/"60px"/"280px"` literals in lines 86-87 with `${COPILOT_WIDTHS.chat}px`, `${COPILOT_WIDTHS.rail}px`, `${COPILOT_WIDTHS.collapsed}px`. |
| `frontend/src/features/growth-studio/__tests__/visual-regression-drawer-bowtie.test.tsx` | MODIFIED | Re-baseline: `COPILOT_OPEN_WIDTH` 380→460 in vi.mock, `mockReturnValue(380→460)` in 3 expanded-state tests, `paddingRight` assertion `"380px"→"460px"`. Rail-state change is authorized per T-2 spec. |
| `frontend/src/hooks/__tests__/use-copilot-offset.test.ts` | NEW | 10 tests: COPILOT_WIDTHS SSoT sanity (3), hook return per sidebarState (5), deprecated aliases (2). TDD RED→GREEN. |
| `frontend/src/features/copilot/components/__tests__/CopilotSidebar-grid-widths.test.tsx` | NEW | 3 tests: gridTemplateColumns === SSoT values for each sidebarState. |
| `docs/product/stories/app-shell-sidebar-copilot-decoupling/06-tickets.yaml` | MODIFIED | T-1 state→pushed, T-2 state→pushed + SHA. |
| `docs/product/stories/app-shell-sidebar-copilot-decoupling/T-2-impl-log.md` | NEW | Implementation log. |

## Validator outputs

| Validator | Result | Detail |
|---|---|---|
| `scenario_2_ssot_widths_unit` | PASS | 13/13 tests (use-copilot-offset.test.ts + CopilotSidebar-grid-widths.test.tsx) |
| `fe_typecheck` | PASS | `tsc --noEmit` — 0 errors |
| `fe_lint_shell` (modified files) | PASS | 0 errors, pre-existing warnings only |
| `fe_arch_fitness_full` | PRE-EXISTING FAIL | `features/growth-studio/pages` non-canonical — confirmed pre-existing via git stash before T-2 started. Owned by `growth-studio-folder-parity` story. |
| `visual_bowtie_regression_unit` | PASS | 6/6 tests (bowtie re-baselined per spec) |
| Full Vitest suite | PASS | 2022/2022 tests pass (+26 from T-2 new tests) |

## COPILOT_WIDTHS shape note

T-1 shipped `{ collapsed:60, rail:280, chat:400, expanded:460, max:680 }` (differs from arch spec key names). T-2 consumes this shape correctly:
- `sidebarState='collapsed'` offset → `collapsed(60)`
- `sidebarState='rail'` offset → `expanded(460)`
- `sidebarState='full'` offset → `max(680)`
- CopilotSidebar chatW=400 → `chat(400)`
- CopilotSidebar railW=60 → `collapsed(60)`
- CopilotSidebar historyW=280 → `rail(280)`

## Commit SHA

`0d8701c2`
