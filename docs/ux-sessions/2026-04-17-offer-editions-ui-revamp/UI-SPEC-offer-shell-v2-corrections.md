# UI-SPEC v2 — Offer Studio Shell (Corrections)

> **Iteration:** 2 (2026-04-17, tarde)
>
> **Status:** Ready for implementation. Supersedes sections 1-4 of `UI-SPEC-offer-studio-shell.md` and section 1 of `UI-SPEC-offer-studio-tabs.md`. Sections on Ventas/Campañas in v1 remain valid.
>
> **Reference prototypes:** `prototype/offer-studio/offer-info-v2.html`, `offer-ventas-v2.html`, `offer-assets-v2.html`, `offer-campanas-v2.html`.
>
> **Rationale:** see DECISIONS D15-D20.

---

## 1. New overall layout (no rail)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ App sidebar (w-60)     │ Main (flex-1)                                  │
│                        │ ┌────────────────────────────────────────────┐ │
│                        │ │ OfferShellHeaderRow1  (offer-level)        │ │
│                        │ │ ← Name · archetype · autosave     [status] │ │
│                        │ ├────────────────────────────────────────────┤ │
│                        │ │ OfferShellHeaderRow2  (offer-level)        │ │
│                        │ │ 78% ━━━━ 8/10 · siguiente: X        [✨IA] │ │
│                        │ ├────────────────────────────────────────────┤ │
│                        │ │ OfferTabBar + LandingSplitButton           │ │
│                        │ │ [📋 Info] [💰 Ventas] [🎨 Assets] ...      │ │
│                        │ ├────────────────────────────────────────────┤ │
│                        │ │ EditionSelectorBar  (conditional)          │ │
│                        │ │ Edición: [#3 Jul 2026 ▾]  [+ Nueva] [Ver]  │ │
│                        │ ├────────────────────────────────────────────┤ │
│                        │ │ WaitlistBanner  (conditional)              │ │
│                        │ ├────────────────────────────────────────────┤ │
│                        │ │ Tab content (Info, Ventas, Assets, Camp.)  │ │
│                        │ └────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

**Tailwind root:**
```tsx
<div className="flex min-h-screen">
  <AppSidebar />
  <main className="flex flex-1 min-w-0 flex-col">
    <OfferShellHeaderRow1 />
    <OfferShellHeaderRow2 />
    <OfferTabBar />
    {tabIsEditionScoped && <EditionSelectorBar />}
    {shouldShowWaitlistBanner && <WaitlistBanner />}
    <div className="flex-1 overflow-auto">{children}</div>
  </main>
</div>
```

`tabIsEditionScoped = offer.has_editions === true && activeTab !== 'info'`.

---

## 2. OfferShellHeaderRow1 (corrected)

### 2.1 Visual
```
┌────────────────────────────────────────────────────────────┐
│ ← MasterClass de Copywriting              [● Borrador]  ⋮  │
│   Programa · DWY · ● Guardado hace 2s                      │
└────────────────────────────────────────────────────────────┘
```

**NO more** "· Edición #N · fecha" suffix in the title. Status/visibility badges are **offer-level** (lifecycle of the offer, not edition).

### 2.2 Props unchanged from v1
Keep `useOfferShell` context. Remove the conditional render of edition number / edition status / visibility inline in the header (those move to `EditionSelectorBar`).

### 2.3 Implementation delta
- `OfferShellHeaderRow1.tsx:78-90` — remove the `<span className="text-blue-700">Edición #{n}</span>` branch and visibility badge. Keep offer-level `OfferStatusSwitcher`.
- Title `<h1>` always renders `offer.name` alone.

---

## 3. OfferShellHeaderRow2 (unchanged visually, semantics changed)

Progress bar always reflects **offer-level** completion (sections of the builder template filled). Switching edition does NOT change the %. Per-edition completion is shown inside `EditionSelectorBar` (small `· 85%` chip next to the dropdown).

---

## 4. OfferTabBar (4 tabs, corrected)

**Change from v1:** tabs go from 5 back to 4. Remove `Conocimiento` tab (it becomes a section inside Info).

```ts
const TABS: TabConfig[] = [
  { id: 'info',     icon: '📋', label: 'Info',     count: null },
  { id: 'ventas',   icon: '💰', label: 'Ventas',   count: enrollmentsCount },
  { id: 'assets',   icon: '🎨', label: 'Assets',   count: assetsCount },
  { id: 'campanas', icon: '📢', label: 'Campañas', count: campaignsCount },
];
```

Delete `/knowledge/page.tsx` route.

---

## 5. EditionSelectorBar (new component, replaces EditionsRail)

### 5.1 File
`frontend/src/features/offer-studio/components/container/EditionSelectorBar.tsx`

### 5.2 Props
```ts
interface EditionSelectorBarProps {
  offerId: string;
  editions: LaunchEdition[];
  currentEditionId: string | null;
  waitlistCount?: number;
  onEditionChange: (editionId: string) => void;  // updates ?edition= query param
  onCreateNew: () => void;                       // opens EditionFormDialog
  onOpenManagement: () => void;                  // navigates to info tab, scrolls to section "ediciones"
}
```

### 5.3 Visual

**Default (edition upcoming):**
```
┌────────────────────────────────────────────────────────────────────────┐
│ Edición: [📅 #3 · Julio 2026  ▾]  [● Próxima] [🌐 Pública]            │
│ 12/50 inscriptos · Inicia en 42 días     [+ Nueva edición] [Ver todas] │
└────────────────────────────────────────────────────────────────────────┘
```

**Edition cancelled / completed (read-only mode):**
```
┌────────────────────────────────────────────────────────────────────────┐
│ Edición: [📦 #2 · Abril 2026  ▾]  [● Completada]                      │
│ 25/25 · Revenue S/ 17,250 · 📦 Solo lectura    [+ Clonar a Edición #5] │
└────────────────────────────────────────────────────────────────────────┘
```

**Edition draft without date:**
```
┌────────────────────────────────────────────────────────────────────────┐
│ Edición: [✏ #4 · Sin fecha  ▾]  [● Borrador] [🔒 Privada]             │
│ 3 en waitlist · Configurá fecha para publicar   [+ Nueva edición]      │
└────────────────────────────────────────────────────────────────────────┘
```

### 5.4 Markup
```tsx
<div className="flex items-center justify-between bg-slate-50 border-b border-slate-200 px-8 py-2.5 gap-4 flex-wrap">
  <div className="flex items-center gap-2 flex-1 min-w-0">
    <span className="text-xs text-slate-500 shrink-0">Edición:</span>
    <EditionDropdown
      editions={editions}
      currentEditionId={currentEditionId}
      onChange={onEditionChange}
    />
    <StatusBadge status={current.status} size="xs" />
    {current.status !== EditionStatus.DRAFT && (
      <VisibilityBadge visibility={current.visibility} size="xs" />
    )}
    <span className="text-xs text-slate-500 truncate">
      {buildEditionSummary(current, waitlistCount)}
    </span>
  </div>
  <div className="flex items-center gap-2 shrink-0">
    {isReadOnly(current) ? (
      <Button size="sm" variant="primary" onClick={onCreateNew}>
        + Clonar a Edición #{nextNumber}
      </Button>
    ) : (
      <Button size="sm" variant="primary" onClick={onCreateNew}>
        + Nueva edición
      </Button>
    )}
    <Button size="sm" variant="ghost" onClick={onOpenManagement}>
      Ver todas →
    </Button>
  </div>
</div>
```

### 5.5 EditionDropdown structure
Uses `@/components/ui/select` or a custom popover. Groups options in the same order as the legacy rail:

- `🔴 EN CURSO` (ACTIVE)
- `⭐ PRÓXIMA` (UPCOMING + PUBLIC)
- `✏ BORRADORES` (DRAFT)
- `✓ PASADAS` (COMPLETED / CANCELLED, sorted desc by start_date)

Each option:
```
#N · fecha_corta · status_label · enrolled/capacity
```

Selected item in the trigger:
```
{icon_por_status} #N · mes año
```

### 5.6 Edition switch behaviour
Identical to rail's (`?edition={id}` replace, preserves active tab, re-fetches scoped data, scrolls content to top).

### 5.7 Visibility rule
```ts
const showsSelector = (
  offer.has_editions === true &&
  activeTab !== 'info'
);
```

When `activeTab === 'info'`, the edition concept lives inside the Info content as a management sub-section (see § 7).

### 5.8 Read-only mode chip
When `current.status ∈ {COMPLETED, CANCELLED}`, the summary string includes "📦 Solo lectura" and the CTA changes from "+ Nueva edición" to "+ Clonar a Edición #{nextNumber}" (same handler — opens `EditionFormDialog` with source pre-filled).

---

## 6. OfferShell.tsx (corrected)

### 6.1 Responsibilities
- Mount header Row1 + Row2 + tab bar + children.
- Conditionally mount `EditionSelectorBar` when active tab is edition-scoped.
- Conditionally mount `WaitlistBanner`.
- Own the `EditionFormDialog` state (open/close) used by all CTAs.
- Resolve current edition via `useOfferWithEdition` (unchanged).

### 6.2 Code skeleton
```tsx
export function OfferShell({ offer, counts, tenantId, children }) {
  const [snapshot, setSnapshot] = useState(DEFAULT_SNAPSHOT);
  const [editionFormOpen, setEditionFormOpen] = useState(false);
  const [editionFormSource, setEditionFormSource] = useState<LaunchEdition | null>(null);

  const { editions } = useEditions(offer.id);
  const { currentEditionId } = useOfferWithEdition(offer.id);
  const current = editions.find(e => e.id === currentEditionId);

  const activeTab = useActiveTab();  // derives from pathname
  const tabIsEditionScoped = offer.has_editions === true && activeTab !== 'info';

  const openNewEdition = () => {
    setEditionFormSource(null);
    setEditionFormOpen(true);
  };

  const openCloneEdition = (source: LaunchEdition) => {
    setEditionFormSource(source);
    setEditionFormOpen(true);
  };

  return (
    <OfferShellContext.Provider value={{ offer, counts, tenantId, openNewEdition, openCloneEdition }}>
      <OfferAutoSaveContext.Provider value={{ ...snapshot, setSnapshot }}>
        <div className="flex min-h-screen bg-background">
          <main className="flex flex-1 min-w-0 flex-col">
            <OfferShellHeaderRow1 />
            <OfferShellHeaderRow2 />
            <OfferTabBar tenantId={tenantId} offerId={offer.id} counts={counts} />

            {tabIsEditionScoped && current && (
              <EditionSelectorBar
                offerId={offer.id}
                editions={editions}
                currentEditionId={currentEditionId}
                waitlistCount={current.waitlist_count ?? 0}
                onEditionChange={switchEditionHandler}
                onCreateNew={openNewEdition}
                onOpenManagement={() => navigateToInfoEditionsSection(tenantId, offer.id)}
              />
            )}

            {shouldShowWaitlistBanner(current) && (
              <WaitlistBanner
                editionId={currentEditionId!}
                editionNumber={current!.edition_number}
                waitlistCount={current!.waitlist_count}
              />
            )}

            <div className="flex-1 overflow-auto">{children}</div>
          </main>

          <EditionFormDialog
            open={editionFormOpen}
            onOpenChange={setEditionFormOpen}
            edition={editionFormSource ?? undefined}  // undefined = create new
            offerPricing={offer.pricing}
            offerId={offer.id}
          />
        </div>
      </OfferAutoSaveContext.Provider>
    </OfferShellContext.Provider>
  );
}
```

### 6.3 Deletions
- `EditionsRail.tsx` — delete.
- `EditionsRailCollapsed.tsx` — delete.
- `use-rail-collapsed.ts` — delete.
- localStorage key `nicolify.offer-studio.rail-collapsed` — dead, no cleanup needed (harmless).

---

## 7. EditionsManagementSection (new, last section of Info tab)

### 7.1 File
`frontend/src/features/offer-studio/components/info/EditionsManagementSection.tsx`

### 7.2 Scope
Rendered only when `offer.has_editions === true`. Replaces the existing `EditionsSection.tsx` (the `editions` entry in `SECTION_REGISTRY`) and all rail-era management.

### 7.3 Visual
```
┌──────────────────────────────────────────────────────────────────┐
│ 12. Ediciones                                       + Nueva      │
│ ───────────────────────────────────────────────────────────────  │
│                                                                  │
│ ⭐ PRÓXIMA                                                       │
│ ┌────────────────────────────────────────────────────────────┐   │
│ │ Edición #3 · Julio 2026    [● Próxima] [🌐 Pública]  ⋮     │   │
│ │ Inicia 15 jul · 6 semanas · 12/50 inscriptos (24%)         │   │
│ │ Revenue proyectado: S/ 34,500                              │   │
│ │ [Editar]  [Clonar]  [Despublicar]                          │   │
│ └────────────────────────────────────────────────────────────┘   │
│                                                                  │
│ ✏ BORRADORES                                                     │
│ ┌────────────────────────────────────────────────────────────┐   │
│ │ Edición #4 · Sin fecha    [● Borrador] [🔒 Privada]  ⋮     │   │
│ │ ⚠ 3 en waitlist · Configurá fecha para publicar            │   │
│ │ [Editar]  [Publicar]  [Eliminar]                           │   │
│ └────────────────────────────────────────────────────────────┘   │
│                                                                  │
│ ✓ PASADAS                                                        │
│ ┌────────────────────────────────────────────────────────────┐   │
│ │ Edición #2 · Abril 2026   [● Completada]           ⋮       │   │
│ │ 25/25 · Revenue S/ 17,250 · NPS 68                         │   │
│ │ [Ver detalle]  [Clonar]                                    │   │
│ └────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

### 7.4 Empty state
```
┌──────────────────────────────────────────────────────────────────┐
│ 12. Ediciones                                                    │
│ ───────────────────────────────────────────────────────────────  │
│                                                                  │
│  📅 Aún no creaste ediciones                                     │
│  Las ediciones te permiten vender la misma oferta en diferentes  │
│  cohortes con fechas, pricing y disponibilidad independientes.   │
│                                                                  │
│           [+ Crear primera edición]                              │
└──────────────────────────────────────────────────────────────────┘
```

### 7.5 Card props
```ts
interface EditionCardProps {
  edition: LaunchEdition;
  onEdit: () => void;        // opens EditionFormDialog with edition preloaded
  onClone: () => void;       // opens EditionFormDialog as clone (D19)
  onPublish: () => void;
  onUnpublish: () => void;
  onCancel: () => void;
  onDelete: () => void;
  onViewDetail: () => void;  // for COMPLETED — navigates to ventas tab of that edition
}
```

Actions are status-aware:

| Edition status | Primary | Secondary | Kebab items |
|---|---|---|---|
| `DRAFT` | Editar | Publicar | Eliminar |
| `UPCOMING` + PUBLIC | Editar | Clonar | Despublicar, Cancelar |
| `UPCOMING` + PRIVATE | Editar | Publicar | Cancelar |
| `ACTIVE` | Editar | — | Finalizar (manual) |
| `COMPLETED` | Ver detalle | Clonar | — |
| `CANCELLED` | Clonar | — | Eliminar |

### 7.6 CTA "+ Nueva edición"
Top-right of the section. Always calls `openNewEdition` (from shell context). The empty-state CTA uses the same handler.

---

## 8. Assets tab (corrected — gallery moves here)

### 8.1 Two zones

**Zone A (top): "Galería de Oferta"** — offer-level, shared across editions. Integrates the existing `GalleryManager` + `GalleryPreview` components migrated from Info.

**Zone B (bottom): "Assets por Edición"** — edition-scoped, respects `EditionSelectorBar` selection. Flyers, reels, carruseles, creatives.

### 8.2 Visual
```
┌──────────────────────────────────────────────────────────────────┐
│ 🎨 Galería de Oferta  (compartida entre ediciones)               │
│ ───────────────────────────────────────────────────────────────  │
│ [thumbs grid 5 cols]   + Subir imagen                            │
│                                                                  │
│ 🎨 Assets · Edición #3 Jul 2026  (↑ cambia en selector)          │
│ ───────────────────────────────────────────────────────────────  │
│ [filter pills: Todos / Flyers / Reels / Carruseles / Docs]       │
│ [thumbs grid 5 cols]                                             │
│                                                                  │
│ 🚧 Editor visual tipo Canva — Próximamente (Fase 2)              │
│ [📥 Jalar de Edición #2]  [+ Generar con IA]                     │
└──────────────────────────────────────────────────────────────────┘
```

### 8.3 Implementation delta
- Quitar `"gallery"` de todos los arrays en `ARCHETYPE_BUILDER_CONFIG` (`offer-builder-config.ts:207-274`).
- `OfferAssetsTab.tsx` importa `GalleryManager` + `GalleryPreview` desde `../editor/sections/visuals/` y los renderiza en Zona A.
- Zona B consume datos existentes del endpoint de assets per-edition.

---

## 9. Info tab (corrected section list)

### 9.1 Final section order (for archetypes with `has_editions`)
1. Identidad de Oferta
2. Estrategia & Avatar
3. Psicología & IA
4. Promesa & Resultado
5. Detalles del Programa/Servicio/Experiencia
6. Instructores (cuando aplica)
7. Stack de Valor
8. Recursos
9. Precios (template)
10. Cierre & Garantía
11. **Conocimiento (RAG)** — ex tab, integrado como sección
12. **Ediciones** — `EditionsManagementSection`, sólo si `has_editions === true`

### 9.2 Final section order (for PRODUCTO / MEMBRESIA — no editions)
1-11 iguales, sin sección 12.

### 9.3 Edits to `offer-builder-config.ts`
- Remove entry `gallery` from every `ARCHETYPE_BUILDER_CONFIG` array.
- Remove entry `editions` from arrays (the management lives as dedicated section, not a config-driven entry). Note: component `EditionsSection.tsx` is replaced by `EditionsManagementSection.tsx` and wired manually at the end of the Info tab body, not via the registry.
- Add `knowledge` entry to the `SECTION_REGISTRY` and to every archetype array. Component = `KnowledgeView` (migrated from the old `/knowledge/page.tsx`).

### 9.4 `OfferInfoTab.tsx`
Renders registry sections in order, then `<EditionsManagementSection />` conditionally:

```tsx
export function OfferInfoTab() {
  const { offer } = useOfferShell();
  const sections = getSectionsForOffer(offer);

  return (
    <div className="px-8 py-5 max-w-5xl space-y-5">
      {sections.map(sectionId => (
        <RegistrySection key={sectionId} id={sectionId} />
      ))}
      {offer.has_editions === true && <EditionsManagementSection />}
    </div>
  );
}
```

---

## 10. WaitlistBanner (unchanged from v1)

Still visible when `current.visibility === PUBLIC && waitlistCount > 0`. Position remains: between `EditionSelectorBar` and tab content.

If `activeTab === 'info'`, the banner renders above the Info sections (still inside the main area, below Row2).

---

## 11. LandingSplitButton (unchanged from v1 — part 2 of Phase 9a still pending)

Keep the spec in v1 `UI-SPEC-offer-studio-shell.md § 5.5`. Wire it in the TabBar row as before.

---

## 12. Implementation checklist (this iteration)

- [ ] Delete `EditionsRail.tsx`, `EditionsRailCollapsed.tsx`, `use-rail-collapsed.ts`.
- [ ] Rewrite `OfferShell.tsx` per § 6.2.
- [ ] Create `EditionSelectorBar.tsx` per § 5.
- [ ] Create `EditionsManagementSection.tsx` per § 7.
- [ ] Create `EditionCard.tsx` (sub-component of EditionsManagementSection) — reuse or refresh existing `editions/EditionCard.tsx`.
- [ ] Modify `OfferShellHeaderRow1.tsx`: remove edition suffix + visibility badge (keep offer-level status).
- [ ] Modify `OfferTabBar.tsx`: 4 tabs (drop Conocimiento).
- [ ] Modify `offer-builder-config.ts`: remove `gallery` and `editions` from archetype arrays; add `knowledge` to every archetype array and to `SECTION_REGISTRY`.
- [ ] Modify `OfferAssetsTab.tsx`: integrate `GalleryManager` + `GalleryPreview` as Zone A.
- [ ] Modify `OfferInfoTab.tsx`: render registry sections then conditional `EditionsManagementSection`.
- [ ] Delete `app/.../offer/[id]/knowledge/page.tsx` route.
- [ ] Wire `openNewEdition` + `openCloneEdition` in shell context; `EditionFormDialog` (existing) replaces the `console.info` stub.
- [ ] Replace `EditionsSection.tsx` (currently in `SECTION_REGISTRY`) with `EditionsManagementSection.tsx`; delete old file.
- [ ] Create hook `use-active-tab.ts` that derives tab id from pathname (for `tabIsEditionScoped` check).
- [ ] Update tests:
  - Remove `editions-rail.test.tsx`, `editions-rail-collapsed.test.tsx`, `use-rail-collapsed.test.ts`.
  - Add `edition-selector-bar.test.tsx` (dropdown + CTA + visibility rule).
  - Add `editions-management-section.test.tsx` (grouped render + empty state + action routing).
  - Update `offer-shell.test.tsx` assertions (no rail).

## 13. Architectural considerations

- `EditionsManagementSection` imports `EditionFormDialog` from the same feature — no cross-feature boundary violation.
- `useOfferShell` context grows by two handlers (`openNewEdition`, `openCloneEdition`) — fine, it's still small.
- Hook `useActiveTab` derives from `usePathname` (no new state), keeping the "no state-in-effect" pattern.
- No new API endpoints needed. All CTAs use existing `editions.*` endpoints + `EditionFormDialog` that already POSTs/PATCHes.

## 14. Out of scope (for clarity)

- `EditionCloneModal` with strategy picker (literal / date_replace / ai_regen) — deferred (D19). `EditionFormDialog` is the interim CTA target.
- Real Puck-based `LandingEditorPage` — stub remains.
- Phase 10 (per-edition analytics) — Growth Studio feature, not Offer Studio.

## 15. References

- Prototype (this iteration): `prototype/offer-studio/offer-info-v2.html`, `offer-ventas-v2.html`, `offer-assets-v2.html`, `offer-campanas-v2.html`.
- Existing dialog to reuse: `frontend/src/features/offer-studio/components/editions/EditionFormDialog.tsx`.
- Backend clone endpoint (for future D19 upgrade): `POST /api/v1/offer/products/{offer_id}/editions/{source_id}/clone`.
