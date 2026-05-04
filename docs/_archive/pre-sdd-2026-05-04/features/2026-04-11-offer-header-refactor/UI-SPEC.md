# UI-SPEC: Offer Studio Header + Lifecycle Refactor

**Feature:** Offer Studio Header + Lifecycle Refactor
**Date:** 2026-04-11
**UI contract:** `/tmp/ux-preview/offer-header-B-v4-1775915391.html`
**Authored by:** orchestrator (creative flow ran in conversation)

---

## Design Intent

**Concept:** Un solo layout persistente para todo lo relacionado con una oferta (Editor · Assets · Campañas · Conocimiento), con lifecycle real controlado desde el header y cambio de tab instantáneo vía layout persistente de Next.js.

**Problem solved:** Hoy el header del offer editor mezcla 5 acciones sin jerarquía (toggle Editor/Preview, Landing Page, Completar IA, Guardar, badge status) y **omite el control más importante: el lifecycle**. El usuario configura una oferta pero no tiene forma de publicarla, pausarla, o volverla a draft. Además progreso (43%) vive desconectado del CTA de publicación, y coexisten dos layouts distintos (`OfferStudioLayout` + `OfferEditorLayout`) para sub-rutas del mismo recurso.

**Target emotion:** Control + confianza. *"Sé dónde estoy, qué me falta, y cuándo puedo lanzar."*

## Persona

**Creador de contenido / infoproductor** construyendo una oferta en el Offer Studio. Nivel técnico medio-bajo: entiende "producto" pero no "funnel". Llega después de crear la oferta y debe completar ~10 secciones. Necesita feedback visual de progreso, saber cuándo puede "lanzar" la oferta, y confianza en que lo que ve es lo que el Sales Agent usará.

## Design Principles

1. **Shell persistente** — la identidad + lifecycle + progreso viven en un layout que no se re-renderiza al cambiar de tab. Eso convierte navegación en cambio de contexto, no en pérdida de contexto.
2. **Acción principal por estado** — cada cambio de estado es intencional y debe confirmarse con consecuencias explícitas. No hay "cambios mudos".
3. **Paralelismo honesto** — oferta y landing tienen ciclos de vida separados, con indicadores claros cuando divergen.

---

## Persistent Shell Layout (`layout.tsx`)

```
┌────────────────────────────────────────────────────────────────────────┐
│ Row 1 — Identity + Lifecycle (h ≈ 60px, border-b, bg-background/80)    │
├────────────────────────────────────────────────────────────────────────┤
│ Row 2 — Progress + Landing + AutocompletarIA (h ≈ 44px, border-b,      │
│          bg-card/30)                                                   │
├────────────────────────────────────────────────────────────────────────┤
│ TabBar — Editor · Assets · Campañas · Conocimiento (h ≈ 44px, border-b) │
├────────────────────────────────────────────────────────────────────────┤
│ <children/>  ← active tab content, scrollable                          │
└────────────────────────────────────────────────────────────────────────┘
```

### Row 1: Identity + Lifecycle

**Left group:**
- Back button (`← ChevronLeft`, navigates to `/offer-studio` list)
- Title: `offer.name` (large, `font-bold text-lg`, truncate 300px)
- Format badge: `Programa grupal` / `Curso` / etc. (small pill, muted colors)
- Below title: `<AutoSaveIndicator />` — passive text "Guardado hace 2s" / "Guardando..." / "⚠ Error al guardar"

**Right group:**
- `<OfferStatusSwitcher />` — segmented control (Draft | Active | Paused) with current state highlighted
- Kebab button (`⋮`) → DropdownMenu with:
  - `Archivar` (active)
  - `Duplicar` (disabled, "Próximamente")
  - `Historial` (disabled, "Próximamente")

**Component:** `components/container/offer-shell-header-row1.tsx`

### Row 2: Progress + Landing + Autocompletar IA

