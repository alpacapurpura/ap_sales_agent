# 03-arch-fe.md — Growth Studio Folder Parity (2A)

> Owner: `/architect-fe` sub-architect (Opus 4.7). Diseño técnico capa FE.
> Output → `/architect` orchestrator para consolidar en `03-arch.md` +
> `04-validators.yaml` + `05-guidelines.md` + `06-tickets.yaml`.

---
story_id: growth-studio-folder-parity
surface: FE
sub_architect: /architect-fe
arch_version: 1
last_modified: 2026-05-07T05:00Z
links:
  spec: "01-spec.md"
  checkpoint: "checkpoint.md"
  outcome: "../../outcomes/growth-copilot-layout-unification.md"
  story_2b: "../growth-studio-actions-schemas-real/checkpoint.md"
  story_1_parallel: "../app-shell-sidebar-copilot-decoupling/checkpoint.md"
  legacy_pi: "../../../archive/2026/legacy-pis/PI-9-growth-studio-architecture/PI.md"
  rules:
    - ".claude/rules/frontend-fsd.md"
    - ".claude/rules/frontend-quality.md"
    - ".claude/rules/architectural-fitness.md"
    - ".claude/rules/anti-duplication.md"
    - ".claude/rules/tdd-mandatory.md"
  arch_tests:
    - "frontend/src/__tests__/architecture/test-studio-structure-parity.test.ts"
    - "frontend/src/__tests__/architecture/test-growth-studio-copilot-offset.test.ts" # renamed to test-shell-copilot-offset by story 1
---

## Decisión arquitectónica clave

Migrar `frontend/src/features/growth-studio/` a la estructura FSD-Lite homologada con brand/offer-studio mediante **factory propia adapter mode**: mismos folders canonical (`pages/`, `actions/`, `schemas/`, `api/`, `components/`, `hooks/`, `lib/`, `types/`, `utils/` + opcional `__tests__/`, `store/`), pero contenido interno propio del dominio growth (`StageDispatcher` 5 stages × `ChannelDispatcher` N canales × 4-tier loading bajo `pages/tiers/`). Tradeoff: rechaza paridad 1:1 transplantable brand/offer (validado por architect 2026-05-01 archived PI-9 — growth invariantes diferentes: 5 stages bowtie + N canales registry-driven + tier loading). El arch fitness `test-studio-structure-parity.test.ts` se refactoriza a **modo adapter** — verifica paridad de FORMA (presencia de canonical files + `pages/sections/` + ≥1 `*-page.tsx`), no de SHAPE interno (factory dispatchers válidos como dispatcher canonical). Coordinación crítica con story 1 (paralela): el rename de `test-growth-studio-copilot-offset.test.ts` → `test-shell-copilot-offset.test.ts` con scope-keyed allowlists pertenece a story 1; story 2A escribe contra el path renamed pero NO ejecuta el rename (timing handled en orchestrator merge sequencing — ver § Open questions).

## Surface diff (FE)

### Routes — sin cambios funcionales (thin delegate per Q3 ratificada)

**Existing routes preservadas, refactoreadas a thin Server Components que delegan al StageDispatcher / ChannelDispatcher.**

| Path | Component pre-refactor | Component post-refactor | Type |
|---|---|---|---|
| `/[tenantId]/growth-studio` | redirect a `atraccion-captura` | (sin cambio — keep redirect) | Server Component |
| `/[tenantId]/growth-studio/atraccion-captura` | `<AtraccionCapturaStage />` directo | `<StageDispatcher slug="atraccion-captura" />` | Server Component thin |
| `/[tenantId]/growth-studio/nutricion-oportunidad` | `<NutricionOportunidadStage />` | `<StageDispatcher slug="nutricion-oportunidad" />` | Server Component thin |
| `/[tenantId]/growth-studio/ventas` | `<VentasStage />` | `<StageDispatcher slug="ventas" />` | Server Component thin |
| `/[tenantId]/growth-studio/adopcion` | `<AdopcionStage />` | `<StageDispatcher slug="adopcion" />` | Server Component thin |
| `/[tenantId]/growth-studio/expansion-evangelizacion` | `<ExpansionEvangelizacionStage />` | `<StageDispatcher slug="expansion-evangelizacion" />` | Server Component thin |
| `/[tenantId]/growth-studio/[stage]/[channelSlug]` | `<ChannelDashboardView channelSlug={...} />` | `<ChannelDispatcher slug={channelSlug} initialTab={...} isRouteBased />` | Server Component thin |
| `/[tenantId]/growth-studio/channel/[channelSlug]` | redirect via `getStageForChannel()` | (sin cambio — usa `lib/registries/channel-registry.ts::getStageForChannel`) | Server Component |
| `/[tenantId]/growth-studio/campanas` | (preservar tal cual — fuera de scope dispatcher) | (sin cambio) | Server Component |
| `/[tenantId]/growth-studio/layout.tsx` | client layout con providers (`GrowthStudioProvider` + `GrowthSyncProvider`) | refactored — `GrowthSyncProvider` migra a `growth-studio/store/sync-store.ts` zustand; `GrowthStudioProvider` queda en `components/metrics-dashboard/context/` SI sigue siendo per-component context (tree-local), o migra a `store/` SI cross-cutting. Decisión: validar en Fase 4. | Client Component |

> **NO se modifican routes paths** — solo el componente render delegado (1 línea cambia per route). Preserva deep-links, bookmarks, copilot navigator deep-link contract intact (`DASHBOARD_SECTIONS` constant migra a registry pero mismas keys).

### Features (FSD-Lite) — target structure

