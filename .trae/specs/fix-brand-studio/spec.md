# Brand Studio Fix Spec

## Why
The Brand Studio is currently non-functional due to recent backend refactoring. The user requires the frontend to be fully functional with **mock data** first, to isolate frontend logic from potential backend issues. Subsequently, the backend must be verified to serve data correctly for the "Visionarias" tenant.

## What Changes
- **Frontend**:
    - **Create Mock Data**: A new file `frontend/src/features/brand/api/mock-data.ts` will be created. (Confirmed: No existing mock file for Brand found).
    - **Implement Mock Adapter**: Modify `frontend/src/features/brand/api/index.ts` to switch between real and mock data based on a `USE_MOCK_API` flag.
    - **Verify Components**: Ensure all Brand Studio components render correctly with the comprehensive mock data.
- **Backend**:
    - **Audit Data Flow**: Verify `BrandRepository` correctly reads/writes `brand_settings` from `Tenant.config_json`.
    - **Verify Routes**: Confirm API routes in `backend/src/modules/brand/api/router.py` match frontend expectations.
    - **Validate Model**: Ensure `BrandSettings` Pydantic model correctly validates the existing data structure in the database.

## Impact
- **Affected Specs**: Brand Studio.
- **Affected Code**:
    - `frontend/src/features/brand/api/index.ts`
    - `frontend/src/features/brand/api/mock-data.ts` (New)
    - `backend/src/modules/brand/infrastructure/repositories/brand_repository.py`

## ADDED Requirements
### Requirement: Mock Data Mode
The system SHALL provide a mechanism to run the Brand Studio in "Mock Mode" where all API calls return static, complete sample data without hitting the backend.

#### Scenario: Enable Mock Mode
- **WHEN** the `USE_MOCK_API` flag is set to true in `brand/api/index.ts`
- **THEN** `getBrandSettings` returns the mock object immediately.
- **THEN** `updateBrandSettings` returns the updated mock object (simulated).

## MODIFIED Requirements
### Requirement: Brand Settings API
The backend SHALL serve the Brand Settings from the `config_json` field of the Tenant model, ensuring backward compatibility with existing data structures.