**Left group (flex-1, max-w-xl):**
- Progress %: bold tabular-nums `text-info`
- Progress bar (`<Progress />`)
- Counter: "4 de 10 secciones · Siguiente: Stack de Valor"

**Right group:**
- `<LandingActionButton />` — 4-state button (see component spec below)
- `<AutocompletarIAButton />` — opens existing `OfferSmartFillDialog`

**Component:** `components/container/offer-shell-header-row2.tsx`

### TabBar

- Underline style (not pills). Active tab shows `info` colored underline
- Each tab: icon + label + optional count badge
- Tabs:
  1. `Editor` (no icon needed, default)
  2. `Assets` + count badge (total assets)
  3. `Campañas` + count badge (active campaigns)
  4. `Conocimiento` + count badge (indexed sources)

**Component:** `components/container/offer-tab-bar.tsx`

---

## Tab 1: Editor (`page.tsx`)

Existing editor layout adapted:

- Left: `OfferNavRail` (keep as-is, shows offer sections with progress)
- Right: form section wrapped by `OfferLivePreview` that renders the current section's form

**Changes:**
1. **Absorb Avatar selection** into section "Estrategia & Avatar" form
2. **Absorb Objections matrix** into section "Psicología & Objeciones" form (using `<ObjectionEditor />` refactored to be controlled by react-hook-form, not local state)
3. **Remove manual Save button** — all field changes trigger debounced autosave
4. **Remove Editor/Preview toggle** — if preview is needed later, it's a split-view inside the editor, not a mode switch

**Auto-save behavior:**
- Every `onChange` in form fields bumps a debounce timer (800ms)
- On debounce fire: `saveSection(currentSectionId, form.getValues())`
- `<AutoSaveIndicator />` subscribes to a TanStack Query mutation state

---

## Tab 2: Assets (`assets/page.tsx`) — NEW

### Layout

```
┌──────────────────────────────────────────────────────────────────┐
│ Toolbar Row 1:                                                   │
│   [🔍 Search...    ] [Ordenar ▼]      [Subir externo] [Generar]  │
├──────────────────────────────────────────────────────────────────┤
│ Toolbar Row 2 (filters):                                         │
│   Tipo: [Todos|Videos|Flyers|Carruseles|Docs]                    │
│   Origen: [Todos|IA|Externos]                    Mostrando 4 de 4│
├──────────────────────────────────────────────────────────────────┤
│ Grid (4 cols):                                                   │
│   ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                            │
│   │ card │ │ card │ │ card │ │ card │                            │
│   └──────┘ └──────┘ └──────┘ └──────┘                            │
└──────────────────────────────────────────────────────────────────┘
```

### Toolbar

**Row 1:**
- `<Input />` with search icon, placeholder "Buscar asset por nombre..." (max-w-md, flex-1)
- `<DropdownMenu />` sort: "Recientes primero" | "Más antiguos" | "Nombre A-Z" | "Nombre Z-A"
- Separator
- `<Button variant="outline">` — Subir externo (opens file picker)
- `<Button>` — Generar con IA (primary, opens `<AssetGenerationWizardDialog />` — stubbed for this feature)

**Row 2 (filters):**
- Label "Tipo" + `ToggleGroup`: Todos, Videos, Flyers, Carruseles, Docs
- Separator
- Label "Origen" + `ToggleGroup`: Todos, IA, Externos
- Right-aligned counter: "Mostrando N de M assets"

### Asset card

Each card (`<AssetCard />`):
- `aspect-[4/5]` rounded thumbnail with type-specific gradient background
- Top-left badge: "IA" (info color) or "Externo" (warning color)
- Top-right badge: duration ("0:45") / slides ("5 slides") / pages ("42p") / size ("2.4 MB")
- On hover: overlay with 3 action buttons:
  - `Eye` (Visualizar — opens `window.open(file_url)`)
  - `Download` (Descargar — triggers download endpoint)
  - `Edit3` (Editar en Puck — disabled for external, tooltip explains)
