# 03-arch-fe.md — App Shell ↔ Copilot Decoupling (FE)

> Owner: `/architect-fe`. FE-only design doc.
> Surface decision: **FE-only**. No BE, no agentic. Per spec ratification 2026-05-07 (Q8) + checkpoint `next_action`.

---
story_id: app-shell-sidebar-copilot-decoupling
surface: FE
sub_architect: /architect-fe
arch_version: 1
last_modified: 2026-05-07T05:30:00Z
links:
  spec: "01-spec.md"
  live_repro: "00-live-repro.md"
  checkpoint: "checkpoint.md"
  outcome: "../../outcomes/growth-copilot-layout-unification.md"
  rules:
    - ".claude/rules/frontend-fsd.md"
    - ".claude/rules/frontend-quality.md"
    - ".claude/rules/architectural-fitness.md"
    - ".claude/rules/anti-duplication.md"
    - ".claude/rules/e2e-testing.md"
    - ".claude/rules/spanish-text.md"
    - ".claude/rules/tdd-mandatory.md"
  source:
    app_sidebar: "frontend/src/components/shared/layout/AppSidebar.tsx"
    copilot_sidebar: "frontend/src/features/copilot/components/CopilotSidebar.tsx"
    copilot_offset_hook: "frontend/src/hooks/use-copilot-offset.ts"
    dashboard_layout: "frontend/src/app/(main)/[tenantId]/(dashboard)/DashboardLayoutClient.tsx"
    sidebar_context: "frontend/src/components/shared/layout/SidebarContext.tsx"
    copilot_store: "frontend/src/features/copilot/store/copilot-store.ts"
    arch_test_offset: "frontend/src/__tests__/architecture/test-growth-studio-copilot-offset.test.ts"
    sheet_primitive: "frontend/src/components/ui/sheet.tsx"
---

## Decisión arquitectónica clave

Reemplazar `DashboardLayoutClient` (flat container con `<AppSidebar/> <main/> <CopilotSidebar/>` siblings, mutual-isolation entre `SidebarContext.isCollapsed` y `useCopilotStore.sidebarState`) por **`<DashboardShell>` Hybrid** (Server wrapper + Client inner) que centraliza el cómputo del chrome (sidebar width + copilot width), aplica un **mutex policy** entre AppSidebar y CopilotSidebar dependiente de viewport, y enforza un **min content width floor** de 720px @≥1024. El refactor introduce 2 SSoT modules nuevos (`copilot-shell-widths.ts` para widths + `lib/tokens/z-index.ts` para layer ladder), 1 store nuevo (`shell-mutex-store` zustand tenant-namespaced), 1 hook nuevo (`useShellMutex`), 1 hook nuevo o lift (`useViewport`), 1 component nuevo (`CopilotFAB`), agrega Sheet izquierdo a `AppSidebar` (mobile drawer), corrige drift de `useCopilotOffset` (380/60/0 → SSoT 460/60/0/680), y extiende arch fitness existente con scope shell + 3 arch tests adicionales (z-index tokens, no-shadowing, ssot-widths). Tradeoff aceptado: bundle +N KB por DashboardShell + zustand store; ROI = elimina tres clases de bug shell (starvation, mis-centered modals, mobile gap) cross-studio.

## Surface diff (FE)

### Routes nuevas / modificadas

NINGUNA ruta nueva. El refactor opera sobre el layout shell consumido por TODAS las rutas dentro del segment `app/(main)/[tenantId]/(dashboard)/...`. La fuente de wiring es `app/(main)/[tenantId]/(dashboard)/layout.tsx` (Server) que renderiza `DashboardLayoutClient` (Client). Post-refactor, `layout.tsx` renderiza `<DashboardShell>` directamente.

| Path | Component pre-refactor | Component post-refactor | Type |
|---|---|---|---|
| `/[tenantId]/(dashboard)/*` (todas) | `DashboardLayoutClient` | `<DashboardShell>` (wrapper Server) → `<DashboardShellClient>` (inner) | Server + Client split |

### Component tree (NEW + MODIFIED)

