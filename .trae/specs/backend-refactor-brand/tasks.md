# Tasks

- [ ] Task 3.1: Implement Brand Domain
    - [ ] Create `src/modules/brand/domain/brand.py` with all Pydantic models (`BrandSettings` and children).
    - [ ] Create `src/modules/brand/domain/avatar.py`.

- [ ] Task 3.2: Implement Brand Infrastructure
    - [ ] Move/Create `AvatarModel` in `src/modules/brand/infrastructure/models/avatar_model.py`.
    - [ ] Create `BrandRepository` in `src/modules/brand/infrastructure/repositories/brand_repository.py`.
    - [ ] Create `AvatarRepository` in `src/modules/brand/infrastructure/repositories/avatar_repository.py`.

- [ ] Task 3.3: Refactor Brand Application
    - [ ] Refactor `BrandExtractionService` to use `BrandRepository`.
    - [ ] Create `AvatarService` (if needed) or use Repository in Router.

- [ ] Task 3.4: Update Brand API Routers
    - [ ] Update `brand_router.py` (or `router.py`) to use new services.
    - [ ] Update `avatars.py` router.
