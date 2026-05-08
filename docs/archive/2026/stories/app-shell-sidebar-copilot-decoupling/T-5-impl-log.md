# T-5 Impl Log — app-shell-sidebar-copilot-decoupling

**Ticket:** T-5 — Phase 5 CopilotFAB + AppSidebar mobile aria-labels (Scenario 3 a11y)
**Owner:** claude-sonnet (builder-frontend)
**Assigned at:** 2026-05-08T22:00:00Z
**Estimate:** 2h
**Acceptance validators:** scenario_3_mobile_mutex_unit, fe_typecheck, fe_lint_shell
**Depends on:** T-4 (DONE — commit 6b691987)

## Plan

NEW CopilotFAB + AppSidebar mobile aria-labels Spanish neutro.

- NEW `frontend/src/features/copilot/components/CopilotFAB.tsx` — bottom-right fixed Button con aria-label="Abrir asistente". Mobile-only + collapsed-only. onClick → useShellMutex.openPanel('copilot'). z-class via Z_INDEX_CLASSES.FAB.
- MODIFY `frontend/src/components/shared/layout/DashboardShellClient.tsx` — mount `<CopilotFAB />` (component returns null when off-mobile or copilot non-collapsed).
- MODIFY `frontend/src/components/shared/layout/AppSidebar.tsx` — aria-label="Abrir menú principal" en hamburger trigger. aria-label="Cerrar menú principal" en Sheet close button. role="status" aria-live="polite" announcement region en Sheet content.
- TESTS: CopilotFAB.test.tsx (visibility transitions + click→mutex). AppSidebar-mobile-drawer.test.tsx (aria-label assertions + drawer trigger).

TDD RED→GREEN. Loop hasta validators GREEN o cap_reached.

## Iteration log

### Iter 1 — RED tests

Wrote tests first (TDD):

**`frontend/src/features/copilot/components/__tests__/CopilotFAB.test.tsx`** — 10 tests:
- null on desktop (width=1440, isMobile=false)
- null on tablet (width=900, isTablet=true)
- null when mobile+rail
- null when mobile+full
- visible when mobile (500px) + collapsed
- aria-label="Abrir asistente" present
- z-[70] class (Z_INDEX_CLASSES.FAB) applied
- openPanel('copilot') called on click
- openPanel called exactly once (no double-call)
- no crash when shellMutex is undefined (graceful fallback)

**`frontend/src/components/shared/layout/__tests__/AppSidebar-mobile-drawer.test.tsx`** — 4 tests:
- hamburger button has aria-label='Abrir menú principal'
- clicking hamburger is interactive (shellMutex.openPanel check)
- SheetClose has aria-label='Cerrar menú principal'
- role='status' aria-live='polite' region present in Sheet content

Both files failed RED (components not yet implemented).

### Iter 2 — GREEN implementation

**`frontend/src/features/copilot/components/CopilotFAB.tsx`** (NEW):
- `"use client"` — needs hooks (useViewport, useCopilotStore, useShellMutexContext)
- Returns null when `!viewport.isMobile`
- Returns null when `sidebarState !== 'collapsed'`
- Button: fixed bottom-4 right-4, h-12 w-12, rounded-full, shadow-lg, z-[70]
- `aria-label="Abrir asistente"` (Spanish neutro LatAm)
- `onClick` → `shellMutex?.openPanel("copilot")` (optional chaining for undefined safety)
- `CopilotFAB.displayName = "CopilotFAB"`

**`frontend/src/components/shared/layout/DashboardShellClient.tsx`** (MODIFY):
- Import CopilotFAB from `@/features/copilot/components/CopilotFAB`
- Mounted after `<CopilotSidebar />` inside DashboardContent
- Component self-guards with null returns — no conditional rendering needed at mount site

**`frontend/src/components/shared/layout/AppSidebar.tsx`** (MODIFY):
- Added `SheetClose` to sheet import
- Added `role="status" aria-live="polite" className="sr-only"` span inside SheetContent:
  - Content toggles: "Menú principal abierto" / "Menú principal cerrado"
  - Polite live region announces state changes to screen readers
- Added `<SheetClose aria-label="Cerrar menú principal">` — visually hidden via sr-only, accessible via keyboard focus (focus:not-sr-only pattern)
- Note: `aria-label="Abrir menú principal"` on hamburger SheetTrigger was already wired in T-4.

### Iter 3 — Fix Prettier formatting

ESLint (prettier/prettier) flagged multiline args:

1. **CopilotFAB.tsx line 51**: `cn()` args on separate lines → collapsed to single line:
   `className={cn("fixed bottom-4 right-4 h-12 w-12 rounded-full shadow-lg", Z_INDEX_CLASSES.FAB)}`

2. **AppSidebar.tsx line 716**: `<span>` attrs on separate lines → collapsed to single line:
   `<span role="status" aria-live="polite" className="sr-only">`

3. **Test files**: `npx prettier --write` on both test files — corrected trailing commas, arrow function formatting, JSX attribute spacing.

### Iter 4 — Fix aria-live test (Radix Portal issue)

`AppSidebar-mobile-drawer.test.tsx` aria-live test used `container.querySelector(...)` — returned null.

Root cause: Radix Sheet renders content via Portal outside the React test `container` div. Sheet content mounts in `document.body` directly.

Fix: changed to `document.querySelector("[role='status'][aria-live='polite']")` with `{ timeout: 2000 }` waitFor.

### Iter 5 — All validators GREEN

Results:
- `scenario_3_mobile_mutex_unit` — **14/14 PASS** (10 CopilotFAB + 4 AppSidebar mobile drawer)
- `fe_typecheck` — **0 TypeScript errors** (tsc --noEmit clean)
- `fe_lint_shell` — **0 ESLint errors** (0 new warnings introduced)
- Architecture fitness: **25 files, 51 tests PASS**

## Skills consulted

| Skill | Reason | Decision |
|---|---|---|
| `tessl__react-patterns` | Error boundary / loading states / aria patterns baseline | Applied: aria-busy=false default, aria-label on interactive elements, aria-hidden on decorative icon, sr-only live region for a11y announcements |
| `tessl__shadcn-ui` | SheetClose usage + accessible Sheet pattern | Used `SheetClose` from `@/components/ui/sheet` — reused existing primitive, no recreation |
| `tessl__tailwind` | cn() utility, fixed positioning, sr-only, focus:not-sr-only | Applied per Tailwind utility-first, no inline style |
| `frontend-expert` | FSD placement (CopilotFAB in features/copilot/components/), barrel export | Confirmed feature-scoped placement per boundary matrix |
| `copilot-expert` | useCopilotStore sidebarState type, ShellMutexContext.openPanel contract | sidebarState: "collapsed" | "rail" | "full"; openPanel('copilot') correct dispatch |

## Files modified

- NEW `frontend/src/features/copilot/components/CopilotFAB.tsx`
- NEW `frontend/src/features/copilot/components/__tests__/CopilotFAB.test.tsx`
- NEW `frontend/src/components/shared/layout/__tests__/AppSidebar-mobile-drawer.test.tsx`
- MODIFY `frontend/src/components/shared/layout/DashboardShellClient.tsx`
- MODIFY `frontend/src/components/shared/layout/AppSidebar.tsx`
