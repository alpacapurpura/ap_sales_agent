# 01-spec.md — App Shell ↔ Copilot Decoupling (content-area starvation + mutex absence + offset SSoT drift)

> Owner: `/po`. Spec ejecutable Gherkin AI-resistant. **Diagnosis correction (2026-05-07):** bug NO es z-index overlap. Live repro confirma overlap=0px siempre. Real bug = content area starvation (`main flex-1 min-w-0` sin floor) + mutex policy ausente (AppSidebar.isCollapsed y CopilotStore.isOpen independientes) + `useCopilotOffset` hook miente por 80-220px vs CopilotSidebar grid widths reales.

---
story_id: app-shell-sidebar-copilot-decoupling
type: service-story
module: shared
capability: app-shell-layout
po_version: 4
last_modified: 2026-05-07T05:45:00Z
ratified_by_chris: true
links:
  outcome: "../../outcomes/growth-copilot-layout-unification.md"
  live_repro: "00-live-repro.md"
  app_sidebar: "../../../../frontend/src/components/shared/layout/AppSidebar.tsx"
  copilot_sidebar: "../../../../frontend/src/features/copilot/components/CopilotSidebar.tsx"
  copilot_offset_hook: "../../../../frontend/src/hooks/use-copilot-offset.ts"
  dashboard_layout: "../../../../frontend/src/app/(main)/[tenantId]/(dashboard)/DashboardLayoutClient.tsx"
  arch_test_offset: "../../../../frontend/src/__tests__/architecture/test-growth-studio-copilot-offset.test.ts"
hotfix_metadata:
  repro_verified: true
  repro_command: "chrome-devtools-verify subagent — 14 screenshots cross-viewport (500/768/1024/1440/1920) cross-studio (offer/brand/growth/sales/settings). See 00-live-repro.md for evidence + numerical findings."
  diagnosis_validates_handoff: false
  diagnosis_correction: "Original framing 'sidebar overlap z-index conflict' refuted by live repro — overlap area = 0px in EVERY measured cell. Real bug = (1) `main flex-1 min-w-0` has no min-width floor → CopilotSidebar consume content space until main = 52px @ 768×expanded sidebar×open copilot. (2) AppSidebar.isCollapsed and CopilotStore.isOpen independent — no mutex policy auto-collapses one when other opens at narrow viewport. (3) `useCopilotOffset` returns 380/60/0 but CopilotSidebar grid renders 460/680/60 → all dialogs/sheets mis-centered 80-220px. (4) Mobile <768: AppSidebar lacks left drawer (only 40px topbar hamburger sin aria-label), no FAB to summon copilot once dismissed."
---

## Resumen ejecutivo

Refactor del shell layout (`DashboardLayoutClient.tsx`) introduciendo un parent component `<DashboardShell>` que centraliza la computación del chrome (sidebar + copilot widths), enforza min content width floor, implementa mutex policy entre AppSidebar y CopilotSidebar en viewports estrechos, alinea SSoT entre `useCopilotOffset` hook y `CopilotSidebar` grid widths, centraliza z-index tokens, y corrige gaps mobile (AppSidebar drawer izquierdo + FAB copilot + aria-label hamburger). Extiende arch fitness existente (`test-growth-studio-copilot-offset.test.ts`) para enforzar contrato a nivel shell.

**Outcome user-facing:**
- main content width ≥720px @ ≥1024 viewport siempre (sin importar copilot/sidebar state)
- mobile <768: AppSidebar y Copilot drawers mutuamente exclusivos (uno abre → otro cierra)
- mobile <768: AppSidebar accessible vía left drawer (no solo topbar)
- mobile <768: FAB copilot persistente para reabrir una vez dismissed
- dialogs/sheets centered correctamente (no mis-aligned 80-220px)
- a11y: hamburger topbar con aria-label

## Acceptance Criteria (Gherkin AI-resistant)

### Scenario 1 — `min-content-width-enforced-via-mutex-and-floor` (`type: happy`)

