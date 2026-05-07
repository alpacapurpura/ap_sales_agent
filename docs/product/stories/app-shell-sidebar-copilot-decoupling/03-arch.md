# 03-arch.md — App Shell ↔ Copilot Decoupling (consolidated)

> Owner: `/architect`. Single-surface story (FE only). Detalle completo en `03-arch-fe.md`.

---
story_id: app-shell-sidebar-copilot-decoupling
arch_version: 1
last_modified: 2026-05-07T05:50:00Z
links:
  spec: "01-spec.md"
  live_repro: "00-live-repro.md"
  arch_fe: "03-arch-fe.md"
  outcome: "../../outcomes/growth-copilot-layout-unification.md"
---

## Surfaces involved

- **BE:** no
- **FE:** **yes** — single sub-architect (`/architect-fe` equivalent agent)
- **AGENTIC:** no

## FE arch (full detail in `03-arch-fe.md`)

### Decisión arquitectónica clave

Reemplazar `DashboardLayoutClient` (flat container con siblings AppSidebar / main / CopilotSidebar, mutual-isolation entre `SidebarContext.isCollapsed` y `useCopilotStore.sidebarState`) por **`<DashboardShell>` Hybrid** (Server wrapper + Client inner) que centraliza el cómputo del chrome (sidebar width + copilot width), aplica un **mutex policy** entre AppSidebar y CopilotSidebar dependiente de viewport, y enforza un **min content width floor** de 720px @≥1024.

### NEW artifacts (8)

| File | Type | Role |
|---|---|---|
| `components/shared/layout/DashboardShell.tsx` | Server Component | Wrapper passthrough + tenantId prop |
| `components/shared/layout/DashboardShellClient.tsx` | Client Component | Hooks consumer, mutex policy host, min-width floor |
| `features/copilot/components/CopilotFAB.tsx` | Client Component | Mobile-only + collapsed-only FAB |
| `features/copilot/lib/copilot-shell-widths.ts` | SSoT module | COPILOT_WIDTHS frozen const (collapsed/chat/rail/history + RAIL_TOTAL/OPEN_RAIL/OPEN_FULL/MOBILE) |
| `lib/tokens/z-index.ts` | SSoT module | Z_INDEX fluid scale 0/10/.../100 |
| `stores/shell-mutex-store.ts` | zustand store | tenant-namespaced activePanel |
| `hooks/use-shell-mutex.ts` | hook | composes viewport+sidebar+copilot+mutex store |
| `hooks/use-viewport.ts` | hook | SSR-safe matchMedia wrapper |

### MODIFIED files (5)

- `AppSidebar.tsx` — z-classes via tokens; mobile Sheet trigger rewire mutex (NOT new Sheet — refactor existing L667-687); aria-labels Spanish
- `CopilotSidebar.tsx` — grid widths consume SSoT; backdrop+Esc dispatch mutex
- `SidebarContext.tsx` — remove inline matchMedia auto-collapse; add expand/collapse actions
- `use-copilot-offset.ts` — consume SSoT widths; migrate isOpen→sidebarState; deprecated re-exports 1 ciclo
- `app/(main)/[tenantId]/(dashboard)/layout.tsx` — render `<DashboardShell>` instead of `<DashboardLayoutClient>`

### DELETED files (1)

- `app/(main)/[tenantId]/(dashboard)/DashboardLayoutClient.tsx` — Phase 8 post-migration

### Architectural Decisions

10 ADs in `03-arch-fe.md` (AD1-AD10) mapped 1:1 a 10 Q ratificadas en spec. Resumen:

- AD1 Hybrid Server+Client DashboardShell
- AD2 Mutex breakpoint ≥1280px no-mutex; <1280 applies
- AD3 Min content width floor 720px @≥1024
- AD4 NEW zustand store tenant-namespaced
- AD5 Z-index fluid scale 0/10/.../100
- AD6 NEW SSoT widths (drift fix)
- AD7 FAB bottom-right mobile-only collapsed-only
- AD8 **REFACTOR existing AppSidebar Sheet** (NOT new) — rewire + aria-labels
- AD9 aria-labels Spanish neutro
- AD10 Visual regression with main content masking

### Phase 10 (post v3 ratification, 2026-05-07): modal z-index alignment

Migrar 6 Shadcn primitives (`ui/dialog`, `ui/alert-dialog`, `ui/sheet`, `ui/popover`, `ui/dropdown-menu`, `ui/tooltip`) de hardcoded `z-50` a `Z_INDEX` tokens (MODAL=80, TOOLTIP=90 según fluid scale Q6).

Implementación: architect-fe decide entre:
- (a) Edit primitives in-place + arch test allowlist initial
- (b) Wrapper components en `components/ui/` que sobreescriben z-index via prop o className
- (c) Theme-injection via Tailwind config

Recommended: (a) in-place edit con jsdoc note + arch test scope ampliado a `components/ui/`. Bundle impact = 0.

## Cross-cutting decisions

| Concern | Decision |
|---|---|
| Tenant isolation | `useShellMutexStore` factory keyed by tenantId via `useMemo([tenantId])`. Cross-tab safe via localStorage namespacing `shell-mutex-${tenantId}`. |
| A11y | Spanish neutro aria-labels (`Abrir menú principal`, `Cerrar menú principal`, `Abrir asistente`). Radix Sheet focus trap reuse. axe-core scan en Playwright. |
| i18n | Voseo glosario respetado (pre-commit hook Section 7 enforces). |
| Server/Client | Hybrid pattern — Server wrapper passes children + tenantId prop to Client inner. Layout `app/(main)/[tenantId]/(dashboard)/layout.tsx` stays Server. |
| FSD-Lite boundaries | `components/shared/layout/` ↔ `features/copilot/{components,lib,store}` allowed via shared→feature documented exception. |
| Bundle budget | Informativo <3% growth (no hard gate). zustand store + 2 hooks + 1 component <2 KB gzip estimated. |

## Migration plan (10 phases)

Phase 1: Skeleton + SSoT modules (no behavioral change)
Phase 2: Migrate consumers to SSoT widths (drift fix)
Phase 3: Activate min-content-width floor
Phase 4: Activate mutex policy
Phase 5: CopilotFAB + AppSidebar mobile aria-labels
Phase 6: Z-index migration to tokens (shell scope)
Phase 7: Arch test rename + scope ampliado + 3 NEW arch tests
Phase 8: ESLint custom rules + DashboardLayoutClient deletion
Phase 9: Visual regression baselines + smoke spec
**Phase 10: Modal z-index alignment ui/* primitives** (post v3 Chris 2026-05-07)

Cada phase commit-able individually. CI green at every boundary. Detalle en `03-arch-fe.md` §Migration plan.

## Riesgos cross-cutting

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Phase 4 mutex effect infinite loop | high | zustand subscribe + idempotency check + unit test ping-pong |
| Phase 2 SSoT migration breaks 4 ui/* consumers de useCopilotOffset | medium | dialog-centered-correctly.spec.ts E2E + snapshot re-baseline |
| Phase 9 visual regression masking misaligns | medium | Q9 explicit mask only main; Chris ratifies baselines |
| Phase 10 ui/* primitives edit afecta features cross-codebase | medium | Allowlist initial → ratchet error + smoke E2E full suite |
| Tenant switch leaves stale mutex state | low | Store factory keyed by tenantId useMemo |

## Hand off

Story state `refining → refined → ready` (post `04-validators` + `05-guidelines` + `06-tickets` cierre).

Next: `/dev-team` toma T-1 ticket primero (Conv 2 autonomous build).
