# T-6 Result — Phase 6 Z-index Migration Shell Scope

**Story:** app-shell-sidebar-copilot-decoupling
**Ticket:** T-6 — Phase 6 Z-index migration to tokens (shell scope, Scenario 4)
**State:** pushed
**Commit SHA:** TBD (populated after push)

## Summary

T-6 migrates all hardcoded z-index classes within shell scope (AppSidebar + CopilotSidebar) to consume from the Z_INDEX_CLASSES SSoT token module established in T-1.

## Files Modified

| File | Change |
|---|---|
| `frontend/src/components/shared/layout/AppSidebar.tsx` | Added Z_INDEX_CLASSES import. Desktop sidebar: `z-50` → `Z_INDEX_CLASSES.APP_SIDEBAR` (z-[40]). Mobile topbar: `z-50` → `Z_INDEX_CLASSES.TOPBAR` (z-[50]). |
| `frontend/src/features/copilot/components/CopilotSidebar.tsx` | Added Z_INDEX_CLASSES import. Backdrop: `z-40` → `Z_INDEX_CLASSES.COPILOT_BACKDROP` (z-[50]). Drawer: `max-md:z-50` → `` `max-md:${Z_INDEX_CLASSES.COPILOT_DRAWER}` `` (max-md:z-[60]). |
| `docs/product/stories/app-shell-sidebar-copilot-decoupling/06-tickets.yaml` | T-6 state: draft → pushed |
| `docs/product/stories/app-shell-sidebar-copilot-decoupling/T-6-impl-log.md` | Populated with implementation log |

## Quality Gates Passed

- `fe_typecheck` (tsc --noEmit): 0 errors
- `fe_lint_shell` (ESLint shell scope): 0 errors
- Architecture fitness (27 test files, 55 tests): all GREEN
- Hardcoded z-50/z-40 grep shell scope: 0 occurrences remaining
- CopilotFAB Z_INDEX_CLASSES.FAB: confirmed (T-5)

## Path Divergence — scenario_4_arch_adversarial (pre-T-7)

The 3 arch tests referenced in `scenario_4_arch_adversarial` validator (`test-zindex-tokens-only.test.ts`, `test-no-shadowing-copilot-offset.test.ts`, `test-shell-copilot-offset.test.ts`) do not exist yet — they are T-7 deliverables. This is expected and documented per ticket prompt. Alternative validation (tsc + eslint + existing arch tests) passed GREEN.

## Z-index Ladder Post T-6 (Shell Scope)

| Layer | Token | Value | Component |
|---|---|---|---|
| APP_SIDEBAR (desktop) | `Z_INDEX_CLASSES.APP_SIDEBAR` | z-[40] | `AppSidebar` `<aside>` |
| TOPBAR (mobile) | `Z_INDEX_CLASSES.TOPBAR` | z-[50] | `AppSidebar` mobile topbar `<div>` |
| COPILOT_BACKDROP | `Z_INDEX_CLASSES.COPILOT_BACKDROP` | z-[50] | `CopilotSidebar` backdrop `<div>` |
| COPILOT_DRAWER (mobile) | `Z_INDEX_CLASSES.COPILOT_DRAWER` | z-[60] | `CopilotSidebar` `<aside>` max-md |
| APP_SIDEBAR_DRAWER | `Z_INDEX_CLASSES.APP_SIDEBAR_DRAWER` | z-[60] | Shadcn Sheet primitive (T-9 scope) |
| FAB | `Z_INDEX_CLASSES.FAB` | z-[70] | `CopilotFAB` (T-5 done) |

## Next Ticket

T-7 is unblocked: Phase 7+8 — Arch test rename/extension + 3 NEW arch tests + ESLint rules + DashboardLayoutClient deletion (Scenario 4).