**Given:**
- DashboardShell parent component (NEW) computa chrome total: `chromeWidth = appSidebarWidth + copilotWidth`.
- Viewport breakpoints + policy:
  - `≥1280px`: ambos pueden estar expanded (no mutex needed). `main` width ≥ `viewport - chromeWidth`, sin floor (suficiente espacio).
  - `1024-1279px`: si copilot.isOpen y appSidebar.isExpanded → mutex auto-collapses appSidebar a rail. `main` floor = 720px.
  - `768-1023px`: si copilot.isOpen → appSidebar auto-collapses a rail SIEMPRE. `main` floor = 720px (puede no alcanzarse si copilot full → degrade copilot a rail también).
  - `<768px`: ambos drawers mutuamente exclusivos (mobile mutex Scenario 3).

**When:**
- Usuario navega 8 studios × 4 viewports (1024/1280/1440/1920) × 3 copilot states (closed/rail/open).
- Por cada combinación, Playwright captura `getBoundingClientRect()` de `main` element.

**Then:**
- Para CADA combinación @≥1024px: `main.width >= 720px` (read-comfort floor).
- Para 1024-1279px + copilot.open: `appSidebar.width === 80px` (auto-collapsed por mutex).
- Para `<1024px + copilot.open`: appSidebar auto-collapsed.
- Bowtie growth-studio + métricas dashboard intactos pixel-perfect (visual regression).
- Cross-studio (offer/brand/growth/sales/settings/connections/scheduling/copilot): main floor respetado.

**Graders:**
- `{ type: contract_test, path: "frontend/src/components/shared/layout/__tests__/DashboardShell-min-width-floor.test.tsx" }` — render component con mocked viewport widths, verify mutex + floor.
- `{ type: integration, path: "frontend/e2e/specs/smoke/app-shell-min-content-width.spec.ts" }` — Playwright 8 studios × 4 viewports × 3 copilot states = 96 main.width assertions.
- `{ type: state_check, target: source, query: "grep -c 'min-w-\\[720px\\]\\|MIN_CONTENT_WIDTH' frontend/src/components/shared/layout/" }` — token exists.
- `{ type: contract_test, path: "frontend/src/features/growth-studio/__tests__/visual-regression-drawer-bowtie.test.tsx" }` — pixel-perfect bowtie post-refactor.

---

### Scenario 2 — `useCopilotOffset-aligned-with-CopilotSidebar-ssot` (`type: negative`)

**Given:**
- Pre-refactor: `useCopilotOffset` retorna `{ open: 380, rail: 60, mobile: 0 }`. `CopilotSidebar.tsx` líneas 86-87 declaran `chatW = "400px"`, `railOrHistoryW = "60px" | "280px"`. Grid template real: `0px 60px` / `400px 60px` / `400px 280px`. Drift 80-220px.
- Adversarial dev intenta agregar nueva constant divergente (e.g., `useCopilotOffset` retorna 500 cuando CopilotSidebar usa 460).

**When:**
- Vitest run con `cd frontend && npx vitest run`.

**Then:**
- Constants centralizados en `frontend/src/features/copilot/lib/copilot-shell-widths.ts` (NEW SSoT module).
- `useCopilotOffset` hook importa SSoT.
- `CopilotSidebar` componente importa SSoT (no re-declara).
- Arch test `test-copilot-widths-ssot.test.ts` (NEW) FAILS si:
  - `CopilotSidebar.tsx` declara `chatW`/`railW`/`historyW` literal hardcoded
  - `useCopilotOffset.ts` declara `COPILOT_OPEN_WIDTH`/`COPILOT_RAIL_WIDTH` literal hardcoded
  - Cualquier código fuera SSoT module declara magic numbers que match `380|400|460|60|280|680`
- Adversarial dev: violación detectada → build break con mensaje claro `"Use COPILOT_WIDTHS from copilot-shell-widths.ts — no hardcoded chat/rail/history widths."`.

