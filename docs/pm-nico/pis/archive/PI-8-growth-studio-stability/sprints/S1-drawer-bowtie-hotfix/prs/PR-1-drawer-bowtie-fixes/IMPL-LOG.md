# IMPL-LOG — PR-1-drawer-bowtie-fixes (FE)

| Campo | Valor |
|---|---|
| Builder | nicolify-frontend (Sonnet) |
| Iter | 1 |
| Fecha | 2026-05-01 |
| Surface | frontend FE-only |
| Estado | implement done — handoff a auto gate-runner + auditor |

## Skills consultados

- `frontend-expert` — FSD-Lite + Server/Client correctness + runtime quality checklist
- `tessl__react-patterns` — hooks correctness + a11y baseline + memoization

## Step 0 grep findings (Anti-duplication GATE)

Ejecuté el bloque `Existing systems audit` de PR.md:

### 1a. `useCopilotOffset` ubicación canónica

```
$ find /home/chris/AISALESHT/frontend/src -name "use-copilot-offset*"
/home/chris/AISALESHT/frontend/src/hooks/use-copilot-offset.ts
```

**Discrepancia con PR.md:** PR.md decía `frontend/src/features/copilot/hooks/use-copilot-offset.ts` — ubicación real es `frontend/src/hooks/use-copilot-offset.ts`. NO bloqueante (hook existe, EXTEND consumers según PR.md). Decision: usar import canónico `@/hooks/use-copilot-offset`.

```
$ grep -rn "useCopilotOffset|copilotWidth" frontend/src
frontend/src/components/ui/alert-dialog.tsx:8,20,27,39,49
frontend/src/components/ui/sheet.tsx:9,23,30,66,67
frontend/src/components/ui/dialog.tsx:8,22,30,41,51
frontend/src/components/ui/detail-panel.tsx:7,54,90,107
frontend/src/hooks/use-copilot-offset.ts:17 (definition)
```

Consumers existentes: `alert-dialog`, `sheet`, `dialog`, `detail-panel`. Cero archivos paralelos `useCopilotOffset.v2.ts` o variantes.

### 1b. `DetailPanel` consumers cross-studio

11 sidebars + 1 strategy-canvas drawer:

- `MetricSidebar` (growth)
- `ChannelDetailSidebar` (growth — el que dispara el bug)
- `AutomationStepSidebar`, `CampaignDetailSidebar` (mail sidebars)
- `MailOverviewPanel`, `ChannelOverviewPanel`, `MetaAdsOverviewPanel`, `IgOrganicOverviewPanel` (overview)
- `NoDataSidebarPanel` (channel-widgets)
- `AdDetailPanel` (CreativosTab)
- `ActionDetailsDrawer` (strategy-canvas — anti-pattern PI-10 — NO TOCAR)

Cero archivos paralelos `DetailPanel.tsx`. SSoT ya canónico en `components/ui/detail-panel.tsx`.

### 1c. Z-index baseline existing

```
features/copilot/CopilotSidebar.tsx:110 → backdrop "z-40 ... md:hidden"
features/copilot/CopilotSidebar.tsx:125 → mobile drawer "max-md:z-50"
components/ui/detail-panel.tsx:87        → backdrop "z-[45]"
components/ui/detail-panel.tsx:102       → panel "z-[45]"
components/ui/{sheet,dialog,alert-dialog,popover,tooltip,select,dropdown-menu}.tsx → "z-50" (shadcn primitives baseline)
```

### 1d. `StageSummaryRow` consumers + parent wrappers

Único consumer:

```
app/(main)/[tenantId]/(dashboard)/growth-studio/layout.tsx:53
```

Renderizado dentro de `<PageContainer>` → main `flex-1 min-w-0`. Layout dashboard: `[AppSidebar][main flex-1][CopilotSidebar]` (flex desktop). Mobile: copilot `max-md:fixed z-50` overlay.

### 1e. Fixed/portal scan growth-studio (input al arch fitness ratchet)