- Below: name (truncate) + `<RelativeTime /> · origen`

### States

- **Loading:** skeleton grid (4 cols × 2 rows)
- **Empty:** centered illustration + "Todavía no hay assets para esta oferta" + 2 CTAs (Subir externo, Generar con IA)
- **Error:** inline alert with retry

**Components:**
- `features/offer-studio/components/assets/asset-gallery.tsx`
- `features/offer-studio/components/assets/asset-card.tsx`
- `features/offer-studio/components/assets/asset-toolbar.tsx`
- `features/offer-studio/components/assets/asset-generation-wizard-dialog.tsx` (stub)

---

## Tab 3: Campañas (`campaigns/page.tsx`) — NEW

### Layout

```
┌──────────────────────────────────────────────────────────────────┐
│ KPI Row (4 cards):                                               │
│   [Activas: 2] [Inversión 7d: S/1240] [Leads: 47] [CPL: S/26,4]  │
├──────────────────────────────────────────────────────────────────┤
│ Toolbar: [estado chips] | [canal chips]           [Crear campaña]│
├──────────────────────────────────────────────────────────────────┤
│ Table:                                                           │
│   Campaña | Canal | Estado | Inversión | Leads | CPL | →         │
│   ────────────────────────────────────────────────────────       │
│   row                                                            │
│   row (active)                                                   │
│   row (finalizada, opacity-60, strikethrough)                    │
└──────────────────────────────────────────────────────────────────┘
```

### KPI cards

- 4 cards in grid-cols-4
- Each: small uppercase label + large tabular-nums value
- Currency respects `useTenantLocale().currency`

### Toolbar

- Status chips: Todas | Activas | Pausadas | Finalizadas (`ToggleGroup`)
- Separator
- Channel chips: Todos los canales | Meta | Google | TikTok (`ToggleGroup`)
- Right: `<Button>` "Crear campaña" → links to `/{tenantId}/growth-studio/advertising?offer_id={id}`

### Table

- `<Table>` from Shadcn
- Columns: Campaña (avatar+name+subtitle), Canal (text), Estado (badge), Inversión (right), Leads (right), CPL (right), Open icon (right)
- Row click navigates to Growth Studio campaign detail
- Finalizada rows: `opacity-60 line-through` on the name

### States

- Loading: skeleton table (6 rows)
- Empty: centered "Sin campañas aún. Creá una en Advertising Studio." + CTA
- Error: alert

**Components:**
- `features/offer-studio/components/campaigns/campaigns-view.tsx`
- `features/offer-studio/components/campaigns/campaigns-kpi-row.tsx`
- `features/offer-studio/components/campaigns/campaigns-table.tsx`

---

## Tab 4: Conocimiento (`knowledge/page.tsx`) — PROMOTED + REAL

### Layout

```
┌────────────────────────────────────────────────────────────────┐
│ Intro callout (info-colored, explains RAG purpose)             │
├────────────────────────────────────────────────────────────────┤
│ Toolbar: [🔍 Search] [type chips]    [Pegar URL] [Subir archivo]│
├────────────────────────────────────────────────────────────────┤
│ Source list (rows, not grid):                                  │
│   [icon] name + status badge                    [hover actions]│
│          type · size · date · chunks indexed                   │
│   ────────────────────────────────                             │
│   row                                                          │
│   row (processing, spinner icon)                               │
└────────────────────────────────────────────────────────────────┘
```

### Intro callout

`<Alert variant="info">` with info icon and text:
> El Sales Agent lee estas fuentes para responder preguntas específicas sobre **"[Offer Name]"**. Cuando un cliente pregunte *"¿cuántos módulos son?"*, el agente busca aquí primero antes de responder. Sin fuentes, el agente solo puede usar lo que está en el editor.

### Toolbar

