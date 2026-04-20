# FLOW-SPEC — Offer Studio Homologation (Brand Studio parity)

**Session:** `2026-04-20-offer-studio-homologation`
**Scope:** Studio-scoped — refactor `features/offer-studio/` frontend to adopt brand-studio architecture, styling, and navigation conventions. Extend with persistent copilot sidebar per section.
**Backend:** Out of scope. Preset catalog (`offer_type_preset_catalog.py`, `resolvePresetSections`, `preset_id` column, Sprint 12–14 arch tests) is intocable.

---

## 1. Audit Summary (quantitative)

| Metric | Current | Target |
|---|---|---|
| Route deep-link pattern | ✅ Present (`/offer/[id]/edition/[code]/[section]/[[...fieldId]]`) | Kept + canonical |
| Form-runtime usage | Mixed (factory + legacy `*Form.tsx`) | 100% `SectionPage` factory |
| Shell layout | Modal sheet (`OfferEditSheetManager`) | 3-col split: Nav / Form / Copilot |
| Section catalog SSoT | Missing (split across `config/offer-builder-config.ts`) | `lib/section-catalog.ts` |
| Field-routing hook | Missing | `useOfferStudioFieldRouting` |
| Copilot in edition | Only at creation (dashboard) | Persistent per section |
| Sub-folder count | 12 sub-dirs | 6 sub-dirs (flat + legitimate sub-domains) |
| Dead-code weight | `OfferShell`, `OfferShellContext`, `OfferSectionWrapper`, `OfferEditSheetManager`, `OfferEditorContent`, `config/*` | Deleted |

---

## 2. Navigation Map

### Sidebar (Nicolify global — unchanged)

```
Nicolify
├── Dashboard
├── ✦ Brand Studio           → /{tenantId}/brand-studio/identity
├── ☰ Offer Studio           → /{tenantId}/offer-studio
├── ↗ Growth Studio          → /{tenantId}/growth-studio
├── ◉ Sales Studio           → /{tenantId}/sales
├── ⚙ Settings              → /{tenantId}/settings
└── 🔌 Conexiones            → /{tenantId}/connections
```

### Offer Studio internal routes (target)

```
/{tenantId}/offer-studio                                               ← OfferStudioDashboardPage (ladder)
/{tenantId}/offer-studio/new                                           ← CreateOfferWizardPage (preset-first, steps 1-3)
/{tenantId}/offer-studio/offer/[id]                                    ← OfferDetailPage (shell default / editor)
/{tenantId}/offer-studio/offer/[id]/layout.tsx                         ← OfferShellLayout (tabs + editions rail)
/{tenantId}/offer-studio/offer/[id]/editor                             ← EditorRoutePage (landing / first section)
/{tenantId}/offer-studio/offer/[id]/editor/[section]/[[...fieldId]]    ← Generic SectionPage + field detail
/{tenantId}/offer-studio/offer/[id]/editor/testimonials                ← Collection landing (list)
/{tenantId}/offer-studio/offer/[id]/editor/testimonials/[testimonialId]/[[...fieldId]]  ← Collection detail
/{tenantId}/offer-studio/offer/[id]/editor/instructors                 ← Collection (same pattern)
/{tenantId}/offer-studio/offer/[id]/editor/faq                         ← Collection (same pattern)
/{tenantId}/offer-studio/offer/[id]/editions                           ← EditionsTabPage
/{tenantId}/offer-studio/offer/[id]/editions/[editionId]               ← EditionDetailPage (edit override fields)
/{tenantId}/offer-studio/offer/[id]/assets                             ← AssetsTabPage
/{tenantId}/offer-studio/offer/[id]/knowledge                          ← KnowledgeTabPage
/{tenantId}/offer-studio/offer/[id]/campaigns                          ← CampaignsTabPage
/{tenantId}/offer-studio/offer/[id]/ventas                             ← VentasTabPage
```

**Deletion vs current:** remove `/offer-studio/interview` standalone route — copilot interview lives inside shell as sidebar (not standalone page).

### Current → target route diff

