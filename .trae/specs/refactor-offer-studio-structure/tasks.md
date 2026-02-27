# Tasks

- [x] Task 1: Rename Offer Studio Components to Kebab-Case
  - [x] SubTask 1.1: Rename `IdentityForm.tsx` to `identity-form.tsx` and `IdentityPreview.tsx` to `identity-preview.tsx`
  - [x] SubTask 1.2: Rename `StrategyForm.tsx` to `strategy-form.tsx` and `StrategyPreview.tsx` to `strategy-preview.tsx`
  - [x] SubTask 1.3: Rename `PricingForm.tsx` to `pricing-form.tsx` and `PricingPreview.tsx` to `pricing-preview.tsx`
  - [x] SubTask 1.4: Rename `ClosingForm.tsx` to `closing-form.tsx` and `ClosingPreview.tsx` to `closing-preview.tsx`
  - [x] SubTask 1.5: Rename `GalleryForm.tsx` to `gallery-form.tsx` and `GalleryPreview.tsx` to `gallery-preview.tsx`
  - [x] SubTask 1.6: Rename `InstructorsForm.tsx` to `instructors-form.tsx` and `InstructorsPreview.tsx` to `instructors-preview.tsx`
  - [x] SubTask 1.7: Rename `ResourcesForm.tsx` to `resources-form.tsx` and `ResourcesPreview.tsx` to `resources-preview.tsx`
  - [x] SubTask 1.8: Rename `ValueStackForm.tsx` to `value-stack-form.tsx` and `ValueStackPreview.tsx` to `value-stack-preview.tsx`
  - [x] SubTask 1.9: Rename `PsychologyForm.tsx` to `psychology-form.tsx`
  - [x] SubTask 1.10: Rename `PromiseForm.tsx` to `promise-form.tsx`
  - [x] SubTask 1.11: Rename `OfferEditor.tsx` to `offer-editor.tsx`, `OfferLivePreview.tsx` to `offer-live-preview.tsx`, `OfferEditSheetManager.tsx` to `offer-edit-sheet-manager.tsx`
  - [x] SubTask 1.12: Rename any remaining CamelCase files in `sections/common`, `sections/ui`, etc.

- [x] Task 2: Implement Manager Pattern for Complex Sections
  - [x] SubTask 2.1: Create `instructors-manager.tsx` in `sections/instructors` to handle data fetching logic (if applicable) or wrap form.
  - [x] SubTask 2.2: Create `resources-manager.tsx` in `sections/resources` to handle data fetching logic.
  - [x] SubTask 2.3: Create `gallery-manager.tsx` in `sections/visuals` (or `gallery`) to handle image fetching/upload logic.

- [x] Task 3: Update Configuration and Imports
  - [x] SubTask 3.1: Update `offer-builder-config.ts` to import from new file paths.
  - [x] SubTask 3.2: Update imports in `offer-edit-sheet-manager.tsx` (now `offer-edit-sheet-manager.tsx`) to use new file paths and Manager components.
  - [x] SubTask 3.3: Verify all imports across the `offer-studio` feature are correct and pointing to the new file names.

- [x] Task 4: Verification and Cleanup
  - [x] SubTask 4.1: Run linting to check for import errors.
  - [x] SubTask 4.2: Verify that the application builds correctly.

# Task Dependencies
- [Task 3] depends on [Task 1] and [Task 2]
- [Task 4] depends on [Task 3]
