# Tenant & User Management Upgrade Spec

## Why
The current system allows Tenant creation but lacks a robust, secure flow for User permissions and multi-user management within a Tenant. Users without a tenant can potentially access the dashboard, and there is no limitation on the number of users per tenant. The Client Dashboard needs to be aware of the user's context (Tenant) efficiently without constant DB lookups.

## What Changes
- **Database**: Add `clerk_id` to `users` table for reliable linking.
- **Backend**: 
  - Update `ClerkService` to support Metadata updates (store `tenant_id` in Clerk).
  - Update `admin/app.py` to sync `clerk_id` and Metadata upon creation.
  - New Endpoint `POST /api/v1/tenant/users` for Tenant Admins to create up to 2 sub-users.
- **Frontend**:
  - **Security**: Update Middleware to check Clerk Metadata for `tenant_id`. Redirect to `/no-permission` if missing.
  - **UI**: New `/no-permission` page.
  - **UI**: New "Team" section in Settings to manage the 2 allowed sub-users.
- **Documentation**: New `PRODUCTION_ACCESS.md` guide.

## Impact
- **Security**: High. Unassociated users are completely blocked from the Dashboard.
- **Performance**: High. Middleware uses JWT claims (Metadata) instead of DB calls for permission checks.
- **UX**: Admins can now manage their team autonomously.

## ADDED Requirements
### Requirement: Clerk Metadata Sync
The system SHALL update Clerk User Public Metadata with `tenant_id` and `role` whenever a user is created or updated in the system.
**Reason**: To allow Frontend Middleware to make zero-latency permission decisions.

### Requirement: Tenant User Limit
The system SHALL prevent creating more than 2 additional users (3 total including Admin) per Tenant.

### Requirement: No Permission Isolation
The system SHALL redirect any authenticated user without a `tenant_id` in their metadata to `/no-permission`.
- This page must NOT have the Dashboard Layout (Sidebar/Header).
- It must show the contact email `hola@alpacapurpura.lat`.

## MODIFIED Requirements
### Requirement: Streamlit User Creation
The Streamlit Admin panel SHALL:
1. Create the user in Clerk.
2. Store `clerk_id` in local DB.
3. Update Clerk Metadata with `tenant_id`.