| Current | Target | Change |
|---|---|---|
| `/offer-studio/offer/[id]/edition/[code]/[section]/[[...fieldId]]` | `/offer-studio/offer/[id]/editor/[section]/[[...fieldId]]` | Drop `edition/[code]` from URL — edition is ephemeral UI state (tab + chip), not URL segment. Reduces URL noise; edition switching stays in EditionsRail. |
| `/offer-studio/offer/[id]/editions/[editionId]/landing` | `/offer-studio/offer/[id]/editions/[editionId]` | Landing preview is section inside edition detail, not separate page. |
| `/offer-studio/offer/[id]/editions/[editionId]/assets` | `/offer-studio/offer/[id]/assets` + edition filter | Assets belong to offer, not edition. Use edition chip as filter. |
| `/offer-studio/interview` | deleted | Copilot is sidebar, not page. |

---

## 3. Journey Maps

### Journey A — Crear oferta nueva

```
[Dashboard] ✅
    │  click "+ Nueva oferta"
    ▼
[Wizard Step 1: PresetPicker] ✅
    │  useTenantProfile().business_types filtra presets
    │  usuario elige preset (ej: "salud_paquete_tratamiento")
    ▼
[Wizard Step 2: ConditionalQuestions] ✅
    │  1-3 preguntas condicionales del preset
    │  resolvePresetSections(preset, questions, answers) resuelve sections efectivas
    ▼
[POST /offer → crea preset_id + conditional_answers + archetype derivado] ✅
    ▼
[Editor shell — estado onboarding] ✅
    │  CopilotSidebar sugiere: "Inicia entrevista" + "Adaptar desde Brand" + flags
    │  usuario puede (a) entrevista guiada (b) click section en NavRail
    ▼
[Section by section] ✅
    │  UniversalEditableSection + schemas/{section}.schema.ts + actions registry
    │  Copilot side-bar específico de section
    ▼
[Publicar] ✅
```

### Journey B — Editar section singleton

```
[Dashboard] → click offer card
    ▼
[Offer detail — tab Editor] ✅ (default tab)
    │  NavRail muestra sections resueltas por preset
    │  Copilot sidebar muestra salud global de sections
    ▼
[Click section en NavRail — ej "Promesa"] ✅
    │  URL: /offer-studio/offer/{id}/editor/promise
    │  SectionPage + promiseSchema + useOfferSettings().updatePromise
    ▼
[Click field card — ej "Promesa central"] ✅
    │  URL: /offer-studio/offer/{id}/editor/promise/central_promise
    │  Detail view con form, copilot sugiere reescrituras/coherencia
    ▼
[Save → React Query mutation → backend persist → cache invalidate] ✅
```

### Journey C — Gestionar editions

```
[Offer detail] → click tab "Editions" ✅
    ▼
[EditionsTabPage — lista 3 editions (Default active, Q2-2026 draft, VIP draft)]
    │  cada edition con: nombre, código, pricing override, fechas, cupos
    ▼
[Click "Duplicar" en Default]
    ▼
[Nuevo draft creado — chip aparece en EditionsRail]
    ▼
[Click chip en rail → switch activo]
    │  URL sigue siendo /editor/promise pero EditionsRail marca edition activa
    │  editar field = CREA override para esa edition (no toca Default)
    ▼
[Tab Editions → click "Publicar"]
    ▼
[Landing de esa edition deploya + sales-agent lee edition por query param]
```

### Journey D — Copilot-assisted section fill

```
[Usuario abre section "Pricing"] ✅
    ▼
[Copilot detecta flag preset.HIGH_TICKET] ✅
    │  suggestion-card: "3-tier con anclaje → +34% conversión tier medio"
    ▼
[Click "Aplicar plantilla"] ✅
    │  Copilot invoca tool POST /copilot/tools/offer-pricing-tier-apply
    │  tool retorna draft fields → form-runtime actualiza valores (pendientes de save)
    ▼
[Usuario ajusta números → Save] ✅
    │  mutation persiste, copilot valida coherencia y marca ✓ en sidebar
    ▼
[Copilot detecta siguiente acción] ✅
    │  "Edition Q2 tiene override. ¿Revisar?" → click = navega a tab Editions
```

---

## 4. Gap Analysis