- Search input: "Buscar fuente..." (max-w-md, flex-1)
- Type chips: Todas | PDFs | Videos | URLs
- Separator
- `<Button variant="outline">` "Pegar URL" → opens dialog with URL input (YouTube/blog/Google Docs)
- `<Button>` "Subir archivo" → file picker (PDF, DOCX, TXT, MD — max 10MB)

### Source row

Each row (`<KnowledgeSourceRow />`):
- Left icon (10x10): file-type specific with type-specific color (info for PDF, danger for video, success for URL)
- Main content (flex-1):
  - Name (truncate) + status badge
  - Metadata line: `{type} · {size/duration} · {pages/chunks} · Subido {relativeDate} · {chunks} chunks indexados`
- Right (hover-visible): action buttons
  - `Eye` — Visualizar contenido (preview in dialog or new tab)
  - `Download` — Descargar (for uploaded files)
  - `ExternalLink` — Abrir en origen (for URLs, opens YouTube/blog)
  - `RefreshCw` — Re-indexar
  - `Trash2` — Eliminar (confirmation dialog)

### Status badge

- `Indexado` (success) — green dot, "INDEXADO"
- `Procesando` (warning) — amber dot, "PROCESANDO" (with spinning icon on the left)
- `Error` (danger) — red dot, "ERROR"

### States

- Loading: skeleton list (5 rows)
- Empty: centered callout explaining + CTAs
- Error: inline alert

**Components:**
- `features/offer-studio/components/knowledge/knowledge-view.tsx`
- `features/offer-studio/components/knowledge/knowledge-toolbar.tsx`
- `features/offer-studio/components/knowledge/knowledge-source-row.tsx`
- `features/offer-studio/components/knowledge/knowledge-url-dialog.tsx`

---

## Shared Components

### `<OfferStatusSwitcher />`

**Location:** `features/offer-studio/components/container/offer-status-switcher.tsx`

**Props:**
```ts
interface OfferStatusSwitcherProps {
  currentStatus: OfferStatus;        // draft | active | paused | archived
  onStatusChange: (newStatus: OfferStatus) => void;
  disabled?: boolean;                // e.g., during save mutation
}
```

**Render:**
- Segmented control with 3 pills: Borrador, Activa, Pausada
- Current state highlighted
- Clicking a different state opens `<OfferStatusChangeModal />`
- Disabled states per lifecycle rules (Draft→Paused not allowed directly)
- Kebab button next to the switcher (archived + duplicate + history)

**Tooltips:**
- Each pill has a `<Tooltip>` explaining the consequence
- Archive kebab item: "Moverá la oferta a 'Archivadas'. Reversible."

### `<OfferStatusChangeModal />`

**Location:** `features/offer-studio/components/container/offer-status-change-modal.tsx`

**Props:**
```ts
interface OfferStatusChangeModalProps {
  open: boolean;
  fromStatus: OfferStatus;
  toStatus: OfferStatus;
  offer: Offer;
  onConfirm: () => Promise<void>;
  onCancel: () => void;
}
```

**Render:** Uses `<Dialog>` (Shadcn). Title + description + **consequence list** (3 bullets per transition) + Cancel / Confirm buttons.

**Consequence library** (hardcoded in component, uses current conversation as source):

```ts
const CONSEQUENCES: Record<`${Status}_${Status}`, Consequence[]> = {
  draft_active: [
    { icon: 'Check', tone: 'success', text: 'Tu Sales Agent empezará a proponerla en conversaciones.' },
    { icon: 'AlertTriangle', tone: 'warning', text: 'Faltan {N} secciones por completar. La landing no se generará hasta llegar al 90%.' },
    { icon: 'Info', tone: 'info', text: 'Podés pausarla o archivarla cuando quieras.' },
  ],
  active_paused: [
    { icon: 'X', tone: 'warning', text: 'El Sales Agent dejará de proponerla, pero la reconocerá como un producto que existió si un cliente pregunta.' },
    { icon: 'Link', tone: 'info', text: 'La landing pública sigue viva. Despublicala manualmente si querés bajarla.' },
    { icon: 'RotateCcw', tone: 'success', text: 'Podés reactivarla en cualquier momento sin perder nada.' },
  ],
  // ... full table documented in REQUIREMENTS.md
};
```

