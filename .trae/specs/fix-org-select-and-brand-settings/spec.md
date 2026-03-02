# Fix Organization Select and Brand Settings Spec

## Why
The user reports "Error al cargar configuración" and a 404 error when fetching brand settings. This is caused by a mismatch between the frontend API client and the refactored backend routes. Specifically, `frontend/src/features/brand/api/index.ts` is calling a deprecated URL (`/api/v1/settings/brand`). Additionally, the backend route for brand settings has a redundant path segment (`/api/v1/brand/settings/brand`). The organization select functionality also needs to be verified as the primary goal.

## What Changes

### Backend
- **Clean up Brand Settings Router**: In `backend/src/modules/brand/api/router.py`, remove the `/brand` suffix from endpoints to align with the module prefix defined in `main.py` (`/api/v1/brand/settings`).
  - `GET /brand` -> `GET /` (Effective path: `/api/v1/brand/settings`)
  - `PATCH /brand` -> `PATCH /` (Effective path: `/api/v1/brand/settings`)

### Frontend
- **Update Brand API Client**: In `frontend/src/features/brand/api/index.ts`, update the API endpoint to match the new backend structure.
  - Change `${API_URL}/api/v1/settings/brand` to `${API_URL}/api/v1/brand/settings`.
- **Verify Tenant API**: Ensure `frontend/src/lib/api/settings.ts` correctly points to `/api/v1/iam/users/me/tenants` (already done in previous task, but will verify integration).

## Impact
- **Affected Specs**: `fix-api-connection` (extends).
- **Affected Code**: 
  - Backend: `backend/src/modules/brand/api/router.py`
  - Frontend: `frontend/src/features/brand/api/index.ts`

## ADDED Requirements
### Requirement: Brand Settings Path
The system SHALL expose brand settings at `/api/v1/brand/settings` (GET and PATCH).

## MODIFIED Requirements
### Requirement: Frontend API Alignment
**Reason**: To resolve 404 errors caused by refactoring.
**Migration**: Update frontend client to use the correct new path.
