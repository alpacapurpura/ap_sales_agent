# Fix Multi-Tenant Data Leak Spec

## Why
A critical data leak was identified where users logged into one tenant (e.g., 'alpacapurpura') could see data from another tenant (e.g., 'visionarias'). This occurs because the backend resolves users solely by email without validating the active tenant context, leading to incorrect user/tenant association when an email exists in multiple tenants or when session state is ambiguous.

## What Changes
- **Backend (Database)**: Remove the unique constraint on `User.email`. Add a composite unique constraint on `(email, tenant_id)` to allow the same email address to exist in multiple tenants (true multi-tenancy).
- **Backend (Auth)**: Update `get_current_user` dependency to strictly validate the `X-Tenant-ID` header against the resolved user's `tenant_id`. If they do not match, reject the request (403 Forbidden).
- **Frontend (API)**: Update `fetchClient` to automatically inject the `X-Tenant-ID` header from the current session/metadata into ALL API requests.
- **Tenant Model**: Add `clerk_org_id` to the `Tenant` model to support future integration with Clerk Organizations.

## Impact
- **BREAKING**: API requests without a valid `X-Tenant-ID` header may now fail if the user is associated with multiple tenants (ambiguous resolution) or if strict validation is enabled.
- **Security**: Data isolation is now enforced at the API gateway level, preventing cross-tenant leaks.

## ADDED Requirements
### Requirement: Strict Tenant Validation
The system SHALL reject any API request where the `X-Tenant-ID` header does not match the authenticated user's `tenant_id`.

#### Scenario: Mismatch Prevention
- **WHEN** user 'chris@example.com' (linked to Tenant A) sends a request with `X-Tenant-ID: Tenant-B`
- **THEN** the system returns 403 Forbidden.

### Requirement: Multi-Tenant User Support
The system SHALL allow the same email address to be registered in multiple tenants as distinct User entities.

#### Scenario: User in Two Tenants
- **WHEN** 'chris@example.com' is created in Tenant A and Tenant B
- **THEN** the database stores two distinct User records with different `tenant_id`s.

## MODIFIED Requirements
### Requirement: User Identification
**Modified**: `get_current_user` now uses `email` AND `X-Tenant-ID` (or Clerk Org ID) to resolve the specific User record.

## REMOVED Requirements
### Requirement: Global Unique Email
**Reason**: Incompatible with multi-tenancy where users belong to isolated environments.
**Migration**: Existing users with unique emails will remain valid. New users can duplicate emails across tenants.
