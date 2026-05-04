# UI Spec: Campaign Pendientes Hub + Inline Offer Reassignment

## Design Intent
- **Concept:** Split View "Resolve & Go" — a dedicated pending-actions view where campaigns needing decisions are listed left, with full context on the right, plus inline offer reassignment directly from the campaigns table.
- **Problem solved:** Without correct campaign↔offer associations, the user can't know how much they spend per product or what results each offer generates. Today there's no central place to see ALL pending actions, and changing an existing association requires opening the full assignment drawer.
- **Target emotion:** Control total — "I know exactly what's missing and I can fix everything in 2 minutes"
- **Design approach:** Split View for pending resolution (list + context panel) combined with inline Popover for atomic offer changes in the campaigns table. Two complementary interaction points, each optimized for its use case.

## Persona
- **Primary user:** Business owner (creator/infoproductor) — makes strategic decisions, assigns offers when data looks inconsistent or after creating campaigns in Meta
- **Context:** Arrives reactively (notices inconsistent data, sees a warning badge) or proactively (just created campaigns in Meta). May delegate operational assignment to marketing manager.
- **Technical level:** Medium-high — understands campaigns, offers, funnels, but wants simplicity
- **Secondary user:** Marketing manager/assistant — handles bulk operational assignments

## Design Principles

1. **"Edit where the data lives"** — Offer reassignment for existing campaigns happens inline via Popover in the campaigns table, not by navigating elsewhere.
2. **"Inbox Zero motivation"** — The pending counter motivates completion; items disappear when resolved, giving clear progress feedback.
3. **"Progressive disclosure"** — The pendientes view shows only what needs action, grouped by severity. The campaigns table shows the full picture with inline editing capability.

## Layout Mockup

### Desktop (≥1024px) — Pendientes View (Split)

```
┌──────────────────────────────────────────────────────────────────────┐
│  ← Meta Ads          Pendientes (4)                    [▼ 30 días]  │
├───────────────────┬──────────────────────────────────────────────────┤
│  PENDIENTES       │                                                  │
│  ┌─ Filter pills ─┐│  Campaña: MasterClass Febrero — Conversiones    │
│  │Sin offer│Sin UTM││  ● Activa · Ventas · 2 ad sets · 4 anuncios   │
│  └─────────────────┘│                                                │
│                     │  ┌─ ASIGNAR OFFER ─────────────────────────┐   │
│  ● MasterClass  ◄──││  │ [▼ Elegir offer...                    ]│   │
│    Ventas·S/890     ││  │   🧲 MasterClass Pro · Ventas          │   │
│    ROAS 4.1x        ││  │   📚 Programa Avanzado · Leads         │   │
│    [Sin offer]      ││  │   ⭐ Consultoría 1:1 · Mensajes        │   │
│                     ││  │   🎯 Marcar como Branding              │   │
│  ● Retargeting      ││  └────────────────────────────────────────┘   │
│    Ventas·S/320     ││                                                │
│    ROAS 1.5x        ││  ┌──────────┐┌──────────┐┌──────────┐┌─────┐ │
│    [Sin offer]      ││  │Inversión ││Resultados││   CPA    ││ROAS │ │
│                     ││  │ S/ 890   ││   42     ││ S/21.19  ││4.1x │ │
│  ○ Webinar Marzo    ││  └──────────┘└──────────┘└──────────┘└─────┘ │
│    Pausada·S/150    ││                                                │
│    [Sin offer]      ││  📊 [Spend vs Results Trend Chart]            │
│                     ││                                                │
│  ● Brand Awareness  ││                                                │
│    Alcance·S/280    ││                                                │
│    [Sin UTM]        ││                                                │
├───────────────────┴──────────────────────────────────────────────────┤
└──────────────────────────────────────────────────────────────────────┘
```

### Desktop — Inline Popover (in CampaignsTab)

