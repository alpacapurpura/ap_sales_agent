# Tasks

- [ ] Task 1: Move and Refactor Shared Components
  - [ ] Move `SectionFormWrapper.tsx` from `wrappers/` to `components/forms/SectionFormWrapper.tsx`.
  - [ ] Move `OfferEditSheetManager.tsx` from `editor/` to `components/forms/OfferEditSheetManager.tsx`.
  - [ ] Update `OfferEditSheetManager.tsx` to:
    - Remove footer save button.
    - Accept `form` (main form) prop but pass `defaultValues={form.getValues()}` to child.
    - Pass `onSave` handler to child.
    - Pass `sectionId` and `title` (if needed by Placeholder).

- [ ] Task 2: Create Atomic Forms (Strategy)
  - [ ] Create `components/forms/StrategyForm.tsx` (based on `StrategyFormWrapper`).
  - [ ] Remove `useParams` and `useOffer`.
  - [ ] Accept `{ defaultValues, onSave }` props.
  - [ ] Use `SectionFormWrapper` with passed values.
  - [ ] Ensure `StrategySection` receives the correct form context.

- [ ] Task 3: Create Atomic Forms (Pricing)
  - [ ] Create `components/forms/PricingForm.tsx`.
  - [ ] Refactor similarly to StrategyForm (remove fetch, use props).

- [ ] Task 4: Create Atomic Forms (Identity)
  - [ ] Create `components/forms/IdentityForm.tsx`.
  - [ ] Refactor similarly to StrategyForm.

- [ ] Task 5: Create Atomic Forms (Placeholder)
  - [ ] Move `PlaceholderFormWrapper` to `components/forms/PlaceholderForm.tsx`.
  - [ ] Update to accept generic props (ignore form/values if not needed, but handle interface).

- [ ] Task 6: Cleanup and Integration
  - [ ] Update `offer-builder-config.ts` to import new forms from `components/forms/`.
  - [ ] Update `OfferEditor.tsx` to import `OfferEditSheetManager` from new location.
  - [ ] Delete `components/forms/wrappers/` directory.

# Task Dependencies
- Task 2, 3, 4, 5 depend on Task 1 (structurally).
- Task 6 depends on all others.
