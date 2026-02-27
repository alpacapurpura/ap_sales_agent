# Reorganize Offer Studio Structure

## Why
The current structure of `frontend/src/features/offer-studio` is cluttered, with files scattered in `components/` root and mixed concerns. The user requested a clean, atomic organization focusing on the "Individual Offer" (Editor) view, including the Landing Page builder and AI functions.

## What Changes
- **Consolidate Editor**: Create `components/editor/` to house all editor-related code (`DynamicOfferEditor`, `sections`, `forms`, `layout`).
- **Consolidate Dashboard**: Move `OfferStudioView.tsx` into `components/dashboard/` and organize dashboard components.
- **Integrate Landing Builder**: Move `frontend/src/features/landing-builder` to `frontend/src/features/offer-studio/components/landing`.
- **Cleanup**: Remove unused files and folders.
- **Update Imports**: Fix all references to moved files.

## Impact
- **Affected Specs**: Offer Studio, Landing Builder.
- **Affected Code**:
  - `frontend/src/features/offer-studio/**/*`
  - `frontend/src/features/landing-builder/**/*` (Moved)
  - `frontend/src/app/**/*` (Import updates)

## New Structure
```
src/features/offer-studio/
├── api/
├── components/
│   ├── dashboard/              # Dashboard View
│   │   ├── OfferStudioView.tsx
│   │   ├── OfferStudioDashboard.tsx
│   │   ├── OfferCard.tsx
│   │   └── ...
│   ├── editor/                 # Editor View
│   │   ├── OfferEditor.tsx     (Renamed from DynamicOfferEditor)
│   │   ├── layout/             
│   │   │   └── OfferEditorLayout.tsx
│   │   ├── sections/           
│   │   ├── forms/              
│   │   ├── ui/                 
│   │   │   ├── OfferContextPanel.tsx
│   │   │   └── ...
│   │   └── components/         
│   │       ├── AIAssistButton.tsx
│   │       ├── AssetUploader.tsx
│   │       └── ...
│   └── landing/                # Landing Page Builder
│       ├── editor/
│       ├── blocks/
│       └── ...
```

## ADDED Requirements
### Requirement: Atomic Structure
The module SHALL follow a strictly hierarchical structure where sub-components are located near their parents or in dedicated directories (`editor`, `dashboard`, `landing`).

## MODIFIED Requirements
### Requirement: Landing Page Location
The Landing Page Builder SHALL be located within `features/offer-studio/components/landing` to reflect its primary usage context.

## REMOVED Requirements
### Requirement: Legacy Steps
The `components/steps` directory and its contents SHALL be removed (already done).