### Orphaned components (delete)
| Component | Current role | Replacement |
|---|---|---|
| `components/editor/OfferEditSheetManager.tsx` | Modal sheet wrapper | `pages/SectionPage.tsx` (split-view route) |
| `components/editor/OfferEditorContent.tsx` | Orchestrator | `pages/section-pages.tsx` factory |
| `components/editor/OfferSectionWrapper.tsx` | Presentational wrapper | `UniversalEditableSection` layout handles it |
| `components/container/OfferShell.tsx` | Shell state | `app/.../offer/[id]/layout.tsx` + React Query |
| `context/OfferShellContext.tsx` | Global edit state | Per-route state — URL + React Query only |
| `config/offer-builder-config.ts` | Form component registry | `actions/registry.ts` (`bootstrapOfferStudioActions`) |
| `app/.../offer-studio/interview/page.tsx` | Standalone copilot interview | Copilot is sidebar in editor shell |

### Missing connections (create)
| Gap | Solution |
|---|---|
| No SectionPage wrapper | Create `pages/SectionPage.tsx` (copy brand pattern) |
| No section-pages factory | Create `pages/section-pages.tsx` with `createPage<TSlice>({slug, schema, select, save})` |
| No field-routing hook | Create `hooks/use-field-routing.ts` → `useOfferStudioFieldRouting` |
| No section catalog SSoT | Create `lib/section-catalog.ts` (OFFER_SECTIONS metadata) |
| No aggregator hook (save flows) | Create `hooks/use-offer-settings.ts` → exposes `updatePromise`, `updatePricing`, etc. per section |
| No copilot slot in form-runtime | Extend `UniversalEditableSection` with optional `copilotSlot?: ReactNode` prop (non-breaking) |
| No section-scoped copilot tools | Create `backend/src/modules/copilot/tools/offer_section_tools.py` with per-section tool bindings |

### Architecture issues (fix)
| Issue | Fix |
|---|---|
| Mixed legacy `*Form.tsx` + schemas | Port all to `SectionSchema` + actions. Delete hand-rolled forms. |
| Fragmented `components/` (12 sub-dirs) | Flatten to 6: `dashboard/`, `editions/`, `assets/`, `knowledge/`, `ventas/`, `campaigns/`, `social-proof/`, `legacy-wizard/`. Root-level shared components (NavRail, Breadcrumb, InstancePickers). |
| Tests at `tests/` top-level | Move to `__tests__/` colocated per feature. |
| URL includes `edition/[code]` segment | Remove; edition = UI state (chip + React Query param). |

---

## 5. Proposed Changes

### 5.1 Folder structure target

```
features/offer-studio/
├── actions/
│   ├── __tests__/
│   ├── stories/
│   ├── SocialProofPickerAction.tsx       (from components/social-proof/*)
│   ├── InstructorsPickerAction.tsx       (new — consume brand team)
│   ├── PaymentProviderPickerAction.tsx   (new — consume connections)
│   ├── SchedulingEventTypePickerAction.tsx (new)
│   ├── ValueStackBuilderAction.tsx       (from editor/sections)
│   ├── FAQBuilderAction.tsx              (from editor/sections)
│   ├── EditionPricingOverrideAction.tsx  (from components/editions/EditionPricingOverride)
│   ├── GalleryPickerAction.tsx
│   ├── placeholders.tsx
│   ├── registry.ts                        ← bootstrapOfferStudioActions()
│   └── index.ts
├── api/                                   (unchanged — already OK)
├── components/
│   ├── __tests__/
│   ├── OfferStudioNavRail.tsx             (flat — from navigation/OfferNavRail)
│   ├── OfferStudioBreadcrumb.tsx          (flat)
│   ├── OfferStudioTabBar.tsx              (flat — from container/OfferTabBar)
│   ├── EditionsRail.tsx                   (flat — from container/)
│   ├── EditionsRailCollapsed.tsx
│   ├── OfferLivePreview.tsx               (kept — viewer only)
│   ├── OfferSectionCopilot.tsx            (NEW — copilot slot component)
│   ├── dashboard/
│   ├── editions/
│   ├── assets/
│   ├── knowledge/
│   ├── ventas/
│   ├── campaigns/
│   ├── social-proof/
│   └── legacy-wizard/                     (from wizard/ — rename prefix like brand's legacy-team/)
├── hooks/
│   ├── __tests__/
│   ├── use-field-routing.ts               (NEW — useOfferStudioFieldRouting)
│   ├── use-offer-settings.ts              (NEW — aggregator hook)
│   ├── use-offer-copilot.ts               (NEW — section-scoped copilot session)
│   └── (existing hooks kept)
├── lib/
│   ├── __tests__/
│   ├── section-catalog.ts                 (NEW — OFFER_SECTIONS metadata SSoT)
│   └── icon-name-resolver.ts              (existing)
├── pages/
│   ├── stories/
│   ├── __tests__/
│   ├── SectionPage.tsx                    (NEW — thin form-runtime wrapper)
│   ├── section-pages.tsx                  (NEW — createPage<TSlice> factory)
│   ├── section-page-map.ts                (existing — update to import from section-pages)
│   ├── CollectionLandingPage.tsx          (NEW — for testimonials/instructors/faq)
│   ├── CollectionDetailPage.tsx           (NEW)
│   ├── EditionDetailPage.tsx              (NEW — edit edition overrides)
│   └── index.ts
├── schemas/                               (unchanged — all SectionSchema already)
├── types/
└── utils/

DELETED:
├── config/                                ✗
├── context/                               ✗
├── components/container/OfferShell.tsx    ✗
├── components/container/OfferShellHeaderRow1.tsx  ✗
├── components/editor/                     ✗ (all 4 files)
├── tests/                                 ✗ (moved to __tests__/)
```

