# Brand Forms Refactor Spec

## Why
The current forms in `src/features/brand/components/forms` have tight coupling between logic (state, handlers) and presentation (UI). This limits reuse and testability. The goal is to separate the "dumb" UI (presentation) from the "smart" logic (container/manager).

## What Changes
- **Refactor**: Split existing form components into `[Name]Form` (Presentation) and `[Name]Manager` (Logic) where applicable, or keep `[Name]Form` as pure presentation and lift state to `EditSheetManager` or a new `[Name]Container`.
- **Standardize**: Ensure all forms accept `initialData`, `onSubmit`, and `isSubmitting` props.
- **Pattern**: Apply the "Container/Presentation" pattern across all forms in `src/features/brand/components/forms`.

## Impact
- **Affected specs**: None directly.
- **Affected code**: All files in `src/features/brand/components/forms/*.tsx`.

## MODIFIED Requirements
### Requirement: Form Architecture
All forms MUST be purely presentational components.
State management and API calls MUST be handled by a parent container or custom hook.

## Atomic Persistence Strategy
The user has explicitly requested **Atomic Persistence** for all modules, similar to `AvatarManager`. This means:
- **Managers are Smart**: `TeamManager`, `AuthorityManager`, `TestimonialsManager` will fetch and save data directly to their respective API endpoints (`/api/v1/team`, `/api/v1/authority`, etc.).
- **Decoupling**: They will NO LONGER rely on `BrandStudioLayout` passing down a monolithic `settings` object and update handlers.
- **Independence**: Each manager manages its own loading state, error handling, and React Query cache invalidation.

### API Implications
We must ensure the backend supports granular updates for these collections.
- `Avatar` already has granular CRUD.
- `Team`, `Authority`, `Testimonials` are currently stored inside the `brand_settings` JSON blob in `Tenant`.
- **Strategy**: We will keep the storage as is (inside JSON) for now, but the **Frontend Managers** will abstract this by calling `updateBrandSettings` with just their specific key (e.g., `updateBrandSettings({ team: newTeam })`). Ideally, in the future, these should be separate tables, but for now, we simulate atomicity via the API client.

## Migration Plan (Per Form)

### 1. IdentityForm & Simple Forms
- **Change**: They will become self-contained managers or use a `useBrandSettings` hook that exposes atomic update methods (`updateIdentity`, `updateLegal`, etc.).
- **Refactor**: Move logic into `[Name]Manager.tsx` which uses the hook, and keep `[Name]Form.tsx` pure.

### 2. Team, Authority, Testimonials
- **Change**: 
    - `TeamManager`: Fetches team data (or takes it from context), handles "Add/Edit/Delete" locally or via optimistic updates, and saves to backend.
    - **Persistence**: Since we don't have a `POST /api/v1/team` endpoint (it's part of settings), the Manager will call `brandSettingsApi.update({ team: newTeam })`. This is "atomic enough" from the frontend perspective.

### 3. Folder Structure
- `components/team/TeamManager.tsx` (Logic + API)
- `components/team/TeamList.tsx` (UI)
- `components/team/TeamMemberForm.tsx` (UI)

