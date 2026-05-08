# 05-guidelines.md — App Shell ↔ Copilot Decoupling

<!-- voseo-allowed: cita glosario voseo→neutro como referencia técnica forbidden patterns; NO user-facing -->

> Owner: `/architect`. Patterns required + forbidden + files in scope para `/dev-team` autonomous build.

## Patterns required

### Frontend / Next.js 16 / React 19
- **Server Components default.** `"use client"` SOLO en files que consumen hooks (DashboardShellClient, AppSidebar, CopilotSidebar, CopilotFAB).
- **Hybrid pattern:** Server wrapper (`<DashboardShell>`) + Client inner (`<DashboardShellClient>`). Server passes `children` + `tenantId` prop. Tessl skill `nextjs-app-router-modularization`.
- **React Query** para data fetching cuando aplique (no hay BE call en este story — N/A).
- **zustand** para shell-mutex state (existing pattern: copilot-store).
- **zustand persist** middleware con `name: \`shell-mutex-${tenantId}\`` y `storage: createJSONStorage(() => localStorage)`.
- **zustand store factory memoized** per tenantId vía `useMemo([tenantId])` en DashboardShellClient — evita re-create store cada render.

### TypeScript
- **strict mode** — 0 errors `tsc --noEmit`.
- **NO `any`** — usar `unknown` + type guards.
- **NO default exports** (excepto Next.js page components).
- **`Object.freeze({...} as const)`** para SSoT modules (COPILOT_WIDTHS, Z_INDEX).

### Tailwind / styling
- **Z-index SOLO via tokens** de `lib/tokens/z-index.ts` (Z_INDEX_CLASSES strings: `z-[40]`, `z-[60]`, etc.). NO hardcoded `z-50`.
- **Width literals SOLO via SSoT** `copilot-shell-widths.ts` para 0/60/280/400/460/680. Hardcoded prohibido en shell + copilot scope.
- **`cn()` from `@/lib/utils`** para class composition.
- **Radix Sheet primitive** reuse (`@/components/ui/sheet`) — NO custom drawer.
- **Lucide icons** reuse — `MessageCircle` para FAB icon.

### A11y
- **aria-labels Spanish neutro** SIEMPRE en interactive elements:
  - Hamburger trigger: `aria-label="Abrir menú principal"`
  - Drawer close button: `aria-label="Cerrar menú principal"`
  - FAB: `aria-label="Abrir asistente"`
- **Radix Sheet focus trap** reuse — Radix provee por default.
- **Esc closes active drawer** — Radix default.
- **role="status" aria-live="polite"** announcements en mutex transitions (existing pattern CopilotSidebar.tsx:94-105).

### Spanish neutro LatAm
- Todos user-facing strings — SIN voseo (no `vos/podés/tenés/...`). Glosario `.claude/rules/spanish-text.md`.
- Strings esperados (zero TODO list):
  - "Abrir menú principal"
  - "Cerrar menú principal"
  - "Abrir asistente"
  - "Menú principal abierto" (aria-live)
  - "Menú principal cerrado" (aria-live)
- Pre-commit hook Section 7 enforza voseo.

### TDD obligatorio
- **RED** tests primero (Vitest unit + Playwright E2E). **GREEN** después implementación.
- Phases 2-9 cada uno tiene validator que va RED → GREEN.
- Visual regression tests RED inicialmente (no baselines) → re-baseline Phase 9 con Chris ratify.

### FSD-Lite boundaries
- `components/shared/layout/` puede importar de `features/copilot/{components,lib,store}` (excepción documentada `shared → feature(:own)` matrix).
- `features/copilot/components/CopilotFAB.tsx` SOLO `feature:own` imports + `lib/`, `hooks/`, `components/ui/`.
- NO cross-feature imports cualquier otro path.

### Anti-duplication
- Step 0 GATE antes crear nuevo file: `find frontend/src -name "X*"` + `grep -rn "X" frontend/src/`.
- SSoT modules (COPILOT_WIDTHS, Z_INDEX) consumidos por TODOS los call sites — NUNCA mirror.
- ESLint rule `nicolify/no-shadowing-copilot-offset` enforza single import source.

## Patterns forbidden