### `<LandingActionButton />`

**Location:** `features/offer-studio/components/container/landing-action-button.tsx`

**4 states (derived from `useLandingStatus(offerId)`):**

```ts
type LandingState =
  | { kind: 'disabled'; progress: number }          // progress < 90
  | { kind: 'ready-to-generate'; progress: number } // progress >= 90, not generated
  | { kind: 'in-sync'; url: string }                // generated, up to date
  | { kind: 'outdated'; url: string; staleSince: string }; // generated, offer modified after
```

**Render:**
- **disabled:** `Button variant="outline"` (opacity 60) with label "Generar landing" + progress badge "47%". Tooltip: "Completá al menos 90% para generarla"
- **ready-to-generate:** `Button variant="info"` with spark icon "Generar landing con IA". Click → modal + POST /landing/generate
- **in-sync:** `Button variant="outline"` with success dot + "Abrir landing" + external-link icon. Kebab next to it: Editar en Puck / Regenerar / Despublicar
- **outdated:** Same as in-sync but with pulsing amber dot + warning tooltip. Kebab shows "Regenerar (recomendado)" at top

**Hook:** `useLandingStatus(offerId)` → TanStack Query fetching `GET /landing/status`

### `<AutoSaveIndicator />`

**Location:** `features/offer-studio/components/container/auto-save-indicator.tsx`

**Props:**
```ts
interface AutoSaveIndicatorProps {
  state: 'idle' | 'saving' | 'saved' | 'error';
  lastSavedAt?: Date;
  errorMessage?: string;
  onRetry?: () => void;
}
```

**Render:**
- `idle`: nothing (hidden)
- `saving`: spinner + "Guardando..."
- `saved`: check + "Guardado hace Ns" (relative time, updates every 10s)
- `error`: alert icon + "Error al guardar" + `<Button variant="link">Reintentar</Button>`

### `<OfferTabBar />`

**Location:** `features/offer-studio/components/container/offer-tab-bar.tsx`

**Props:**
```ts
interface OfferTabBarProps {
  tenantId: string;
  offerId: string;
  counts: { assets: number; campaigns: number; knowledge: number };
}
```

**Render:** Uses `usePathname()` to determine active tab. Underline style (not `<Tabs>` since tab content lives in separate route). Each tab is a `<Link>` with active styling.

---

## Data Flow

### Server-side (layout.tsx)

```ts
// layout.tsx
async function OfferLayout({ params, children }) {
  const { tenantId, id } = await params;
  const token = await getToken();

  // Parallel fetches for shell data
  const [offer, counts] = await Promise.all([
    offerApi.getOffer(id, token),
    offerApi.getOfferCounts(id, token), // new endpoint: returns { assets, campaigns, knowledge }
  ]);

  return (
    <OfferShell offer={offer} counts={counts}>
      {children}
    </OfferShell>
  );
}
```

Shell is a Server Component. `<OfferShell />` is a Client Component that receives the data as props. This way mutations (status change, autosave) happen client-side while initial load is SSR.

### Client-side (tabs)

- Each tab `page.tsx` is a thin wrapper that calls a Client Component
- Client components use TanStack Query for data fetching with `fetchClient` (auto X-Tenant-ID)
- Shared state (offer, status) lives in a Context provided by `<OfferShell />` so tabs can read it without refetching

### Mutations

- `useChangeOfferStatus(offerId)` — mutation for status transitions
- `useAutoSaveSection(offerId)` — debounced mutation for section save
- `useGenerateLanding(offerId)` — mutation for landing generation
- `useAssetMutations(offerId)` — CRUD mutations for assets
- `useKnowledgeMutations(offerId)` — CRUD mutations for knowledge sources

All mutations invalidate `['offer', offerId]` + relevant sub-queries on success.

