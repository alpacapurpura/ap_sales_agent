# Fix Offer Studio Loading Spec

## Why
Users are experiencing an error "No se pudieron cargar las ofertas" when accessing the Offer Studio. This prevents them from managing their offers. The issue seems to be related to the data fetching flow or backend processing for specific tenants (e.g., "visionarias").

## What Changes
- **Backend Debugging**: Identify and fix the root cause of the API failure at `GET /api/v1/offer/products/`.
- **Data Validation**: Ensure the `Offer` data in the database complies with the Pydantic schemas, specifically regarding polymorphic fields like `specific_details`.
- **Frontend Error Handling**: Improve error reporting if necessary to provide more detail than a generic message.

## Impact
- **Affected specs**: Offer Studio (Listing).
- **Affected code**: 
  - `backend/src/modules/offer/api/products.py`
  - `backend/src/modules/offer/domain/offer.py`
  - `frontend/src/features/offer-studio/components/dashboard/offer-studio-dashboard.tsx`

## ADDED Requirements
### Requirement: Robust Data Loading
The system SHALL gracefully handle invalid data in the database without crashing the entire list endpoint.
- **WHEN** one offer has invalid data
- **THEN** log the error and skip the invalid offer OR return a partial list (if feasible), or fix the data structure to match schema.

## MODIFIED Requirements
### Requirement: Offer List API
**Fix**: Ensure `list_products` correctly serializes all offers, handling potential `null` or mismatching types in `specific_details` or enums.