- ❌ `z-50` / `z-40` hardcoded en `components/shared/layout/**` o `features/copilot/components/**` (arch test bloquea).
- ❌ Width literals 380/400/460/60/280/680 fuera de `copilot-shell-widths.ts` SSoT (arch test bloquea).
- ❌ `setSidebarState("collapsed"|"rail"|"full")` directo cuando viewport <1280 (ESLint warn → ratchet error post-refactor).
- ❌ `useState(false)` para `isMobileOpen` en AppSidebar — usar `useShellMutex.activePanel === 'app-sidebar'`.
- ❌ Local `useEffect + window.matchMedia` — usar `useViewport()` hook.
- ❌ Importar `useCopilotOffset` desde NO `@/hooks/use-copilot-offset` (arch test bloquea shadowing).
- ❌ `// eslint-disable` sin justification comment (ESLint base rule).
- ❌ `any` TypeScript — usar `unknown` + type guards.
- ❌ Default exports (excepto Next.js page).
- ❌ Hex color literals — usar tokens semánticos Tailwind.
- ❌ Voseo en strings user-facing (`vos/podés/tenés/...`).
- ❌ Modificar `frontend/src/components/ui/{dialog,alert-dialog,sheet,popover,dropdown-menu,tooltip}.tsx` SIN coordinación architect (Phase 10 scope — explicit ticket).
- ❌ Modificar `frontend/src/lib/api/fetchClient.ts` (cross-cutting — out of scope).
- ❌ Modificar tests inside `__tests__/architecture/test-growth-studio-copilot-offset.test.ts` SIN rename a `test-shell-copilot-offset.test.ts` (Phase 7).
- ❌ Crear `lib/hooks/` directorio (architect ratificó `hooks/` top-level — useViewport allá).
- ❌ Persist mutex store sin `tenant-namespaced` key (cross-tab leak).

## Files in scope (`/dev-team` edits ONLY these)

### NEW
- `frontend/src/components/shared/layout/DashboardShell.tsx`
- `frontend/src/components/shared/layout/DashboardShellClient.tsx`
- `frontend/src/components/shared/layout/__tests__/DashboardShell-min-width-floor.test.tsx`
- `frontend/src/components/shared/layout/__tests__/AppSidebar-mobile-drawer.test.tsx`
- `frontend/src/components/shared/layout/__tests__/use-shell-mutex.test.ts`
- `frontend/src/features/copilot/components/CopilotFAB.tsx`
- `frontend/src/features/copilot/components/__tests__/CopilotFAB.test.tsx`
- `frontend/src/features/copilot/components/__tests__/CopilotSidebar-grid-widths.test.tsx`
- `frontend/src/features/copilot/lib/copilot-shell-widths.ts`
- `frontend/src/lib/tokens/z-index.ts` (NEW directory)
- `frontend/src/stores/shell-mutex-store.ts` (NEW directory)
- `frontend/src/hooks/use-shell-mutex.ts`
- `frontend/src/hooks/use-viewport.ts`
- `frontend/src/hooks/__tests__/use-copilot-offset.test.ts`
- `frontend/src/hooks/__tests__/use-viewport.test.ts`
- `frontend/src/__tests__/architecture/test-zindex-tokens-only.test.ts`
- `frontend/src/__tests__/architecture/test-copilot-widths-ssot.test.ts`
- `frontend/src/__tests__/architecture/test-no-shadowing-copilot-offset.test.ts`
- `frontend/eslint-rules/no-shadowing-copilot-offset.ts`
- `frontend/eslint-rules/use-shell-mutex-for-drawer-toggles.ts`
- `frontend/e2e/specs/smoke/app-shell-min-content-width.spec.ts`
- `frontend/e2e/specs/smoke/dialog-centered-correctly.spec.ts`
- `frontend/e2e/specs/smoke/app-shell-mobile-mutex-fab.spec.ts`
- `frontend/e2e/specs/smoke/app-shell-visual-regression.spec.ts`
- `frontend/e2e/specs/smoke/app-shell-a11y.spec.ts`

