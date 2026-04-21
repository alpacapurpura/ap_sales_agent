# Offer Studio — Frontend Architecture (post-homologation)

**Last updated:** 2026-04-20 (F4-F9 homologation complete)
**Scope:** `frontend/src/features/offer-studio/` + `frontend/src/app/(main)/[tenantId]/(dashboard)/offer-studio/` route tree.
**Backend:** `backend/src/modules/offer/` — catalogs, preset resolution, sections registry. Intocable per offer-studio catalog SSoT rules (see `.claude/rules/offer-catalogs.md`).

## Canonical shape

Offer Studio mirrors brand-studio architecture — any developer opening either studio sees identical folder layout, hook naming, factory pattern, actions registry, route contract.

```
features/offer-studio/
├── actions/
│   ├── __tests__/
│   ├── registry.ts                        # OFFER_STUDIO_ACTION_KEYS + bootstrap
│   ├── placeholders.tsx                   # stub actions pending real wiring
│   └── index.ts
├── api/
│   ├── __tests__/
│   ├── adapter.ts                         # backend ⇄ frontend DTO bridge
│   ├── archetype-catalog-api.ts
│   ├── format-catalog-api.ts
│   ├── value-level-catalog-api.ts
│   └── ...
├── components/                            # FLAT (no subdirs for studio-level shell)
│   ├── __tests__/                         # colocated
│   ├── OfferShellLayout.tsx               # shell mounted once per offer
│   ├── OfferShellHeader.tsx               # row 1 — title + status switcher + kebab
│   ├── OfferStudioNavRail.tsx             # vertical rail — section catalog driven
│   ├── OfferStudioBreadcrumb.tsx
│   ├── OfferStudioTabBar.tsx              # Editor / Editions / Assets / Ventas / Campaigns
│   ├── OfferAutoSaveIndicator.tsx
│   ├── VariantRail.tsx (in variant-rail/) # polymorphic variant entries
│   ├── EditionsManagementClient.tsx
│   ├── GenerateLandingConfirmDialog.tsx
│   ├── LandingActionButton.tsx
│   ├── LandingKebabMenu.tsx
│   ├── OfferStatusChangeModal.tsx
│   ├── OfferStatusSwitcher.tsx
│   ├── OfferStudioBreadcrumb.tsx
│   ├── edition-route.ts                   # URL helpers
│   ├── dashboard/                         # OfferStudioView + cards
│   ├── editions/                          # EditionCard, EditionFormDialog, ...
│   ├── variant-rail/                      # polymorphic rail + entries per structure
│   ├── variant/                           # variant-card templates (TIER, SKU, REGIONAL, ...)
│   ├── assets/
│   ├── campaigns/
│   ├── knowledge/
│   ├── ventas/
│   ├── landing/                           # Puck.js editor blocks
│   ├── social-proof/
│   └── legacy-wizard/                     # Sprint-13 preset-first wizard (renamed from wizard/)
├── hooks/
│   ├── __tests__/
│   ├── use-offer.ts
│   ├── use-offer-settings.ts              # aggregator — updatePromise, updatePricing, ...
│   ├── use-editions.ts
│   ├── use-offer-with-edition.ts
│   ├── use-should-show-variant-rail.ts    # + buildNoVariantRedirect helper
│   ├── use-status-mutation.ts
│   ├── use-archetype-catalog.ts
│   ├── use-format-catalog.ts
│   ├── use-offer-type-preset-catalog.ts
│   ├── use-section-catalog.ts
│   ├── use-variant-structure-catalog.ts
│   └── ...
├── lib/
│   ├── __tests__/
│   ├── section-catalog.ts                 # OFFER_SECTIONS SSoT (icon, label, slug)
│   └── icon-name-resolver.ts
├── pages/
│   ├── __tests__/
│   ├── SectionPage.tsx                    # thin form-runtime wrapper
│   ├── section-pages.tsx                  # factory — createPage<TSlice>
│   └── section-page-map.ts                # { [sectionSlug]: PageComponent }
├── schemas/                               # SectionSchema per section
├── types/
├── utils/
├── __tests__/
│   └── fixtures/                          # shared test fixtures (archetype catalog, offers)
├── index.ts
└── PENDING-REFACTOR.md                    # status log
```