**Graders:**
- `{ type: contract_test, path: "frontend/src/__tests__/architecture/test-copilot-widths-ssot.test.ts" }` — NEW arch test, parsea source y enforza SSoT.
- `{ type: state_check, target: source, query: "test -f frontend/src/features/copilot/lib/copilot-shell-widths.ts" }` — exists.
- `{ type: contract_test, path: "frontend/src/hooks/__tests__/use-copilot-offset.test.ts" }` — hook return value === SSoT constants.
- `{ type: contract_test, path: "frontend/src/features/copilot/components/__tests__/CopilotSidebar-grid-widths.test.tsx" }` — grid template matches SSoT.
- `{ type: integration, path: "frontend/e2e/specs/smoke/dialog-centered-correctly.spec.ts" }` — dialog/sheet open con copilot rail/full → `dialog.left + dialog.width / 2 ≈ availableContentArea / 2` (±5px tolerance).

---

### Scenario 3 — `mobile-mutex-drawers-and-fab-and-a11y` (`type: edge`)

**Given:**
- Viewport <768 (500px tested via MCP, 375 inferred).
- AppSidebar pre-refactor: `md:flex` → `display:none` mobile, ONLY 40px topbar hamburger sin aria-label.
- CopilotSidebar pre-refactor: mobile drawer correcto (translate-x + backdrop) PERO no FAB para reabrir.
- DashboardShell con `useShellMutex` hook (NEW) gestiona `activePanel: 'app-sidebar' | 'copilot' | null`.

**When:**
- Mobile flow:
  1. Usuario tap hamburger (left, ahora con aria-label `"Abrir menú principal"`).
  2. AppSidebar mobile drawer (NEW Sheet izquierdo) abre. Backdrop visible.
  3. Usuario tap copilot trigger button mientras AppSidebar drawer abierto.
  4. AppSidebar drawer auto-cierra. CopilotSidebar drawer abre.
  5. Usuario tap backdrop → CopilotSidebar drawer cierra.
  6. CopilotSidebar dismissed: FAB copilot (NEW, posicionado bottom-right `fixed`) visible.
  7. Usuario tap FAB → CopilotSidebar drawer reabre.
  8. Inverso: con CopilotSidebar abierto, tap hamburger → CopilotSidebar cierra, AppSidebar abre.

**Then:**
- En CADA paso del flow: solo UN drawer abierto a la vez (mutex strict).
- `useShellMutex.activePanel` refleja state (zustand o React Context global).
- aria-label hamburger present + descriptive.
- FAB copilot visible solo cuando `viewport <768 && copilotStore.sidebarState === 'collapsed'`.
- FAB tiene aria-label `"Abrir asistente"`.
- Backdrops: drawer abierto → backdrop click cierra drawer + restaura body scroll.
- Focus trap en cada drawer (Sheet primitive ya provee).
- En desktop (≥768): drawers/FAB hidden (display:none), behavior pre-existente preservado.

**Graders:**
- `{ type: contract_test, path: "frontend/src/components/shared/layout/__tests__/AppSidebar-mobile-drawer.test.tsx" }` — render mobile, abrir drawer NEW, mutex con copilot.
- `{ type: contract_test, path: "frontend/src/features/copilot/components/__tests__/CopilotFAB.test.tsx" }` — render mobile + dismissed → FAB visible. Click → drawer abre.
- `{ type: integration, path: "frontend/e2e/specs/smoke/app-shell-mobile-mutex-fab.spec.ts" }` — Playwright mobile viewport, 8-step flow assertions.
- `{ type: state_check, target: a11y, query: "axe-core scan mobile viewport: hamburger aria-label present, FAB aria-label present, drawer focus trap" }` — 0 violations.
- `{ type: state_check, target: store, query: "useShellMutex.activePanel: only 'app-sidebar' OR 'copilot' OR null mobile viewport" }`.

---

### Scenario 4 — `arch-fitness-extends-shell-zindex-tokens-and-rejects-shadowing` (`type: adversarial`)

