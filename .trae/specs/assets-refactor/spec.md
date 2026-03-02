# Assets Module Refactor Spec

## Why
Currently, the "Assets" module (formerly Gallery) is tightly coupled to the "Offer" module, forcing every uploaded image to belong to a specific product. This limits the system's ability to manage brand assets, generic files, or multi-media types (video, audio) efficiently. Additionally, the storage logic is hardcoded to the local file system, and the AI extraction is entangled. We need a robust, generic Assets module that serves as a central repository for the Tenant, supporting various media types and storage providers (preparing for S3).

## What Changes

### Database (PostgreSQL)
- **Rename Table**: `offer_gallery_images` -> `assets`.
- **Schema Updates**:
  - `offer_id`: Change from `NOT NULL` to `NULLABLE` (to allow generic tenant assets).
  - `type`: Add column (Enum: `IMAGE`, `VIDEO`, `AUDIO`, `DOCUMENT`).
  - `storage_provider`: Add column (Enum: `LOCAL`, `S3`).
  - `storage_path`: Add column (Internal path/key).
  - `mime_type`: Add column.
  - `ai_metadata`: Add `JSONB` column to consolidate `ai_description`, `ai_colors` (keep existing columns for now to avoid breaking changes, or migrate data). *Decision: Keep existing columns for backward compatibility but populate `ai_metadata` for new logic.*

### Backend (`src/modules/assets`)
- **Architecture**:
  - Implement **Repository Pattern** for database access.
  - Implement **Strategy Pattern** for Storage (`StorageProvider`: `LocalStorage`, `S3Storage` placeholder).
- **Service Layer**:
  - Refactor `GalleryService` to `AssetsService`.
  - Add logic to detect MIME type and assign `AssetType`.
  - Decouple AI processing into `AssetProcessor` using the Copilot/LLM infrastructure.
- **API**:
  - Update generic upload endpoint to not require `offer_id`.
  - Add endpoints for filtering assets by Type and generic Tenant listing.

### Frontend (`src/lib/api`)
- **API Client**:
  - Rename/Refactor `galleryApi` to `assetsApi`.
  - Update interfaces to match the new backend DTOs.
  - Ensure "Back of the Front" handles the new optional `offer_id`.

## Impact
- **Affected Specs**: `module_assets.md`.
- **Affected Code**:
  - `backend/src/modules/assets/*`
  - `frontend/src/lib/api/gallery.ts` (Renamed to `assets.ts`)
  - `frontend/src/features/brand/sections/gallery/gallery-manager.tsx` (Update API calls)
  - `frontend/src/features/offer-studio/components/editor/sections/visuals/gallery-manager.tsx` (Update API calls)

## ADDED Requirements
### Requirement: Generic Asset Upload
The system SHALL allow uploading files without an `offer_id`, associating them only with the `tenant_id`.

#### Scenario: Brand Asset Upload
- **WHEN** user uploads a logo in Brand settings
- **THEN** the asset is saved with `type=IMAGE` and `offer_id=NULL`.

### Requirement: Multi-media Support
The system SHALL detect and store the file type (`IMAGE`, `VIDEO`, `AUDIO`, `DOCUMENT`) upon upload.

## MODIFIED Requirements
### Requirement: Offer Gallery Compatibility
The system SHALL continue to support listing assets by `offer_id` to maintain functionality in the Offer Studio.
