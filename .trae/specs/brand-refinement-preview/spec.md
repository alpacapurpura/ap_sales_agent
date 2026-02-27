# Brand Refinement Preview Spec

## Why
Users report that the "Refine Brand" feature in Brand Studio is not working as expected. Specifically, after running the refinement, the changes are not visible in the UI until a page reload, and there is no way to preview the changes before applying them. This leads to a confusing UX where the user feels the feature is broken.

## What Changes
- **Backend**: Introduce a `dry_run` mode in `BrandExtractionService` and the `extract-full-brand` endpoint to return extracted data without saving it to the database.
- **Frontend**:
  - Update `BrandStudioLayout` to support a "Preview Mode" where it renders a merged view of current `settings` + `previewData`.
  - Update `SmartFillCard` to use `dry_run=true` during refinement and pass the result to `BrandStudioLayout` for preview.
  - Implement a "Confirm Changes" flow where the user can review the previewed data in the actual UI sections before committing.
  - Add visual indicators (e.g., a banner) when in Preview Mode.

## Impact
- **Affected Specs**: Brand Studio.
- **Affected Code**:
  - `backend/src/core/services/brand_extraction_service.py`
  - `backend/src/api/routers/tools.py`
  - `frontend/src/features/brand/components/container/brand-studio-layout.tsx`
  - `frontend/src/features/brand/components/smart-fill/smart-fill-card.tsx`

## ADDED Requirements
### Requirement: Preview Mode
The system SHALL allow users to preview the results of a brand refinement operation in the actual UI components (Strategy, Story, etc.) without permanently saving the changes to the database.

#### Scenario: Refinement Flow
- **WHEN** user clicks "Refinar Información" in Smart Fill
- **THEN** the system extracts data using `dry_run=true`
- **AND** the UI updates to show the new values in their respective sections (e.g., StrategySection shows new UVP)
- **AND** a banner "Previewing Changes" is displayed
- **WHEN** user clicks "Aplicar Cambios"
- **THEN** the preview data is saved to the database and the UI refreshes.

## MODIFIED Requirements
### Requirement: Extraction Service
The `BrandExtractionService.extract_all` method SHALL accept a `dry_run` boolean parameter. If `true`, it MUST return the merged `BrandSettings` object WITHOUT committing changes to the database.

## REMOVED Requirements
N/A