```
frontend/src/features/growth-studio/
├── actions/                          # NEW (Fase 7) — placeholder 2B
│   └── .gitkeep                       # 2B real actions: queryStageMetrics, queryChannelOverview, triggerETLRefresh, exportStageReport
├── api/                              # KEEP — sin cambios estructurales
│   ├── campaigns-api.ts               # (existing)
│   ├── channel-dashboard-api.ts       # (existing)
│   ├── connection-health-api.ts       # (existing)
│   ├── crm-actions-api.ts             # (existing)
│   ├── etl-api.ts                     # (existing)
│   ├── mail-api.ts                    # (existing)
│   ├── mappers/                       # (existing)
│   ├── metrics-api.ts                 # (existing)
│   ├── offer-association-api.ts       # (existing)
│   ├── product-mapping-api.ts         # (existing)
│   ├── stage-detail-api.ts            # MODIFIED — `__mocks__/` import path → `__tests__/__mocks__/`
│   ├── stage-overview-api.ts          # (existing)
│   ├── stage-summaries-fallback.ts    # (existing)
│   ├── summary-api.ts                 # (existing)
│   ├── sync-channel-api.ts            # (existing)
│   ├── youtube-analytics-api.ts       # (existing)
│   └── __tests__/
├── components/                       # KEEP — bowtie + dashboard pixel-intact (invariantes negocio)
│   ├── ConnectionHealthBanner.tsx
│   ├── SyncProgressDialog.tsx        # MODIFIED — useGrowthSync from `store/sync-store.ts` instead of `context/`
│   ├── campaign-panel/                # (existing)
│   ├── metrics-dashboard/             # KEEP — internals invariante negocio
│   │   ├── attraction/...             # MODIFIED — channel-chart-config import path → `lib/registries/channel-color-registry.ts`
│   │   ├── channel-widgets/...        # MODIFIED — channel-display-registry import path → `lib/registries/channel-display-registry.ts`
│   │   ├── context/                   # (existing — GrowthStudioContext stays per-component context)
│   │   ├── detail-panels/...          # MODIFIED — useGrowthSync import path → `store/sync-store.ts`
│   │   ├── hooks/                     # MODIFIED — `use-stage-summaries.ts` MOVES to `pages/tiers/tier0-summary.ts`
│   │   ├── stages/...                 # KEEP — stage components (consumidos por `pages/sections/*-page.tsx` wrappers)
│   │   └── sidebar/...                # MODIFIED — ChannelDashboardView.tsx switch → reads from `lib/registries/dashboard-registry.ts`
│   ├── strategy-canvas/               # KEEP — bowtie pixel-intact
│   └── __tests__/
├── hooks/                            # KEEP — feature-local hooks
│   ├── use-bowties-summary.ts         # MOVED to `pages/tiers/tier0-summary.ts` consumer (orig stays as data-fetch primitive)
│   ├── use-channel-dashboard.ts       # KEEP
│   ├── use-connection-health.ts       # KEEP
│   ├── use-group-detail.ts            # SOURCE for tier2 — see `pages/tiers/tier2-group-detail.ts` re-export wrapper
│   ├── use-growth-studio-url.ts       # KEEP
│   ├── use-hash-scroll.ts             # KEEP
│   ├── use-ignored-notices.ts         # KEEP
│   ├── use-initial-load.ts            # KEEP
│   ├── use-intersection-observer.ts   # KEEP
│   ├── use-mail-dashboard.ts          # KEEP
│   ├── use-meta-ads-notices.ts        # KEEP
│   ├── use-metric-catalog.ts          # KEEP
│   ├── use-metric-click-handler.ts    # KEEP
│   ├── use-stage-detail.ts            # SOURCE for tier3 — see `pages/tiers/tier3-stage.ts` re-export wrapper
│   ├── use-stage-overview.ts          # SOURCE for tier1 — see `pages/tiers/tier1-overview.ts` re-export wrapper
│   ├── use-sync-all-sources.ts        # KEEP
│   ├── use-sync-channel.ts            # KEEP
│   └── use-youtube-analytics.ts       # KEEP
├── lib/                              # KEEP + EXTEND with registries/
│   ├── channel-icons.ts               # (existing)
│   ├── channel-view-map.ts            # (existing)
│   ├── classify-channel.ts            # (existing)
│   ├── metric-labels.ts               # (existing)
│   ├── provider-to-connection-route.ts # (existing)
│   ├── registries/                    # NEW (Fase 1) — SSoT registries
│   │   ├── stage-registry.ts          # NEW — 5 stages metadata (slug, label, icon, order, mainKpiLabel)
│   │   ├── channel-registry.ts        # NEW — N channels metadata (slug, stageSlug, name, etlProvider, color)
│   │   ├── dashboard-registry.ts      # NEW — per-channel dashboard component map (lazy-loaded)
│   │   ├── channel-display-registry.ts # MOVED from config/channel-display-registry.ts
│   │   ├── channel-color-registry.ts  # MOVED from config/channel-chart-config.ts (re-export from lib/constants)
│   │   ├── dashboard-sections-registry.ts # MOVED from config/dashboard-sections.ts
│   │   └── __tests__/                  # MOVED from config/__tests__/
│   └── __tests__/                     # (existing)
├── pages/                            # NEW (Fase 2) — factory propia
│   ├── stage-slugs.ts                 # NEW — server-safe slug list + isGrowthStudioStage guard
│   ├── StageDispatcher.tsx            # NEW — client dispatcher stage → component lazy
│   ├── channel-slugs.ts               # NEW — server-safe slug list + isGrowthStudioChannel guard
│   ├── ChannelDispatcher.tsx          # NEW — client dispatcher channel → dashboard lazy (replaces ChannelDashboardView switch)
│   ├── sections/                      # NEW — per-stage page wrappers (1 per stage)
│   │   ├── atraccion-captura-page.tsx # wraps existing AtraccionCapturaStage
│   │   ├── nutricion-oportunidad-page.tsx
│   │   ├── ventas-page.tsx
│   │   ├── adopcion-page.tsx
│   │   └── expansion-evangelizacion-page.tsx
│   ├── tiers/                         # NEW (Fase 3) — 4-tier loading hooks renamed
│   │   ├── tier0-summary.ts           # MOVED from `components/metrics-dashboard/hooks/use-stage-summaries.ts` (export `useTier0Summary` aliasing `useStageSummaries`)
│   │   ├── tier1-overview.ts          # WRAPPER re-exporting `use-stage-overview.ts` as `useTier1Overview`
│   │   ├── tier2-group-detail.ts      # WRAPPER re-exporting `use-group-detail.ts` as `useTier2GroupDetail`
│   │   └── tier3-stage.ts             # WRAPPER re-exporting `use-stage-detail.ts` as `useTier3Stage`
│   └── __tests__/                     # NEW — dispatcher unit tests
├── schemas/                          # NEW (Fase 7) — placeholder 2B
│   └── .gitkeep                       # 2B real schemas: stage-filter-params, channel-config, kpi-selection, tier-loading
├── store/                            # NEW (Fase 4 per Q1 ratificada) — zustand local
│   ├── sync-store.ts                  # NEW — zustand from `context/growth-sync-context.tsx` content
│   └── index.ts                       # NEW — barrel export
├── types/                            # KEEP — sin cambios
├── utils/                            # KEEP — sin cambios
├── __tests__/                        # KEEP + EXTEND
│   ├── __mocks__/                     # NEW — moved from `growth-studio/__mocks__/`
│   │   └── metrics-mock-data.ts       # MOVED from `__mocks__/metrics-mock-data.ts`
│   ├── visual-regression-drawer-bowtie.test.tsx   # REPLACED — pattern story 1 (Playwright + masking) per Q2 ratificada
│   └── performance/                   # (existing)
├── index.tsx                         # KEEP
├── config/                           # DELETE (Fase 4)
├── context/                          # DELETE (Fase 4)
└── __mocks__/                        # DELETE (Fase 4 — content moved to __tests__/__mocks__/)
```

### Inventory diff (current vs target) — exhaustivo

#### Files: `config/` → `lib/registries/`

| Current path | Target path | Action |
|---|---|---|
| `growth-studio/config/channel-display-registry.ts` | `growth-studio/lib/registries/channel-display-registry.ts` | MOVE (atomic find-replace en 2 consumers: `ChannelRowMetrics.tsx`, `ChannelRow.tsx`) |
| `growth-studio/config/channel-chart-config.ts` | `growth-studio/lib/registries/channel-color-registry.ts` | RENAME + MOVE (1 consumer: `AttractionTrendChart.tsx`). NOTA: file solo re-exporta de `@/lib/constants/channel-colors` — preserve re-export pattern |
| `growth-studio/config/channel-stage-map.ts` | absorbed by `growth-studio/lib/registries/channel-registry.ts` | MERGE (1 consumer: `app/.../channel/[channelSlug]/page.tsx`. `getStageForChannel()` re-exported from `channel-registry.ts`) |
| `growth-studio/config/dashboard-sections.ts` | `growth-studio/lib/registries/dashboard-sections-registry.ts` | MOVE (verify consumers via grep — likely consumed by deep-link copilot navigator if exists) |
| `growth-studio/config/__tests__/channel-stage-map.test.ts` | `growth-studio/lib/registries/__tests__/channel-registry.test.ts` | MOVE + UPDATE imports (test now exercises `channel-registry.ts::getStageForChannel`) |
| `growth-studio/config/__tests__/channel-display-registry.test.ts` | `growth-studio/lib/registries/__tests__/channel-display-registry.test.ts` | MOVE (test re-imports from new path) |
| `growth-studio/config/` (directory) | DELETE | rmdir post-move |

#### Files: `context/` → `store/` + `hooks/`

| Current path | Target path | Action |
|---|---|---|
| `growth-studio/context/growth-sync-context.tsx` | `growth-studio/store/sync-store.ts` | REWRITE — context API → zustand store. API surface preserved: `useGrowthSync()` exported (now reads zustand slice). `<GrowthSyncProvider>` removed (zustand needs no provider — replace usage in `app/.../layout.tsx` con simple no-op or delete wrapper). Consumers (3 files): `components/SyncProgressDialog.tsx`, `components/metrics-dashboard/detail-panels/AttractionCaptureDetail.tsx`, `app/.../layout.tsx` |
| `growth-studio/context/` (directory) | DELETE | rmdir post-move |

#### Files: `__mocks__/` → `__tests__/__mocks__/`

| Current path | Target path | Action |
|---|---|---|
| `growth-studio/__mocks__/metrics-mock-data.ts` | `growth-studio/__tests__/__mocks__/metrics-mock-data.ts` | MOVE — update 9 dynamic import paths in `growth-studio/api/stage-detail-api.ts` (lines 630-776 per grep) from `../__mocks__/metrics-mock-data` → `../__tests__/__mocks__/metrics-mock-data` |
| `growth-studio/__mocks__/` (directory) | DELETE | rmdir post-move |

#### Files: 4-tier hook rename (Fase 3 — break-and-fix atomic per Q5 ratificada)

| Source hook | Target tier file | Action |
|---|---|---|
| `growth-studio/components/metrics-dashboard/hooks/use-stage-summaries.ts` | `growth-studio/pages/tiers/tier0-summary.ts` | MOVE — file relocates. Export rename: `useStageSummaries` → `useTier0Summary` (also export legacy alias for transition? NO — Q5 ratificada: break-and-fix atomic, no shim). 1 consumer: `app/.../growth-studio/layout.tsx:12` |
| `growth-studio/hooks/use-stage-overview.ts` | `growth-studio/pages/tiers/tier1-overview.ts` | RE-EXPORT WRAPPER (option A) OR MOVE (option B) — DECISION: WRAPPER. Reason: `use-stage-overview` is also used inside `metrics-dashboard/` components for stage-detail rendering (per grep), so wrapper minimizes blast radius. Wrapper file content: `export { useStageOverview as useTier1Overview } from "../../hooks/use-stage-overview";` |
| `growth-studio/hooks/use-group-detail.ts` | `growth-studio/pages/tiers/tier2-group-detail.ts` | RE-EXPORT WRAPPER same pattern |
| `growth-studio/hooks/use-stage-detail.ts` | `growth-studio/pages/tiers/tier3-stage.ts` | RE-EXPORT WRAPPER same pattern |

> **Tier rename rationale (deferred from spec):** the 4 tiers represent progressive loading levels per `metrics-expert` skill (tier0 = bowtie summary, tier1 = stage overview cache, tier2 = group-detail cache, tier3 = stage DB). The rename SURFACES this contract under `pages/tiers/` so adding a new channel/dashboard in 2B has obvious lookup ("which tier am I on?"). Tier0 is MOVED (not wrapper) because `use-stage-summaries.ts` is local to `metrics-dashboard/hooks/` and only consumed by `layout.tsx` — clean cut. Tiers 1-3 are WRAPPERS because their source hooks (`use-stage-overview/group-detail/stage-detail.ts`) are consumed inside `metrics-dashboard/**` internals (invariante per spec); wrapper preserves invariant + exposes tier-named entry under `pages/tiers/`. Arch fitness `test-no-hardcoded-tier-numbering.test.ts` (NEW — see § Tests) ensures no consumer outside `pages/tiers/` uses the legacy hook names directly post-refactor (forces consumers to import via `pages/tiers/tier{0,1,2,3}-*.ts`).

> **Open trade-off:** if Chris/orchestrator prefers strict atomic MOVE (no wrapper), tiers 1-3 also relocate and ALL `metrics-dashboard/**` consumer imports update in same commit. Estimated +12-18 imports to update vs current proposal +0. Wrapper proposal documented as default per Q5 spirit (break-and-fix atomic = single commit) while preserving "components/metrics-dashboard pixel-intact" invariant interpretation.

#### Files: existing Stage components → wrapped under `pages/sections/`

| Existing component | New page wrapper | Action |
|---|---|---|
| `components/metrics-dashboard/stages/AtraccionCapturaStage.tsx` | `pages/sections/atraccion-captura-page.tsx` | NEW WRAPPER — exports `AtraccionCapturaPage` that renders `<AtraccionCapturaStage />`. Stage component stays in components/ (invariante). |
| `components/metrics-dashboard/stages/NutricionOportunidadStage.tsx` | `pages/sections/nutricion-oportunidad-page.tsx` | NEW WRAPPER same pattern |
| `components/metrics-dashboard/stages/VentasStage.tsx` | `pages/sections/ventas-page.tsx` | NEW WRAPPER same pattern |
| `components/metrics-dashboard/stages/AdopcionStage.tsx` | `pages/sections/adopcion-page.tsx` | NEW WRAPPER same pattern |
| `components/metrics-dashboard/stages/ExpansionEvangelizacionStage.tsx` | `pages/sections/expansion-evangelizacion-page.tsx` | NEW WRAPPER same pattern |

#### Files: Channel dashboards → ChannelDispatcher consumes from registry

| Existing component | Action | Notes |
|---|---|---|
| `components/metrics-dashboard/sidebar/ChannelDashboardView.tsx` | DEPRECATE → routes use `pages/ChannelDispatcher.tsx` instead | Legacy switch (lines 46-60) becomes `dashboard-registry.ts::DASHBOARD_COMPONENT_MAP[slug]` — `ChannelDispatcher` reads from registry. Remove file (or keep as 1-line re-export of ChannelDispatcher if any other consumer). 1 consumer: `app/.../[stage]/[channelSlug]/page.tsx`. |
| `components/metrics-dashboard/sidebar/ig-organic/IgOrganicDashboard.tsx` | KEEP component — registered in `dashboard-registry.ts` |
| `components/metrics-dashboard/sidebar/meta-ads/MetaAdsDashboard.tsx` | idem | |
| `components/metrics-dashboard/sidebar/youtube-organic/YouTubeDashboard.tsx` | idem | |
| `components/metrics-dashboard/sidebar/mail/MailDashboard.tsx` | idem | |
| `components/metrics-dashboard/sidebar/website/WebsiteDashboard.tsx` | idem | |

#### Files: Visual regression replacement

| Current file | Action | Replacement |
|---|---|---|
| `growth-studio/__tests__/visual-regression-drawer-bowtie.test.tsx` | DELETE (per Q2 ratificada) | New file under same dir using **story 1 visual regression baseline pattern** (Playwright + masking, lift VR pattern shared cross-studio). Path TBD by story 1: likely `frontend/e2e/visual/growth-studio-bowtie.spec.ts` consuming shared `vr-helpers` from story 1. **Coordination point:** story 1 lift must complete BEFORE 2A Fase 4 deletion — see § Open questions. |

### State / data flow

- **React Query keys:** sin cambios — preservados existing (`['stage', stageId, period]`, `['channel-dashboard', channelSlug, ...]`, etc.)
- **Mutations:** sin cambios estructurales (sync mutations unchanged)
- **Auth:** sin cambios — `fetchClient` auto-injects `X-Tenant-ID`
- **Zustand stores (NEW):**
  - `growth-studio/store/sync-store.ts` — sync state global (replace `growth-sync-context.tsx`). Slice shape:
    ```typescript
    interface SyncStore {
      isSyncing: boolean;
      syncResult: SyncAllResponse | undefined;
      syncError: Error | null;
      startSync: (days?: number) => void;
      resetSync: () => void;
    }
    ```
    Internally calls `useSyncAllSources` mutation. Tenant-namespaced: NOT NEEDED — sync state is per-session (mutation lifetime), no need for tenant-keyed store. Note: zustand slice must call mutation imperatively — pattern: store exposes `startSync` that triggers mutation hook (created via `create` factory using mutation result via subscription, OR keep `useSyncAllSources` consumer + zustand only for UI state). RECOMMENDED: lightweight store for UI state only (`isSyncing` mirrored from mutation `isLoading`); mutation continues to live in React Query. Builder decides exact wiring during impl per `frontend-expert` skill.
- **Coexistence with story 1 stores:** story 1 introduces `useShellMutex` + `copilot-store`. growth-studio `sync-store.ts` is feature-local — zero overlap.

### Factory dispatchers — design contract

#### `pages/stage-slugs.ts` (server-safe)

```typescript
export const GROWTH_STUDIO_STAGE_SLUGS = [
  "atraccion-captura",
  "nutricion-oportunidad",
  "ventas",
  "adopcion",
  "expansion-evangelizacion",
] as const;

export type GrowthStudioStageSlug = typeof GROWTH_STUDIO_STAGE_SLUGS[number];

const SLUG_SET: ReadonlySet<string> = new Set(GROWTH_STUDIO_STAGE_SLUGS);

export function isGrowthStudioStage(slug: string): slug is GrowthStudioStageSlug {
  return SLUG_SET.has(slug);
}
```

> Mirrors brand/offer-studio pattern (`section-slugs.ts`). Server-safe: zero `"use client"`, zero component imports.

#### `pages/StageDispatcher.tsx` (client)

```typescript
"use client";

import dynamic from "next/dynamic";
import { SectionPageLoading } from "@/lib/studio-section-page";
import type { GrowthStudioStageSlug } from "./stage-slugs";

const STAGE_COMPONENT_MAP: Record<GrowthStudioStageSlug, ReturnType<typeof dynamic>> = {
  "atraccion-captura": dynamic(
    () => import("./sections/atraccion-captura-page").then((m) => ({ default: m.AtraccionCapturaPage })),
    { loading: () => <SectionPageLoading /> },
  ),
  // ...4 more entries (one per stage)
};

export interface StageDispatcherProps {
  slug: GrowthStudioStageSlug;
}

export function StageDispatcher({ slug }: StageDispatcherProps) {
  const Component = STAGE_COMPONENT_MAP[slug];
  return <Component />;
}
```

> **Ratchet:** map keys MUST equal `GROWTH_STUDIO_STAGE_SLUGS` exactly (TS type union enforces compile-time). Adding stage = +1 entry both files (and registry — see below).

#### `pages/channel-slugs.ts` (server-safe)

```typescript
// Mirrored from initial channel set per spec scenario 1:
// meta-ads, youtube-organic, mail, ig-organic, website
// VERIFY against current ChannelDashboardView consumers — actual slugs are:
//   ig-organic, meta-ads, yt-organic, email-nurture, website-total
// Spec wording uses friendly-names; actual code uses canonical slugs above.
export const GROWTH_STUDIO_CHANNEL_SLUGS = [
  "ig-organic",
  "meta-ads",
  "yt-organic",
  "email-nurture",
  "website-total",
] as const;

export type GrowthStudioChannelSlug = typeof GROWTH_STUDIO_CHANNEL_SLUGS[number];

const SET: ReadonlySet<string> = new Set(GROWTH_STUDIO_CHANNEL_SLUGS);
export function isGrowthStudioChannel(slug: string): slug is GrowthStudioChannelSlug {
  return SET.has(slug);
}
```

> **Mismatch flag spec ↔ code:** spec scenario 1 lists "meta-ads, youtube-organic, mail, ig-organic, website" but actual code (verified `ChannelDashboardView.tsx` lines 46-60) uses canonical slugs `ig-organic`, `meta-ads`, `yt-organic`, `email-nurture`, `website-total`. Defer to actual code (canonical slugs). Spec wording rewritten by orchestrator/PM if need to align.

#### `pages/ChannelDispatcher.tsx` (client)

```typescript
"use client";

import { DASHBOARD_COMPONENT_MAP } from "../lib/registries/dashboard-registry";
import type { GrowthStudioChannelSlug } from "./channel-slugs";
import type { MetaAdsDashboardTab } from "../types/metrics";

export interface ChannelDispatcherProps {
  slug: GrowthStudioChannelSlug;
  initialTab?: string;
  isRouteBased?: boolean;
}

export function ChannelDispatcher({ slug, initialTab, isRouteBased = true }: ChannelDispatcherProps) {
  const entry = DASHBOARD_COMPONENT_MAP[slug];
  if (!entry) {
    return <div className="...">Dashboard no disponible para este canal</div>;
  }
  const Component = entry.component;
  // each component has slightly different prop shape (e.g. MetaAdsDashboard takes typed initialTab);
  // dispatcher unifies via entry.propAdapter (registry-defined per channel)
  const props = entry.propAdapter({ initialTab, isRouteBased });
  return <Component {...props} />;
}
```

> **Critical:** `DASHBOARD_COMPONENT_MAP` lives in `lib/registries/dashboard-registry.ts` — dispatcher contains ZERO hardcoded slug→component branches. Adding channel = +1 entry registry (verified by `test-no-hardcoded-channel-slugs.test.ts` arch fitness NEW).

### Registries SSoT (NEW — Fase 1)

#### `lib/registries/stage-registry.ts`

```typescript
import type { GrowthStudioStageSlug } from "../../pages/stage-slugs";

export interface StageMetadata {
  slug: GrowthStudioStageSlug;
  label: string;
  description: string;
  order: number; // 0-4
  bowtieId: string; // matches StageId enum (legacy)
}

export const STAGE_REGISTRY: Record<GrowthStudioStageSlug, StageMetadata> = {
  "atraccion-captura": { slug: "atraccion-captura", label: "Atracción & Captura", description: "...", order: 0, bowtieId: "ATRACCION_CAPTURA" },
  "nutricion-oportunidad": { /* ... */ },
  "ventas": { /* ... */ },
  "adopcion": { /* ... */ },
  "expansion-evangelizacion": { /* ... */ },
};

