# Tasks

- [x] Task 1: Clean up dead code in `live-preview`
  - [ ] Delete `frontend/src/features/brand/components/live-preview/brand-health-sidebar.tsx`
  - [ ] Delete `frontend/src/features/brand/components/live-preview/team-grid-section.tsx`

- [x] Task 2: Refactor Gallery Component
  - [ ] Create directory `frontend/src/features/brand/components/gallery`
  - [ ] Move `frontend/src/features/brand/components/live-preview/gallery-section.tsx` to `frontend/src/features/brand/components/gallery/gallery-manager.tsx`
  - [ ] Update internal imports in `gallery-manager.tsx` if necessary
  - [ ] Update usage in `brand-studio-layout.tsx` to import from new location

- [x] Task 3: Refactor Avatar Manager
  - [ ] Move `frontend/src/features/brand/components/avatar-manager.tsx` to `frontend/src/features/brand/components/avatars/avatar-manager.tsx`
  - [ ] Update imports in `avatar-manager.tsx` (fix relative paths)
  - [ ] Update usage in `brand-settings/page.tsx` and other consumers

- [x] Task 4: Final Cleanup
  - [ ] Remove empty `frontend/src/features/brand/components/live-preview` directory
  - [ ] Verify application builds without import errors
