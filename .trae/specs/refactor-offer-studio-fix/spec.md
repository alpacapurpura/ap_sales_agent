# Refactor & Fix Offer Studio Visualization Spec

## Why
The Offer Studio dashboard is failing to render offer cards despite data being present. Previous attempts introduced technical debt (commented out filters, loose type checking) instead of addressing the root cause. We need a robust, tested solution that cleans up the "spaghetti code" and ensures correct data flow and rendering.

## What Changes
- **Clean Up**: Remove all temporary "fixes" and commented-out code in `offer-studio-dashboard.tsx`.
- **Refactor Adapter**: Ensure the `backendToFrontend` adapter handles data transformation correctly and robustly, with proper type safety, not just "OR" hacks.
- **Implement UI Tests**: Create a proper test suite for the dashboard components using Vitest/React Testing Library to verify rendering logic *before* deploying to the browser.
- **Root Cause Fix**: Identify exactly why the data structure mismatches the component expectations (likely Enum case sensitivity or undefined optional fields) and fix it at the source (Adapter/Type definition).

## Impact
- Affected specs: Offer Studio (Listing & Rendering).
- Affected code:
  - `frontend/src/features/offer-studio/components/dashboard/offer-studio-dashboard.tsx`
  - `frontend/src/features/offer-studio/api/adapter.ts`
  - `frontend/src/features/offer-studio/components/dashboard/offer-card.tsx`
  - **NEW**: `frontend/src/features/offer-studio/tests/dashboard.test.tsx` (Test file)

## ADDED Requirements
### Requirement: Verifiable Rendering
The dashboard components MUST be verified via unit tests that simulate the exact data shape returned by the backend.
- **WHEN** the API returns a list of offers with various states/types
- **THEN** the `OfferCard` components MUST be present in the DOM with correct titles and badges.

## MODIFIED Requirements
### Requirement: Strict Type Handling
**Fix**: The frontend types (`OfferType`, `OfferStatus`) and the Adapter must align perfectly. No more "casting to unknown" or loose string comparisons. We will enforce strict Enum matching in the adapter.

## REMOVED Requirements
### Requirement: Legacy Code
**Remove**: Any `// TODO: Technical Debt` comments and disabled logic introduced in the previous debugging session.