export const STAGES_ORDERED: ReadonlyArray<StageMetadata> = Object.values(STAGE_REGISTRY).sort((a, b) => a.order - b.order);

export function getStageMetadata(slug: GrowthStudioStageSlug): StageMetadata {
  return STAGE_REGISTRY[slug];
}
```

#### `lib/registries/channel-registry.ts`

```typescript
import type { GrowthStudioChannelSlug } from "../../pages/channel-slugs";
import type { GrowthStudioStageSlug } from "../../pages/stage-slugs";

export interface ChannelMetadata {
  slug: GrowthStudioChannelSlug;
  name: string;
  stageSlug: GrowthStudioStageSlug;
  etlProvider: string;
  colorKey: string; // resolves via channel-color-registry
}

export const CHANNEL_REGISTRY: Record<GrowthStudioChannelSlug, ChannelMetadata> = {
  "meta-ads": { slug: "meta-ads", name: "Meta Ads", stageSlug: "atraccion-captura", etlProvider: "meta", colorKey: "meta-ads" },
  "ig-organic": { /* ... */ stageSlug: "atraccion-captura" },
  "yt-organic": { /* ... */ stageSlug: "atraccion-captura" },
  // includes ALL channels currently in CHANNEL_STAGE_MAP (channel-stage-map.ts) — meta-ads, ig-organic, yt-organic, google-organic, google-ads, facebook-organic, email-nurture, email-launch, email-sequences, meta-retargeting + website-total
};