### 5.2 App route structure target

```
frontend/src/app/(main)/[tenantId]/(dashboard)/offer-studio/
├── page.tsx                               ← OfferStudioDashboard
├── new/
│   └── page.tsx                           ← CreateOfferWizardPage
└── offer/[id]/
    ├── layout.tsx                         ← OfferShellLayout (tabs + EditionsRail)
    ├── page.tsx                           ← redirect → editor
    ├── editor/
    │   ├── page.tsx                       ← OnboardingOrFirstSection (default landing)
    │   └── [section]/
    │       └── [[...fieldId]]/page.tsx    ← generic singleton section + field detail
    ├── editor/testimonials/
    │   ├── page.tsx                       ← CollectionLandingPage(testimonials)
    │   └── [testimonialId]/[[...fieldId]]/page.tsx  ← CollectionDetailPage
    ├── editor/instructors/
    │   ├── page.tsx                       ← CollectionLandingPage(instructors)
    │   └── [instructorId]/[[...fieldId]]/page.tsx
    ├── editor/faq/
    │   ├── page.tsx
    │   └── [faqId]/[[...fieldId]]/page.tsx
    ├── editions/
    │   ├── page.tsx                       ← EditionsTabPage
    │   └── [editionId]/page.tsx           ← EditionDetailPage
    ├── assets/page.tsx
    ├── knowledge/page.tsx
    ├── campaigns/page.tsx
    └── ventas/page.tsx
```

**Brand-studio parity note:** brand uses `/brand-studio/[section]/[[...fieldId]]` as generic route + dedicated routes for collections (`/team`, `/authority`, `/testimonials`, `/publico`). Offer mirrors this: generic `/editor/[section]/[[...fieldId]]` + dedicated `/editor/testimonials`, `/editor/instructors`, `/editor/faq` for collections.

### 5.3 Component composition (tree)

```
<OfferShellLayout>                           ← app/.../offer/[id]/layout.tsx
  <AppSidebar/>                              ← global Nicolify nav
  <main>
    <Topbar>                                 ← breadcrumb + status + actions
    <OfferStudioTabBar active="editor" />    ← Editor / Editions / Assets / ...
    <EditionsRail />                         ← chips (only rendered in Editor + Editions tabs)
    <OfferEditorShell>                       ← grid 3-col
      <OfferStudioNavRail sections={resolvedSections} />
      <SectionPage
         sectionSlug
         schema
         values
         onSave
         copilotSlot={<OfferSectionCopilot sectionSlug offerId />}
      />
        └── <UniversalEditableSection ...> (form-runtime, extended with copilotSlot)
      {copilotSlot}                          ← rendered inside UniversalEditableSection
    </OfferEditorShell>
  </main>
</OfferShellLayout>
```

---

## 6. New Components