```
features/growth-studio/components/metrics-dashboard/sidebar/youtube-organic/YouTubeDashboard.tsx (createPortal + fixed)
features/growth-studio/components/metrics-dashboard/sidebar/mail/MailDashboard.tsx (createPortal + fixed)
features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/MetaAdsDashboard.tsx (createPortal + fixed)
features/growth-studio/components/metrics-dashboard/sidebar/ig-organic/IgOrganicDashboard.tsx (createPortal + fixed)
features/growth-studio/components/metrics-dashboard/sidebar/website/WebsiteDashboard.tsx (createPortal + fixed)
features/growth-studio/components/metrics-dashboard/channel-widgets/ChannelConnectionModal.tsx (className fixed z-50)
```

6 archivos NO consumen `useCopilotOffset` ni envuelven en `DetailPanel` → violan invariante. **PI-9/PI-10 territory** (refactor masa metrics-dashboard/components/ deferido). Allowlist initial = estos 6, ratchet shrink-only.

### Conclusión Step 0

NO archivos paralelos detectados. CERO duplicación. Procedí con EDIT existing files + 2 NEW test files (justified per PR.md § 3 Decisión por sistema).

---

## Decisión z-index final (panel up vs copilot down)

**Elegido:** bumpear `DetailPanel` mobile-only a `z-[60]` vía `max-md:z-[60]` Tailwind responsive prefix. Desktop preserva `z-[45]`.

**Justificación:**

1. **Alternativas evaluadas:**
   - **A** — `z-[55]` mobile: panel arriba copilot z-50 pero ínfimo gap (5 unidades) — PR.md sugiere z-[60].
   - **B** — `z-[60]` mobile (ELEGIDO): gap claro de 10 unidades, semánticamente "panel = active focus" prevalece sobre copilot drawer cuando ambos abiertos en mobile. Solo afecta mobile.
   - **C** — Lower copilot mobile `z-[40]`: rompe — backdrop copilot ya está en `z-40`, solapamiento backdrop/drawer.
   - **D** — Bump global panel a `z-[60]`: rompe shadcn `<Dialog>`/`<Sheet>`/`<Alert>` modal semantics en desktop (panel tapaba modals z-50).

2. **Aplicación específica:** `max-md:z-[60]` clase responsive en `<className>` cn(...) — desktop sigue `z-[45]` intacto (donde DetailPanel coexistir con copilot flex-column funciona OK).

3. **Riesgo cross-studio:** Brand/Offer Studios consumen mismo `DetailPanel`. Bump SOLO mobile = comportamiento desktop idéntico = cero regresión Brand/Offer.

4. **z-[60] vs shadcn primitives mobile (Dialog/Sheet/Alert z-50):** En mobile cuando user abre `<Dialog>` SOBRE un DetailPanel, dialog `z-50` queda DEBAJO de panel `z-[60]`. **Tradeoff aceptado:** dialogs en mobile dentro de DetailPanel son raros (DetailPanel ya es la "modal" del flow). Si surge regresión, se eleva el ladder consistente.

---

## 3 fixes implementados

### Fix 1 — z-index ladder mobile (DetailPanel `max-md:z-[60]`)

**Archivo:** `frontend/src/components/ui/detail-panel.tsx`

```diff
   {/* Overlay — does NOT cover the copilot */}
+  {/* Mobile (max-md): copilot drawer is `fixed z-50`, so the panel must
+      render ABOVE it (panel is the user's explicit focus when opened).
+      Desktop (md+): copilot is in flex column, no overlap → keep z-[45]. */}
   <div
     className={cn(
-      "fixed top-0 bottom-0 left-0 z-[45] bg-black/50 transition-opacity duration-300",
+      "fixed top-0 bottom-0 left-0 z-[45] max-md:z-[60] bg-black/50 transition-opacity duration-300",
       visible ? "opacity-100" : "opacity-0",
     )}
     ...
   />

   {/* Panel */}
   <div
     ...
     className={cn(
-      `fixed top-0 bottom-0 z-[45] flex w-full flex-col overflow-y-auto border-l bg-background shadow-lg outline-none ${SIZE_CLASSES[size]}`,
+      `fixed top-0 bottom-0 z-[45] max-md:z-[60] flex w-full flex-col overflow-y-auto border-l bg-background shadow-lg outline-none ${SIZE_CLASSES[size]}`,
       ...
     )}
   />
```

