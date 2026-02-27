# Refactor Gallery & Avatar Spec

## Why
The user requests that `gallery` be a standalone module (reused across the solution) and `avatar` be part of `brand` (since it belongs to the brand but is used by products). This completes the backend modularization, ensuring `content` module is focused only on generation/assembly, not core entity management.

## What Changes
- **Gallery Module**:
  - Create `backend/src/modules/gallery`.
  - Move Gallery logic (Models, Repository, API) from `content` to `gallery`.
  - Ensure `GalleryImage` is a proper entity.

- **Avatar Logic**:
  - Move Avatar logic from `content` to `brand`.
  - `brand` module will now host proper SQLAlchemy entities (Avatar) alongside the JSON-based BrandSettings.
  - Structure:
    - `backend/src/modules/brand/api/avatars.py`
    - `backend/src/modules/brand/domain/avatar.py` (or similar)
    - `backend/src/modules/brand/infrastructure/models/avatar.py`
    - `backend/src/modules/brand/infrastructure/repositories/avatar_repository.py`

- **Clean up Content**:
  - Remove moved files from `content`.
  - Update imports in `main.py` and other consumers.

## Impact
- **Affected Specs**: Brand Studio, Offer Studio (Avatars).
- **Affected Code**:
  - `backend/src/modules/content/` (Removals).
  - `backend/src/modules/gallery/` (New).
  - `backend/src/modules/brand/` (Additions).
  - `backend/src/main.py` (Router updates).

## ADDED Requirements
### Requirement: Gallery Module
The system SHALL provide a dedicated Gallery module for managing media assets, accessible at `/api/v1/gallery`.

### Requirement: Brand Avatars
The system SHALL manage Avatars within the Brand module, accessible at `/api/v1/brand/avatars` (or `/api/v1/avatars` routed to Brand module). *Decision: Keep `/api/v1/avatars` for now or move to `/api/v1/brand/avatars`? User didn't specify URL, just module ownership. Let's move to `/api/v1/brand/avatars` to reflect hierarchy, or keep global if used heavily. Let's keep global URL `/api/v1/avatars` but routed from `brand` module for simplicity in frontend.*

## MODIFIED Requirements
### Requirement: Avatar Ownership
Avatars SHALL be defined in the `brand` module but referenced by `offer` products via `avatar_id`.
