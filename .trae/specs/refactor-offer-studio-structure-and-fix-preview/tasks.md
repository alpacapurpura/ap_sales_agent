# Tasks

- [ ] Task 1: Move Directories
  - [ ] Move `frontend/src/features/offer-studio/components/forms` to `frontend/src/features/offer-studio/components/editor/forms`.
  - [ ] Move `frontend/src/features/offer-studio/components/preview` to `frontend/src/features/offer-studio/components/editor/preview`.

- [ ] Task 2: Fix OfferLivePreview
  - [ ] Modify `frontend/src/features/offer-studio/components/editor/OfferLivePreview.tsx` to pass `data={formValues}` to the rendered `PreviewComponent`.
  - [ ] Ensure `StrategyPreview.tsx` and all other previews use the `data` prop correctly (fallback to context is fine but prop is primary).

- [ ] Task 3: Migrate Core Forms (Merge Section Logic)
  - [ ] Refactor `StrategyForm.tsx`: Integrate logic/UI from `StrategySection.tsx`.
  - [ ] Refactor `IdentityForm.tsx`: Integrate logic/UI from `IdentitySection.tsx`.
  - [ ] Refactor `PricingForm.tsx`: Integrate logic/UI from `PricingSection.tsx`.

- [ ] Task 4: Create Missing Forms (Batch 1 - High Value)
  - [ ] Create `PsychologyForm.tsx` from `PsychologySection.tsx`.
  - [ ] Create `PromiseForm.tsx` from `PromiseSection.tsx`.
  - [ ] Create `ClosingForm.tsx` from `ClosingSection.tsx`.
  - [ ] Create `InstructorsForm.tsx` from `InstructorsSection.tsx`.
  - [ ] Create `ValueStackForm.tsx` from `ValueStackSection.tsx`.

- [ ] Task 5: Create Missing Forms (Batch 2 - Assets & Details)
  - [ ] Create `ResourcesForm.tsx` from `ResourcesSection.tsx`.
  - [ ] Create `GalleryForm.tsx` from `GallerySection.tsx`.
  - [ ] Create `ProgramDetailsForm.tsx` from `ProgramDetailsSection.tsx`.
  - [ ] Create `ProductDetailsForm.tsx` from `ProductDetailsSection.tsx`.
  - [ ] Create `ServiceDetailsForm.tsx` from `ServiceDetailsSection.tsx`.
  - [ ] Create `EventDetailsForm.tsx` from `EventDetailsSection.tsx`.
  - [ ] Create `SubscriptionDetailsForm.tsx` from `SubscriptionDetailsSection.tsx`.

- [ ] Task 6: Update Configuration & Cleanup
  - [ ] Update `offer-builder-config.ts` to use all the new Forms.
  - [ ] Remove `component` property from `SECTION_REGISTRY`.
  - [ ] Delete `frontend/src/features/offer-studio/components/editor/sections/` directory.

# Task Dependencies
- Task 3, 4, 5 depend on Task 1.
- Task 6 depends on Task 3, 4, 5.
