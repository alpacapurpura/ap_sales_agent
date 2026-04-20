# Offer Studio — Pending Refactor (Sprint 15.1 → future sprints)

Sprint 15.1 landed the **foundations** for full brand-studio homologation:
- Backend variant catalog extension (MEMBRESIA → TIER, PRODUCTO → SKU_VARIANT).
- Frontend type mirrors, `lib/section-catalog.ts`, `lib/variant-structure-catalog.ts`.
- `SectionPage` thin wrapper + `useOfferStudioFieldRouting` hook.
- `UniversalEditableSection` gained optional `copilotSlot` prop (non-breaking).
- Polymorphic `VariantCard` + `VariantCollectionLandingPage` covering 8 structures.

What remains (migration, not foundation) — each item is a **safe incremental refactor**, none of them blocks usage:

## Layer A — Legacy shell / editor retirement

| Path | Action | Why | Blocked by |
|---|---|---|---|
| `components/editor/OfferEditSheetManager.tsx` | Delete | Modal sheet pattern — replaced by `SectionPage` split-view deep-link | Route migration to `/editor/[section]/[[...fieldId]]` using `SectionPage` factory |
| `components/editor/OfferSectionWrapper.tsx` | Delete | Unused wrapper — `UniversalEditableSection` handles layout | After removing last consumer (`OfferLivePreview`) |
| `components/editor/OfferEditorContent.tsx` | Delete | Orchestrator replaced by `pages/section-pages.tsx` factory | Routes migrated |
| `components/editor/OfferLivePreview.tsx` | Audit | Still referenced; decide: keep for preview-only OR delete | — |
| `context/OfferShellContext.tsx` | Delete | State fits URL + React Query; no real global state needed | Components migrated off context |
| `components/container/OfferShell.tsx` | Delete | Replace by thin `app/.../offer/[id]/layout.tsx` | All consumers migrated |
| `components/container/OfferShellHeaderRow1.tsx` | Delete | Consumed by `OfferShell` | Same |
| `config/offer-builder-config.ts` | Delete | `SECTION_REGISTRY` anti-pattern — reads now go via
`lib/section-catalog.ts` + `actions/registry.ts` | `OfferNavRail` + `OfferEditSheetManager` + `OfferLivePreview` migrated |

## Layer B — Folder flattening (cosmetic)

Match brand-studio's flat shape:
- `components/navigation/OfferNavRail.tsx` → `components/OfferStudioNavRail.tsx`
- `components/container/OfferTabBar.tsx` → `components/OfferStudioTabBar.tsx`
- `components/container/EditionsRail*.tsx` → `components/EditionsRail*.tsx`
- `components/wizard/` → `components/legacy-wizard/` (brand convention)
- `tests/` top-level → distribute to `__tests__/` colocated

Low risk but wide imports — do in a single dedicated PR with codemod grep-sed on imports.

## Layer C — Section page factory migration

Current `pages/section-pages.tsx` reads the schema + offerId + editionCode and
produces a page per section. Replace with the brand-studio factory:

```tsx
// Target shape — identical to brand-studio/pages/section-pages.tsx
const PromisePage = createPage<OfferPromise>({
  slug: "promise",
  schema: offerPromiseSchema,
  select: (s) => s.promise,
  save: (h) => h.updatePromise,
});
```

Requires an `useOfferSettings()` aggregator hook exposing `updatePromise`,
`updatePricing`, etc. Map each section's save path to the right mutation
(some write to Offer, some to LaunchEdition overrides).

## Layer D — Copilot section tools (backend)

`SectionPage` accepts `copilotSlot`. To activate it:

1. Create `backend/src/modules/copilot/tools/offer_section_tools.py`.
2. Register per-section tools under `entity_type="offer-section"` — see
   `docs/ux-sessions/2026-04-20-offer-studio-homologation/UI-SPEC-copilot-sidebar.md` §4.
3. Create `features/offer-studio/components/OfferSectionCopilot.tsx`.
4. Create `features/offer-studio/hooks/use-offer-copilot.ts`.
5. Pass `copilotSlot={<OfferSectionCopilot ... />}` from `SectionPage`
   consumers.

## Layer E — Per-variant content override expansion (optional)

Today variants override: `pricing_tiers` + `dates` + `capacity` +
`location_override` + `assets` (via `edition_id`).

If a product decision makes sense later, extend with:
- `promise_override` (promise per variant — LANGUAGE case)
- `value_stack_override` (tier differential beneficios — TIER case)
- `deliverables_override` (SKU-specific items — SKU_VARIANT case)
- `testimonials_override` (per-locale testimonials — LANGUAGE case)

**Not needed for initial TIER / SKU launch.** The current
`structure_data: dict[str, Any]` JSONB bucket is enough: TIER carries
`features[]` + `price_amount`; SKU carries `attributes{}`. Promote to
typed columns only when analytics / sales-agent / landing generator
actually need to read them via indexed queries.

## Layer F — Wizard multi-structure picker (Sprint 13.1)

Supported archetypes now have multiple `supported_variant_structures`. When
the preset does NOT fix `default_variant_structure`, wizard should ask:

> ¿Cómo varía tu oferta? Cohortes / Modalidades / Idiomas / Regiones

Implementation: new `WizardVariantStructureStep.tsx` in `components/legacy-wizard/`
that reads `supported_variant_structures` from the archetype catalog and
renders a radio-card picker. Skip the step if the preset's
`default_variant_structure` is non-null.

## Verification policy

No layer above blocks Sprint 15.1 usage. Each layer is a well-scoped
independent PR. Safe order: C → A → B → D → F → E (E is demand-driven).
Every PR must keep: backend 3616 tests + frontend 1063 tests green, TSC
clean, arch fitness allowlists non-growing.