Cobertura cross-studio: 11 consumers heredan automatic. Cero cambio desktop (preserva z-[45]).

### Fix 2 — Bowtie respeta copilot offset

**Archivo:** `frontend/src/features/growth-studio/components/metrics-dashboard/stage-widgets/StageSummaryRow.tsx`

```diff
+import { memo, useCallback, useMemo } from "react";

+import { useCopilotOffset } from "@/hooks/use-copilot-offset";

 export const StageSummaryRow = memo(function StageSummaryRow({...}) {
   const { navigate } = useNavigation();
   const pathname = usePathname();
+  // Reserve the copilot column on the right so the bowtie clip-path does
+  // NOT extend behind the copilot drawer on tablet (640-767px) where copilot
+  // is `max-md:fixed` overlay AND the offset hook returns its open width.
+  // PI-8 PR-1.
+  const copilotWidth = useCopilotOffset();
+  const outerStyle = useMemo(() => ({ paddingRight: `${copilotWidth}px` }), [copilotWidth]);
   ...
   return (
-    <div className="w-full overflow-x-auto pb-4 scrollbar-thin">
+    <div className="w-full overflow-x-auto pb-4 scrollbar-thin" style={outerStyle}>
```

`useMemo` para evitar nuevo `react-perf/jsx-no-new-object-as-prop` warning (no introducir nueva violación pre-existing baseline).

Comportamiento por viewport (verified via mock + tests):
- mobile <640: `copilotWidth=0` → `paddingRight: 0px` (sin layout shift)
- tablet 640-767: `copilotWidth=380` → bowtie no extiende detrás copilot fixed-overlay
- desktop ≥768 collapsed: `copilotWidth=60` → padding minimal
- desktop ≥768 open: `copilotWidth=380` → padding alineado a flex column copilot

### Fix 3 — Arch fitness ratchet (viewport edges adoption)

**Archivo NEW:** `frontend/src/__tests__/architecture/test-growth-studio-copilot-offset.test.ts`

Scan `features/growth-studio/**/*.{ts,tsx}` por:
- `createPortal(` (react-dom)
- `className="...fixed..."` Tailwind class

Cada match exige: `useCopilotOffset` import OR `from "@/components/ui/detail-panel"` import (DetailPanel internamente envuelve hook).

**Allowlist initial (KNOWN_VIOLATIONS):** 6 archivos PI-9/PI-10 territory:
- 5 channel dashboards: YouTube, Mail, MetaAds, IgOrganic, Website
- ChannelConnectionModal

Ratchet **shrink-only**: stale entries fail; new offenders fuera allowlist = build break. PI-9/PI-10 reduce allowlist progresivamente.

**No new files se requieren ajustar:** los DetailPanel consumers (sidebars/drawers) heredan automáticamente del fix #1 (max-md:z-[60]).

---

## Tests verdes

### Tests nuevos (RED→GREEN)

```
src/features/growth-studio/__tests__/visual-regression-drawer-bowtie.test.tsx (6 tests)
  ✓ panel renders with mobile z-[60] override (above copilot z-50)
  ✓ desktop z-[45] is preserved (no regression for desktop drawer ladder)
  ✓ applies paddingRight: copilotWidth when copilot is expanded
  ✓ applies paddingRight: 0 on mobile (no layout shift)
  ✓ applies paddingRight: railWidth when copilot is collapsed (rail)
  ✓ renders all stages even with loadingMap entries (skeleton smoke)

src/__tests__/architecture/test-growth-studio-copilot-offset.test.ts (1 test)
  ✓ every fixed/portal element imports useCopilotOffset OR uses DetailPanel
```

