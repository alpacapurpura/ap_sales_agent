# Tasks

- [x] Task 1: Database Schema Migration
  - [x] SubTask 1.1: Rename `offer_gallery_images` to `assets`.
  - [x] SubTask 1.2: Alter `assets` table: make `offer_id` nullable.
  - [x] SubTask 1.3: Add columns: `asset_type`, `storage_provider`, `storage_path`, `mime_type`, `ai_metadata`.
  - [x] SubTask 1.4: Update SQLAlchemy Model `GalleryImageModel` (rename to `AssetModel` and update fields).

- [x] Task 2: Backend Core Refactor (Storage & Domain)
  - [x] SubTask 2.1: Define `AssetType` and `StorageProvider` enums.
  - [x] SubTask 2.2: Implement `StorageStrategy` interface and `LocalStorageStrategy`.
  - [x] SubTask 2.3: Update `AssetModel` and Domain Entity `Asset` to reflect new schema.

- [x] Task 3: Service Layer Implementation
  - [x] SubTask 3.1: Create `AssetsService` (replacing/refactoring `GalleryService`).
  - [x] SubTask 3.2: Implement `upload_asset` logic with MIME detection and Storage Strategy.
  - [x] SubTask 3.3: Implement `delete_asset` using Storage Strategy.
  - [x] SubTask 3.4: Integrate `AssetProcessor` for AI metadata extraction (refactor existing logic).

- [x] Task 4: API Layer Updates
  - [x] SubTask 4.1: Refactor `router.py` to expose generic `/assets` endpoints.
  - [x] SubTask 4.2: Ensure `offer_gallery.py` endpoints use the new `AssetsService` but maintain backward compatibility for URLs.

- [x] Task 5: Frontend API Integration
  - [x] SubTask 5.1: Create `frontend/src/lib/api/assets.ts` (porting `gallery.ts`).
  - [x] SubTask 5.2: Update `frontend/src/types/assets.ts` (or equivalent) with new interfaces.
  - [x] SubTask 5.3: Update `GalleryManager` components (Brand & Offer) to use new API methods.

# Task Dependencies
- Task 2 depends on Task 1.
- Task 3 depends on Task 2.
- Task 4 depends on Task 3.
- Task 5 depends on Task 4.
