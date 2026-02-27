# Tasks

- [x] Task 1: Prepare Directories
  - [ ] Create `components/editor`, `components/editor/layout`, `components/editor/sections`, `components/editor/forms`, `components/editor/ui`, `components/editor/components`.
  - [ ] Create `components/landing`.

- [x] Task 2: Move Dashboard Components
  - [x] Move `OfferStudioView.tsx` to `components/dashboard/OfferStudioView.tsx`.
  - [x] Update imports in `app/(main)/[tenantId]/(dashboard)/offer-studio/page.tsx`.

- [x] Task 3: Move Editor Components
  - [ ] Move `DynamicOfferEditor.tsx` to `components/editor/OfferEditor.tsx`.
  - [ ] Move `layout/offer-editor-layout.tsx` to `components/editor/layout/OfferEditorLayout.tsx`.
  - [ ] Move `components/sections/*` to `components/editor/sections/*`.
  - [ ] Move `components/forms/*` to `components/editor/forms/*`.
  - [ ] Move `components/ui/*` to `components/editor/ui/*`.
  - [ ] Move `ai-assist-button.tsx`, `asset-uploader.tsx`, `objection-editor.tsx`, `offer-gallery-section.tsx`, `widgets/`, `cards/` to `components/editor/components/` (organize as needed).

- [x] Task 4: Move Landing Builder
  - [ ] Move `features/landing-builder/*` to `features/offer-studio/components/landing/*`.
  - [ ] Delete `features/landing-builder`.

- [x] Task 5: Update Imports
  - [ ] Update imports in `OfferEditor.tsx` (formerly Dynamic).
  - [ ] Update imports in `OfferEditorLayout.tsx`.
  - [ ] Update imports in all moved sections and forms.
  - [ ] Update imports in `app/` pages that reference these components.
  - [ ] Update imports in `offer-builder-config.ts`.

- [x] Task 6: Final Cleanup
  - [ ] Remove empty directories in `components/`.
  - [ ] Verify application builds.

# Task Dependencies
- Task 5 depends on Tasks 2, 3, 4.