```
app/(main)/[tenantId]/(dashboard)/offer-studio/
├── page.tsx                               # dashboard (ladder)
├── new/page.tsx                           # CreateOfferWizard (preset-first)
└── offer/[id]/
    ├── layout.tsx                         # OfferShellLayout (client, mounts once)
    ├── page.tsx                           # 307 → /editor
    ├── editor/
    │   ├── layout.tsx                     # NavRail + children (brand-studio parity)
    │   ├── page.tsx                       # onboarding landing
    │   └── [section]/
    │       └── [[...fieldId]]/page.tsx    # generic singleton section + field detail
    ├── editor/{testimonials|instructors|faq}/
    │   ├── page.tsx                       # collection landing
    │   └── [id]/[[...fieldId]]/page.tsx   # collection detail
    ├── editions/
    │   ├── page.tsx                       # EditionsManagementClient (polymorphic)
    │   └── [editionId]/page.tsx           # 307 → /editor (legacy)
    ├── assets/page.tsx
    ├── campaigns/page.tsx
    ├── ventas/page.tsx
    └── edition/[code]/[section]/[[...fieldId]]/page.tsx  # legacy 301 redirect shim
                                                          # (retires 2026-05-20)
```

## URL contract

| Route | Behavior |
|---|---|
| `/offer-studio` | Dashboard (ladder) |
| `/offer-studio/new` | Create wizard |
| `/offer-studio/offer/{id}` | 307 → `/editor` |
| `/offer-studio/offer/{id}/editor` | Editor landing (onboarding or first section) |
| `/offer-studio/offer/{id}/editor/{section}` | SectionPage — singleton |
| `/offer-studio/offer/{id}/editor/{section}/{fieldId}` | Field detail — form-runtime |
| `/offer-studio/offer/{id}/editor/{testimonials\|instructors\|faq}` | Collection landing |
| `/offer-studio/offer/{id}/editor/{collection}/{itemId}` | Collection detail |
| `/offer-studio/offer/{id}/editions` | EditionsManagementClient (polymorphic noun by variant_structure) |
| `/offer-studio/offer/{id}/editions/{editionId}` | 307 → `/editor` (dead route, redirects) |
| `/offer-studio/offer/{id}/{assets\|campaigns\|ventas}` | Tab views |
| `/offer-studio/offer/{id}/edition/{code}/{section}/{fieldId?}` | 301 → `/editor/{section}/{fieldId}?edition={code}` — legacy shim (retires 2026-05-20) |
| `/offer-studio/interview` | Deleted — copilot is sidebar, not page (D5) |

Edition context lives in **UI state + `?edition={code}` query param**, never as URL segment (D6).

## Single sources of truth

| Concern | Source | Consumer |
|---|---|---|
| Section metadata (icon, label, slug) | `lib/section-catalog.ts` | `OfferStudioNavRail`, `section-page-map` |
| Action kinds (text, picker, builder, ...) | `actions/registry.ts` | `bootstrapOfferStudioActions()`, form-runtime |
| Section → schema | `schemas/index.ts` → `OFFER_SCHEMA_REGISTRY` | `section-pages.tsx` factory |
| Archetype / format / value-level / preset / variant-structure catalogs | Backend (see `.claude/rules/offer-catalogs.md`) | Typed React Query hooks |
| Copilot section tools (17 tools) | Backend `offer_section_tools.py` | Global copilot orchestrator (`tools/registry.py` group `offer_studio`) |

## Shell composition

```
<OfferShellLayout>                         # app/.../offer/[id]/layout.tsx
  <Topbar>                                 # <OfferStudioBreadcrumb />
  <OfferShellHeader>                       # title + status switcher + kebab + autosave
  <div>
    {showVariantRail ? <VariantRail /> : null}
    <div>
      <OfferStudioTabBar />                # Info / Ventas / Assets / Campañas
      <main>{children}</main>              # route-level page
    </div>
  </div>
  <EditionFormDialog />
</OfferShellLayout>

<OfferEditorLayout>                        # app/.../offer/[id]/editor/layout.tsx — scoped to Info tab
  <OfferStudioNavRail />                   # section column (260px) — brand-studio parity
  <div>{children}</div>                    # SectionPage contributes FinderColumn + FieldDetail
</OfferEditorLayout>
```

The `editor/layout.tsx` sub-layout gives the editor the canonical **3-column Finder** of brand-studio (sections rail → field list → field detail) while Ventas / Assets / Campañas tabs render directly under the shell without the rail. `OfferStudioNavRail` is self-contained — reads `tenantId` + `id` from URL params, fetches the offer via `useOffer` (React Query de-duped with the shell query).

No React Context providers — children consume `useOffer`, `useOfferCounts`, `useEditions`, `useShouldShowVariantRail`, `useOfferWithEdition`, etc. directly from React Query (`.claude/rules/frontend-fsd.md` — per-route state in URL + React Query).

## Copilot integration

The 17 section tools in `backend/src/modules/copilot/application/tools/offer_section_tools.py` are registered under `tools/registry.py` group `offer_studio` and reached from the **global copilot orchestrator** (chat/sidebar owned by the `copilot` module), not an embedded per-section panel. The offer-studio SectionPage is a pure 2-column form editor, identical to brand-studio.

