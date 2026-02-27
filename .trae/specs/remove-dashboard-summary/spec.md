# Remove Dashboard Summary Module Spec

## Why
The user requested to remove the "Resumen" (Summary) module from the client dashboard as it is no longer needed. This cleanup will simplify the codebase and the user interface.

## What Changes
- **Frontend**:
    - Remove "Resumen" item from the sidebar navigation.
    - Redirect the root path `/` to `/brand-settings`.
    - Delete the `dashboard` feature module (`frontend/src/features/dashboard`).
    - Delete the dashboard API client (`frontend/src/lib/api/dashboard.ts`).
- **Backend**:
    - Remove the dashboard router registration from `main.py`.
    - Delete the dashboard router (`backend/src/api/routers/dashboard.py`).
    - Delete the dashboard service (`backend/src/services/dashboard_service.py`).
    - Delete the dashboard schema (`backend/src/core/domain/dashboard_schema.py`).

## Impact
- **Affected specs**: Dashboard navigation and default route.
- **Affected code**:
    - `frontend/src/components/shared/layout/app-sidebar.tsx`
    - `frontend/src/app/(main)/(dashboard)/page.tsx`
    - `backend/src/main.py`
    - Deleted files in frontend and backend.

## ADDED Requirements
### Requirement: Root Redirect
The system SHALL redirect the root path `/` to `/brand-settings` for authenticated users.

## REMOVED Requirements
### Requirement: Dashboard Summary
**Reason**: User request.
**Migration**: None. The feature is removed completely.