// Replaces config/channel-stage-map.ts
export function getStageForChannel(channelSlug: string): GrowthStudioStageSlug {
  const entry = CHANNEL_REGISTRY[channelSlug as GrowthStudioChannelSlug];
  return entry?.stageSlug ?? "atraccion-captura";
}
```

#### `lib/registries/dashboard-registry.ts`

```typescript
"use client"; // dynamic imports = client

import dynamic from "next/dynamic";
import { Skeleton } from "@/components/ui/skeleton";
import type { GrowthStudioChannelSlug } from "../../pages/channel-slugs";
import type { MetaAdsDashboardTab } from "../../types/metrics";

const DashboardSkeleton = () => (
  <div className="flex flex-col gap-4 p-6">
    <Skeleton className="h-8 w-48" />
    <Skeleton className="h-64 w-full" />
  </div>
);

interface DashboardEntry {
  component: ReturnType<typeof dynamic>;
  propAdapter: (input: { initialTab?: string; isRouteBased?: boolean }) => Record<string, unknown>;
}

export const DASHBOARD_COMPONENT_MAP: Partial<Record<GrowthStudioChannelSlug, DashboardEntry>> = {
  "ig-organic": {
    component: dynamic(() => import("../../components/metrics-dashboard/sidebar/ig-organic/IgOrganicDashboard").then((m) => ({ default: m.IgOrganicDashboard })), { ssr: false, loading: DashboardSkeleton }),
    propAdapter: ({ initialTab, isRouteBased }) => ({ initialTab, isRouteBased }),
  },
  "meta-ads": {
    component: dynamic(() => import("../../components/metrics-dashboard/sidebar/meta-ads/MetaAdsDashboard").then((m) => ({ default: m.MetaAdsDashboard })), { ssr: false, loading: DashboardSkeleton }),
    propAdapter: ({ initialTab, isRouteBased }) => ({ initialTab: initialTab as MetaAdsDashboardTab, isRouteBased }),
  },
  // 3 more entries
};
```

### Anti-duplication audit (Step 0 grep — pre-architectural-claim)

```bash
# Verified absence of FE registries — net-new patterns:
grep -rn "stage-registry\|StageRegistry" frontend/src/ --include="*.ts" --include="*.tsx"
# → 0 matches (only BE has ChannelRegistry Python class — different concern)