### Tests pre-existentes (NO regresión)

```
$ npx vitest run src/features/growth-studio src/__tests__/architecture src/components/ui/__tests__
Test Files  61 passed (61)
Tests       595 passed (595)
Duration    12.30s
```

### Quality gates locales

```
$ npx tsc --noEmit
✓ 0 errors

$ npx eslint <touched files>
✓ 0 errors (3 warnings: 1 file-ignored detail-panel.tsx — config-level pre-existing;
  2 react-perf warnings StageSummaryRow.tsx lines 65 + 79 — pre-existing baseline,
  no introduzco nuevos)
```

Mi código:
- DetailPanel.tsx: 0 errors, file ignored config-level (pre-existing pattern)
- StageSummaryRow.tsx: 0 errors, 2 pre-existing warnings (clipPath inline obj line 65, onClick inline line 79 — pre-fix baseline)
- visual-regression test: 0 errors, 0 warnings (NOOP hoisted)
- arch fitness test: 0 errors

---

## chrome-devtools-verify smoke

**Estado:** Deferido a Chris-mediated smoke (per PR.md § Aceptación → "Chrome devtools smoke Chris-mediated 5 stages × mobile + desktop").

**Razón:** Smoke profundo requiere Clerk authenticated session + interactive nav 5 stages × 2 viewports. Builder runtime no tiene credenciales Clerk para auto-smoke.

**Coverage compensatorio en este PR:**
- Visual regression test (6 cases) cubre invariantes layout via mock useCopilotOffset (mobile 0 / tablet 380 / desktop rail 60 / desktop open 380)
- Arch fitness ratchet protege regresión futura
- 595 tests vitest verdes (cero regresión)
- TSC strict + ESLint baseline preservado

**Action item Chris (post-merge):** Smoke navegación local dev-app:
1. Login tenant test
2. Visitar `/[tenantId]/growth-studio`
3. 5 stages × 2 viewports (375x667 + 1280x800):
   - Click ChannelRow → DetailPanel abre
   - Bowtie superior NO se distorsiona con copilot expanded
   - Mobile: panel visible arriba copilot drawer
   - Desktop: bowtie respeta espacio copilot (no extiende debajo)
4. Smoke cross-studio: Brand/Offer DetailPanel sin regresión

---

## Surface tocada (final)

| Tipo | Path | Acción |
|---|---|---|
| FE component | `frontend/src/components/ui/detail-panel.tsx` | EDIT z-index `max-md:z-[60]` mobile (backdrop + panel) |
| FE component | `frontend/src/features/growth-studio/components/metrics-dashboard/stage-widgets/StageSummaryRow.tsx` | EDIT wrap outer container con `useCopilotOffset` + `paddingRight` style memoized |
| FE tests | `frontend/src/features/growth-studio/__tests__/visual-regression-drawer-bowtie.test.tsx` | NEW (regresión visual breakpoints + z-index ladder) |
| FE arch fitness | `frontend/src/__tests__/architecture/test-growth-studio-copilot-offset.test.ts` | NEW (ratchet shrink-only — 6 allowlisted + protege futuros) |

**NO tocado (correcto per PR.md anti-patterns):**
- `CopilotSidebar.tsx` — no necesario tras decision z-[60] panel up
- `metrics-dashboard/components/` (177 archivos) — PI-10
- `strategy-canvas/` — PI-10
- 5 channel dashboards portals — PI-9/PI-10 (allowlisted)

---

## Próximo paso

Auto-spawn:
1. `nicolify-gate-runner` Haiku → `/test-frontend` gate-output.json
2. `nicolify-frontend-auditor` Opus → REVIEW.md verdict
3. Auto-fix loop max 3 iter si verdict ≠ PASS
