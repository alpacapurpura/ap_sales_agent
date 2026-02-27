# Tenant Routing Refactor Spec

## Why
To adhere to SaaS best practices and permanently resolve data isolation issues, we are migrating from a hidden state (localStorage) model to a **URL-based Tenancy** model. This ensures:
1.  **Deep Linking**: Users can bookmark and share organization-specific URLs.
2.  **Cache Isolation**: Browsers naturally partition cache based on the URL, preventing data leaks between tenants.
3.  **Scalability**: Simplifies multi-tenant architecture by making the tenant context explicit in the route.

## What Changes
- **Routing Structure**: Move all dashboard routes from `(main)/(dashboard)` to `(main)/[tenantId]`.
- **URL Format**: URLs will change from `/brand-settings` to `/[tenantId]/brand-settings`.
- **Root Redirection**: The root `/` path will automatically redirect to the user's last active tenant or the first available one.
- **Tenant Switcher**: Switching tenants will navigate to the new URL `/[newTenantId]/...` instead of reloading the page.
- **API Client**: `fetchClient` will extract the tenant ID directly from the URL path as the source of truth, falling back to localStorage only if necessary. It will also append `?_t=` to GET requests for extra cache safety.

## Impact
- **Breaking Changes**: Old bookmarks to `/brand-settings` will 404. We will add a redirect or let the user navigate from root.
- **Affected Files**:
    - `src/app/(main)/(dashboard)/**/*` (Moved)
    - `src/components/shared/layout/app-sidebar.tsx` (Link updates)
    - `src/components/shared/layout/tenant-switcher.tsx` (Logic update)
    - `src/lib/http-client.ts` (Tenant extraction logic)
    - `src/middleware.ts` (Optional route protection)

## ADDED Requirements
### Requirement: URL-Based Tenancy
The system SHALL organize all dashboard routes under a dynamic `[tenantId]` segment.
- **WHEN** a user accesses `/tenant-a/dashboard`
- **THEN** the system must derive the tenant context from the URL.

### Requirement: Root Redirection
The system SHALL redirect authenticated users from `/` to `/[tenantId]/dashboard`.

## MODIFIED Requirements
### Requirement: API Context Injection
**Old**: Inject `X-Tenant-ID` from `localStorage`.
**New**: Inject `X-Tenant-ID` derived from the current URL path segment `[tenantId]`.

### Requirement: Tenant Switching
**Old**: `localStorage.setItem` + `reload()`.
**New**: `router.push('/[newTenantId]/[currentPath]')`.
