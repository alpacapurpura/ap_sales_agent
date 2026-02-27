# Refactor Offer Studio: Structure, Preview Fix, and Full Form Migration

## Why
The Offer Studio is transitioning from a "Section" based architecture (where sections were just UI components) to a "Form" based architecture (where each section is an atomic, self-saving form). 
Currently:
1.  The directory structure is fragmented (`forms` and `preview` are outside `editor`).
2.  The preview functionality is broken because it doesn't receive data correctly.
3.  Most sections (Psychology, Promise, etc.) are disabled because they point to `PlaceholderForm` in the config, even though their UI logic exists in `sections/`.

## What Changes
- **Directory Structure**:
  - Move `forms` and `preview` into `frontend/src/features/offer-studio/components/editor/`.
- **Preview Logic**:
  - Fix `OfferLivePreview` to pass form data to preview components.
  - Update all Preview components to accept `data` prop.
- **Form Migration (The Big Shift)**:
  - Convert ALL existing `Section` components (in `editor/sections/`) into fully functional `Form` components (in `editor/forms/`).
  - This involves wrapping the UI logic of each section with `SectionFormWrapper`, handling `defaultValues`, and implementing `onSave`.
  - Merge existing forms (`Strategy`, `Identity`, `Pricing`) with their corresponding sections to eliminate the split.
- **Configuration**:
  - Update `offer-builder-config.ts` to use the new atomic Forms for ALL sections.
- **Cleanup**:
  - Delete `frontend/src/features/offer-studio/components/editor/sections/` after migration.

## Impact
- **Affected Specs**: Offer Studio Editor
- **Affected Code**:
  - `frontend/src/features/offer-studio/components/editor/forms/*.tsx` (New & Updated)
  - `frontend/src/features/offer-studio/components/editor/preview/*.tsx` (Moved & Updated)
  - `frontend/src/features/offer-studio/components/editor/OfferLivePreview.tsx`
  - `frontend/src/features/offer-studio/config/offer-builder-config.ts`

## ADDED Requirements
### Requirement: Atomic Forms for All Sections
Every section defined in `OFFER_BUILDER_CONFIG` (Strategy, Psychology, Promise, etc.) SHALL have a corresponding Atomic Form component that handles its own state and saving.

### Requirement: Preview Data Flow
The `OfferLivePreview` component SHALL pass the current form values to all preview components via a `data` prop to ensure real-time updates.

## REMOVED Requirements
### Requirement: Section Components
The standalone `Section` components (e.g., `StrategySection`) SHALL be removed, as their logic will be integrated directly into the Atomic Forms (`StrategyForm`).