### MODIFIED
- `frontend/src/components/shared/layout/AppSidebar.tsx` (z-classes via tokens; Sheet trigger rewire mutex; aria-labels)
- `frontend/src/components/shared/layout/SidebarContext.tsx` (remove inline matchMedia; add expand/collapse actions)
- `frontend/src/features/copilot/components/CopilotSidebar.tsx` (consume SSoT widths; backdrop+Esc dispatch mutex; z-classes via tokens)
- `frontend/src/hooks/use-copilot-offset.ts` (consume SSoT; migrate isOpen→sidebarState; deprecated re-exports 1 ciclo)
- `frontend/src/app/(main)/[tenantId]/(dashboard)/layout.tsx` (render `<DashboardShell>` instead of `<DashboardLayoutClient>`)
- `frontend/src/features/growth-studio/__tests__/visual-regression-drawer-bowtie.test.tsx` (re-baseline)
- `frontend/eslint.config.mjs` (wire custom rules)
- `frontend/src/components/ui/{dialog,alert-dialog,sheet,popover,dropdown-menu,tooltip}.tsx` — **Phase 10 ONLY**, requiere ticket explícito (T-N marked `phase: 10`)

### DELETED
- `frontend/src/app/(main)/[tenantId]/(dashboard)/DashboardLayoutClient.tsx` (Phase 8 post-migration)

### RENAMED
- `frontend/src/__tests__/architecture/test-growth-studio-copilot-offset.test.ts` → `test-shell-copilot-offset.test.ts` (Phase 7 — `git mv` puro commit ANTES scope expansion)

## Files /dev-team NEVER touches (escalate to Chris)

- `frontend/src/lib/api/fetchClient.ts` (cross-cutting — out of scope)
- `frontend/src/components/shared/layout/TenantSwitcher.tsx` (out of scope, no shell-mutex impact)
- `frontend/src/features/copilot/store/copilot-store.ts` (consume only — NO modify; copilot-store es feature-owned)
- `backend/src/**` (story FE only)
- `.claude/**` (skills/rules edits — manual only)

## Reference docs (load before coding)

### Skills
- `frontend-expert` (FSD-Lite, Shadcn reuse, form-runtime patterns)
- `copilot-expert` (copilot-store conventions, drawer patterns)
- `playwright-expert` (E2E smoke + Clerk auth + visual regression)

### Rules
- `.claude/rules/frontend-fsd.md` (boundary matrix)
- `.claude/rules/frontend-quality.md` (ESLint 60+ rules, ratchet allowlists)
- `.claude/rules/architectural-fitness.md` (ratchet shrink-only)
- `.claude/rules/anti-duplication.md` (Step 0 grep before NEW)
- `.claude/rules/spanish-text.md` (voseo glosario)
- `.claude/rules/tdd-mandatory.md` (RED→GREEN→REFACTOR)
- `.claude/rules/e2e-testing.md` (Playwright smoke patterns + native WSL only)

### Tessl skills
- `tessl__nextjs-app-router-modularization` (Server+Client split pattern)
- `tessl__react-patterns` (boundary error, loading, controlled forms, stable keys)
- `tessl__shadcn-ui` (Radix primitive reuse + customization)
- `tessl__tailwind` (utility-first + theme tokens)
- `tessl__zod` (validation if forms emerge — N/A this story)
- `tessl__vitest` (unit testing config)

### Story artifacts (re-read mid-build si surge ambigüedad)
- `01-spec.md` v4 (10 ratifications + 7 v2 ratifications post architect-fe)
- `00-live-repro.md` (14 screenshots + DOM evidence)
- `03-arch.md` consolidated
- `03-arch-fe.md` full FE design

## Migration phases reminder

Phase 1: Skeleton + SSoT modules (no behavioral change)
Phase 2: Migrate consumers to SSoT widths (drift fix)
Phase 3: Activate min-content-width floor
Phase 4: Activate mutex policy
Phase 5: CopilotFAB + AppSidebar mobile aria-labels
Phase 6: Z-index migration to tokens (shell scope)
Phase 7: Arch test rename + scope ampliado
Phase 8: ESLint custom rules + DashboardLayoutClient deletion
Phase 9: Visual regression baselines + smoke spec
**Phase 10: Modal z-index alignment ui/* primitives** (post v3 ratification)

Cada phase commit-able individually. CI green at every boundary.