---

## API Integration

See `CONTRACT.md` (to be produced by architect) for full endpoint specs. Frontend hooks map 1:1:

| Hook | Endpoint |
|---|---|
| `useOffer(offerId)` | `GET /offers/{id}` (existing) |
| `useOfferCounts(offerId)` | `GET /offers/{id}/counts` (NEW) |
| `useChangeOfferStatus(offerId)` | `POST /offers/{id}/status` (NEW) |
| `useAutoSaveSection(offerId, sectionId)` | `PATCH /offers/{id}/{section}` (existing) |
| `useLandingStatus(offerId)` | `GET /offers/{id}/landing/status` (NEW) |
| `useGenerateLanding(offerId)` | `POST /offers/{id}/landing/generate` (NEW) |
| `usePublishLanding(offerId)` | `POST /offers/{id}/landing/publish` (NEW) |
| `useUnpublishLanding(offerId)` | `POST /offers/{id}/landing/unpublish` (NEW) |
| `useRegenerateLanding(offerId)` | `POST /offers/{id}/landing/regenerate` (NEW) |
| `useAssets(offerId, filters)` | `GET /offers/{id}/assets` (NEW) |
| `useCreateAsset(offerId)` | `POST /offers/{id}/assets/generate` or `/upload` (NEW) |
| `useDeleteAsset(offerId)` | `DELETE /offers/{id}/assets/{asset_id}` (NEW) |
| `useKnowledgeSources(offerId, filters)` | `GET /offers/{id}/knowledge` (NEW) |
| `useUploadKnowledge(offerId)` | `POST /offers/{id}/knowledge/upload` (NEW) |
| `useAddKnowledgeUrl(offerId)` | `POST /offers/{id}/knowledge/url` (NEW) |
| `useDeleteKnowledge(offerId)` | `DELETE /offers/{id}/knowledge/{id}` (NEW) |
| `useReindexKnowledge(offerId)` | `POST /offers/{id}/knowledge/{id}/reindex` (NEW) |
| `useOfferCampaigns(offerId, filters)` | `GET /offers/{id}/campaigns` (NEW, aggregates from advertising) |

---

## Shadcn Components Used

**Already installed:** button, badge, card, dialog, dropdown-menu, input, label, progress, scroll-area, separator, table, tabs (reference only), textarea, tooltip, alert-dialog, alert, popover, select, sheet, skeleton, sonner, form, avatar

**No new Shadcn components needed.** All UI is composable from existing primitives.

**Custom components to create:**
- `components/ui/toggle-group.tsx` (for filter chips) — Shadcn primitive, install via `npx shadcn add toggle-group`

---

## FSD File Structure