**Given:**
- Refactor done: `frontend/src/lib/tokens/z-index.ts` exporta tokens nombrados (Z_APP_SIDEBAR, Z_COPILOT_DRAWER, Z_COPILOT_BACKDROP, Z_FAB, Z_MODAL, Z_TOOLTIP, Z_TOAST).
- Existing arch test `test-growth-studio-copilot-offset.test.ts` extendido a `components/shared/layout/**` y `features/copilot/components/**` (allowlist scope ampliado, ratchet shrinks-only).
- Adversarial dev intenta:
  1. Agregar nueva clase Tailwind `z-[60]` hardcoded en AppSidebar/CopilotSidebar.
  2. Crear copy local de `useCopilotOffset` con valor falso (e.g., shadow hook).
  3. Bypass mutex policy abriendo drawers programáticamente directo a CopilotStore (sin `useShellMutex`).
  4. Crear nuevo fixed/portal element en `components/shared/layout/` o `features/copilot/components/` que NO consume `useCopilotOffset` ni width SSoT.

**When:**
- Build CI run + arch fitness suite + ESLint.

**Then:**
- Adversarial 1: arch test `test-zindex-tokens-only.test.ts` (NEW) detecta hardcoded Tailwind z classes en layout shell paths → FAIL.
- Adversarial 2: arch test `test-no-shadowing-copilot-offset.test.ts` (NEW) detecta imports `useCopilotOffset` que NO vienen de `@/hooks/use-copilot-offset` o `@/features/copilot/lib/copilot-shell-widths` → FAIL.
- Adversarial 3: ESLint custom rule `nicolify/use-shell-mutex-for-drawer-toggles` (NEW) detecta calls directos a `useCopilotStore.setState({sidebarState: 'open'})` o `useSidebar().toggleSidebar()` fuera de `useShellMutex` → warn (ratchet error post-refactor).
- Adversarial 4: arch test `test-growth-studio-copilot-offset.test.ts` extendido (renamed `test-shell-copilot-offset.test.ts`) cubre `components/shared/layout/**` + `features/copilot/components/**` con SAME ratchet pattern. Allowlist set vacío post-refactor (0 known violations en shell scope).
- Build CI bloquea con mensajes accionables.

**Graders:**
- `{ type: contract_test, path: "frontend/src/__tests__/architecture/test-zindex-tokens-only.test.ts" }` — NEW arch test, layout + copilot shell paths NO hardcoded z classes.
- `{ type: contract_test, path: "frontend/src/__tests__/architecture/test-no-shadowing-copilot-offset.test.ts" }` — NEW.
- `{ type: contract_test, path: "frontend/src/__tests__/architecture/test-shell-copilot-offset.test.ts" }` — RENAMED de `test-growth-studio-copilot-offset.test.ts` con scope ampliado (incluye shell). Allowlist `KNOWN_VIOLATIONS_SHELL` set vacío.
- `{ type: state_check, target: eslint, query: "npx eslint src/components/shared/layout/ src/features/copilot/components/" }` — 0 errors hardcoded z-index, 0 warnings shell-mutex bypass.
- `{ type: state_check, target: ratchet, expect: "no new violations introduced" }`.

---

## Non-functional requirements

| Categoría | Requisito | Verificador |
|---|---|---|
| Performance | Layout reflow on copilot toggle <16ms (60fps) | Lighthouse perf trace |
| Mobile | Drawer transition smooth 60fps en viewport 375 (inferido vía 500 testing) | Playwright trace + perf |
| Accesibilidad | Focus management drawer ↔ copilot mutex sin trap; aria-labels en hamburger + FAB; ARIA live region en mutex transitions | axe-core + manual a11y review |
| i18n | Strings nuevos spanish neutro (aria-labels, FAB tooltip, transition announcements) | Lint regex |
| Tenant isolation | zustand `copilot-store` y `shell-mutex-store` tenant-namespaced (key suffix `${tenantId}`); cross-tab seguro | Adversarial scenario edge |
| Z-index discipline | Solo tokens de `lib/tokens/z-index.ts` en shell + copilot shell paths | ESLint rule + arch test |
| SSoT widths | `useCopilotOffset` y `CopilotSidebar` consumen mismas constants SSoT | Arch test |
| No regression | Bowtie + métricas dashboard pixel-perfect post-fix; growth-studio routes intactos | Visual regression test |
| Bundle | Layout shell + copilot shell bundle size NO aumenta >3% (acepta más por DashboardShell) | Bundle analyzer |
| Min content width | `main.width >= 720px` @ ≥1024 viewport siempre | Scenario 1 grader |
| Mobile mutex | Drawers mutuamente exclusivos <768; FAB visible solo dismissed copilot | Scenario 3 graders |