| Component | File | Role |
|---|---|---|
| `OfferStudioNavRail` | `components/OfferStudioNavRail.tsx` | FinderColumn clone. Consumes `OFFER_SECTIONS` + `useSectionsForArchetype`. |
| `OfferStudioBreadcrumb` | `components/OfferStudioBreadcrumb.tsx` | Mirrors `BrandStudioBreadcrumb`. |
| `OfferSectionCopilot` | `components/OfferSectionCopilot.tsx` | Copilot sidebar per section. Consumes `useCopilotStore` + `useOfferCopilot(sectionSlug, offerId)`. |
| `SectionPage<TSlice>` | `pages/SectionPage.tsx` | Thin form-runtime wrapper. |
| `CollectionLandingPage` | `pages/CollectionLandingPage.tsx` | List view for collection sections (testimonials, instructors, faq). |
| `CollectionDetailPage` | `pages/CollectionDetailPage.tsx` | Detail edit for collection item. |
| `EditionDetailPage` | `pages/EditionDetailPage.tsx` | Edit edition overrides (pricing, dates, capacity). |

---

## 7. States per screen

| Screen | Loading | Empty | Error | Filled |
|---|---|---|---|---|
| **Dashboard (ladder)** | Skeleton rows per level (3 rows × 3 cards) | Empty state: "Aún no tienes ofertas" + CTA "Crear primera oferta" | Toast + retry button | Grid of offer cards per preset level |
| **Wizard Step 1** | Preset grid skeleton (6 cards) | N/A (business_types gating guarantees non-empty) | Fallback: text list of all presets | Filtered grid |
| **Wizard Step 2** | "Resolviendo sections..." spinner | N/A | Fallback: skip to Step 3 with default sections | Conditional questions + live section badges |
| **Offer Editor (default)** | Shell skeleton | Onboarding card ("Tu oferta se creó") + copilot suggestion | Error card | Redirect to first section if progress > 0 |
| **Section Page (singleton)** | Form card skeletons (3) | All empty fields visible with "empty" badge | Inline error per field | Form-runtime `UniversalEditableSection` |
| **Section Field Detail** | Single form skeleton | N/A (field exists by definition) | Inline error | Active field highlighted + form-runtime action |
| **Collection Landing** | Card grid skeleton | Empty state: "Aún no tienes testimonios" + "Importar desde Brand Vault" + "+ Nuevo" | Toast | Grid of collection cards + `+` card |
| **Collection Detail** | Form skeleton | N/A | Inline | Form-runtime |
| **Editions Tab** | List skeleton | "Solo tienes la edition Default" + explainer | Toast | List of editions + explainer callout |
| **Assets / Knowledge / Campaigns / Ventas** | Delegated to existing components | per-component | per-component | per-component |

---

## 8. Responsive behavior

| Breakpoint | Layout |
|---|---|
| ≥ 1440px (desktop wide) | 3-col: 260 / fluid / 340 (copilot) |
| 1024–1439px (desktop) | 3-col: 240 / fluid / 320 |
| 768–1023px (tablet) | 2-col: 240 / fluid. Copilot collapsed to 48px rail — click to overlay |
| < 768px (mobile) | 1-col stacked. NavRail → drawer (hamburger). Copilot → bottom sheet |

---

## 9. Interaction patterns

| Pattern | Behavior |
|---|---|
| **Click section in NavRail** | `router.push(getFieldHref(null))` — URL updates, page transitions via route |
| **Click field card** | `router.push(getFieldHref(fieldId))` — loads detail view |
| **Hover section row** | `bg-muted/60` background, no cursor change (link behavior) |
| **Active section** | `border-left-color: var(--brand)` accent + `bg-brand/10` |
| **Keyboard nav** | `Tab` cycles fields; `Enter` saves active field; `Esc` closes field detail |
| **Copilot collapse toggle** | Local state in `OfferShellLayout`; persists to localStorage `offer-studio:copilot-collapsed` |
| **Edition chip click** | Updates React Query param `?edition={code}` — no URL hard change |
| **Save field** | Optimistic update + React Query mutation. Shows auto-save indicator in topbar |
| **Unsaved changes** | Prompt on navigate-away (`useBeforeUnload`) |

---

## 10. Copilot integration points (per section)

