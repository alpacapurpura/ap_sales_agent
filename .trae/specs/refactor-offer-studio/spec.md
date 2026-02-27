# Refactor Offer Studio Spec

## Why
Improve the maintainability and scalability of the Offer Studio editor by adopting a Domain-Driven Design (DDD) structure, similar to Brand Studio. Ensure backend updates are atomic to prevent data loss and improve validation.

## What Changes
- **Backend**:
    - Introduce granular Pydantic schemas (`OfferIdentityUpdate`, `OfferStrategyUpdate`, etc.) for each section.
    - Create specific `PATCH` endpoints (e.g., `/{product_id}/identity`) instead of a monolithic update.
- **Frontend**:
    - Reorganize `components/editor/forms` and `components/editor/preview` into `components/editor/sections/{domain}`.
    - Each domain folder (e.g., `sections/identity`) will contain both the Form and Preview components.
    - Update `offer-builder-config.ts` to reflect the new paths.
    - Update API client to use the new atomic endpoints.

## Impact
- **Affected Specs**: None directly.
- **Affected Code**:
    - `frontend/src/features/offer-studio/components/editor/`
    - `backend/src/api/routers/products.py`
    - `backend/src/core/domain/offer/schema.py`
- **Breaking Changes**: None expected, as this is a refactor of the internal structure of the Offer Studio. Existing data should be preserved.

## ADDED Requirements
### Requirement: Atomic Updates
The system SHALL provide specific API endpoints for updating each section of an offer independently.

#### Scenario: Update Identity
- **WHEN** user updates the Identity form (Name, Description).
- **THEN** only the identity fields are updated in the backend via `PATCH /products/{id}/identity`.

## MODIFIED Requirements
### Requirement: Component Structure
- **Old**: `forms/IdentityForm.tsx`, `preview/IdentityPreview.tsx`.
- **New**: `sections/identity/IdentityForm.tsx`, `sections/identity/IdentityPreview.tsx`.