```
frontend/src/
  app/(main)/[tenantId]/(dashboard)/offer-studio/
    offer/[id]/
      layout.tsx                       # NEW — persistent shell
      page.tsx                         # Editor tab (repurposed)
      assets/page.tsx                  # NEW
      campaigns/page.tsx               # NEW
      knowledge/page.tsx               # NEW (replaces existing mock)
      avatar/                          # DELETE folder
      objections/                      # DELETE folder

  features/offer-studio/
    api/
      assets-api.ts                    # NEW
      campaigns-api.ts                 # NEW
      knowledge-api.ts                 # NEW (replaces mock)
      landing-api.ts                   # NEW
      status-api.ts                    # NEW

    hooks/
      use-assets.ts                    # NEW
      use-auto-save.ts                 # NEW
      use-campaigns.ts                 # NEW
      use-knowledge.ts                 # NEW
      use-landing-status.ts            # NEW
      use-offer-counts.ts              # NEW
      use-status-mutation.ts           # NEW

    types/
      assets.ts                        # NEW
      campaigns.ts                     # NEW
      knowledge.ts                     # NEW
      landing-status.ts                # NEW

    components/
      container/
        offer-shell.tsx                # NEW (client shell, wraps children)
        offer-shell-header-row1.tsx    # NEW
        offer-shell-header-row2.tsx    # NEW
        offer-tab-bar.tsx              # NEW
        offer-status-switcher.tsx      # NEW
        offer-status-change-modal.tsx  # NEW
        landing-action-button.tsx     # NEW
        landing-kebab-menu.tsx         # NEW
        auto-save-indicator.tsx        # NEW
        offer-progress-bar.tsx         # NEW
        autocompletar-ia-button.tsx    # NEW (wraps existing dialog)
        offer-studio-layout.tsx        # REMOVE (replaced by new shell)
      editor/
        layout/                        # DELETE folder (offer-editor-layout.tsx)
        offer-editor.tsx               # ADAPT (no longer passes header props; autosave wired)
        sections/
          strategy/                    # ABSORB avatar selection here
          psychology/                  # ABSORB objections matrix here
        components/
          objection-editor.tsx         # DELETE (standalone mock)
          asset-uploader.tsx           # DELETE (mock, replaced by knowledge view)
      views/
        avatar-selection-view.tsx      # DELETE
      assets/                          # NEW FOLDER
        asset-gallery.tsx
        asset-card.tsx
        asset-toolbar.tsx
        asset-generation-wizard-dialog.tsx
      campaigns/                       # NEW FOLDER
        campaigns-view.tsx
        campaigns-kpi-row.tsx
        campaigns-table.tsx
      knowledge/                       # NEW FOLDER
        knowledge-view.tsx
        knowledge-toolbar.tsx
        knowledge-source-row.tsx
        knowledge-url-dialog.tsx

    tests/                             # Co-located per-component tests
      ...
```

---

## Responsive Behavior

- **Desktop (≥1280px)**: full shell with all rows visible, tab bar horizontal, 4-col asset grid
- **Tablet (768–1279px)**: 3-col asset grid, tab bar horizontal, header rows stack tighter
- **Mobile (<768px)**: 2-col asset grid, tab bar becomes horizontal scrollable, Row 2 wraps to 2 lines, kebab hides in overflow

Primary target is **desktop** — Nicolify is a desktop-first SaaS, mobile is best-effort.

---

## Loading / Error / Empty States

Every data-driven component MUST specify all 3 states.