```
frontend/src/components/shared/layout/
├── DashboardShell.tsx                    # NEW — Server Component
│                                          # - recibe `children` (page) + `tenantId` (de route segment via prop drilling de layout.tsx)
│                                          # - emite metadata SEO si aplica (currently none — pass-through)
│                                          # - renderiza <DashboardShellClient tenantId={tenantId}>{children}</…>
│                                          # - NO state, NO hooks, NO browser APIs
│
├── DashboardShellClient.tsx              # NEW — Client Component ("use client")
│                                          # - consumes useViewport() + useSidebar() + useCopilotStore() + useShellMutex()
│                                          # - computes `appSidebarWidth` (80 collapsed | 256 expanded)
│                                          # - computes `copilotWidth` (consumes COPILOT_WIDTHS SSoT)
│                                          # - applies mutex policy via useShellMutex effects
│                                          # - renders the same JSX shell that DashboardLayoutClient renders today,
│                                          #   PLUS: <main className="lg:min-w-[var(--shell-content-min-width)]">
│                                          #         <CopilotFAB /> (only when mobile + copilot collapsed)
│                                          # - wraps tree in <SidebarProvider> (relocated from DashboardLayoutClient)
│
├── AppSidebar.tsx                        # MODIFIED
│                                          # - desktop <aside> z-class swapped from `z-50` → `z-[var(--z-app-sidebar)]`
│                                          #   or `z-40` from Z_INDEX SSoT (Tailwind arbitrary value w/ CSS var)
│                                          # - mobile <Sheet side="left"> ENABLED (already imports Sheet at line 34;
│                                          #   today only used as in-place wrapper around hamburger). Refactor: extract
│                                          #   the Sheet into a NEW left-drawer pattern triggered by useShellMutex
│                                          #   `activePanel === 'app-sidebar'` instead of local `isMobileOpen` state.
│                                          # - hamburger button gains aria-label="Abrir menú principal"
│                                          # - close button on mobile drawer header gains aria-label="Cerrar menú principal"
│                                          # - removes local `isMobileOpen` useState; replaces with useShellMutex API
│
├── SidebarContext.tsx                    # MODIFIED (minor)
│                                          # - removes the embedded `useEffect`-based `matchMedia("(max-width: 1279px)")`
│                                          #   auto-collapse logic. That responsibility moves to `useShellMutex`
│                                          #   (now viewport-aware via useViewport). SidebarContext keeps ONLY:
│                                          #   { isCollapsed, toggleSidebar, expandSidebar, collapseSidebar }.
│                                          # - exposes new imperative actions `expandSidebar()` / `collapseSidebar()`
│                                          #   so useShellMutex can drive state without simulating user clicks.
│
└── DashboardLayoutClient.tsx             # DELETED (post-migration Phase 1; see Migration plan §9)

frontend/src/features/copilot/
├── components/
│   ├── CopilotSidebar.tsx                # MODIFIED
│   │                                      # - imports COPILOT_WIDTHS from features/copilot/lib/copilot-shell-widths.ts
│   │                                      # - replaces literal "0px"|"400px" / "60px"|"280px" (lines 86-87)
│   │                                      #   with COPILOT_WIDTHS.{collapsed|chat|rail|history}
│   │                                      # - replaces hardcoded `z-40` (line 110) and `max-md:z-50` (line 125)
│   │                                      #   with Z_INDEX.COPILOT_BACKDROP / Z_INDEX.COPILOT_DRAWER tokens
│   │                                      # - mobile backdrop click + escape key route through useShellMutex (set
│   │                                      #   activePanel=null) instead of direct setSidebarState("collapsed").
│   │                                      # - fixes test-id propagation; no other functional change.
│   │
│   └── CopilotFAB.tsx                    # NEW — Client Component ("use client")
│                                          # - returns null unless: viewport < 768 AND copilotStore.sidebarState === 'collapsed'
│                                          # - <Button aria-label="Abrir asistente"> bottom-right fixed
│                                          # - z-index = Z_INDEX.FAB
│                                          # - onClick → useShellMutex.openPanel('copilot')
│
├── lib/
│   └── copilot-shell-widths.ts           # NEW — SSoT widths
│                                          # - exports COPILOT_WIDTHS const (frozen)
│                                          # - canonical numbers for column widths AND derived totals
│
└── store/
    └── copilot-store.ts                  # NOT MODIFIED (consumed unchanged)

frontend/src/hooks/
├── use-copilot-offset.ts                 # MODIFIED
│                                          # - removes literals 380/60/0 (lines 7, 28-29)
│                                          # - imports COPILOT_WIDTHS from features/copilot/lib/copilot-shell-widths.ts
│                                          # - returns: viewport<768 → 0; sidebarState='collapsed' → COPILOT_WIDTHS.RAIL_TOTAL (60);
│                                          #   sidebarState='rail' → COPILOT_WIDTHS.OPEN_RAIL (460); sidebarState='full' → COPILOT_WIDTHS.OPEN_FULL (680)
│                                          # - migrates from `isOpen` boolean to `sidebarState` 3-state for fidelity
│                                          # - re-exports COPILOT_OPEN_WIDTH/COPILOT_RAIL_WIDTH as deprecated aliases for
│                                          #   1 cycle (with @deprecated JSDoc) — Phase 6 cleanup removes
│
├── use-shell-mutex.ts                    # NEW
│                                          # - reads viewport from useViewport
│                                          # - reads sidebar.isCollapsed from useSidebar
│                                          # - reads copilotStore.sidebarState from useCopilotStore
│                                          # - reads activePanel from useShellMutexStore (zustand)
│                                          # - applies effects per breakpoint (see §AD2 below)
│                                          # - exposes API: { activePanel, openPanel(panel), closePanel(), togglePanel(panel) }
│
└── use-viewport.ts                       # NEW (anti-dup grep: NO existing match)
                                          # - SSR-safe: returns { width: number | null, breakpoint: Breakpoint }
                                          # - Breakpoint = 'mobile' (<768) | 'sm-tablet' (768-1023) | 'lg-tablet' (1024-1279) | 'desktop' (>=1280)
                                          # - subscribes to window.matchMedia for each breakpoint (3 MQLs); not resize listener (cheaper)
                                          # - hydration-safe initial value: null until mounted, then computed

frontend/src/stores/                      # NEW directory (anti-dup grep: did NOT exist)
└── shell-mutex-store.ts                  # NEW — zustand store
                                          # - exports useShellMutexStore + factory ensureMutexStore(tenantId)
                                          # - tenant-namespaced via persist middleware key: `shell-mutex-${tenantId}`
                                          # - state: { activePanel: 'app-sidebar' | 'copilot' | null }
                                          # - actions: setActivePanel, closeAll
                                          # - persist localStorage so refresh respects last user toggle on mobile

frontend/src/lib/tokens/                  # NEW directory (anti-dup grep: did NOT exist)
└── z-index.ts                            # NEW — SSoT z-index token ladder
                                          # - exports Z_INDEX const (fluid scale 0/10/.../100 per Q6 ratification)
                                          # - paired Tailwind arbitrary class strings (`z-[var(--z-fab)]` if CSS-var
                                          #   wired) OR direct numeric class strings (`z-[70]`). DECISION: numeric
                                          #   strings (no CSS-var indirection) for grep-ability + arch test parsing.

frontend/src/__tests__/architecture/
├── test-growth-studio-copilot-offset.test.ts   # RENAMED → test-shell-copilot-offset.test.ts
│                                                # - scope ampliado (3 dirs: shared/layout, copilot/components, growth-studio)
│                                                # - allowlists scope-keyed: KNOWN_VIOLATIONS_GROWTH (existing 6) + KNOWN_VIOLATIONS_SHELL (empty post-fix)
│
├── test-zindex-tokens-only.test.ts             # NEW
│                                                # - scans shared/layout/** + features/copilot/components/** for hardcoded `z-NN` Tailwind classes
│                                                # - permits ONLY classes that match values in Z_INDEX SSoT (e.g. `z-[40]`, `z-[60]`)
│                                                # - skips files in __tests__/, .test, .spec
│
├── test-copilot-widths-ssot.test.ts            # NEW
│                                                # - scans frontend/src for raw width literals matching /\b(380|400|460|60|280|680)px?\b/
│                                                # - permits ONLY in copilot-shell-widths.ts (the SSoT)
│                                                # - skips test files; allowlist for legitimate non-copilot uses (e.g. tooltip max-w-[120px])
│
└── test-no-shadowing-copilot-offset.test.ts    # NEW
                                                # - scans imports of `useCopilotOffset` AST-style (regex)
                                                # - permits ONLY imports from `@/hooks/use-copilot-offset` or `@/features/copilot/lib/copilot-shell-widths`
                                                # - any other source = build break

frontend/src/__tests__/components/                  # contract tests (Vitest)
├── shared/layout/DashboardShell-min-width-floor.test.tsx       # NEW — Scenario 1
├── shared/layout/AppSidebar-mobile-drawer.test.tsx             # NEW — Scenario 3
├── shared/layout/use-shell-mutex.test.ts                       # NEW — mutex policy unit
├── copilot/components/CopilotFAB.test.tsx                      # NEW — Scenario 3
├── copilot/components/CopilotSidebar-grid-widths.test.tsx      # NEW — Scenario 2
└── hooks/use-copilot-offset.test.ts                            # NEW — Scenario 2 (hook return == SSoT)

frontend/src/features/growth-studio/__tests__/
└── visual-regression-drawer-bowtie.test.tsx                    # MODIFIED — re-baselined with masking (Q9)

frontend/e2e/specs/smoke/
├── app-shell-min-content-width.spec.ts                         # NEW — Scenario 1 (8×4×3 = 96 assertions)
├── dialog-centered-correctly.spec.ts                           # NEW — Scenario 2
└── app-shell-mobile-mutex-fab.spec.ts                          # NEW — Scenario 3 (8-step flow)

frontend/eslint-rules/                            # custom ESLint rules dir (anti-dup grep: confirm via builder Step 0)
├── no-shadowing-copilot-offset.ts                # NEW
└── use-shell-mutex-for-drawer-toggles.ts         # NEW (warn → ratchet error post-refactor)
```