## Constraints técnicos heredados

- `.claude/rules/frontend-fsd.md` — `components/shared/layout/` puede importar de `features/copilot/lib/` (excepción documentada `shared → feature(:own)`).
- `.claude/rules/frontend-quality.md` — ESLint 0 errors, TypeScript strict 0 errors.
- `.claude/rules/architectural-fitness.md` — ratchet shrink-only allowlists.
- `.claude/rules/anti-duplication.md` — Step 0 grep antes nuevo hook/component:
  - `useShellMutex` NEW (no shadowing, no mirror)
  - `copilot-shell-widths.ts` lift de inline literals (no duplicate SSoT)
- `.claude/rules/spanish-text.md` — voseo glosario aria-labels + tooltips.
- `.claude/rules/tdd-mandatory.md` — arch tests RED + Playwright smoke RED antes implementar fix.
- `.claude/rules/e2e-testing.md` — Playwright smoke obligatorio para mutex flow + dialog centering.
- Skills cargar: `frontend-expert`, `copilot-expert`, `playwright-expert`, `chrome-devtools-verify` (live repro evidence).

## Architect orientation hints

### `<DashboardShell>` Hybrid pattern (Chris ratified Q8)

Server wrapper + Client inner. Pattern documentado tessl `nextjs-app-router-modularization`:

```
frontend/src/components/shared/layout/
├── DashboardShell.tsx              # Server Component — emite metadata, recibe children, pasa al Client
└── DashboardShellClient.tsx        # Client Component — consume useViewport + useCopilotStore + useShellMutex
```

`DashboardShell` (Server) responsibilities:
- Recibe `children` (page content) como prop
- Emite metadata SEO si aplica
- Renderiza `<DashboardShellClient>` envolviendo children + AppSidebar + CopilotSidebar slots

`DashboardShellClient` (Client) responsibilities:
- Compute `appSidebarWidth` from SidebarContext (80 collapsed | 256 expanded)
- Compute `copilotWidth` from CopilotStore + viewport breakpoint
- Apply mutex policy via `useShellMutex` hook based on viewport breakpoint
- Pass computed offsets to AppSidebar (via context or props) so it can position correctly
- Enforce `main` min-width 720px @≥1024 (Tailwind class `lg:min-w-[var(--shell-content-min-width)]` o equivalente)

### `useShellMutex` hook (NEW)

```ts
// frontend/src/hooks/use-shell-mutex.ts
export type ActivePanel = 'app-sidebar' | 'copilot' | null;

export function useShellMutex() {
  const viewport = useViewport(); // < 768 | 768-1023 | 1024-1279 | >= 1280
  const sidebar = useSidebar();
  const copilot = useCopilotStore();
  
  // Effect: on copilot.isOpen change, if viewport < 1280 and sidebar.expanded, collapse it
  // Effect: on sidebar.expand attempt, if viewport < 1280 and copilot.open, collapse copilot
  // Effect: mobile (<768): toggling one closes the other (true mutex)
  
  return { activePanel: ..., setActivePanel: ... };
}
```

### `copilot-shell-widths.ts` SSoT (NEW)

```ts
// frontend/src/features/copilot/lib/copilot-shell-widths.ts
export const COPILOT_WIDTHS = {
  collapsed: 0,
  rail: 60,
  chat: 400,
  history: 280,
  // Derived totals (open states)
  RAIL_TOTAL: 60,                  // collapsed+rail
  OPEN_RAIL: 460,                  // chat+rail (default open)
  OPEN_FULL: 680,                  // chat+history (full)
  MOBILE: 0,                       // hidden on mobile (drawer instead)
} as const;

// useCopilotOffset and CopilotSidebar grid template both consume this.
```

