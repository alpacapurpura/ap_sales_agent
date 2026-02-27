# Offer Studio Mock Data Spec

## Why
The Offer Studio is currently non-functional, likely due to backend issues or missing data. The user requests to enable a "Mock Mode" similar to Brand Studio, populated with comprehensive mock data covering every single `OfferType`. This ensures the frontend can be fully validated in isolation.

## What Changes
- **Frontend**:
    - Update `frontend/src/features/offer-studio/api/mock-data.ts` to export a `MOCK_OFFERS` array.
    - Populate `MOCK_OFFERS` with at least one `Offer` object for each `OfferType` defined in `OfferType` enum.
    - Set `USE_MOCK_DATA = true` in `frontend/src/features/offer-studio/api/index.ts`.

## Impact
- **Affected Specs**: Offer Studio.
- **Affected Code**:
    - `frontend/src/features/offer-studio/api/mock-data.ts`
    - `frontend/src/features/offer-studio/api/index.ts`

## ADDED Requirements
### Requirement: Comprehensive Mock Data
The system SHALL provide a mock offer for every `OfferType` to validate UI rendering for all product variations.

#### Scenario: List Offers in Mock Mode
- **WHEN** the user visits Offer Studio with `USE_MOCK_DATA = true`
- **THEN** the list should display roughly 23 offers (one for each type).
- **THEN** clicking on any offer should load its specific details correctly from the mock.

## MODIFIED Requirements
### Requirement: Mock API Switch
The `offerApi` adapter SHALL use the expanded `MOCK_OFFERS` array when `USE_MOCK_DATA` is true.