### State / data flow

**Pre-refactor (broken):**
```
SidebarContext (isCollapsed, toggleSidebar)   [autonomous; matchMedia(<1279)]
        │
        ▼
   AppSidebar (aside, w-20|w-64, fixed z-50)
   <main flex-1 min-w-0 ml-20|ml-64>          [no min-width floor]
   CopilotSidebar (grid 0|400 + 60|280)        [autonomous from copilot-store]
        │
        └── useCopilotOffset → 380|60|0       [DRIFT: not 460|60|0|680]
```

**Post-refactor (mutex + SSoT):**
```
useViewport (mobile|sm-tablet|lg-tablet|desktop)
        │
        ├──→ useSidebar (isCollapsed, expandSidebar, collapseSidebar)
        │
        ├──→ useCopilotStore (sidebarState, setSidebarState)
        │
        ├──→ useShellMutexStore (activePanel) [tenant-namespaced]
        │
        └──→ useShellMutex  ← composes all above + applies effects
                  │
                  ▼
        DashboardShellClient
                  │
        ┌─────────┼─────────────────┐
        ▼         ▼                 ▼
   AppSidebar  <main>            CopilotSidebar  + CopilotFAB
   (z-40,      (lg:min-w-[720px]) (z-60 mobile,   (z-70 mobile only,
    desktop+    overflow-y-auto)   z-auto desktop)  collapsed only)
    mobile-Sheet)                       │
                                        │
                                  consumes COPILOT_WIDTHS SSoT
                                        │
   useCopilotOffset(consumed by ui/dialog, ui/sheet, ui/alert-dialog,
                    ui/detail-panel) — also consumes COPILOT_WIDTHS SSoT
```

### Hooks API contracts

```ts
// frontend/src/hooks/use-viewport.ts
export type Breakpoint = 'mobile' | 'sm-tablet' | 'lg-tablet' | 'desktop';
export type ViewportState = { width: number | null; breakpoint: Breakpoint | null };

export function useViewport(): ViewportState;
// SSR-safe. Returns { width: null, breakpoint: null } until mounted.
// Subscribes to window.matchMedia for: '(max-width: 767px)', '(min-width: 768px) and (max-width: 1023px)',
// '(min-width: 1024px) and (max-width: 1279px)', '(min-width: 1280px)'.
```

```ts
// frontend/src/hooks/use-shell-mutex.ts
export type ActivePanel = 'app-sidebar' | 'copilot' | null;

export interface ShellMutexAPI {
  activePanel: ActivePanel;
  openPanel: (panel: 'app-sidebar' | 'copilot') => void;
  closePanel: () => void;
  togglePanel: (panel: 'app-sidebar' | 'copilot') => void;
}

export function useShellMutex(): ShellMutexAPI;

/**
 * Effects applied internally per viewport (declarative, NOT useEffect for fetch):
 * - mobile (<768): mutex strict — opening one panel closes the other.
 *   activePanel is the source of truth on mobile.
 * - sm-tablet (768-1023): on copilot.sidebarState becoming 'rail' or 'full', call sidebar.collapseSidebar().
 *   On user toggling sidebar to expanded, call setSidebarState('collapsed').
 * - lg-tablet (1024-1279): same as sm-tablet but only when copilot is 'rail' or 'full' AND user attempts
 *   to expand sidebar; preserves user's collapsed-by-default preference.
 * - desktop (>=1280): no mutex; both can coexist.
 *
 * Implementation: 1 useEffect that subscribes to copilotStore + sidebar + viewport via selectors;
 * on relevant change, dispatch policy. Idempotent (no infinite loops).
 */
```

```ts
// frontend/src/stores/shell-mutex-store.ts
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

type ShellMutexState = {
  activePanel: 'app-sidebar' | 'copilot' | null;
  setActivePanel: (panel: 'app-sidebar' | 'copilot' | null) => void;
};

export const useShellMutexStore = (tenantId: string) =>
  create<ShellMutexState>()(
    persist(
      (set) => ({
        activePanel: null,
        setActivePanel: (panel) => set({ activePanel: panel }),
      }),
      {
        name: `shell-mutex-${tenantId}`,
        storage: createJSONStorage(() => localStorage),
      },
    ),
  );

// IMPLEMENTATION NOTE: zustand store factory must be memoized per tenantId
// inside DashboardShellClient via useMemo to avoid re-creating store on
// every render. Pattern reuse from existing copilot-store conversation
// persistence (copilot-store.ts:346 — "localStorage key prefix tenant-keyed").
```

```ts
// frontend/src/features/copilot/lib/copilot-shell-widths.ts
export const COPILOT_WIDTHS = Object.freeze({
  // Per-column widths (CSS grid template values)
  collapsed: 0,    // chat column when sidebarState === 'collapsed'
  chat: 400,       // chat column when sidebarState !== 'collapsed'
  rail: 60,        // rail column when sidebarState !== 'full'
  history: 280,    // history column when sidebarState === 'full'

  // Derived totals (consumed by useCopilotOffset for offset math)
  RAIL_TOTAL: 60,  // collapsed: 0 + 60
  OPEN_RAIL: 460,  // rail: 400 + 60
  OPEN_FULL: 680,  // full: 400 + 280
  MOBILE: 0,       // hidden on mobile (drawer overlays instead of pushing)
} as const);

export type CopilotWidthKey = keyof typeof COPILOT_WIDTHS;
```

