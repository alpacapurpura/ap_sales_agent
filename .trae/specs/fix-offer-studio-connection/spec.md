# Fix Offer Studio Backend Connection Spec

## Why
Currently, the Offer Studio frontend is failing to connect properly with the backend due to API mismatches (e.g., `pricing_options` vs `pricing`) and missing endpoints for Landing Page management. This prevents users from creating/editing offers and generating landing pages effectively.

## What Changes
- Update frontend `frontendToBackend` adapter to map `pricing_options` to `pricing`.
- Add `GET /api/v1/offers/{offer_id}/landing` endpoint to backend.
- Add `POST /api/v1/offers/{offer_id}/landing/generate` endpoint to backend.
- Add `PUT /api/v1/offers/{offer_id}/landing` endpoint to backend.
- Add `POST /api/v1/offers/{offer_id}/landing/ai/regenerate-block` endpoint to backend.
- Ensure backend `ProductResponse` and `ProductUpdate` schemas align with frontend expectations.

## Impact
- Affected specs: Offer Management, Landing Page Generation.
- Affected code:
  - `frontend/src/features/offer-studio/api/adapter.ts`
  - `backend/src/modules/landing/api/landing.py`
  - `backend/src/modules/offer/api/dto/products.py` (if needed)

## ADDED Requirements
### Requirement: Landing Page Management by Offer ID
The system SHALL provide endpoints to manage landing pages directly via `offer_id`.

#### Scenario: Get Landing Config
- **WHEN** frontend requests `GET /api/v1/offers/{offer_id}/landing`
- **THEN** backend returns the landing page configuration for that offer, or 404 if not found.

#### Scenario: Generate Landing Page
- **WHEN** frontend requests `POST /api/v1/offers/{offer_id}/landing/generate`
- **THEN** backend generates a new landing page for the offer and returns the configuration.

#### Scenario: Update Landing Page
- **WHEN** frontend requests `PUT /api/v1/offers/{offer_id}/landing` with updated config
- **THEN** backend updates the landing page configuration for that offer.

## MODIFIED Requirements
### Requirement: Offer Data Consistency
The system SHALL ensure `pricing` data is correctly transmitted between frontend and backend.

#### Scenario: Save Offer
- **WHEN** frontend saves an offer with `pricing_options`
- **THEN** backend receives `pricing` list correctly mapped.