An earlier experiment (F7.2) wired a per-section `OfferSectionCopilot` sidebar + REST endpoint `POST /copilot/offer-section-tools/{tool_key}`. It was reverted — it broke visual parity with brand-studio and duplicated the copilot module with hardcoded tool cards.

## Variant structures (polymorphic)

`VariantCollectionLandingPage` + `VariantCard` dispatch template by `meta.cardTemplate` (from `variant-structure-catalog.ts`):

| `variant_structure` | Noun | Card template |
|---|---|---|
| `TIER` | Planes | `TierVariantCard` |
| `SKU_VARIANT` | Variantes | `SkuVariantCard` |
| `REGIONAL` | Regiones | `RegionalVariantCard` |
| `MODALITY` | Modalidades | `ModalityVariantCard` |
| `LANGUAGE` | Idiomas | `LanguageVariantCard` |
| `TEMPORAL_COHORT` | Cohortes | Temporal `EditionCard` |
| `TEMPORAL_SINGLE_DATE` | Salidas | Temporal `EditionCard` |
| `RECURRING_INTAKE` | Convocatorias | Temporal `EditionCard` |

Single-variant lead-magnets (`archetype.allow_single_variant=true` + `variants.length=1`) hide VariantRail + Editions tab — `useShouldShowVariantRail` returns `false` + `/editions` redirects to `/editor` via `buildNoVariantRedirect`.

## Test layout (post-F5)

| Dir | Covers |
|---|---|
| `api/__tests__/` | adapter bridge + response shape |
| `components/__tests__/` | shell components (OfferShellLayout, OfferShellHeader, TabBar, ...) |
| `components/dashboard/__tests__/` | ladder progress, offer cards, stream cards, studio view |
| `components/editions/__tests__/` | edition-pricing-override, form dialog |
| `components/variant/__tests__/` | polymorphic cards |
| `components/variant-rail/__tests__/` | rail entries |
| `hooks/__tests__/` | `use-offer-settings`, archetype / preset / section catalog, `use-should-show-variant-rail`, ... |
| `utils/__tests__/` | ladder-completeness, section-helpers |
| `lib/__tests__/` | section-catalog, icon-name-resolver |
| `pages/__tests__/` | SectionPage, section-pages factory, field-routing |
| `schemas/__tests__/` | schema-level invariants |
| `__tests__/fixtures/` | shared fixtures (MOCK_BACKEND_RESPONSE, archetype-catalog) |

E2E (Playwright) — `frontend/e2e/`:

- `specs/smoke/offer-studio-homologation.smoke.spec.ts` — Journey A (crear), Journey E (lead-magnet no variant), Journey F (TEMPORAL_COHORT variant switch).
- `specs/regression/offer-variants-polymorphic.regression.spec.ts` — one test per `variant_structure`.
- `fixtures/offer-studio.fixture.ts` — per-structure mock factories.
- `pages/offer-studio.page.ts` — POM.

## Arch fitness (frontend)

Run: `cd frontend && npx vitest run src/__tests__/architecture/`

Gates that constrain offer-studio:
- `test-component-naming.test.ts` — PascalCase components
- `test-file-naming.test.ts` — kebab-case non-component files
- `test-folder-naming.test.ts` — kebab-case directories (except `__tests__` / `__mocks__`)
- `test-hook-location.test.ts` — hooks only in `hooks/` / `api/` / `context/`
- `test-no-default-exports.test.ts` — no `export default` in features/
- `test-no-duplicate-names.test.ts` — no same-name components across features
- `test-feature-structure.test.ts` — canonical top-level dirs (+ offer-studio allow `schemas`, `actions`, `pages`)
- `test-api-location.test.ts` — `fetchClient` calls only in `api/`
- `test-no-catalog-duplicates.test.ts` — no `ARCHETYPE_METADATA` / `FORMAT_PRESETS` / `LEVEL_RICH_INFO` / `VALUE_LEVEL_LABELS` / `SECTION_METADATA` / `getSectionsForOffer` duplicates (catalogs consumed via backend hooks only).
- `test-section-key-backend-alignment.test.ts` — frontend `OFFER_SCHEMA_REGISTRY` keys match backend `SectionKey` enum.
- `test-no-section-schema-duplicates.test.ts` — schemas omit `title`/`description` (catalog-driven).

All allowlists are ratchet — they may only shrink.

## Intentional divergences from brand-studio

- **Editions dimension** — offer-studio has `VariantRail` + `Editions` tab; brand-studio has no per-brand variants (D1).
- **Preset-driven sections** — backend resolver (`resolve_preset_sections`) returns the effective section list per offer based on `preset_id` + `conditional_answers`. Brand-studio has a fixed section set (D2).

## History

Phase-by-phase commits in `PENDING-REFACTOR.md`. Session spec + decisions in `docs/ux-sessions/2026-04-20-offer-studio-homologation/`.