### Z-index tokens (NEW — fluid scale 0/10/.../100, Chris ratified Q6)

```ts
// frontend/src/lib/tokens/z-index.ts
export const Z_INDEX = {
  AUTO: 'auto',
  CONTENT: 0,
  STICKY: 30,
  APP_SIDEBAR: 40,
  COPILOT_BACKDROP: 50,
  MOBILE_DRAWER_BACKDROP: 50,
  COPILOT_DRAWER: 60,
  APP_SIDEBAR_DRAWER: 60,           // mobile drawer same layer as copilot but mutex prevents both
  TOPBAR: 60,
  FAB: 70,
  MODAL: 80,
  TOOLTIP: 90,
  TOAST: 100,
} as const;
```

Architect ratifica valores definitivos post-medir actual ladder; spacing 10 entre layers permite insertar tokens futuros sin renumeración.

### AppSidebar mobile drawer (NEW Sheet izquierdo)

Estructura paralela a CopilotSidebar mobile pattern:
```tsx
{viewport < 768 && (
  <Sheet open={isMobileSidebarOpen} onOpenChange={setIsMobileSidebarOpen}>
    <SheetContent side="left" className="w-72 p-0">
      <NavContent mobile ... />
    </SheetContent>
  </Sheet>
)}
```

Topbar hamburger trigger: agregar `aria-label="Abrir menú principal"` (fix a11y bug pre-existing).

### FAB copilot (NEW)

`frontend/src/features/copilot/components/CopilotFAB.tsx`:
```tsx
"use client";
export function CopilotFAB() {
  const isOpen = useCopilotStore((s) => s.isOpen);
  const setOpen = useCopilotStore((s) => s.setOpen);
  const viewport = useViewport();
  
  if (viewport >= 768 || isOpen) return null;
  
  return (
    <Button
      onClick={() => setOpen(true)}
      aria-label="Abrir asistente"
      className={cn("fixed bottom-4 right-4 rounded-full h-14 w-14", `z-[${Z_INDEX.FAB}]`)}
    >
      <MessageCircle className="h-6 w-6" />
    </Button>
  );
}
```

### Migración arch test

Renombre: `test-growth-studio-copilot-offset.test.ts` → `test-shell-copilot-offset.test.ts`. Scope ampliado:
```ts
const SCAN_DIRS = [
  path.join(SRC_ROOT, "components", "shared", "layout"),  // NEW
  path.join(SRC_ROOT, "features", "copilot", "components"), // NEW
  path.join(SRC_ROOT, "features", "growth-studio"),         // existing
];
```

Allowlists per scope. Growth-studio existing 6 entries; shell scope new = 0 (refactor garantiza).

## Ratification log (Chris 2026-05-07)

| Q | Pregunta | Decisión |
|---|---|---|
| 1 | Min content width | **720px global**. Sales-inbox 3-col responsive separate idea (creada `sales-inbox-responsive-collapse` en ideas-pool). |
| 2 | Mutex breakpoint | **≥1280px** ambos expanded sin mutex. <1280 mutex aplica. |
| 3 | FAB position | **Bottom-right** `fixed bottom-4 right-4`. |
| 4 | useShellMutex storage | **New zustand store** `shell-mutex-store` tenant-namespaced. Independiente de SidebarContext + CopilotStore existing. |
| 5 | Arch test rename | **Rename a `test-shell-copilot-offset.test.ts`** con scope-keyed allowlists (`KNOWN_VIOLATIONS_SHELL` + `KNOWN_VIOLATIONS_GROWTH`). |
| 6 | Z-index values | **Fluid scale 0/10/.../100** (no valores propuestos 40/45/50/55/60/70/80). Spacing 10 entre layers. |
| 7 | Aria-labels | Hamburger: **"Abrir menú principal"**. FAB: **"Abrir asistente"**. Close button drawer: **"Cerrar menú principal"**. |
| 8 | DashboardShell | **Hybrid**: Server wrapper (`DashboardShell.tsx`) + Client inner (`DashboardShellClient.tsx`). Pattern tessl `nextjs-app-router-modularization`. |
| 9 | Visual regression | **Sí con masking** del main content area (cambia por floor). Bowtie + AppSidebar nav + CopilotSidebar visual son invariantes pixel-perfect. |
| 10 | Sales-inbox 3-col | **OUT scope** — idea `sales-inbox-responsive-collapse` agregada a ideas-pool.yaml. |

