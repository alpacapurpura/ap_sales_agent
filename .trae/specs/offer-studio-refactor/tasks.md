# Tasks

- [x] Task 1: Extend Configuration System
  - [ ] SubTask 1.1: Update `OfferBuilderSectionConfig` interface in `config/offer-builder-config.ts` to include `icon`, `previewComponent`, and `formComponent`.
  - [ ] SubTask 1.2: Import necessary icons and prepare placeholder components for Previews.
  - [ ] SubTask 1.3: Update `SECTION_REGISTRY` to include icons and placeholders (initially) for all existing sections.

- [x] Task 2: Create Infrastructure Components
  - [ ] SubTask 2.1: Create `OfferNavRail` that iterates `OFFER_BUILDER_CONFIG` to render navigation items dynamically.
  - [ ] SubTask 2.2: Implement `getOfferHealth` logic that iterates the config and checks validation rules for each section.
  - [ ] SubTask 2.3: Create `OfferStudioLayout` to scaffold the sidebar and main content area.

- [x] Task 3: Implement Atomic Form Wrappers (The "Adapter" Layer)
  - [ ] SubTask 3.1: Create a generic `SectionFormWrapper` or specific wrappers (e.g., `StrategyFormWrapper`) that instantiate `useForm` and handle `PATCH` requests.
  - [ ] SubTask 3.2: Connect existing UI sections (`StrategySection`, `IdentitySection`, etc.) into these wrappers.
  - [ ] SubTask 3.3: Register these wrappers as `formComponent` in `SECTION_REGISTRY`.

- [x] Task 4: Implement Live Preview Components
  - [ ] SubTask 4.1: Create `StrategyPreview` component (Read-only view of strategy data).
  - [ ] SubTask 4.2: Create `IdentityPreview` component.
  - [ ] SubTask 4.3: Create `PricingPreview` component.
  - [ ] SubTask 4.4: Create generic/placeholder previews for other sections (`ProgramDetails`, `Gallery`, etc.).
  - [ ] SubTask 4.5: Register these components as `previewComponent` in `SECTION_REGISTRY`.

- [x] Task 5: Integrate & Orchestrate
  - [ ] SubTask 5.1: Create `OfferLivePreview` container that iterates config and renders registered Preview components.
  - [ ] SubTask 5.2: Create `OfferEditSheetManager` that listens to edit events and renders the registered `formComponent`.
  - [ ] SubTask 5.3: Replace the old `OfferEditor` page with the new `OfferStudioLayout` implementation.

# Task Dependencies
- Task 1 is the foundation.
- Task 3 and Task 4 can be done in parallel after Task 1.
- Task 2 depends on Task 1.
- Task 5 integrates everything.