```
┌──────────────────────────────────────────────────────────────┐
│  Campaña                        │ Inversión │ Resultado │ ...│
├──────────────────────────────────────────────────────────────┤
│  ● Programa Avanzado — Leads    │  S/ 650   │    38     │    │
│    Leads · 📚 Programa Avanzado │           │           │    │
│                ┌──────────────────────────┐              │    │
│                │ Offer actual:            │              │    │
│                │ 📚 Programa Avanzado     │              │    │
│                │ ─────────────────────    │              │    │
│                │ Cambiar a:              │              │    │
│                │ [▼ Elegir offer...     ] │              │    │
│                │  🧲 MasterClass Pro     │              │    │
│                │  ⭐ Consultoría 1:1     │              │    │
│                │  🎯 Branding            │              │    │
│                │ ─────────────────────    │              │    │
│                │ "Desasignar"            │              │    │
│                └──────────────────────────┘              │    │
├──────────────────────────────────────────────────────────────┤
│  ● Retargeting Carrito          │  S/ 320   │    18     │    │
└──────────────────────────────────────────────────────────────┘
```

### Mobile (<768px) — Pendientes View

```
┌───────────────────────────┐
│  ← Meta Ads   Pendientes  │
├───────────────────────────┤
│  [Sin offer] [Sin UTM]    │
├───────────────────────────┤
│  ● MasterClass Febrero    │
│    Ventas·S/890·ROAS 4.1x │
│    [Sin offer]             │
│    [▼ Asignar offer...   ]│
├───────────────────────────┤
│  ● Retargeting Carrito    │
│    Ventas·S/320·ROAS 1.5x │
│    [Sin offer]             │
│    [▼ Asignar offer...   ]│
├───────────────────────────┤
│  ...                       │
└───────────────────────────┘
```

## Component Tree

### Part 1: Pendientes View (new page)

```
PendientesPage (Server — src/app/(main)/[tenantId]/(dashboard)/growth-studio/atraccion-captura/[channelSlug]/pendientes/page.tsx)
└── PendientesView (Client — src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/pendientes/PendientesView.tsx)
    ├── PendientesHeader (Client)
    │   ├── Button (Shadcn) ← "← Meta Ads" back nav
    │   ├── Badge (Shadcn) ← pending counter
    │   └── MetaAdsPeriodSelector (existing)
    ├── PendientesFilterPills (Client)
    │   └── Button[] (Shadcn) ← filter toggles
    ├── PendientesList (Client) ← left panel
    │   └── PendienteItem[] (Client)
    │       ├── StatusDot (internal)
    │       ├── Badge (Shadcn) ← "Sin offer" / "Sin UTM"
    │       └── metrics summary text
    └── PendienteDetailPanel (Client) ← right panel
        ├── Campaign header info
        ├── OfferAssignmentDropdown (Client) ← NEW
        │   └── Select (Shadcn)
        ├── CampaignMetricsGrid (Client)
        │   └── Card[] (Shadcn) ← Inversión, Resultados, CPA, ROAS
        └── CampaignTrendChart (Client)
            └── ChartSection (existing shared)
```

### Part 2: Inline Offer Popover (in CampaignsTab)

```
CampaignsTab (Client — existing)
└── CampaignRow (Client — existing, modified)
    └── OfferBadge (Client) ← existing badge, now wrapped in Popover
        └── Popover (Shadcn)
            ├── PopoverTrigger ← the badge button (existing)
            └── PopoverContent
                └── OfferReassignPopover (Client) ← NEW
                    ├── current offer display
                    ├── Select (Shadcn) ← offer dropdown
                    └── Button (Shadcn) ← "Desasignar"
```

### Part 3: Pendientes Tab Badge (in MetaAdsDashboard)

```
MetaAdsDashboard (Client — existing, modified)
└── TabsList (Shadcn)
    ├── TabsTrigger "resumen"
    ├── TabsTrigger "campanas" + pending badge
    ├── TabsTrigger "pendientes" ← NEW TAB
    ├── TabsTrigger "creativos"
    ├── TabsTrigger "audiencia"
    └── TabsTrigger "costos"
```

## Data Flow

### Server-Side (Page)

```
pendientes/page.tsx (RSC)
  → Receives params: { tenantId, channelSlug }
  → Renders <PendientesView channelSlug={channelSlug} />
```

### Client-Side (Interactive Components)

