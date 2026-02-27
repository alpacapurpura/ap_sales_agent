# Tasks

- [x] Task 1: Backend Model Relaxation
  - [ ] Modify `backend/src/modules/brand/domain/models.py`:
    - [ ] Make all fields in `BrandIdentity`, `BrandStrategy`, `BrandStory` Optional.
    - [ ] Add `brand_name: Optional[str]` to `BrandIdentity`.

- [x] Task 2: Frontend Structure Refactor (Move to `sections/`)
  - [ ] Create `frontend/src/features/brand/sections` directory.
  - [ ] Move folders from `components/` to `sections/`: `identity`, `strategy`, `story`, `team`, `contact`, `visuals`, `voice`, `authority`, `methodology`, `testimonials`, `avatars`, `gallery`.
  - [ ] Update imports in `BrandStudioLayout`, `BrandNavRail`, and any other consumers.

- [x] Task 3: Frontend Logic & Types Fix
  - [ ] Update `frontend/src/features/brand/types/index.ts`: Add `brand_name` to `BrandIdentity`, make fields optional.
  - [ ] Update `frontend/src/features/brand/hooks/useBrandSettings.ts`: Handle null nested objects.
  - [ ] Fix `BrandStudioLayout.tsx`:
    - [ ] Use `visuals?.logo_url` instead of `identity.logo_url`.
    - [ ] Use `contact?.website` instead of `identity.website`.
    - [ ] Check `brand_name` for `hasExistingData`.

- [x] Task 4: Verification
  - [ ] Verify "Error al cargar configuración" is resolved.
  - [ ] Verify independent saving of sections works.
  - [ ] Verify new folder structure is correct and imports work.
