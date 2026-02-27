# Offer Studio Fix & Integration Spec

## Why
The Offer Studio module was refactored but left in a "broken" and disconnected state. The frontend and backend have mismatched API signatures (methods, paths, payload structures), causing failures. We need to stabilize the module, ensure data flows correctly, and verify both ends.

## What Changes
- **Frontend API Client (`api/index.ts`)**:
  - Change HTTP methods from `PUT` to `PATCH` for section updates to match backend.
  - Fix endpoint paths to match backend routes (e.g., `/{id}/identity` instead of `/identity`).
- **Frontend Adapter (`api/adapter.ts`)**:
  - Fix payload mapping for `pricing` (Backend expects `pricing_options`).
  - Fix payload mapping for `public_name` (Backend expects `public_name`, not `name`).
  - Update response mapping to read `pricing_options` from backend.
- **Backend Verification**:
  - Verify all atomic update endpoints.
  - Ensure Pydantic schemas accept the payloads sent by frontend.

## Impact
- **Affected Specs**: Offer Studio features.
- **Affected Code**:
  - `frontend/src/features/offer-studio/api/index.ts`
  - `frontend/src/features/offer-studio/api/adapter.ts`
  - `backend/src/modules/offer/api/products.py` (Verification only)

## ADDED Requirements
### Requirement: Mock Data Verification
The system SHALL provide a mechanism to load mock JSON data in the frontend to verify UI rendering before connecting to the real backend.

### Requirement: API Consistency
The Frontend API Client SHALL send payloads strictly matching the Backend Pydantic Schemas (`OfferIdentityUpdate`, `OfferPricingUpdate`, etc.).

## MODIFIED Requirements
### Requirement: Section Updates
**Current**: Uses `PUT` and mismatched payloads.
**New**: MUST use `PATCH` and payloads matching `src/modules/offer/domain/schemas.py`.

## REMOVED Requirements
N/A
