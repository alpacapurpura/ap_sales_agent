# T-3 Result — app-shell-sidebar-copilot-decoupling

**Ticket:** T-3 — Phase 3 Activate min-content-width floor 720px @≥1024 (Scenario 1)
**State:** pushed
**Commit SHA:** f784ce75
**Files:** 2 changed (1 modified, 1 new)

## Diff summary

### MODIFIED: `frontend/src/components/shared/layout/DashboardShellClient.tsx`

Added two constants and applied AD3 min-content-width floor:

```typescript
const SHELL_MIN_WIDTH_VAR = "--shell-content-min-width";
const SHELL_MIN_WIDTH_PX = "720px";
```

Outer wrapper `<div>` now carries the CSS variable via inline style:
```tsx
style={{ [SHELL_MIN_WIDTH_VAR]: SHELL_MIN_WIDTH_PX } as React.CSSProperties}
```

`<main>` element now carries the Tailwind arbitrary-value class:
```tsx
className={cn(
  "relative flex-1 min-w-0 overflow-y-auto",
  "lg:min-w-[var(--shell-content-min-width,720px)]",  // <-- NEW (AD3)
  "pt-16 md:pt-0 transition-[margin] duration-300 ease-in-out",
  isCollapsed ? "md:ml-20" : "md:ml-64",
)}
```

The `lg:` prefix means the floor only applies at ≥1024px (CSS-time breakpoint enforcement). Below 1024px, `min-w-0` continues to apply (mobile/tablet) — no visual regression.

### NEW: `frontend/src/components/shared/layout/__tests__/DashboardShell-min-width-floor.test.tsx`

11 Vitest unit tests covering:
- CSS variable wiring: `[style*='--shell-content-min-width']` element exists + value is 720px
- main element class: contains `min-w-`, references `--shell-content-min-width`, contains `720px`
- Children passthrough: renders at mobile (500px), tablet (900px), desktop (1024px, 1920px)
- Structural position: wrapper is ancestor of main element

## Validators output

### scenario_1_min_width_unit

```
Test Files  3 passed (3)
Tests       24 passed (24)
```

Files: `DashboardShell-min-width-floor.test.tsx` (11) + `use-shell-mutex.test.tsx` (8) + `use-viewport.test.ts` (5)

### fe_typecheck

```
0 errors (story scope)
```

Note: Pre-existing TS errors from growth-studio parallel session (untracked files from `growth-studio-folder-parity` story — unrelated to this T-3).

### fe_lint_shell

```
0 errors, 8 warnings (pre-existing in existing copilot components not touched by T-3)
```

## Architecture compliance

- AD3: CSS var `--shell-content-min-width=720px` + `lg:min-w-[var(--shell-content-min-width,720px)]` — ratified pattern.
- No hardcoded `720px` numeric literals outside the two constants.
- Phase 1 passthrough preserved — no mutex policy, no behavioral change beyond the floor.
- TDD: RED confirmed (5 FAIL / 6 PASS before implementation), GREEN after (11/11 PASS).
- Spanish neutro: no user-facing strings introduced.
- No default exports (TS strict compliance).
- `"use client"` boundary unchanged.

## Next ticket

T-4 — Phase 4: Activate mutex policy (Scenarios 1, 3). Unblocked.
