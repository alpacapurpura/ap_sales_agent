# Fix Brand Settings & Refactor to Sections Spec

## Why
1.  **"Error al cargar configuración"**: Caused by strict Backend validation failing on existing/partial data (500 Internal Server Error).
2.  **Independent Saving Support**: To ensure each section (Identity, Strategy, etc.) can be saved independently without validating unrelated missing data, the Backend models must be flexible (Optional fields).
3.  **Architecture Improvement**: The user requested moving data-handling components to a `sections/` directory for better organization.

## What Changes

### Backend (`backend/src/modules/brand`)
- **Relax Validation**: Modify `BrandIdentity`, `BrandStrategy`, `BrandStory`, `BrandTeam` Pydantic models to make ALL fields `Optional` (defaulting to `None`).
    - **Reason**: Supports partial updates and loading of legacy data.
- **Add Fields**: Add `brand_name: Optional[str]` to `BrandIdentity`.

### Frontend (`frontend/src/features/brand`)
- **Refactor Structure**: Move feature components into `sections/` directory:
    - `components/identity` -> `sections/identity`
    - `components/strategy` -> `sections/strategy`
    - `components/story` -> `sections/story`
    - `components/team` -> `sections/team`
    - `components/contact` -> `sections/contact`
    - `components/visuals` -> `sections/visuals`
    - `components/voice` -> `sections/voice`
    - `components/authority` -> `sections/authority`
    - `components/methodology` -> `sections/methodology`
    - `components/testimonials` -> `sections/testimonials`
    - `components/avatars` -> `sections/avatars`
    - `components/gallery` -> `sections/gallery`
- **Update Imports**: Fix all import paths in `BrandStudioLayout` and `BrandNavRail`.
- **Update Types**: Sync `BrandIdentity` interface (add `brand_name`, make fields optional).
- **Fix Logic**:
    - Update `BrandStudioLayout` to access `visuals.logo_url` and `contact.website`.
    - Fix `hasExistingData` to check `brand_name`.

## Impact
- **Affected Specs**: Brand Studio.
- **Affected Code**: 
    - Backend: `models.py`.
    - Frontend: `types/index.ts`, `components/` (moved to `sections/`), `BrandStudioLayout`.

## ADDED Requirements
### Requirement: Partial Data Support
The system SHALL support saving and loading partial Brand Settings.
- **WHEN** a user saves only the Identity section.
- **THEN** the backend updates only the Identity fields, ignoring validation errors for missing Strategy/Story fields.

### Requirement: Section-Based Architecture
The frontend codebase SHALL be organized by functional sections in `src/features/brand/sections`.

## MODIFIED Requirements
### Requirement: Brand Name
`BrandIdentity` SHALL include `brand_name`.
