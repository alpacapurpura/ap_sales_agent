# Fix Brand Studio Connection Spec

## Why
After a recent refactor of both frontend and backend, the connection between them is broken. The user reports that "nothing works". We need to debug and fix the connection, starting with the Brand Studio module, using a systematic approach to identify root causes.

## What Changes
- **Debug & Fix**: Systematically debug the API calls from frontend to backend for the Brand Studio module.
- **Unit Tests**: Create reproduction scripts (unit tests) for backend endpoints to verify they work in isolation.
- **Integration**: Verify the frontend-backend integration.
- **Refactor**: Fix any code issues found during debugging (e.g., mismatched types, incorrect endpoints, missing fields).

## Impact
- **Affected Specs**: Brand Studio module.
- **Affected Code**:
  - Backend: `backend/src/modules/iam/api/settings.py` (Brand Settings API)
  - Backend: `backend/src/modules/marketing/domain/brand_models.py` (Brand Models)
  - Frontend: `frontend/src/features/brand/api/index.ts` (API Client)
  - Frontend: `frontend/src/features/brand/types.ts` (Types)

## ADDED Requirements
### Requirement: Debugging & Testing
- Create a test script to verify `GET /api/v1/settings/brand` and `PATCH /api/v1/settings/brand`.
- Ensure backend models (`BrandSettings`) match frontend interfaces.
- Verify CORS and authentication handling for these endpoints.

## MODIFIED Requirements
### Requirement: Brand Studio API
- Ensure the API correctly handles the `BrandSettings` object structure.
- Fix any Pydantic validation errors or missing fields.