## Ratification log v2 (Chris 2026-05-07 post architect-fe)

Architect-fe levantó 7 follow-ups; ratificados:

| AD-Q | Decisión |
|---|---|
| **AD8 scope correction** | AppSidebar mobile drawer **YA EXISTE** (Sheet side='left' L667-687 — fuente: `AppSidebar.tsx:667-687`). Spec wording original "NEW Sheet izquierdo" → corregir a **REFACTOR existing**: rewire trigger desde local `useState isMobileOpen` a `useShellMutex.activePanel === 'app-sidebar'` + agregar aria-labels (hamburger trigger + close button drawer). NO se agrega Sheet nuevo. |
| **Modal z-index alignment Phase 10** | **IN scope** este story como Phase 10 post-shell. Migrar `ui/dialog`, `ui/alert-dialog`, `ui/sheet`, `ui/popover`, `ui/dropdown-menu`, `ui/tooltip` (6 primitives Shadcn) de `z-50` hardcoded a `Z_INDEX` tokens. Riesgo: tocar Shadcn primitives shrink-only via wrappers. Architect decide implementación (extend wrappers vs in-place edit). |
| **Scenario 1 viewport list** | **8 routes existentes** del segment `app/(main)/[tenantId]/(dashboard)/`: brand-studio, offer-studio, growth-studio, sales, settings, connections, brand-settings, audit (or avatars). Copilot NO tiene top-level route — drawer cross-shell, ya cubierto separately. 8×4×3=96 assertions main.width. |
| **useViewport placement** | `frontend/src/hooks/use-viewport.ts` (alongside existing `use-copilot-offset.ts`). |
| **shell-mutex-store location** | `frontend/src/stores/shell-mutex-store.ts` (NEW top-level dir for shell-scope cross-feature stores). |
| **ESLint custom rule plumbing** | Builder Step 0 grep `frontend/eslint-rules/` o equivalente. Si plugin local pattern existe → reuse; sino inline definitions en `eslint.config.mjs`. |
| **Bundle size** | NFR <3% growth informativo, sin gate hard. |

## Story size + split consideration

Scope grande (11+ workstreams identificados):
1. `<DashboardShell>` parent component
2. `useShellMutex` hook + zustand store
3. `useViewport` hook (si no existe)
4. `copilot-shell-widths.ts` SSoT + refactor consumers
5. `lib/tokens/z-index.ts` SSoT
6. AppSidebar mobile drawer (NEW Sheet izquierdo)
7. AppSidebar consume `useCopilotOffset` + DashboardShell offsets
8. CopilotFAB component (NEW)
9. Arch test rename + scope ampliado
10. ESLint custom rule (no-shadowing-copilot-offset, use-shell-mutex)
11. Visual regression baselines + Playwright smoke (≥96 assertions)

**Recomendación /po:** mantener 1 story — architect decide split en `06-tickets.yaml` si excede 10 tickets. Cohesión semántica alta (todos componentes shell layout). Split prematuro fragmenta validación end-to-end.

## Hand off post ratificación

```
state: refining → refined  (si Chris ratifica scenarios + open questions resueltos)
next: /architect orchestrator → produce ready package CON sub-architect /architect-fe (DashboardShell + useShellMutex + SSoT widths + tokens + AppSidebar drawer + FAB + arch test extension + ESLint rule + visual regression). Sin BE ni agentic surfaces.
```

## Live repro reference

Evidence completa en `00-live-repro.md` (subagent chrome-devtools-verify, 14 capturas + DOM dumps + computed styles + numerical findings). 5 viewports × 5 studios cubiertos. Diagnosis correction documentada arriba en `hotfix_metadata.diagnosis_correction`. Spec scenarios y AC magnitudes pueden ajustarse post-review evidence.
