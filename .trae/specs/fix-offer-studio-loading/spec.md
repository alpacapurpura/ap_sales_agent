# Fix Offer Studio Form Loading & Architecture Spec

## Why
The Offer Studio editor currently fails to load form data because the form wrappers independently fetch data using an incorrect route parameter (`offerId` instead of `id`). Additionally, the architecture relies on mixed form state management (global vs isolated) and an unclear file structure. The goal is to align with the "Brand Studio" pattern: atomic, isolated forms for each section that can be saved independently, with a clean directory structure.

## What Changes
- **Refactor Form Architecture**: 
  - Adopt the "Brand Studio" pattern where each section is an independent form with its own "Save" button.
  - Remove the global "Save" button from the `OfferEditSheetManager` footer.
  - Initialize section forms with data passed from the main `OfferEditor` (via `defaultValues`), eliminating redundant API calls.
- **Clean Up File Structure**:
  - Delete `frontend/src/features/offer-studio/components/forms/wrappers/`.
  - Create/Move atomic form components directly to `frontend/src/features/offer-studio/components/forms/` (e.g., `StrategyForm.tsx`, `PricingForm.tsx`).
  - Move `OfferEditSheetManager` to `frontend/src/features/offer-studio/components/forms/`.
  - Move `SectionFormWrapper` to `frontend/src/features/offer-studio/components/forms/`.
- **Update Configuration**:
  - Update `offer-builder-config.ts` to use the new form components.

## Impact
- **Affected Specs**: Offer Studio Editor
- **Affected Code**: 
  - `frontend/src/features/offer-studio/components/editor/OfferEditor.tsx`
  - `frontend/src/features/offer-studio/components/editor/OfferEditSheetManager.tsx` (Move & Refactor)
  - `frontend/src/features/offer-studio/components/forms/wrappers/*.tsx` (Delete/Move)
  - `frontend/src/features/offer-studio/config/offer-builder-config.ts`

## ADDED Requirements
### Requirement: Atomic Forms
Each section (Strategy, Pricing, etc.) SHALL be implemented as an independent form component that:
1. Accepts `initialValues` (or `defaultValues`) and `onSave` callback.
2. Manages its own validation using `SectionFormWrapper`.
3. Contains its own "Save" button.
4. Updates the backend via `saveSection` and triggers a refresh of the main offer state.

### Requirement: Clean Directory Structure
All form-related components SHALL be located in `frontend/src/features/offer-studio/components/forms/`, replacing the nested `wrappers` directory.

## REMOVED Requirements
### Requirement: Footer Save Button
The `OfferEditSheetManager` SHALL NOT display a generic "Guardar Cambios" button in the footer, delegating this responsibility to the individual form components.