| Component | Loading | Empty | Error |
|---|---|---|---|
| Shell (layout) | full-page skeleton with shell shape | N/A (can't be empty) | Error page with "Volver al Studio" |
| Editor | Existing skeleton | Existing empty states per section | Existing alerts |
| Assets grid | Skeleton grid (8 cards) | Centered "No hay assets" + CTAs | Inline alert + retry |
| Campaigns | Skeleton KPI + table skeleton (5 rows) | "Sin campañas. Creá una en Advertising." + CTA | Alert + retry |
| Knowledge list | Skeleton rows (5) | Intro callout + "Subí tu primera fuente" + CTAs | Alert + retry |
| Status change modal | Button shows spinner on submit | N/A | Error toast + modal stays open |
| Landing generation | Button → spinner → polling | N/A | Error toast |

---

## Interaction Patterns

### Status change flow (Draft → Active)

1. User clicks "Activa" pill in switcher
2. `<OfferStatusChangeModal>` opens with consequences list
3. User reads, clicks "Activar"
4. Button shows spinner
5. Mutation fires POST /offers/{id}/status
6. On success: modal closes, toast "Oferta activada", badge in header updates, TanStack Query invalidates
7. On error: toast with error message, modal stays open

### Auto-save flow

1. User edits a field
2. React-hook-form onChange triggers
3. Debounce timer starts (800ms)
4. On debounce fire: `<AutoSaveIndicator>` goes to "saving"
5. Mutation fires PATCH /offers/{id}/{section}
6. On success: "saving" → "saved Ns ago" (counter updates every 10s)
7. On error: "error" with retry button

### Landing generation flow

1. User clicks "Generar landing con IA" (state: ready-to-generate)
2. Dialog opens: "Voy a generar la landing con IA basándome en tu oferta. Tarda ~30s."
3. User confirms
4. Button → spinner + "Generando..." (polling every 2s)
5. Backend job completes → button transitions to state: `in-sync` ("Abrir landing")
6. Toast "Landing generada"

### Tab navigation

1. User clicks "Assets" tab
2. Next.js client navigation (no page reload)
3. Layout persists (Row 1 + Row 2 + TabBar unchanged)
4. Children swap: assets page mounts
5. URL updates to `/offer/{id}/assets`
6. Back button works natively (browser history)
7. Copilot can deep-link to this URL and land here directly

---

## Typography, Color, Spacing

Follows existing Nicolify design tokens from `globals.css`:

- **Typography:** `font-sans` (Inter) everywhere. `text-lg font-bold` for title, `text-xs text-muted-foreground` for metadata, `tabular-nums` for numbers
- **Color (60/30/10):**
  - 60% neutral: `bg-background`, `bg-card`, `text-foreground`, `text-muted-foreground`
  - 30% brand: primary buttons, tab underline, progress fill (`hsl(var(--primary))`)
  - 10% accent: `info` (landing), `warning` (paused, outdated), `success` (indexed, active), `danger` (archive)
- **Spacing:** Tailwind scale. Standard row padding `px-6 py-3`, filter toolbars `gap-3`

---

## Accessibility

- All interactive elements have `aria-label` where icon-only
- Tooltips use Shadcn `<Tooltip>` which handles keyboard focus
- Modals trap focus (Shadcn `<Dialog>` handles)
- Status switcher is a `<div role="tablist">` with pills as `<button role="tab">`
- Tab bar uses `<nav>` with list of links
- Color-coded status indicators ALSO include text labels (color is not the only signal)

---

## Testing Requirements

### Unit / component tests (Vitest + happy-dom)

Required tests per component:
- `offer-status-switcher.test.tsx` — renders current state, clicking opens modal
- `offer-status-change-modal.test.tsx` — renders consequences, confirms/cancels correctly
- `landing-action-button.test.tsx` — renders 4 states based on props
- `auto-save-indicator.test.tsx` — renders 4 UI states
- `offer-tab-bar.test.tsx` — active tab based on pathname
- `asset-gallery.test.tsx` — loading, empty, populated, filters work
- `asset-card.test.tsx` — hover actions, edit disabled for external
- `campaigns-view.test.tsx` — KPIs render, table rows link out
- `knowledge-view.test.tsx` — list renders with status badges
- Hooks tests: `use-auto-save.test.ts` (debouncing), `use-landing-status.test.ts`

### E2E smoke (Playwright)

One new smoke test:
- `offer-header-refactor.smoke.spec.ts`:
  1. Navigate to `/offer-studio/offer/{id}` (Editor)
  2. Verify shell renders (title, status switcher, tabs)
  3. Click "Assets" tab, verify URL changes and assets view loads
  4. Click "Editor" tab, verify return without full reload
  5. Click status switcher → "Activa", verify modal opens
  6. Cancel modal, verify status unchanged
  7. Verify deep-link: `/offer/{id}/knowledge` loads directly

---

## Notes for `nicolify-frontend` agent

- **Read CONTRACT.md before writing any TypeScript types** — types come from CONTRACT.md, not invented
- **Use existing `fetchClient`** — don't create new API clients
- **Reuse `<OfferSmartFillDialog>` as-is** for the Autocompletar IA button — just wrap it
- **`OfferNavRail` stays as-is** inside the Editor tab (it's the sub-navigation for offer sections)
- **TDD mandatory** per `.claude/rules/tdd-mandatory.md`: test files first, then implementation
- **No `any` types** — use `unknown` + type guards if needed
- **All Spanish text** must use correct tildes/eñes per `.claude/rules/spanish-text.md`
- **Currency** must come from `useTenantLocale()`, never hardcoded `"USD"`
