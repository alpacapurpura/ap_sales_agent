# Secure Tenant Switching & Data Isolation Spec

## Why
Currently, switching organizations (tenants) leaves "stale" data from the previous organization visible in the frontend (e.g., in Brand Strategy/Positioning). This is a **critical security vulnerability** (Data Leakage) caused by:
1.  **Browser Caching**: API endpoints (e.g., `/api/v1/settings/brand`) are identical for all tenants. The browser caches the response from Tenant A and serves it for Tenant B because it doesn't respect the `X-Tenant-ID` header as a cache key.
2.  **Shared URL State**: The application uses the same URL (`/brand-settings`) for all tenants, relying solely on `localStorage` which is invisible to the browser's HTTP cache logic.

## What Changes
- **Network Layer (`fetchClient`)**: Automatically append `?_tenantId=${id}` to all GET requests. This forces the browser to treat requests as distinct resources, guaranteeing cache isolation.
- **Tenant Switcher**: Update logic to ensure a clean state reset.
- **Best Practice Alignment**: While a full move to `/org/[id]/...` routing is the long-term architectural goal, we will implement **Query-Based Isolation** (`?org=...` and `?_tenantId=...`) immediately to resolve the vulnerability without a high-risk refactor of the entire routing tree.

## Impact
- **Security**: Eliminates cross-tenant data leakage.
- **Performance**: Slight increase in network requests (less caching between tenants), which is desired for security.
- **Affected Code**: `frontend/src/lib/http-client.ts`, `frontend/src/components/shared/layout/tenant-switcher.tsx`.

## ADDED Requirements
### Requirement: API Cache Partitioning
The system SHALL append the current `tenant_id` as a query parameter (e.g., `_t=...`) to all outgoing API GET requests.
- **WHEN** user is in Tenant A and requests data
- **THEN** the request URL must be unique to Tenant A.

### Requirement: Visual Tenant Context
The system SHOULD reflect the active tenant in the browser URL (e.g., via `?org=...`) to aid in deep linking and further prevent browser cache collisions.

## MODIFIED Requirements
### Requirement: Tenant Switching Logic
**Old**: Set `localStorage` and `reload()`.
**New**: Set `localStorage`, update URL query param to `?org=${id}`, and `reload()` (or redirect).

## REMOVED Requirements
N/A
