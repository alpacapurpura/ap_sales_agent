# Multi-Tenant Switching Spec

## Why
Currently, the system enforces a strict 1:1 relationship between Users and Tenants. This prevents a single user (e.g., an agency admin or a user with multiple businesses) from accessing multiple workspaces using the same account. The goal is to allow users to belong to multiple tenants and switch between them in the UI.

## What Changes
- **Backend**:
  - Convert User-Tenant relationship from One-to-Many (1:N) to Many-to-Many (M:N).
  - Introduce `user_tenants` association table.
  - Update `User` model to remove `tenant_id` and add `tenants` relationship.
  - Update Authentication logic (`get_current_user`) to resolve tenant context based on `X-Tenant-ID` header and the new M:N relationship.
  - Add API endpoint to list all tenants for the current user.
- **Frontend**:
  - Create a `TenantSwitcher` component in the Sidebar.
  - Update API client to handle `X-Tenant-ID` persistence and injection.
  - Update User Profile logic to support context-aware data.

## Impact
- **Database**:
  - **BREAKING**: Removes `tenant_id` column from `users` table.
  - Adds `user_tenants` table.
- **API**:
  - `GET /api/v1/users/me/tenants` (New).
  - `GET /api/v1/settings/profile` (Modified behavior: context-aware).
- **Admin Panel**:
  - `admin/modules/users.py` needs significant refactoring to handle M:N user management.

## ADDED Requirements
### Requirement: Multi-Tenant Data Structure
The system SHALL store user-tenant associations in a dedicated table `user_tenants` containing `user_id`, `tenant_id`, and `role`.

### Requirement: Tenant Listing API
The system SHALL provide an endpoint `GET /api/v1/users/me/tenants` that returns a list of all tenants associated with the authenticated user.

### Requirement: Context-Aware Authentication
The system SHALL use the `X-Tenant-ID` header to determine the active tenant context.
- **WHEN** `X-Tenant-ID` is present: Validate user belongs to that tenant.
- **WHEN** `X-Tenant-ID` is missing: Default to the user's first available tenant or return a 403 if none.

### Requirement: Frontend Tenant Switcher
The Sidebar SHALL display the current tenant's name and allow switching to other associated tenants via a dropdown.

#### Scenario: Switching Tenant
- **WHEN** user selects a different tenant "Tenant B" from the dropdown
- **THEN** the application stores "Tenant B" ID in local storage
- **AND** reloads/refreshes to apply the new `X-Tenant-ID` context to all data fetches.

## MODIFIED Requirements
### Requirement: User Model
**Modified**: `User` entity no longer has a single `tenant_id`. It has a collection of `tenants`.
**Migration**: Existing `tenant_id` data must be migrated to `user_tenants` table.

### Requirement: Admin User Management
**Modified**: The Admin Panel must allow assigning an existing user (by email) to a new tenant, creating a new entry in `user_tenants`, instead of failing with "User already exists".

## REMOVED Requirements
### Requirement: Single Tenant Constraint
**Reason**: Obsolete. Users can now belong to multiple organizations.
