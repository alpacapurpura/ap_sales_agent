# Tasks

- [ ] Task 1: Refactor Team Module (Atomic)
  - [ ] Create `frontend/src/features/brand/components/team/team-list.tsx` (UI)
  - [ ] Create `frontend/src/features/brand/components/team/team-member-form.tsx` (UI)
  - [ ] Create `frontend/src/features/brand/components/team/team-manager.tsx` (Smart Container)
  - [ ] `TeamManager` handles `useBrandSettings` hook to save `team` array atomically.
  - [ ] Delete old forms.

- [ ] Task 2: Refactor Authority Module (Atomic)
  - [ ] Create `frontend/src/features/brand/components/authority/authority-list.tsx`
  - [ ] Create `frontend/src/features/brand/components/authority/authority-item-form.tsx`
  - [ ] Create `frontend/src/features/brand/components/authority/authority-manager.tsx`
  - [ ] Delete old forms.

- [x] Task 3: Refactor Testimonials Module (Atomic)
  - [ ] Create `frontend/src/features/brand/components/testimonials/testimonials-list.tsx`
  - [ ] Create `frontend/src/features/brand/components/testimonials/testimonial-item-form.tsx`
  - [ ] Create `frontend/src/features/brand/components/testimonials/testimonials-manager.tsx`
  - [ ] Delete old forms.

- [x] Task 4: Refactor Simple Modules (Atomic Managers)
  - [ ] Create `frontend/src/features/brand/components/identity/identity-manager.tsx` (Smart) & `identity-form.tsx` (Pure)
  - [ ] Create `frontend/src/features/brand/components/strategy/strategy-manager.tsx` & forms
  - [ ] Create `frontend/src/features/brand/components/visuals/visuals-manager.tsx` & forms
  - [ ] Update `EditSheetManager` to render Managers instead of raw Forms.

- [x] Task 5: Cleanup and Verification
  - [ ] Verify all imports in `EditSheetManager` are correct.
  - [ ] Ensure no regression in Brand Studio functionality.