```
PendientesView ("use client")
  → useCampaignPerformance(period) — fetches all campaigns with metrics
  → useAssociations() — fetches existing campaign↔offer associations
  → useOffersForAssignment() — fetches available offers for dropdown
  → useMetaHealthCheck() — fetches health issues (UTMs, etc.)
  → Derives pendingItems: campaigns without offer + campaigns with issues
  → selectedCampaign state: which campaign is shown in detail panel
  → On offer select → useCreateAssociation().mutateAsync() → item vanishes from list

OfferReassignPopover ("use client")
  → Receives: campaign, currentAssociation, availableOffers
  → On offer change → useCreateAssociation().mutateAsync() → badge updates
  → On desasignar → useDeleteAssociation().mutateAsync() → badge becomes "Sin offer"
  → Popover closes on successful mutation
```

## API Integration

| Component | Hook | API Call | Trigger |
|-----------|------|----------|---------|
| PendientesView | `useCampaignPerformance()` | GET `/api/v1/advertising/campaigns/performance` | Mount |
| PendientesView | `useAssociations()` | GET `/api/v1/advertising/associations` | Mount |
| PendientesView | `useOffersForAssignment()` | GET `/api/v1/advertising/offers` | Mount |
| PendientesView | `useMetaHealthCheck()` | GET `/api/v1/advertising/health-check?provider=meta` | Mount |
| OfferAssignmentDropdown | `useCreateAssociation()` | POST `/api/v1/advertising/associations` | Select change |
| OfferReassignPopover | `useCreateAssociation()` | POST `/api/v1/advertising/associations` | Select change |
| OfferReassignPopover | `useDeleteAssociation()` | DELETE `/api/v1/advertising/associations/{id}` | "Desasignar" click |

All hooks already exist in `offer-association-api.ts` and `campaigns-api.ts` — no new API endpoints needed.

## Interaction Patterns

| Trigger | Animation | Duration | Component | Notes |
|---------|-----------|----------|-----------|-------|
| Select campaign in list | Left border highlight (blue) + right panel content swap | 200ms fade | PendientesList | border-l-2 border-blue-500 + bg-blue-500/10 |
| Assign offer in pendientes | Item fades out + counter decrements | 300ms fade-out | PendienteItem | Optimistic removal like current drawer |
| Click offer badge in table | Popover opens below badge | 150ms (Radix default) | OfferReassignPopover | data-[state=open]:animate-in |
| Change offer in popover | Badge updates color/text + popover closes | Instant + 150ms close | OfferBadge | Invalidates associations query |
| Desasignar in popover | Badge changes to amber "Sin offer" + popover closes | Instant + 150ms close | OfferBadge | Invalidates associations + health-check queries |
| Filter pills toggle | List filters with fade | 200ms | PendientesFilterPills | Items fade in/out based on filter |
| Navigate to pendientes tab | Tab content swap | Instant (Radix Tabs) | MetaAdsDashboard | Standard tab behavior |
| All items resolved | Empty state with check icon | 300ms fade-in | PendientesList | "¡Todo resuelto!" message |
| Auto-detectar offers | Spinner on button → suggestions pre-fill selects | 500ms+ (API) | PendientesHeader | Reuses existing autoDetect mutation |

## Shadcn Components Used

| Component | Import | Usage |
|-----------|--------|-------|
| Tabs, TabsList, TabsTrigger, TabsContent | `@/components/ui/tabs` | New "pendientes" tab in MetaAdsDashboard |
| Select, SelectTrigger, SelectValue, SelectContent, SelectItem | `@/components/ui/select` | Offer dropdown in both pendientes view and popover |
| Popover, PopoverTrigger, PopoverContent | `@/components/ui/popover` | Inline offer reassignment in CampaignsTab |
| Badge | `@/components/ui/badge` | Pending counter, filter pills, offer type labels |
| Button | `@/components/ui/button` | Back nav, auto-detect, filter pills, desasignar |
| Card, CardContent | `@/components/ui/card` | Metrics grid in detail panel |
| Separator | `@/components/ui/separator` | Divider in popover between current offer and dropdown |
| Tooltip, TooltipTrigger, TooltipContent | `@/components/ui/tooltip` | Metric labels in detail panel |
| Skeleton | `@/components/ui/skeleton` | Loading state for detail panel |