| Section | Copilot tools (backend: `offer_section_tools.py`) |
|---|---|
| **Identity** | `adapt_from_brand_identity` (lee `brand-studio/identity`) |
| **Promise** | `adapt_from_brand_narrative`, `rewrite_tones` (3 variants from Brand Voice), `validate_preset_coherence` |
| **Audience** | `reuse_brand_buyer_personas` (importa de brand-studio/publico) |
| **Methodology** | `inherit_brand_methodology` |
| **Pricing** | `high_ticket_tiering_template` (trigger: flag HIGH_TICKET), `recurring_billing_setup` (flag RECURRING_BILLING), `detect_currency_mismatch` |
| **Schedule** | `import_scheduling_event_type` (requires connection) |
| **Location** | `detect_hybrid_split` |
| **Testimonials** | `import_from_brand_vault`, `suggest_missing_objections`, `auto_transcribe_video` |
| **FAQ** | `generate_from_preset_flags`, `pull_sales_agent_common_questions` |
| **Value stack** | `assemble_from_brand_authority` |
| **Instructors** | `reuse_brand_team` (brand-studio/team) |

All tools follow existing `copilot` module contract (`POST /copilot/tools/{tool_key}` with `entity_type="offer-section"`, `context={offerId, sectionSlug, editionCode?}`).

---

## 11. File changes required

### Delete
```
frontend/src/features/offer-studio/config/offer-builder-config.ts
frontend/src/features/offer-studio/context/OfferShellContext.tsx
frontend/src/features/offer-studio/context/                        (empty dir)
frontend/src/features/offer-studio/components/container/OfferShell.tsx
frontend/src/features/offer-studio/components/container/OfferShellHeaderRow1.tsx
frontend/src/features/offer-studio/components/editor/OfferEditSheetManager.tsx
frontend/src/features/offer-studio/components/editor/OfferEditorContent.tsx
frontend/src/features/offer-studio/components/editor/OfferSectionWrapper.tsx
frontend/src/features/offer-studio/components/navigation/                (rename below)
frontend/src/app/(main)/[tenantId]/(dashboard)/offer-studio/interview/  (entire dir)
```

### Rename / move
```
components/navigation/OfferNavRail.tsx → components/OfferStudioNavRail.tsx (flat)
components/container/OfferTabBar.tsx → components/OfferStudioTabBar.tsx (flat)
components/container/EditionsRail.tsx → components/EditionsRail.tsx (flat)
components/container/EditionsRailCollapsed.tsx → components/EditionsRailCollapsed.tsx (flat)
components/container/AutoSaveIndicator.tsx → components/OfferAutoSaveIndicator.tsx (flat)
components/wizard/ → components/legacy-wizard/
components/editor/OfferLivePreview.tsx → components/OfferLivePreview.tsx (flat)
tests/ → distributed to __tests__/ colocated with features
```

### Create
```
features/offer-studio/lib/section-catalog.ts
features/offer-studio/hooks/use-field-routing.ts
features/offer-studio/hooks/use-offer-settings.ts
features/offer-studio/hooks/use-offer-copilot.ts
features/offer-studio/pages/SectionPage.tsx
features/offer-studio/pages/section-pages.tsx
features/offer-studio/pages/CollectionLandingPage.tsx
features/offer-studio/pages/CollectionDetailPage.tsx
features/offer-studio/pages/EditionDetailPage.tsx
features/offer-studio/components/OfferStudioNavRail.tsx
features/offer-studio/components/OfferStudioBreadcrumb.tsx
features/offer-studio/components/OfferSectionCopilot.tsx
features/offer-studio/actions/SocialProofPickerAction.tsx
features/offer-studio/actions/InstructorsPickerAction.tsx
features/offer-studio/actions/PaymentProviderPickerAction.tsx
features/offer-studio/actions/SchedulingEventTypePickerAction.tsx
features/offer-studio/actions/ValueStackBuilderAction.tsx
features/offer-studio/actions/FAQBuilderAction.tsx
features/offer-studio/actions/EditionPricingOverrideAction.tsx
features/offer-studio/actions/GalleryPickerAction.tsx
features/offer-studio/actions/placeholders.tsx
(update) features/offer-studio/actions/registry.ts — bootstrapOfferStudioActions()

src/components/form-runtime/UniversalEditableSection.tsx — add optional copilotSlot prop

(app routes — rewrite)
app/(main)/[tenantId]/(dashboard)/offer-studio/new/page.tsx
app/(main)/[tenantId]/(dashboard)/offer-studio/offer/[id]/editor/page.tsx
app/(main)/[tenantId]/(dashboard)/offer-studio/offer/[id]/editor/[section]/[[...fieldId]]/page.tsx
app/(main)/[tenantId]/(dashboard)/offer-studio/offer/[id]/editor/testimonials/page.tsx
app/(main)/[tenantId]/(dashboard)/offer-studio/offer/[id]/editor/testimonials/[testimonialId]/[[...fieldId]]/page.tsx
app/(main)/[tenantId]/(dashboard)/offer-studio/offer/[id]/editor/instructors/page.tsx
app/(main)/[tenantId]/(dashboard)/offer-studio/offer/[id]/editor/instructors/[instructorId]/[[...fieldId]]/page.tsx
app/(main)/[tenantId]/(dashboard)/offer-studio/offer/[id]/editor/faq/page.tsx
app/(main)/[tenantId]/(dashboard)/offer-studio/offer/[id]/editor/faq/[faqId]/[[...fieldId]]/page.tsx

(backend — new)
backend/src/modules/copilot/tools/offer_section_tools.py
```

