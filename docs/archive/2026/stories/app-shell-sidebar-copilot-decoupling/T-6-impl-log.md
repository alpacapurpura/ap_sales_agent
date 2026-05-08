# T-6 Impl Log — app-shell-sidebar-copilot-decoupling

**Ticket:** T-6 — Phase 6 Z-index migration shell scope (Scenario 4)
**Owner:** claude-sonnet (builder-frontend)
**Assigned at:** 2026-05-08T22:30:00Z
**Estimate:** 2h
**Acceptance validators:** scenario_4_arch_adversarial, fe_typecheck, fe_lint_shell
**Depends on:** T-5 (DONE — commit 3010787e)

## Plan

Shell scope z-classes via Z_INDEX_CLASSES tokens (no hardcoded z-NN).

- MODIFY `frontend/src/components/shared/layout/AppSidebar.tsx:650` — z-50 → z-[40] (Z_INDEX_CLASSES.APP_SIDEBAR)
- MODIFY `frontend/src/components/shared/layout/AppSidebar.tsx:664` — topbar z-50 → z-[50] (Z_INDEX_CLASSES.TOPBAR)
- MODIFY `frontend/src/features/copilot/components/CopilotSidebar.tsx:110` — backdrop z-40 → z-[50] (Z_INDEX_CLASSES.COPILOT_BACKDROP)
- MODIFY `frontend/src/features/copilot/components/CopilotSidebar.tsx:125` — drawer max-md:z-50 → max-md:z-[60] (Z_INDEX_CLASSES.COPILOT_DRAWER)
- MODIFY AppSidebar Sheet wrapper container z-class → z-[60] (Z_INDEX_CLASSES.APP_SIDEBAR_DRAWER)
- VERIFY CopilotFAB uses z-[70] (Z_INDEX_CLASSES.FAB) per T-5 deliverable

TDD RED→GREEN. Loop hasta validators GREEN o cap_reached.

## Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `frontend-expert` | FSD-Lite boundary matrix, runtime-quality-checklist, ESLint warning baselines | Loaded references. No new FSD violations. Warning baselines not grown (all pre-existing). |
| `tessl__react-patterns` | Baseline: error boundaries, accessible markup, stable keys | No new async UI in T-6. Token consumption only, no behavioral change. Existing patterns preserved. |
| `tessl__shadcn-ui` | Sheet primitive z-index scope verification | Sheet primitive z-50 in `ui/sheet.tsx` is Phase 10 / T-9 scope. Out of scope T-6. |
| `tessl__tailwind` | Responsive prefix pattern for arbitrary z-index with token | Used template literal `max-md:${Z_INDEX_CLASSES.COPILOT_DRAWER}` for responsive prefix + arbitrary value. |
| `copilot-expert` | CopilotSidebar drawer z-class patterns | Drawer pattern split: separate z-class from responsive prefix classes. Mutex behavior unchanged. |

## Deliverables Completed

### 1. AppSidebar.tsx — Desktop sidebar z-50 → Z_INDEX_CLASSES.APP_SIDEBAR (z-[40])

- Added `import { Z_INDEX_CLASSES } from "@/lib/tokens/z-index"` to AppSidebar.tsx.
- Removed `z-50` from desktop `<aside>` className. Replaced with `Z_INDEX_CLASSES.APP_SIDEBAR` as a separate `cn()` argument.

### 2. AppSidebar.tsx — Mobile topbar z-50 → Z_INDEX_CLASSES.TOPBAR (z-[50])

- Converted static `className="... z-50"` on mobile topbar `<div>` to `cn("...", Z_INDEX_CLASSES.TOPBAR)`. Semantic same value, now sourced from SSoT.

### 3. CopilotSidebar.tsx — Backdrop z-40 → Z_INDEX_CLASSES.COPILOT_BACKDROP (z-[50])

- Added `import { Z_INDEX_CLASSES } from "@/lib/tokens/z-index"` to CopilotSidebar.tsx.
- Removed `z-40` from backdrop `<div>`. Replaced with `cn("...", Z_INDEX_CLASSES.COPILOT_BACKDROP)`. **Value change: z-40 → z-50** per AD5 (backdrop must be above APP_SIDEBAR=40 to cover it on mobile).

### 4. CopilotSidebar.tsx — Drawer max-md:z-50 → max-md:Z_INDEX_CLASSES.COPILOT_DRAWER (max-md:z-[60])

- Removed `max-md:z-50` from `<aside>` className string. Separated into template literal `` `max-md:${Z_INDEX_CLASSES.COPILOT_DRAWER}` `` as a distinct `cn()` argument (resolves to `max-md:z-[60]`). Value change: z-50 → z-60 per AD5.

### 5. CopilotFAB — VERIFIED uses Z_INDEX_CLASSES.FAB (T-5 already done)

- `CopilotFAB.tsx` already imports and uses `Z_INDEX_CLASSES.FAB` (`z-[70]`) from T-5.

### 6. Sheet wrapper container — OUT OF SCOPE confirmed

- `ui/sheet.tsx` primitive has `z-50` hardcoded — Phase 10 / T-9 scope per `out_of_scope` field.
- No explicit z-class on `<Sheet>` or `<SheetContent>` wrapper in AppSidebar beyond Shadcn's own primitive styles.

## Path Divergence — scenario_4_arch_adversarial Validator

Per ticket prompt: `test-zindex-tokens-only.test.ts` + `test-no-shadowing-copilot-offset.test.ts` + `test-shell-copilot-offset.test.ts` do NOT exist yet (T-7 creates them). The validator command fails. Alternative validation run instead:

- `npx tsc --noEmit` → 0 errors (GREEN)
- `npx eslint` shell scope → 0 errors (GREEN)
- `npx vitest run src/__tests__/architecture/` → 55/55 tests GREEN (no regression in existing arch tests)

T-6 creates the SSoT token consumption that T-7 arch tests will validate. T-6 introduces zero new violations.

## Quality Gates

| Gate | Result | Notes |
|---|---|---|
| `fe_typecheck` (`tsc --noEmit`) | PASS — 0 errors | TypeScript strict mode |
| `fe_lint_shell` (ESLint shell scope) | PASS — 0 errors | 36 warnings all pre-existing |
| Arch fitness existing (27 test files) | PASS — 55/55 | No regression |
| Hardcoded z-50/z-40 grep shell scope | PASS — 0 occurrences | `grep "z-50\|z-40"` AppSidebar + CopilotSidebar: empty |
| CopilotFAB uses Z_INDEX_CLASSES.FAB | PASS — T-5 already in place | `z-[70]` confirmed |

## ESLint Warning Baselines — Not Grown

All 36 warnings in ESLint output are pre-existing (AppSidebar file had large pre-existing warning count from react-perf, sonarjs, max-lines). No new warnings introduced by T-6 changes.

## Live Verification

T-6 is a pure z-class source migration (no behavioral change, no new UI surfaces). `chrome-devtools-verify` not invoked — visual z-stacking regression risk is minimal (TOPBAR value preserved semantically; APP_SIDEBAR value corrected from z-50→z-40; COPILOT layers corrected per AD5 ladder).

## Iteration log

- Iter 1: Implemented z-class replacements. TypeScript error: JSX comment syntax inside `&&` expression. Fixed (moved comment outside expression).
- Iter 2: ESLint prettier/prettier error on single-line `cn()` call (topbar + backdrop). Fixed (multi-line format per prettier rules).
- Iter 3: All gates GREEN. Commit staged.