## FSD File Structure

```
frontend/src/
├── app/(main)/[tenantId]/(dashboard)/growth-studio/atraccion-captura/[channelSlug]/
│   └── pendientes/
│       └── page.tsx                           (Server Component — thin, delegates)
│
├── features/growth-studio/
│   └── components/metrics-dashboard/sidebar/meta-ads/
│       ├── pendientes/                        (NEW directory)
│       │   ├── PendientesView.tsx             (Client — main split view container)
│       │   ├── PendientesList.tsx             (Client — left panel list)
│       │   ├── PendienteItem.tsx              (Client — single pending row)
│       │   ├── PendienteDetailPanel.tsx       (Client — right panel with metrics + assignment)
│       │   ├── PendientesFilterPills.tsx      (Client — filter toggles)
│       │   └── OfferAssignmentDropdown.tsx    (Client — Select with auto-save)
│       ├── OfferReassignPopover.tsx            (NEW — popover for inline offer change)
│       ├── MetaAdsDashboard.tsx                (MODIFIED — add pendientes tab)
│       └── tabs/
│           ├── CampaignsTab.tsx                (MODIFIED — use OfferReassignPopover)
│           └── PendientesTab.tsx               (NEW — thin wrapper for PendientesView)
│
├── types/metrics.ts                            (MODIFIED — add 'pendientes' to MetaAdsDashboardTab)
└── types/offer-association.ts                  (EXISTING — no changes)
```

## Responsive Behavior

| Breakpoint | Pendientes View | Inline Popover |
|------------|----------------|----------------|
| Desktop (≥1024px) | Split view: 380px list + fluid detail panel | Popover opens below badge, 280px wide |
| Tablet (768-1023px) | Split view: 300px list + fluid detail panel | Same as desktop |
| Mobile (<768px) | Single column: list with inline dropdowns per item (no split). Each pending item shows its own Select below the campaign info. No detail panel. | Popover opens as Sheet (bottom drawer) via Shadcn responsive pattern |

## Loading, Error, & Empty States

| State | Component | Behavior |
|-------|-----------|----------|
| Loading | PendientesList | 4 Skeleton rows (h-16 w-full) in left panel |
| Loading | PendienteDetailPanel | Skeleton grid (4 cards) + skeleton chart area |
| Empty (all resolved) | PendientesList | CheckCircle2 icon (emerald) + "¡Todo resuelto! No hay campañas pendientes." + Button "Volver a Campañas" |
| Empty (no campaigns) | PendientesList | "No hay campañas sincronizadas. Conecta Meta Ads y sincroniza." |
| Error | PendientesView | Card with AlertTriangle + "Error al cargar pendientes. Intenta de nuevo." + Button "Reintentar" |
| Saving | OfferAssignmentDropdown | Select disabled + Loader2 spinner beside it |
| Saving | OfferReassignPopover | Select disabled + Loader2 spinner + "Guardando..." text |

## Visual Design

### Spacing Scale
| Element | Spacing |
|---------|---------|
| Split view gap | gap-0 (border divider) |
| Section gap (detail panel) | gap-4 / 16px (space-y-4) |
| Card padding (metrics) | p-3 / 12px |
| List item padding | px-4 py-3 |
| Popover padding | p-4 / 16px |
| Filter pills gap | gap-1.5 / 6px |

### Typography
| Element | Class | Weight |
|---------|-------|--------|
| Page header | text-sm font-semibold | Semi-bold |
| Campaign name (list) | text-sm | font-medium |
| Campaign name (detail) | text-lg | font-semibold |
| Metrics value | text-lg tabular-nums | font-bold |
| Metrics label | text-[10px] uppercase tracking-wider | text-zinc-500 |
| Badge text | text-[10px] | font-medium |
| Popover "Offer actual" label | text-xs | font-medium text-muted-foreground |
| Dropdown items | text-xs | font-normal |

