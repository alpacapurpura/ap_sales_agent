# Tasks

- [x] Task 1: Extract Gallery Module
  - [x] SubTask 1.1: Create `backend/src/modules/gallery` structure (`api`, `domain`, `infrastructure`).
  - [x] SubTask 1.2: Move `content/domain/gallery.py` -> `gallery/domain/entity.py`.
  - [x] SubTask 1.3: Move `content/infrastructure/gallery_repository.py` -> `gallery/infrastructure/repository.py`.
  - [x] SubTask 1.4: Move `content/api/gallery.py` -> `gallery/api/router.py`.
  - [x] SubTask 1.5: Update imports in `gallery` module.

- [x] Task 2: Move Avatar to Brand
  - [x] SubTask 2.1: Create `backend/src/modules/brand/infrastructure/models` and `repositories` if not exist.
  - [x] SubTask 2.2: Move `content/infrastructure/models/avatar.py` -> `brand/infrastructure/models/avatar.py`.
  - [x] SubTask 2.3: Move `content/infrastructure/repositories/avatar_repository.py` -> `brand/infrastructure/repositories/avatar_repository.py`.
  - [x] SubTask 2.4: Move `content/api/avatars.py` -> `brand/api/avatars.py`.
  - [x] SubTask 2.5: Move `content/api/dto/avatars.py` -> `brand/api/dto/avatars.py`.

- [x] Task 3: Update System Configuration
  - [x] SubTask 3.1: Update `backend/src/main.py` to mount `gallery` and `brand.avatars` routers.
  - [x] SubTask 3.2: Grep and update all imports from `src.modules.content...` to new locations.
  - [x] SubTask 3.3: Ensure `Offer` model still imports `Avatar` correctly (if relationship exists) or uses loose coupling (ID only).

- [x] Task 4: Cleanup Content Module
  - [x] SubTask 4.1: Delete moved files from `content`.
  - [x] SubTask 4.2: Verify `content` module still works for Landing Pages (which use Gallery/Avatars).

- [x] Task 5: Verification
  - [x] SubTask 5.1: Create test script `backend/tests/integration/test_gallery_avatar_refactor.py`.
  - [x] SubTask 5.2: Verify Gallery upload/list.
  - [x] SubTask 5.3: Verify Avatar CRUD.