```ts
// frontend/src/lib/tokens/z-index.ts
// Q6 ratification: fluid scale 0/10/20/.../100. Spacing 10 between layers
// permits inserting future tokens without renumeration.

export const Z_INDEX = Object.freeze({
  AUTO: 'auto',
  CONTENT: 0,
  STICKY: 30,
  APP_SIDEBAR: 40,                  // desktop <aside fixed>
  COPILOT_BACKDROP: 50,             // mobile copilot scrim
  MOBILE_DRAWER_BACKDROP: 50,       // mobile app-sidebar Sheet backdrop (Sheet primitive default)
  TOPBAR: 50,                       // mobile topbar (60 — tied with copilot drawer; mutex prevents collision)
  COPILOT_DRAWER: 60,               // mobile copilot drawer (max-md:z-50 today; bumps to 60 to win over topbar)
  APP_SIDEBAR_DRAWER: 60,           // mobile app-sidebar Sheet content (Radix Sheet uses 50 internally;
                                    // wrapper container sets 60 to win over topbar; arch test exempts ui/sheet.tsx)
  FAB: 70,
  MODAL: 80,                        // ui/dialog, ui/alert-dialog (currently z-50 — not in scope: only shell scope changes)
  TOOLTIP: 90,
  TOAST: 100,
} as const);

// IMPORTANT — Tailwind arbitrary value class strings that arch test recognizes:
export const Z_INDEX_CLASSES = Object.freeze({
  APP_SIDEBAR: 'z-[40]',
  COPILOT_BACKDROP: 'z-[50]',
  TOPBAR: 'z-[50]',
  COPILOT_DRAWER: 'z-[60]',
  APP_SIDEBAR_DRAWER: 'z-[60]',
  FAB: 'z-[70]',
} as const);

// SCOPE NOTE: ui/dialog/sheet/alert-dialog/tooltip/popover/dropdown-menu primitives
// (`frontend/src/components/ui/*.tsx`) ALSO declare `z-50` internally. This refactor
// does NOT modify those primitives (out of shell scope). Arch test exempts ui/* path.
// Future story may align modal=80, tooltip=90 (separate concern).
```

### Tests requeridos

| Category | Path | Type | Scenario | Notes |
|---|---|---|---|---|
| `non_functional` | `frontend/src/__tests__/architecture/test-shell-copilot-offset.test.ts` | RENAMED + ampliado | 4 | scope shell + growth + copilot; `KNOWN_VIOLATIONS_SHELL = []` post-fix |
| `non_functional` | `frontend/src/__tests__/architecture/test-zindex-tokens-only.test.ts` | NEW | 4 | scans shell paths for un-tokenized `z-NN` |
| `non_functional` | `frontend/src/__tests__/architecture/test-copilot-widths-ssot.test.ts` | NEW | 2 | enforces SSoT widths |
| `non_functional` | `frontend/src/__tests__/architecture/test-no-shadowing-copilot-offset.test.ts` | NEW | 4 | enforces unique import source |
| `non_functional` | ESLint rule `nicolify/no-shadowing-copilot-offset` | NEW | 4 | duplicate enforcement (lint + arch test) |
| `non_functional` | ESLint rule `nicolify/use-shell-mutex-for-drawer-toggles` | NEW | 4 | warn → ratchet error |
| `functional` | `frontend/src/components/shared/layout/__tests__/DashboardShell-min-width-floor.test.tsx` | NEW (Vitest) | 1 | render with mocked viewport widths × mocked copilot states; assert `main.style.minWidth` matches policy |
| `functional` | `frontend/src/components/shared/layout/__tests__/AppSidebar-mobile-drawer.test.tsx` | NEW (Vitest) | 3 | render mobile, click hamburger, assert Sheet open + mutex with copilot drawer |
| `functional` | `frontend/src/components/shared/layout/__tests__/use-shell-mutex.test.ts` | NEW (Vitest) | 1, 3 | mutex policy unit tests per breakpoint |
| `functional` | `frontend/src/features/copilot/components/__tests__/CopilotFAB.test.tsx` | NEW (Vitest) | 3 | render mobile + collapsed → FAB visible; render desktop → null; click → mutex.openPanel('copilot') |
| `functional` | `frontend/src/features/copilot/components/__tests__/CopilotSidebar-grid-widths.test.tsx` | NEW (Vitest) | 2 | grid template === SSoT values per state |
| `functional` | `frontend/src/hooks/__tests__/use-copilot-offset.test.ts` | NEW (Vitest) | 2 | hook return per state === COPILOT_WIDTHS derived totals |
| `functional` | `frontend/src/hooks/__tests__/use-viewport.test.ts` | NEW (Vitest) | 1 | matchMedia mock + breakpoint transitions |
| `functional` (E2E) | `frontend/e2e/specs/smoke/app-shell-min-content-width.spec.ts` | NEW (Playwright) | 1 | 8 studios × 4 viewports × 3 copilot states = 96 `main.width` assertions |
| `functional` (E2E) | `frontend/e2e/specs/smoke/dialog-centered-correctly.spec.ts` | NEW (Playwright) | 2 | open dialog at 1440 × copilot-rail; assert `dialog.left + dialog.width/2` ≈ available content center ±5px |
| `functional` (E2E) | `frontend/e2e/specs/smoke/app-shell-mobile-mutex-fab.spec.ts` | NEW (Playwright) | 3 | 8-step mobile flow assertions per spec |
| `visual` | `frontend/src/features/growth-studio/__tests__/visual-regression-drawer-bowtie.test.tsx` | MODIFIED (Vitest snapshot) | 1 | re-baseline with main content masking (Q9) |
| `visual` (E2E) | `frontend/e2e/specs/smoke/app-shell-visual-regression.spec.ts` | NEW (Playwright + screenshots) | 1 | bowtie + AppSidebar nav + CopilotSidebar pixel-perfect; main content masked |
| `visual` (a11y) | embedded in `app-shell-mobile-mutex-fab.spec.ts` via `@axe-core/playwright` | NEW | 3 | hamburger aria-label, FAB aria-label, drawer focus trap, drawer escape close |

**Coverage:** vitest existing 1063+ tests, threshold 20% all categories. NEW tests must NOT decrease coverage. Estimated new tests = ~20 unit + 4 e2e specs.

## Cross-cutting concerns

### Tenant isolation
- `useShellMutexStore` keyed by `tenantId`. Store factory memoized per tenantId in `DashboardShellClient` (`useMemo([tenantId])`). Cross-tab safe via localStorage namespacing. Tenant switch clears prev tenant's mutex state implicitly (different store instance).
- No BE call originates from this refactor — `fetchClient` not in scope.

### A11y
- **Hamburger** (`AppSidebar.tsx:670` mobile trigger): add `aria-label="Abrir menú principal"` (Spanish neutro) per Q7.
- **FAB** (NEW component): `aria-label="Abrir asistente"` per Q7.
- **Mobile drawer (Sheet) close button**: `aria-label="Cerrar menú principal"` (NEW) — currently auto-generated by Radix; ratify Spanish copy.
- **`role="status" aria-live="polite"`** announcements on mutex transitions: leverage existing CopilotSidebar `<span role="status">` (lines 94-105). Add equivalent in AppSidebar mobile drawer for `"Menú principal abierto"` / `"Menú principal cerrado"`.
- **Focus trap**: Radix `Sheet` (`frontend/src/components/ui/sheet.tsx`) provides focus trap by default. Verified in axe scan (Scenario 3 grader).
- **Keyboard**: Esc closes active drawer (Radix default). Tab order: hamburger → topbar logo → ... → FAB (mobile only).
- Axe-core scan in Playwright spec `app-shell-mobile-mutex-fab.spec.ts` asserts 0 violations.

### i18n / Spanish neutro
- All NEW strings: `"Abrir menú principal"`, `"Cerrar menú principal"`, `"Abrir asistente"`, `"Menú principal abierto"`, `"Menú principal cerrado"` — todos tuteo neutro, sin voseo. Per `.claude/rules/spanish-text.md` glosario.
- Pre-commit hook (Section 7) catches voseo.

### Server/Client boundaries
- **`<DashboardShell>` Server Component**: NO `"use client"` directive. Receives `children` (Server-rendered page or sub-Client components by Next.js convention) + `tenantId` (from `app/(main)/[tenantId]/(dashboard)/layout.tsx` route segment).
- **`<DashboardShellClient>` Client Component**: `"use client"` directive. ALL hook usage (`useViewport`, `useSidebar`, `useCopilotStore`, `useShellMutex`) lives here. Wraps children prop in passive container.
- **`<AppSidebar>` Client**: already `"use client"` (line 1). Modifications keep boundary.
- **`<CopilotSidebar>` Client**: already `"use client"` (line 1). Modifications keep boundary.
- **`<CopilotFAB>` Client**: NEW with `"use client"` (consumes hooks).
- Pattern reference: tessl `nextjs-app-router-modularization` (`Page.tsx` Server + `*Client.tsx` Client).
- **Layout wiring** (`app/(main)/[tenantId]/(dashboard)/layout.tsx`): MODIFIED to render `<DashboardShell tenantId={params.tenantId}>{children}</DashboardShell>` instead of `<DashboardLayoutClient>`. Layout itself stays Server Component.

### FSD-Lite boundaries
Per `.claude/rules/frontend-fsd.md` matrix:
- `components/shared/layout/` (NEW DashboardShell + DashboardShellClient + modified AppSidebar) imports:
  - `@/components/ui/*` ✅ (allowed)
  - `@/lib/tokens/z-index.ts` ✅ (lib → ✅)
  - `@/hooks/use-shell-mutex.ts` ✅ (hooks → ✅)
  - `@/hooks/use-viewport.ts` ✅
  - `@/features/copilot/components/CopilotSidebar.tsx` ✅ (shared → feature documented exception per matrix `shared → feature(:own)`)
  - `@/features/copilot/lib/copilot-shell-widths.ts` ✅ (lift exception path)
  - `@/features/copilot/store/copilot-store.ts` ✅ (consumes existing — needed for mutex policy effects)
  - `@/components/shared/layout/SidebarContext.tsx` ✅ (own scope)
  - `@/stores/shell-mutex-store.ts` ✅ (NEW lib)
- `features/copilot/components/CopilotFAB.tsx` (NEW) imports:
  - `@/features/copilot/store/copilot-store.ts` ✅ (feature:own)
  - `@/features/copilot/lib/copilot-shell-widths.ts` ✅ (feature:own)
  - `@/lib/tokens/z-index.ts` ✅
  - `@/hooks/use-shell-mutex.ts` ✅
  - `@/hooks/use-viewport.ts` ✅
  - `@/components/ui/button` ✅
  - NO cross-feature imports (besides own).

## Anti-duplication audit (mandatory Step 0 grep)

Per `.claude/rules/anti-duplication.md` Step 0 GATE — pre-architectural-claim greps executed:

| NEW artifact | Grep command | Match? | Decision |
|---|---|---|---|
| `useShellMutex` hook | `grep -rln "useShellMutex\|use-shell-mutex" frontend/src/` | 0 matches | NEW — proceed |
| `useViewport` hook | `grep -rln "useViewport\|use-viewport" frontend/src/` | 0 matches | NEW — proceed. NOTE: `SidebarContext.tsx:31-41` has inline `window.matchMedia("(max-width: 1279px)")` — that logic is **lifted** into `useShellMutex` (not duplicated). |
| `useMediaQuery`/`useBreakpoint` | `grep -rln "useMediaQuery\|useBreakpoint\|window.matchMedia" frontend/src/hooks/ frontend/src/lib/` | 1 match (`use-copilot-offset.ts:22` `window.addEventListener("resize")`) | No prior generic media-query hook exists. `useViewport` is canonical NEW. `use-copilot-offset.ts` resize-listener is migrated to consume `useViewport` (replace `useState+useEffect` with hook composition). |
| `copilot-shell-widths.ts` SSoT | `find frontend/src -name "copilot-shell-widths*"` + `grep -rln "COPILOT_WIDTHS\|COPILOT_OPEN_WIDTH\|COPILOT_RAIL_WIDTH" frontend/src/` | 0 + 1 match in `use-copilot-offset.ts:7-8` (literals). Plus 1 match in `growth-studio/__tests__/visual-regression-drawer-bowtie.test.tsx` (likely importing from hook) | **NEW SSoT — lift literals.** Existing `COPILOT_OPEN_WIDTH`/`COPILOT_RAIL_WIDTH` in `use-copilot-offset.ts` are **migrated** to import from new SSoT (kept as `@deprecated` re-exports for 1 cycle). Also unifies `CopilotSidebar.tsx:86-87` `chatW`/`railOrHistoryW` literal branches. |
| `lib/tokens/z-index.ts` | `ls frontend/src/lib/tokens/` | dir does not exist | NEW directory + file. Lift hardcoded `z-50`/`z-40` from 4 known shell locations (`AppSidebar.tsx:650, 664`, `CopilotSidebar.tsx:110, 125`). |
| `shell-mutex-store` zustand | `grep -rln "shell-mutex" frontend/src/` + `ls frontend/src/stores/` | 0 + dir does not exist | NEW. Pattern reuse: tenant-namespaced localStorage key per `copilot-store.ts:346` precedent. |
| `CopilotFAB` component | `find frontend/src -name "CopilotFAB*"` | 0 matches | NEW. |
| `DashboardShell` / `DashboardShellClient` | `find frontend/src -name "DashboardShell*"` | 0 matches | NEW. |
| AppSidebar mobile drawer left Sheet | `grep -n "side=\"left\"" frontend/src/components/shared/layout/AppSidebar.tsx` | exists at line 673 (CURRENT mobile drawer USES Sheet side="left"!) | **NOT NEW — refactor existing.** AppSidebar already renders a `<Sheet><SheetTrigger><Menu></Menu></SheetTrigger><SheetContent side="left">` pattern (lines 667-687). Refactor: extract trigger to mutex-driven open state instead of local `isMobileOpen` useState; add aria-labels; preserve drawer pattern. **DOWNGRADE AD8** — see §AD8. |

**Existing pattern reuse (no new layer):**
- `Sheet` primitive (`@/components/ui/sheet`) — Radix wrapper ✅ reuse
- `Button` primitive (`@/components/ui/button`) — for FAB ✅ reuse
- `MessageCircle` from lucide-react — FAB icon ✅ reuse
- `cn()` from `@/lib/utils` — class composition ✅ reuse
- `zustand` + `zustand/middleware` `persist` — already used in copilot-store, reuse pattern
- `Tooltip` primitive — already used in AppSidebar ✅ reuse for FAB hover label

## Architectural Decisions (DECISIONS table)

| ID | Decision | Rationale | Tradeoff | Source |
|---|---|---|---|---|
| **AD1** | DashboardShell **Hybrid pattern** (Server wrapper `DashboardShell.tsx` + Client inner `DashboardShellClient.tsx`) | Q8 ratification + tessl `nextjs-app-router-modularization`. Server wrapper preserves SSR boundary for the layout (page metadata/streaming benefits future-proofed). Client inner consolidates ALL shell state. Replaces today's flat `DashboardLayoutClient` (single Client Component wrapping everything). | +1 file vs single Client; pattern overhead negligible. Required for Server Component composability with future RSC features. | Spec §"Architect orientation hints" + Q8 |
| **AD2** | **Mutex breakpoint policy ≥1280px no-mutex; <1280 mutex applies** | Q2 ratification. Below 1280, screen real-estate cannot afford both expanded sidebar (256) + open copilot (460) + 720 main = 1436px > 1279. At 1280+, both fit. | More logic in `useShellMutex`. Predictable thresholds (no fuzzy resize). | Spec §Scenario 1 + Q2 |
| **AD3** | **Min content width floor 720px @≥1024 viewport** | Q1 ratification. 720px = read-comfort floor for forms / dashboards / inbox detail panes. Lower → degraded UX (live repro: 52px catastrophic, 484px broken). Sales-inbox 3-col responsive is separate idea (Q10). | At 1024 + sidebar collapsed (80) + copilot open (460) + main 720 = 1260 < 1024 → mutex collapses copilot to rail (60 → main 1024-80-60 = 884). | Live repro evidence + Q1 |
| **AD4** | **NEW zustand store `shell-mutex-store`** tenant-namespaced (key `shell-mutex-${tenantId}`), persist localStorage | Q4 ratification. Independent from `SidebarContext` (React Context, ephemeral) and `copilot-store` (zustand, copilot domain). Mutex is cross-domain shell concern. zustand chosen for: (a) consistency with copilot-store, (b) localStorage persistence trivial, (c) cross-component subscription without prop-drilling. | +1 store. Bundle delta minimal (zustand already loaded). | Q4 + spec §useShellMutex |
| **AD5** | **Z-index fluid scale 0/10/20/30/40/50/60/70/80/90/100** in `lib/tokens/z-index.ts` SSoT | Q6 ratification. Spacing 10 between layers permits inserting future tokens without renumeration. Replaces ad-hoc `z-50` collisions (AppSidebar=z-50, CopilotSidebar mobile=z-50, ui/dialog=z-50, etc. — undocumented ladder). | Shell scope only — ui/* primitives keep their `z-50` (out of scope, separate future story). Arch test exempts ui/* path. | Q6 + spec §Z-index tokens |
| **AD6** | **NEW SSoT module `copilot-shell-widths.ts`** (under `features/copilot/lib/`) | Drift fix. Today: `use-copilot-offset.ts:7-8` declares 380/60 + `CopilotSidebar.tsx:86-87` declares "0px"/"400px"/"60px"/"280px" → 80-220px drift. SSoT in copilot domain (own widths) consumed by both. | Both consumers must migrate atomically (Phase 4). Existing `COPILOT_OPEN_WIDTH`/`COPILOT_RAIL_WIDTH` exports kept as `@deprecated` for 1 cycle. | Live repro §"Three load-bearing issues" point 3 |
| **AD7** | **CopilotFAB position bottom-right `fixed bottom-4 right-4`** + **mobile-only + collapsed-only** | Q3 ratification. Bottom-right = standard chat-bubble convention. Mobile-only because desktop has the rail (60px) trigger always visible. Collapsed-only because when copilot is open, drawer covers most of viewport — no need for FAB. | Tappable area must be ≥44px (a11y). `h-14 w-14` = 56px ✅. | Q3 + spec §FAB copilot |
| **AD8** | AppSidebar mobile drawer **REFACTOR EXISTING Sheet** (already uses `side="left"`); rewire trigger from local `useState isMobileOpen` to `useShellMutex.activePanel === 'app-sidebar'`. Add aria-label. | Anti-dup grep result: AppSidebar.tsx:673 already declares `<SheetContent side="left" className="p-0 w-72">`. Refactor (not invent). The "missing left drawer" framing in spec/00-live-repro is partially incorrect — drawer exists but is **invisible on the rendered topbar in 00-live-repro** because the topbar hamburger has no `aria-label` (line 670-672, no `aria-label` prop) and the Sheet is functional but un-scanned. | Smaller scope than spec implies. CHECK with /pm whether spec scenario 3 wording must update. | `AppSidebar.tsx:667-687` source + 00-live-repro footer note "no `aria-label`" |
| **AD9** | aria-labels Spanish neutro: `"Abrir menú principal"`, `"Cerrar menú principal"`, `"Abrir asistente"` | Q7 ratification + `.claude/rules/spanish-text.md`. | None. | Q7 |
| **AD10** | Visual regression with **main content masking** | Q9 ratification. Main content area changes (floor, mutex side-effects) are EXPECTED diffs. Bowtie + AppSidebar nav + CopilotSidebar visuals are pixel-perfect invariants. | Re-baseline existing `visual-regression-drawer-bowtie.test.tsx` snapshot post-refactor. New `app-shell-visual-regression.spec.ts` with `mask` regions for `main` content. | Q9 |

## Migration plan (phased)

> **Goal:** zero production breakage. Each phase commit-able individually. CI green at every phase boundary.

### Phase 1 — Skeleton + SSoT modules (no behavioral change)
1. Create `frontend/src/lib/tokens/z-index.ts` (Z_INDEX + Z_INDEX_CLASSES exports). No consumers yet.
2. Create `frontend/src/features/copilot/lib/copilot-shell-widths.ts` (COPILOT_WIDTHS exports). No consumers yet.
3. Create `frontend/src/hooks/use-viewport.ts`.
4. Create `frontend/src/stores/shell-mutex-store.ts`.
5. Create `frontend/src/hooks/use-shell-mutex.ts` (logic in place, but no UI consumes yet).
6. Create `frontend/src/components/shared/layout/DashboardShell.tsx` + `DashboardShellClient.tsx` — initially a **passthrough** that renders the same JSX as today's `DashboardLayoutClient` (no min-width floor, no mutex effects yet).
7. Update `app/(main)/[tenantId]/(dashboard)/layout.tsx` to render `<DashboardShell tenantId={params.tenantId}>{children}</DashboardShell>`. Keep `DashboardLayoutClient.tsx` file in place (unused) for rollback safety.
8. **Verification:** all existing E2E smoke pass + manual Chris check 4 viewports + `pnpm tsc --noEmit` clean.

### Phase 2 — Migrate consumers to SSoT widths (correctness fix)
1. Edit `frontend/src/hooks/use-copilot-offset.ts`:
   - Replace literals 380/60/0 with `COPILOT_WIDTHS.OPEN_RAIL` / `COPILOT_WIDTHS.RAIL_TOTAL` / `COPILOT_WIDTHS.MOBILE`.
   - Migrate from `isOpen` boolean to `sidebarState` 3-state (returns 0|60|460|680).
   - Replace internal `window.addEventListener("resize")` with `useViewport()`.
   - Re-export `COPILOT_OPEN_WIDTH` + `COPILOT_RAIL_WIDTH` as `@deprecated` aliases for 1 cycle (keeps any external consumer green).
2. Edit `frontend/src/features/copilot/components/CopilotSidebar.tsx` lines 86-87:
   - Replace `"0px"`/`"400px"`/`"60px"`/`"280px"` with `${COPILOT_WIDTHS.collapsed}px` / `${COPILOT_WIDTHS.chat}px` / `${COPILOT_WIDTHS.rail}px` / `${COPILOT_WIDTHS.history}px`.
3. **Verification:** existing `frontend/src/features/growth-studio/__tests__/visual-regression-drawer-bowtie.test.tsx` should still pass (offsets shift slightly but bowtie pattern preserved by masking). RED → re-baseline if needed (Q9).
4. Run `cd frontend && npx vitest run` — fix any test that asserted on the old 380 value.

### Phase 3 — Activate min-content-width floor (Scenario 1)
1. In `DashboardShellClient.tsx` apply: `<main className="... lg:min-w-[var(--shell-content-min-width,720px)]">` OR pass through inline style `style={{ minWidth: width >= 1024 ? 720 : undefined }}`.
2. Add CSS variable wiring in DashboardShellClient root: `<div style={{ '--shell-content-min-width': '720px' }}>`. Permits future per-route override without component change.
3. **Verification:** new `app-shell-min-content-width.spec.ts` Playwright; manual Chris check.

### Phase 4 — Activate mutex policy (Scenario 1, 3)
1. In `DashboardShellClient.tsx`, mount `useShellMutex()` (no-op return value; effects fire internally).
2. Edit `SidebarContext.tsx`:
   - Remove the inline `useEffect`-based `matchMedia("(max-width: 1279px)")` auto-collapse (lines 31-41) — `useShellMutex` now owns this with viewport-aware policy.
   - Add `expandSidebar()` + `collapseSidebar()` imperative actions.
3. Edit `CopilotSidebar.tsx`: backdrop click + Esc handler dispatch `useShellMutex.closePanel()` instead of `setSidebarState("collapsed")` directly.
4. Edit `AppSidebar.tsx`:
   - Remove local `isMobileOpen` useState.
   - Wire `<Sheet open={shellMutex.activePanel === 'app-sidebar'} onOpenChange={(o) => o ? shellMutex.openPanel('app-sidebar') : shellMutex.closePanel()}>`.
   - Add `aria-label="Abrir menú principal"` on the trigger Button (line 669-672).
5. **Verification:** `app-shell-mobile-mutex-fab.spec.ts` Playwright RED → GREEN. `use-shell-mutex.test.ts` unit RED → GREEN.

### Phase 5 — CopilotFAB + AppSidebar mobile aria-labels (Scenario 3)
1. Create `frontend/src/features/copilot/components/CopilotFAB.tsx` per spec §FAB copilot.
2. Mount `<CopilotFAB />` inside `DashboardShellClient.tsx` (always rendered; component returns null when off-mobile or copilot non-collapsed).
3. **Verification:** `CopilotFAB.test.tsx` Vitest. Manual mobile.

### Phase 6 — Z-index migration to tokens (Scenario 4)
1. Edit `AppSidebar.tsx:650` — `z-50` → `z-[40]` (Z_INDEX_CLASSES.APP_SIDEBAR).
2. Edit `AppSidebar.tsx:664` — topbar `z-50` → `z-[50]` (Z_INDEX_CLASSES.TOPBAR).
3. Edit `CopilotSidebar.tsx:110` — backdrop `z-40` → `z-[50]` (COPILOT_BACKDROP).
4. Edit `CopilotSidebar.tsx:125` — drawer `max-md:z-50` → `max-md:z-[60]` (COPILOT_DRAWER).
5. Edit AppSidebar mobile Sheet wrapper container z-class → `z-[60]` (APP_SIDEBAR_DRAWER).
6. CopilotFAB uses `z-[70]` from tokens.
7. **Verification:** `test-zindex-tokens-only.test.ts` arch fitness GREEN.

### Phase 7 — Arch test rename + scope ampliado (Scenario 4)
1. Rename `test-growth-studio-copilot-offset.test.ts` → `test-shell-copilot-offset.test.ts`.
2. Refactor to scan 3 dirs:
   - `features/growth-studio` (existing scope; allowlist `KNOWN_VIOLATIONS_GROWTH` = current 6 entries)
   - `components/shared/layout` (NEW; allowlist `KNOWN_VIOLATIONS_SHELL` = empty post-fix)
   - `features/copilot/components` (NEW; allowlist = empty)
3. Add `test-zindex-tokens-only.test.ts` + `test-copilot-widths-ssot.test.ts` + `test-no-shadowing-copilot-offset.test.ts`.
4. **Verification:** all arch tests pass, including allowlist freshness check.

### Phase 8 — ESLint custom rules + DashboardLayoutClient deletion
1. Author `frontend/eslint-rules/no-shadowing-copilot-offset.ts` (rule).
2. Author `frontend/eslint-rules/use-shell-mutex-for-drawer-toggles.ts` (rule, level=warn initially; ratchet→error post-refactor green).
3. Wire rules into `frontend/eslint.config.mjs`.
4. **Delete** `frontend/src/app/(main)/[tenantId]/(dashboard)/DashboardLayoutClient.tsx` — no longer imported.
5. **Verification:** `npx eslint src/components/shared/layout/ src/features/copilot/components/` GREEN.

### Phase 9 — Visual regression baselines + smoke spec
1. Re-baseline `visual-regression-drawer-bowtie.test.tsx` snapshot.
2. Create `app-shell-visual-regression.spec.ts` Playwright with masked main content.
3. **Verification:** manual Chris ratification of new baselines.

## Riesgos y mitigaciones

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Phase 4 mutex effect causes infinite loop (sidebar.expand → copilot.collapse → re-renders → re-evaluates) | high | Effect uses zustand subscribe with selector + idempotency check (`if (current === target) return;`). Unit test `use-shell-mutex.test.ts` covers ping-pong scenario. |
| Phase 2 SSoT migration breaks existing `useCopilotOffset` consumers (`ui/dialog`, `ui/sheet`, `ui/alert-dialog`, `ui/detail-panel`) by changing return value 380→460 | medium | Phase 2 includes Vitest + Playwright `dialog-centered-correctly.spec.ts` to verify centering against new SSoT. Snapshot tests for affected dialogs re-baselined if needed. |
| Visual regression masking misaligns and hides real bugs | medium | Q9 explicit: mask ONLY main content area; bowtie + nav + copilot visuals stay pixel-perfect (no mask). Chris ratifies new baselines per Phase 9. |
| Tenant switch leaves stale mutex state cross-tenant | low | Store factory keyed by tenantId via `useMemo([tenantId])`. New tenant = new store instance. Old tenant's localStorage entry persists but is unread (different key). |
| ESLint custom rule ergonomics (false positives) | low | Phase 8 introduces both rules at level=warn first. Ratchet to error only after refactor green for 1 cycle. |
| Z-index `z-[40]` Tailwind arbitrary value not purged | low | Tailwind arbitrary values within string literals are picked up by Tailwind JIT. Verified by existing `z-[60]` patterns elsewhere. |
| `useViewport` SSR mismatch | low | Returns null until mounted. DashboardShellClient gates min-width application on `width !== null`. CSS-only fallback (`lg:min-w-[720px]` Tailwind class) covers SSR paint. |
| FAB collides with floating action elements (toaster) | low | Z_INDEX.TOAST=100 > Z_INDEX.FAB=70. Toast wins layer. Position: toaster bottom-right same area; if collision visible, future story can swap FAB to bottom-left. Out of scope. |

## Open questions for orchestrator

1. **AD8 scope — does spec language about "AppSidebar mobile drawer NEW" require update?** Source confirms `AppSidebar.tsx:667-687` already renders `<Sheet side="left">`. Refactor scope is **smaller** than spec implies (rewire trigger + add aria-labels, no NEW Sheet component). Recommend: orchestrator notes this in `06-tickets.yaml` and flags `/po` to either ratify smaller scope OR clarify if the intent was to add a SECOND/different drawer (unlikely given Q ratification log).
2. **`useViewport` placement** — `frontend/src/hooks/use-viewport.ts` (alongside `use-copilot-offset.ts`) is current proposal. Alternative: `frontend/src/lib/hooks/use-viewport.ts`. Per FSD-Lite + existing convention (use-copilot-offset already in `/hooks/`), proposal stands. Confirm.
3. **`shell-mutex-store` location** — proposal: `frontend/src/stores/shell-mutex-store.ts` (new top-level dir for shell-scope cross-feature stores). Alternative: `frontend/src/components/shared/layout/shell-mutex-store.ts` (collocate with shell components). Decision: **proposal** wins because (a) hooks/ is already top-level, (b) future shell-level stores (theme, density) can sit alongside, (c) keeps shared/layout/ folder focused on JSX components. Confirm.
4. **Modal z-index alignment** — `ui/dialog` `ui/alert-dialog` `ui/sheet` `ui/popover` `ui/dropdown-menu` `ui/tooltip` all hardcoded `z-50` internally. Z_INDEX SSoT proposes MODAL=80, TOOLTIP=90. Out-of-scope per spec (only shell scope changes). Confirm out-of-scope OR include as Phase 10.
5. **ESLint custom rule plumbing** — `frontend/eslint.config.mjs` flat config plugin path needs verification. If team has prior local-plugin pattern (e.g., `nicolify-eslint-plugin/`), reuse; otherwise inline definitions. Builder Step 0 should grep `eslint-rules/` or similar.
6. **Bundle size budget** — non-functional NFR says "no aumenta >3% (acepta más por DashboardShell)". Estimated zustand store + 2 hooks + 1 component < 2 KB gzip. Confirm threshold acceptable, no specific gate set.
7. **Playwright spec viewport list for Scenario 1** — spec says "8 studios × 4 viewports × 3 copilot states = 96 main.width assertions". 8 studios: offer/brand/growth/sales/settings/connections/scheduling/copilot. Confirm copilot is in list (no copilot studio route exists today; replace with explicit `(dashboard)/[tenantId]/copilot` route OR drop to 7 studios?).

## Próximo paso

`done -> docs/product/stories/app-shell-sidebar-copilot-decoupling/03-arch-fe.md`

(Orchestrator `/architect` reúne con cualquier `03-arch-{be,agentic}.md` — none required for this story per surface decision — y produce `03-arch.md` + `04-validators.yaml` + `05-guidelines.md` + `06-tickets.yaml`.)