### Update (minor)
```
frontend/src/components/shared/layout/AppSidebar.tsx — (no change — already points to /offer-studio)
frontend/src/features/offer-studio/schemas/index.ts — side-effect import of actions/registry.ts
frontend/src/features/offer-studio/index.ts — re-exports
frontend/src/features/offer-studio/pages/section-page-map.ts — point to new section-pages.tsx
```

---

## 12. Backend touch points (NOT intocable — minor additions only)

| File | Change |
|---|---|
| `backend/src/modules/copilot/tools/offer_section_tools.py` | NEW — 11 tool functions (one per section, see §10) |
| `backend/src/modules/copilot/tools/registry.py` | Register new tools under `entity_type="offer-section"` |
| Existing offer catalogs, `preset_id`, `resolve_preset_sections`, arch tests | **INTOCABLE** ✓ |

---

## 13. Prototype reference

Served on `http://localhost:8888/` from `prototype/`.

**Files:**
- `index.html` — hub (links to all screens)
- `compare.html` — brand vs offer side-by-side
- `offer-studio/dashboard.html` — Journey A step 1
- `offer-studio/wizard-step1.html` — Journey A step 2 (preset picker)
- `offer-studio/wizard-step2.html` — Journey A step 3 (conditional questions)
- `offer-studio/offer-editor.html` — Journey A step 4 (editor shell onboarding)
- `offer-studio/section-promise.html` — Journey B (singleton section list)
- `offer-studio/section-promise-field.html` — Journey B + Journey D (field detail + copilot reescrituras)
- `offer-studio/section-pricing.html` — Journey D (HIGH_TICKET tiering)
- `offer-studio/collection-testimonials.html` — Journey B' (collection landing)
- `offer-studio/collection-testimonial-detail.html` — Journey B' (collection detail)
- `offer-studio/offer-editions.html` — Journey C (editions management)

---

## 14. Acceptance criteria

- [ ] `features/offer-studio/` structure matches §5.1 exactly — 6 top-level dirs, flat components, legacy-wizard/ prefix.
- [ ] All 11 sections route through `SectionPage<TSlice>` factory. No standalone `*Form.tsx` components remain in `components/editor/sections/`.
- [ ] `lib/section-catalog.ts` exists with `OFFER_SECTIONS` readonly tuple + `getOfferSection()` + `getOfferSectionLabel()`.
- [ ] `hooks/use-field-routing.ts` exports `useOfferStudioFieldRouting(section: string): FieldRouting`.
- [ ] `actions/registry.ts` exports `OFFER_STUDIO_ACTION_KEYS` + `bootstrapOfferStudioActions()`. Side-effect registered via `schemas/index.ts`.
- [ ] `UniversalEditableSection` accepts `copilotSlot?: ReactNode` — brand-studio pages still compile without it.
- [ ] App routes match §5.2. `/offer-studio/interview` route deleted.
- [ ] Arch fitness tests all green (DDD + naming + no-default-exports).
- [ ] Frontend arch tests pass: PascalCase components, kebab-case files, canonical feature structure.
- [ ] E2E smoke: create offer → wizard → editor → save one section → verify persisted.
