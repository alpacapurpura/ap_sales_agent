# Fix API Routes Alignment Spec

## Why
There is a mismatch between the frontend API calls and the backend route definitions, specifically for **Brand Settings**.
- Frontend calls `/api/v1/settings/brand` or `/api/v1/brand/settings`.
- Backend exposes `/api/v1/brand/settings/brand` (due to router prefix + endpoint path).
This causes `404 Not Found` errors when fetching brand settings.

## What Changes

### Backend
- **`src/modules/brand/api/router.py`**:
  - Remove `/brand` path from endpoints.
  - Change `@router.get("/brand")` to `@router.get("")`.
  - Change `@router.patch("/brand")` to `@router.patch("")`.
  - This makes the final URL `/api/v1/brand/settings` (consistent with `main.py` mounting).

### Frontend
- **`src/features/brand/api/index.ts`**:
  - Update `API_URL` usage to point to `/api/v1/brand/settings`.
- **`src/lib/api/settings.ts`**:
  - Verify `getBrandSettings` points to `/api/v1/brand/settings`.

## Impact
- **Affected Specs**: None.
- **Affected Code**: `backend/src/modules/brand/api/router.py`, `frontend/src/features/brand/api/index.ts`.

## ADDED Requirements
### Requirement: Brand Settings Endpoint
The system SHALL expose brand settings at `GET /api/v1/brand/settings` and `PATCH /api/v1/brand/settings`.

## MODIFIED Requirements
### Requirement: API Route Structure
**Reason**: Eliminate redundant path segments and align frontend/backend.
**Migration**: Update frontend clients.