grep -rn "channel-registry\|channelRegistry" frontend/src/ --include="*.ts" --include="*.tsx"
# → 0 matches FE-side

grep -rn "dashboard-registry\|DashboardRegistry" frontend/src/ --include="*.ts" --include="*.tsx"
# → 0 matches

grep -rn "StageDispatcher\|ChannelDispatcher" frontend/src/ --include="*.ts" --include="*.tsx"
# → 0 matches (current code uses `ChannelDashboardView` switch — to be replaced by ChannelDispatcher)

grep -rn "pages/tiers" frontend/src/
# → 0 matches (NEW directory)
```

**BE-side ChannelRegistry (`backend/src/modules/analytics/application/services/channel_registry.py:737`)** is a **different concern**: BE registry resolves channel slugs to ETL providers + connection state (used by stage_services). FE `channel-registry.ts` is UI-display concern (slug → display metadata + stage parent + dashboard component). Wire format unchanged — both sides stay independent.

**Existing growth-studio `config/` files inventory + summary:**

| File | LOC | Content summary | Migration target |
|---|---|---|---|
| `config/channel-display-registry.ts` | 136 | `CHANNEL_DISPLAY_REGISTRY` map + `getChannelConfig`, `getSummaryMetrics`, `getPrimaryMetricSpec`, `getExpandedMetrics` accessors. UI display concern. | `lib/registries/channel-display-registry.ts` (rename only — same content) |
| `config/channel-chart-config.ts` | 6 | Re-export of `CHANNEL_COLORS`, `DEFAULT_CHANNEL_COLOR`, `getChannelColor` from `@/lib/constants/channel-colors`. Trivially small. | `lib/registries/channel-color-registry.ts` (preserve re-export pattern) |
| `config/channel-stage-map.ts` | 25 | `CHANNEL_STAGE_MAP: Record<string, string>` + `getStageForChannel()`. 10 channels listed. | ABSORBED into `lib/registries/channel-registry.ts` (`getStageForChannel` re-exported for backwards compat 1 commit, then removed) |
| `config/dashboard-sections.ts` | 56 | `DASHBOARD_SECTIONS` const — deep-link DOM section IDs per channel/tab. | `lib/registries/dashboard-sections-registry.ts` (rename only) |

### Cross-cutting concerns

- **Tenant isolation:** N/A en este story — refactor estructural FE puro. NO toca queries (preservado por consumir `lib/api/` + `growth-studio/api/` existing). `fetchClient` auto-inyección `X-Tenant-ID` intacta. Story 2B introduce real actions/schemas con tenant scoping explícito.
- **A11y:** preserve existing — bowtie + dashboard internals invariante. Arch fitness `axe-core` baseline comparison pre/post (per spec § non-functional).
- **i18n:** zero new strings esperado (refactor structural). `spanish-text.md` rule check passes by absence (zero new copy).
- **Server/Client boundaries:**
  - `pages/stage-slugs.ts` + `pages/channel-slugs.ts` + `lib/registries/stage-registry.ts` + `lib/registries/channel-registry.ts` → **server-safe** (zero `"use client"`, zero component imports). Routes Server Components import these for slug validation + redirect logic.
  - `pages/StageDispatcher.tsx` + `pages/ChannelDispatcher.tsx` + `lib/registries/dashboard-registry.ts` → **client** (`"use client"`, dynamic imports of components). Mirror brand/offer pattern.
  - Routes (`app/.../growth-studio/[stage]/page.tsx`) → Server Component thin (validate slug server-side via `isGrowthStudioStage`, then `<StageDispatcher slug={...} />` rendered client-side).
- **FSD-Lite boundaries:** `growth-studio` self-contained post-refactor. Boundaries matrix unchanged. **Adversarial scenario 4 enforcement:** ESLint `boundaries/dependencies` rule already enforces no cross-feature imports — `growth-studio` cannot import from `copilot/` or other features (current state likely already compliant; verify via Step 0 grep `grep -rn "from.*features/(copilot|brand-studio|offer-studio|sales-agent)" frontend/src/features/growth-studio/`).
- **Master-data:** `useTenantLocale` consumed inside dashboards (preserve via wrappers untouched).
- **Voseo:** N/A (no new strings).

### Tests requeridos

#### Non-functional (arch fitness — RED before refactor per TDD)

1. **`frontend/src/__tests__/architecture/test-studio-structure-parity.test.ts` — EXTEND (modo adapter)**
    Refactor `STUDIO_PAGE_DIRS` constant to record-of-records:
    ```typescript
    const STUDIO_PAGE_DIRS: Record<string, { dir: string; canonical: readonly string[] }> = {
      brand: { dir: ".../brand-studio/pages", canonical: ["section-slugs.ts", "SectionDispatcher.tsx"] },
      offer: { dir: ".../offer-studio/pages", canonical: ["section-slugs.ts", "SectionDispatcher.tsx"] },
      growth: { dir: ".../growth-studio/pages", canonical: ["stage-slugs.ts", "StageDispatcher.tsx", "channel-slugs.ts", "ChannelDispatcher.tsx"] },
    };
    ```
    Update describe block to iterate `Object.entries` and check each studio's per-config canonical files. Section directory check stays uniform (all studios have `pages/sections/` ≥1 `*-page.tsx`).

2. **`frontend/src/__tests__/architecture/test-no-hardcoded-stage-list.test.ts` — NEW**
    Verifies no source file outside `lib/registries/stage-registry.ts` and `pages/stage-slugs.ts` contains hardcoded array of all 5 stage slugs. Detection regex: looks for arrays containing all 5 slugs as string literals. Adversarial scenario 4 grader.

3. **`frontend/src/__tests__/architecture/test-no-hardcoded-channel-slugs.test.ts` — NEW**
    Verifies `ChannelDispatcher.tsx` source contains zero hardcoded channel slug switches. Detection: checks file content does NOT match `/case ["'][^"']+["']\s*:/g` more than 0 times for known channel slugs. Forces consumption via `dashboard-registry.ts`.

4. **`frontend/src/__tests__/architecture/test-no-hardcoded-tier-numbering.test.ts` — NEW (optional, see § Open questions)**
    Verifies no consumer outside `pages/tiers/` directly imports `use-stage-summaries`, `use-stage-overview`, `use-group-detail`, `use-stage-detail` (must go through tier wrappers). Allowlist: `metrics-dashboard/**` because invariant. Ratchet shrinks over time.

5. **`frontend/src/__tests__/architecture/test-shell-copilot-offset.test.ts` (renamed from `test-growth-studio-copilot-offset.test.ts`)** — owned by **STORY 1**, story 2A only consumes:
    - `KNOWN_VIOLATIONS_GROWTH` allowlist must shrink to `new Set()` (empty) post-2A. 6 dashboards (5 sidebar + 1 ChannelConnectionModal) must adopt `useCopilotOffset` or `DetailPanel` wrapper.

6. **`frontend/src/__tests__/architecture/test-feature-structure.test.ts`** — verify `growth-studio` top-level folder set matches canonical 9-folder set: `actions/`, `api/`, `components/`, `hooks/`, `lib/`, `pages/`, `schemas/`, `types/`, `utils/` (+ optional `__tests__/`, `store/`).

#### Functional (Vitest unit)

1. `frontend/src/features/growth-studio/pages/__tests__/StageDispatcher.test.tsx` — renders correct lazy component per slug; throws/falls-through on unknown slug.
2. `frontend/src/features/growth-studio/pages/__tests__/ChannelDispatcher.test.tsx` — registry-driven, renders correct dashboard per slug, fallback message on unknown.
3. `frontend/src/features/growth-studio/lib/registries/__tests__/stage-registry.test.ts` — 5 entries, ordering monotonic, slugs match `GROWTH_STUDIO_STAGE_SLUGS`.
4. `frontend/src/features/growth-studio/lib/registries/__tests__/channel-registry.test.ts` — `getStageForChannel` resolves all known channels + falls back to `atraccion-captura` for unknown (replaces `config/__tests__/channel-stage-map.test.ts`).
5. `frontend/src/features/growth-studio/lib/registries/__tests__/dashboard-registry.test.ts` — every channel slug in `GROWTH_STUDIO_CHANNEL_SLUGS` has a `DASHBOARD_COMPONENT_MAP` entry.
6. `frontend/src/features/growth-studio/pages/tiers/__tests__/tier0-summary.test.ts` — `useTier0Summary` proxies `useStageSummaries` correctly (move test from existing).
7. `frontend/src/features/growth-studio/store/__tests__/sync-store.test.ts` — zustand sync-store API matches preserved `useGrowthSync` contract (consumers unaffected).

#### Visual (replace existing per Q2)

- DELETE `frontend/src/features/growth-studio/__tests__/visual-regression-drawer-bowtie.test.tsx`.
- ADD `frontend/e2e/visual/growth-studio-bowtie.spec.ts` (or wherever story 1 lifts shared VR helpers). Uses Playwright + masking pattern from story 1. **Coordination:** story 1 must ship VR shared helpers BEFORE 2A Fase 4; if order inverts, 2A keeps existing VR test until story 1 lands.

#### Coverage

- growth-studio chunk coverage MUST NOT decrease vs baseline (~25% per spec § non-functional).
- Net change: +tests for dispatchers/registries (raises numerator) − tests for deleted `config/__tests__/` (move to `registries/__tests__/`, neutral).

### Telemetría

N/A — refactor structural sin nuevos events. Existing `growth_*` events preservados via component invariants.

### Master-data

`useTenantLocale` continues to be consumed inside dashboards (`metrics-dashboard/**`) — no changes needed in 2A.

### Spanish neutro

Zero new user-facing strings. Voseo glosario check passes by absence.

## Architectural Decisions (registradas)

- **AD1 (2026-05-07) — `store/index.ts` zustand local growth-studio (per Q1 ratificada).**
  Razón: `growth-sync-context.tsx` content is sync state shared across `<SyncProgressDialog>` + `<AttractionCaptureDetail>` + `app/.../layout.tsx`. Zustand removes provider tree dependency, aligns with FSD-Lite pattern (feature-local store). Coexistence with story 1 stores (`copilot-store`, `shell-mutex-store`) confirmed — zero overlap. `tenant-namespaced: false` (sync state per-session, not tenant-keyed).

- **AD2 (2026-05-07) — Replace `__tests__/visual-regression-drawer-bowtie.test.tsx` with story 1 visual regression baseline pattern (per Q2 ratificada).**
  Razón: avoid 2 VR patterns living in repo. Lift VR pattern shared cross-studio via story 1 helpers. Sequencing: story 1 ships VR helpers → story 2A Fase 4 deletes legacy + adds new. If story 1 lands later, 2A defers VR replacement to Fase 4 only after story 1 helpers exist (track via PR dependency).

- **AD3 (2026-05-07) — Routes thin Server Component delegate to StageDispatcher / ChannelDispatcher (per Q3 ratificada).**
  Razón: matches brand/offer pattern (`app/.../[section]/page.tsx` = thin SC that mounts `<SectionDispatcher slug={...} />`). Preserves Server-side slug validation (via `isGrowthStudioStage` server-safe guard) before client component mount. Routes paths unchanged — only delegated component name swaps.

- **AD4 (2026-05-07) — Consumers `config/` migration: grep-first + plan + atomic find-replace (per Q4 ratificada + R12 anti-duplication Step 0 GATE).**
  Razón: 4 config files have 4 known consumers (per § Inventory diff). Builder MUST grep before each move, plan all import path updates, execute as single atomic commit per file (move + update consumers). Arch fitness `test-feature-structure.test.ts` enforces no `config/` folder post-Fase 4.

- **AD5 (2026-05-07) — 4-tier hooks rename `pages/tiers/{0..3}-*.ts` break-and-fix atomic (per Q5 ratificada).**
  Razón: tier0 = MOVE (use-stage-summaries → tier0-summary, single consumer in layout.tsx). Tiers 1-3 = WRAPPERS (re-export from existing hooks/) to preserve `metrics-dashboard/**` internals invariant per spec while exposing tier-named entry. Single commit per Fase 3. Arch fitness optional (#4 above) ratchets future consumers into tier wrappers.

- **AD6 (2026-05-07) — Factory propia adapter mode for `test-studio-structure-parity.test.ts`.**
  Razón: brand/offer pattern non-transplantable per legacy PI-9 architect analysis (5 stages × N channels × 4-tier loading = different invariants than per-section CRUD). Adapter mode: per-studio canonical files config in arch test allows `growth: ["stage-slugs.ts", "StageDispatcher.tsx", "channel-slugs.ts", "ChannelDispatcher.tsx"]` while brand/offer keep `["section-slugs.ts", "SectionDispatcher.tsx"]`. Section directory check (`pages/sections/` ≥1 `*-page.tsx`) uniform.

- **AD7 (2026-05-07) — Allowlist cleanup: 6 dashboards adopt `useCopilotOffset` (KNOWN_VIOLATIONS_GROWTH = empty post-2A).**
  Razón: scenario 4 ratchet shrink-only, target 0. Implementation: add `const { copilotWidth } = useCopilotOffset();` to each of 6 files; apply `style={{ right: copilotWidth }}` or `paddingRight` to fixed/portal element. **Coordination story 1:** allowlist file is `KNOWN_VIOLATIONS_GROWTH` set inside `test-shell-copilot-offset.test.ts` (renamed by story 1). 2A drains the set; story 1 owns the rename + introduces `KNOWN_VIOLATIONS_SHELL` alongside. Scenarios 4 grader cites `KNOWN_VIOLATIONS_GROWTH = new Set()`.

- **AD8 (2026-05-07) — `getStageForChannel()` re-exported from `channel-registry.ts` for 1-commit backwards compat then removed.**
  Razón: `channel-stage-map.ts` has 1 consumer (`app/.../channel/[channelSlug]/page.tsx`). Atomic move: register channel-registry.ts with re-export → update consumer import → delete channel-stage-map.ts. Or single commit if find-replace. Builder choice.

## Migration plan (8 phases per spec — fleshed out)

> Each phase = candidate ticket boundary for `/architect` orchestrator. Acceptance criteria listed are observable; tests required gate ticket close.

### Fase 1 — Registries SSoT (`lib/registries/`)

**Files created:**
- `lib/registries/stage-registry.ts` (NEW)
- `lib/registries/channel-registry.ts` (NEW — absorbs `channel-stage-map.ts` semantics)
- `lib/registries/dashboard-registry.ts` (NEW — uses dynamic imports of dashboard components)

**Files moved (no content change beyond path):**
- `config/channel-display-registry.ts` → `lib/registries/channel-display-registry.ts`
- `config/channel-chart-config.ts` → `lib/registries/channel-color-registry.ts` (rename)
- `config/dashboard-sections.ts` → `lib/registries/dashboard-sections-registry.ts`
- `config/__tests__/*.test.ts` → `lib/registries/__tests__/*.test.ts` (update imports)

**Acceptance criteria:**
- All 6 registries files exist under `lib/registries/`
- Tests for registries pass (5 unit tests per § Tests > Functional)
- Consumers of moved files (4 known per grep) updated atomically OR `config/` re-exports for transition (chosen: atomic per AD4)

**Tests required (RED before, GREEN after):**
- `lib/registries/__tests__/stage-registry.test.ts`
- `lib/registries/__tests__/channel-registry.test.ts`
- `lib/registries/__tests__/dashboard-registry.test.ts`

**Commit boundary:** single commit `feat(growth-studio): seed lib/registries SSoT (Fase 1)`.

### Fase 2 — Factory dispatchers (`pages/`)

**Files created:**
- `pages/stage-slugs.ts` (server-safe)
- `pages/StageDispatcher.tsx` (client)
- `pages/channel-slugs.ts` (server-safe)
- `pages/ChannelDispatcher.tsx` (client, consumes `dashboard-registry.ts`)
- `pages/sections/{atraccion-captura,nutricion-oportunidad,ventas,adopcion,expansion-evangelizacion}-page.tsx` (5 wrappers)
- `pages/__tests__/{StageDispatcher,ChannelDispatcher}.test.tsx`

**Routes updated (5 stage routes + 1 channel route):**
- `app/.../growth-studio/atraccion-captura/page.tsx` → import `StageDispatcher`, render `<StageDispatcher slug="atraccion-captura" />`
- ... (4 more stage routes same pattern)
- `app/.../growth-studio/[stage]/[channelSlug]/page.tsx` → import `ChannelDispatcher`, render `<ChannelDispatcher slug={channelSlug} initialTab={...} />` (with server-side `isGrowthStudioChannel` guard)
- `app/.../growth-studio/channel/[channelSlug]/page.tsx` → update import `getStageForChannel` from new path

**Components deprecated:**
- `components/metrics-dashboard/sidebar/ChannelDashboardView.tsx` → replaced by `ChannelDispatcher`. Either delete (preferred, 1 consumer) or make 1-line re-export.

**Acceptance criteria:**
- `StageDispatcher` + `ChannelDispatcher` exist + tested
- All 5 stage routes + 1 channel route updated to thin delegate
- Smoke E2E `growth-studio-bowtie.spec.ts` passes (5 stages render OK)

**Tests required:**
- `pages/__tests__/StageDispatcher.test.tsx`
- `pages/__tests__/ChannelDispatcher.test.tsx`

**Commit boundary:** single commit `feat(growth-studio): seed pages/ factory dispatchers (Fase 2)`.

### Fase 3 — 4-tier rename (`pages/tiers/`)

**Files created:**
- `pages/tiers/tier0-summary.ts` (MOVED from `components/metrics-dashboard/hooks/use-stage-summaries.ts`; export `useTier0Summary`)
- `pages/tiers/tier1-overview.ts` (WRAPPER re-export `useStageOverview as useTier1Overview` from `hooks/use-stage-overview.ts`)
- `pages/tiers/tier2-group-detail.ts` (WRAPPER re-export `useGroupDetail as useTier2GroupDetail` from `hooks/use-group-detail.ts`)
- `pages/tiers/tier3-stage.ts` (WRAPPER re-export `useStageDetail as useTier3Stage` from `hooks/use-stage-detail.ts`)

**Consumer updates:**
- `app/.../growth-studio/layout.tsx:12` — import path `useStageSummaries` → `useTier0Summary` from `pages/tiers/tier0-summary`

**Acceptance criteria:**
- Tier files exist under `pages/tiers/`
- Layout consumer updated
- Optional `test-no-hardcoded-tier-numbering.test.ts` (NEW arch fitness #4) green
- Bowtie + dashboard render unchanged (visual regression)

**Tests required:**
- `pages/tiers/__tests__/tier0-summary.test.ts` (move from existing)

**Commit boundary:** `refactor(growth-studio): rename 4-tier loading hooks under pages/tiers/ (Fase 3)`.

### Fase 4 — Legacy purge (`config/` + `context/` + `__mocks__/`)

**Files deleted:**
- `growth-studio/config/` (4 files + `__tests__/`)
- `growth-studio/context/` (1 file `growth-sync-context.tsx`)
- `growth-studio/__mocks__/` (1 file `metrics-mock-data.ts`)

**Files moved:**
- `__mocks__/metrics-mock-data.ts` → `__tests__/__mocks__/metrics-mock-data.ts`
- `context/growth-sync-context.tsx` → REWRITTEN to `store/sync-store.ts` (zustand)

**Consumer updates:**
- `api/stage-detail-api.ts` — 9 dynamic import paths updated `../__mocks__/metrics-mock-data` → `../__tests__/__mocks__/metrics-mock-data`
- `components/SyncProgressDialog.tsx` — `useGrowthSync` import path → `store/sync-store`
- `components/metrics-dashboard/detail-panels/AttractionCaptureDetail.tsx` — same
- `app/.../growth-studio/layout.tsx` — remove `<GrowthSyncProvider>` wrapper (zustand stateful store needs no provider)

**Visual regression replacement (per Q2 — coordination story 1):**
- DELETE `__tests__/visual-regression-drawer-bowtie.test.tsx`
- ADD `frontend/e2e/visual/growth-studio-bowtie.spec.ts` (depends on story 1 VR helpers — gate)

**Acceptance criteria:**
- `test ! -d frontend/src/features/growth-studio/{config,context,__mocks__}` exits 0
- All 13+ consumer imports updated (4 config + 3 sync + 9 mocks)
- Smoke E2E + new VR spec pass
- `store/sync-store.ts` test green; consumers function unchanged

**Tests required:**
- `store/__tests__/sync-store.test.ts`
- New VR spec (Playwright + masking)

**Commit boundary:** `refactor(growth-studio): purge legacy config/context/__mocks__ folders (Fase 4)`.

### Fase 5 — Allowlist cleanup (6 dashboards adopt `useCopilotOffset`)

**Files modified (6):**
- `components/metrics-dashboard/sidebar/youtube-organic/YouTubeDashboard.tsx`
- `components/metrics-dashboard/sidebar/mail/MailDashboard.tsx`
- `components/metrics-dashboard/sidebar/meta-ads/MetaAdsDashboard.tsx`
- `components/metrics-dashboard/sidebar/ig-organic/IgOrganicDashboard.tsx`
- `components/metrics-dashboard/sidebar/website/WebsiteDashboard.tsx`
- `components/metrics-dashboard/channel-widgets/ChannelConnectionModal.tsx`

**Pattern per file:**
```typescript
import { useCopilotOffset } from "@/hooks/use-copilot-offset";
// ...
const { copilotWidth } = useCopilotOffset();
// In fixed/portal element:
<div style={{ right: copilotWidth, /* OR */ paddingRight: copilotWidth }} className="fixed ...">
```

OR wrap content with `<DetailPanel>` (which already uses the hook).

**Allowlist update:**
- File `frontend/src/__tests__/architecture/test-shell-copilot-offset.test.ts` (renamed by story 1)
- Set `KNOWN_VIOLATIONS_GROWTH = new Set()` (empty)

**Coordination story 1:** if story 1 hasn't shipped rename when 2A Fase 5 begins, work against current path `test-growth-studio-copilot-offset.test.ts` and update `KNOWN_VIOLATIONS` set. Story 1 merge subsequently renames file + splits sets — both keep allowlist EMPTY.

**Acceptance criteria:**
- `KNOWN_VIOLATIONS_GROWTH = new Set()`
- Arch test green (no stale entries, no new violations)
- Visual regression: copilot offset visible on each dashboard when copilot open (e2e smoke check optional)

**Commit boundary:** `refactor(growth-studio): adopt useCopilotOffset in 6 dashboards (Fase 5)`.

### Fase 6 — Arch fitness extension (modo adapter)

**File modified:**
- `frontend/src/__tests__/architecture/test-studio-structure-parity.test.ts` — refactor `STUDIO_PAGE_DIRS` per § Tests > Non-functional #1

**Files created (3 new arch fitness):**
- `test-no-hardcoded-stage-list.test.ts` (NEW — scenario 4 grader)
- `test-no-hardcoded-channel-slugs.test.ts` (NEW — scenario 2 grader)
- `test-no-hardcoded-tier-numbering.test.ts` (NEW — optional, see Open Q)

**Acceptance criteria:**
- Extended `test-studio-structure-parity` includes `growth` mode + passes
- 3 new arch tests pass

**Commit boundary:** `test(growth-studio): extend studio-structure-parity to growth + add 3 arch tests (Fase 6)`.

### Fase 7 — Placeholders 2B

**Files created:**
- `actions/.gitkeep` (placeholder for 2B real actions)
- `schemas/.gitkeep` (placeholder for 2B real schemas)

**Acceptance criteria:**
- `ls frontend/src/features/growth-studio/{actions,schemas}` shows directories with `.gitkeep`
- `test-feature-structure.test.ts` passes (folders match canonical 9-folder set)

**Commit boundary:** `chore(growth-studio): seed actions/ + schemas/ placeholders for 2B (Fase 7)`.

### Fase 8 — Verify (gate)

**Commands run (CI parity):**
```bash
cd frontend
npx tsc --noEmit              # 0 errors
npx eslint src/ --cache       # 0 errors
npx vitest run --coverage     # passes, coverage ≥ baseline (~25%)
npx vitest run src/__tests__/architecture/  # all arch tests green incl. growth
E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke  # 5 stages render
# visual regression spec
```

**Acceptance criteria:**
- All gates green
- Bundle analyzer: growth-studio chunk size ≤ +5% baseline (per spec § non-functional)
- Build time growth-studio chunk ≤ +10% baseline

**Commit boundary:** `chore(growth-studio): verify ready package (Fase 8)` (only if any cleanup needed; usually no commit).

## Cross-cutting concerns recap

- **Tenant isolation:** N/A
- **Idempotency:** N/A (refactor structural)
- **Rate limiting:** N/A
- **Caching:** preserved (React Query keys unchanged)
- **Backwards compat:** routes paths unchanged → bookmarks/deep-links intact. Copilot navigator deep-link contract via `dashboard-sections-registry.ts` content unchanged (rename only).

## Riesgos y mitigaciones

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Story 1 VR helpers no shipped before 2A Fase 4 | medium | Defer Fase 4 VR replacement; keep legacy VR test until story 1 lands. Track via PR dep. |
| `test-shell-copilot-offset.test.ts` rename collision con 2A Fase 5 | low | If 2A Fase 5 runs first, edit file at current path `test-growth-studio-copilot-offset.test.ts`. Story 1 rename merges allowlist split atomically. Conflict highly unlikely (different changes). |
| `growth-sync-context` zustand migration breaks 3 consumers | low | Builder writes test for `useGrowthSync` API contract first; consumers pass thru without source change. |
| `ChannelDashboardView` deletion breaks downstream consumer | low | Grep verified 1 consumer (`[stage]/[channelSlug]/page.tsx`); also check `Storybook` stories or test fixtures. |
| Dynamic import paths in `stage-detail-api.ts` (9 sites) miss update | low | Atomic find-replace `../__mocks__/metrics-mock-data` → `../__tests__/__mocks__/metrics-mock-data`. Vitest fails immediately if any miss. |
| Build size +5% regression | low | Refactor moves files but doesn't add LOC; tier wrappers are 1-line re-exports. Bundle analyzer pre/post. |
| Coverage drop | low | Tests move with files, plus 7 new functional tests added. |
| Spec scenario 1 channel slug mismatch (spec lists "youtube-organic, mail, ig-organic, website" — code uses `yt-organic, email-nurture, ig-organic, website-total`) | medium | Spec wording is friendly-name; code is canonical. Builder uses canonical (verified `ChannelDashboardView.tsx:46-60`). Spec rewrite by orchestrator/PM if needed for alignment. |

## Open questions for orchestrator

1. **Coordination timing rename `test-growth-studio-copilot-offset.test.ts` → `test-shell-copilot-offset.test.ts` (story 1 owns).**
    If story 1 PR merges BEFORE 2A Fase 5: 2A edits renamed file, sets `KNOWN_VIOLATIONS_GROWTH = new Set()`.
    If 2A Fase 5 merges BEFORE story 1: 2A edits current path, sets `KNOWN_VIOLATIONS = new Set()` (single set). Story 1 rename later splits empty set into `KNOWN_VIOLATIONS_SHELL` + (preserved empty) `KNOWN_VIOLATIONS_GROWTH`.
    **Recommend:** orchestrator calls story 1 to ship rename FIRST (lower coupling); 2A can proceed in parallel from Fase 1-4 and Fase 5 waits on rename.

2. **VR pattern lift coordination (Q2 ratificada).**
    Q2 says "replace with story 1 pattern". Need confirmation: does story 1 actually lift VR helpers shared, or just establish baseline screenshots? If latter, 2A may need own VR spec mirroring story 1 scaffolding.
    **Action:** orchestrator confirms with story 1 architect output before validators.yaml.

3. **Optional arch test `test-no-hardcoded-tier-numbering.test.ts` — scope decision.**
    AD5 chose wrappers for tiers 1-3 (preserves invariant). If orchestrator prefers atomic MOVE (no wrappers), tier 1-3 source hooks relocate + ALL `metrics-dashboard/**` consumer imports update. Estimated +12-18 imports vs current proposal +0. Wrapper proposal is default; flag for ratification or revision.

4. **Channel slug list mismatch spec ↔ code.**
    Spec scenario 1 phrasing ("meta-ads, youtube-organic, mail, ig-organic, website") doesn't match canonical slugs (`yt-organic`, `email-nurture`, `website-total`). Architect proposes using canonical slugs (verified in `ChannelDashboardView.tsx`). Spec rewrite by PM if needed.

5. **`GrowthStudioContext` (per-component context inside `metrics-dashboard/context/`) — migrate to store?**
    Per-component context (in `components/metrics-dashboard/context/GrowthStudioContext.tsx`, used by `layout.tsx` and `<GrowthStudioShell>`). Stays as React Context (UI tree-local) per default; OR migrate to zustand if story 1 mutex reveals cross-cutting need. **Recommend:** keep as Context in 2A; revisit during Fase 8 verify if test breakage signals need.

6. **Dashboard-sections-registry consumers (deep-link).**
    `DASHBOARD_SECTIONS` const consumed where? Grep returned only definition (and copilot navigator may use string literals via `UIAction.section_id`). Verify no ETL/automation tooling depends on it. Builder Step 0 grep confirms scope.

## Próximo paso

`done -> docs/product/stories/growth-studio-folder-parity/03-arch-fe.md` (return to `/architect` orchestrator).

Orchestrator next:
- Reúne con (no other surfaces) → 03-arch.md = this file (FE-only story).
- Produce `04-validators.yaml` con commands ejecutables: tsc, eslint, vitest (incl. arch tests), playwright smoke + VR (if story 1 helpers ready).
- Produce `05-guidelines.md` con patterns required/forbidden + files in scope (this 03-arch-fe.md = primary input).
- Produce `06-tickets.yaml` con 7-8 tickets (one per Fase) + ordering + acceptance criteria + owner_eligibility (qwen/Sonnet OK — non-agentic FE refactor per R23).
