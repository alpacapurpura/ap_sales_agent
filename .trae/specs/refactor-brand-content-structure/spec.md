# Refactor Brand & Content Structure Spec

## Why
The user reports that the Brand Studio in the frontend is empty ("no veo nada"), and correctly identifies a structural mismatch between Frontend and Backend.
- **Frontend**: Distinct `brand` and `offer-studio` features.
- **Backend**: Brand logic is scattered in `marketing` and `iam`, while Offer logic is in `content`.

To improve maintainability and fix the visibility issue, we will refactor the backend to align with the frontend structure, consolidating Brand logic into `modules/content/brand`.

## What Changes
- **Refactor Structure**:
  - Create `backend/src/modules/content/brand`.
  - Move `backend/src/modules/marketing/domain/brand_models.py` -> `backend/src/modules/content/brand/domain/models.py`.
  - Extract Brand endpoints from `iam/api/settings.py` -> `backend/src/modules/content/brand/api/router.py`.
  - Move `marketing/application/services/brand_extraction_service.py` -> `backend/src/modules/content/brand/application/extraction_service.py`.
  - (Optional) Organize existing content logic into `backend/src/modules/content/offer`.

- **Fix "Nothing Visible"**:
  - Ensure the new Brand API router is correctly mounted in `main.py`.
  - Verify that the API response structure matches the Frontend's expectation (which was updated in the previous task).
  - Ensure seeded/default data exists so the UI isn't blank.

## Impact
- **Affected Specs**: Brand Studio, Offer Studio.
- **Affected Code**:
  - `backend/src/modules/marketing/` (Will be emptied of brand logic).
  - `backend/src/modules/iam/api/settings.py` (Will lose brand endpoints).
  - `backend/src/modules/content/` (Will gain `brand` submodule).
  - `backend/src/main.py` (Router updates).

## ADDED Requirements
### Requirement: Backend Structure
The backend SHALL organize business logic into `content/brand` and `content/offer` (or similar) to match frontend features.

### Requirement: Brand API
The Brand API SHALL be accessible at `/api/v1/content/brand` (or keep legacy `/api/v1/settings/brand` but routed from the new module). *Decision: Keep URL `/api/v1/settings/brand` for compatibility or move to `/api/v1/brand`? User didn't specify URL change, only folder structure. Keeping URL `/api/v1/settings/brand` is safer for frontend, but routing it from `content/brand` module.*

## MODIFIED Requirements
### Requirement: Brand Persistence
Brand settings SHALL be stored in `Tenant.config_json['brand_settings']` but managed by the `content/brand` module.
