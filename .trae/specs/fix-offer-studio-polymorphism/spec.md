# Fix Offer Studio Polymorphism Spec

## Why
The Offer Studio was refactored to allow independent section saving, but the implementation is currently broken for polymorphic details (Program, Product, Service, etc.). The frontend is sending incorrectly nested data (`{ specific_details: { specific_details: ... } }`) to the backend, and some top-level fields edited in specific sections might not be saving correctly.

## What Changes
- **Frontend API Logic**: Fix `getSectionData` and `offerApi.saveSection` to correctly structure the payload for `PATCH /{id}/details`.
- **Frontend Mocking**: Implement a mock data service to verify frontend logic in isolation as requested.
- **Backend Schema (If needed)**: Ensure `OfferDetailsUpdate` includes necessary fields or frontend splits updates.
- **Form Logic**: Verify `ProgramDetailsForm` and others correctly bind to the schema.

## Impact
- Affected specs: `Offer Studio` editor.
- Affected code:
  - `frontend/src/features/offer-studio/api/index.ts`
  - `frontend/src/features/offer-studio/utils/section-helpers.ts`
  - `frontend/src/features/offer-studio/components/editor/sections/**/*`
  - `backend/src/modules/offer/domain/schemas.py` (Potential)

## ADDED Requirements
### Requirement: Independent Section Saving
The system SHALL allow saving "Program Details", "Product Details", etc., independently without overwriting other sections or losing data.

#### Scenario: Save Program Details
- **WHEN** user edits "Duration" and "Structure Type" in Program Details and clicks "Save".
- **THEN** the frontend sends a `PATCH` request to `/details` with the correct `specific_details` payload.
- **AND** the backend updates the `specific_details` column in the database.

## MODIFIED Requirements
### Requirement: API Payload Structure
The frontend MUST NOT nest `specific_details` inside another `specific_details` object when calling `saveSection`.