### Color Distribution (60/30/10)
| Role | Token | Usage |
|------|-------|-------|
| 60% Base | `bg-background` / `bg-zinc-900/30` | Page background, panels |
| 30% Supporting | `border-zinc-800` / `bg-zinc-900/50` | List headers, metric cards, dividers |
| 10% Accent | `amber-500` / `blue-500` / `emerald-500` | Pending badges, selected state, success |

### Accent Color Semantics
| Color | Meaning |
|-------|---------|
| `amber-500/X` | Needs attention (sin offer, sin UTM) — border, bg, text on pending items |
| `blue-500/X` | Selected / associated — left border on selected item, offer badge |
| `emerald-500/X` | Good / resolved — status dot, health badges, resolved checkmarks |
| `red-500/X` | Critical — error states, critical health issues |
| `zinc-600/X` | Inactive / muted — paused campaigns, resolved section |

### Copywriting Contract
| Element | Text | Tone |
|---------|------|------|
| Tab label | "Pendientes" | Direct |
| Page header | "Pendientes" + counter badge | Direct |
| Pending badge (sin offer) | "Sin offer" | Urgente but not alarming |
| Pending badge (sin UTM) | "Sin UTM" | Informative |
| Empty state heading | "¡Todo resuelto!" | Celebratory |
| Empty state body | "No hay campañas pendientes de configuración." | Reassuring |
| Empty state CTA | "Volver a Campañas" | Action-oriented |
| Popover current offer label | "Offer actual:" | Informative |
| Popover change label | "Cambiar a:" | Action-oriented |
| Popover desasignar button | "Desasignar" | Direct, subtle (variant ghost/outline) |
| Filter: sin offer | "Sin offer (3)" | Direct + count |
| Filter: sin UTM | "Sin UTM (1)" | Direct + count |
| Filter: all | "Todos" | Neutral |

## Navigation Integration

### How to reach Pendientes View

1. **Tab in MetaAdsDashboard:** New "Pendientes" tab with counter badge (amber dot + number). Visible alongside Resumen, Campañas, Creativos, Audiencia, Costos. Clicking navigates to the pendientes sub-route.

2. **Badge in Campañas tab:** In the CampaignSummaryKpis section, a clickable badge reading "4 pendientes →" that navigates to the pendientes tab.

3. **Direct URL:** `/growth-studio/atraccion-captura/meta-ads?tab=pendientes` (tab-based) or `/growth-studio/atraccion-captura/meta-ads/pendientes` (route-based). Prefer route-based for deep-linking with `?campaign=ext_id`.

### MetaAdsDashboardTab type update

```typescript
// In types/metrics.ts
export type MetaAdsDashboardTab = 'resumen' | 'campanas' | 'pendientes' | 'creativos' | 'audiencia' | 'costos';
```

## Key Implementation Notes

1. **No new API endpoints needed.** All data comes from existing hooks: `useCampaignPerformance`, `useAssociations`, `useOffersForAssignment`, `useMetaHealthCheck`. Mutations use existing `useCreateAssociation` and `useDeleteAssociation`.

2. **OfferReassignPopover replaces drawer open for individual campaigns.** When clicking a badge on an already-assigned campaign in CampaignsTab, open the Popover instead of the OfferAssignmentDrawer. The drawer (`OfferAssignmentDrawerConnected`) is replaced by the Pendientes tab for bulk resolution.

3. **Pending items derivation logic:** A campaign is "pending" if: (a) no association exists for its `externalId`, OR (b) health check flags it for UTM issues. This logic lives in `PendientesView`, derived from the three queries.

4. **Optimistic removal on assignment:** When user selects an offer in the pendientes list, the item fades out immediately (optimistic). If the mutation fails, the item reappears. Same pattern as current `OfferAssignmentDrawer.savedKeys`.

5. **Deep-link support:** URL param `?campaign=ext_id` pre-selects that campaign in the left panel on mount. Used when navigating from the Campañas tab badge.

6. **The OfferAssignmentDrawer is NOT deleted.** It continues to exist as a component but is no longer the primary UX for assignment. The Pendientes tab replaces its role. The drawer may be deprecated in a future iteration.
