# Tasks

- [ ] Task 1: Implement API Cache Partitioning
  - [ ] Modify `frontend/src/lib/http-client.ts` to read `x-tenant-id` from localStorage.
  - [ ] Append `_t=${tenantId}` to the URL search parameters for every GET request.
  - [ ] Ensure this does not break existing query parameters.

- [ ] Task 2: Enhance Tenant Switcher
  - [ ] Modify `frontend/src/components/shared/layout/tenant-switcher.tsx`.
  - [ ] Update `handleTenantChange` to redirect to the current path with `?org=${tenantId}` instead of just reloading.
  - [ ] Ensure the application reads the `org` query param on load if `localStorage` is empty (optional robustness).

- [ ] Task 3: Verification & Cleanup
  - [ ] Verify that switching tenants immediately reflects new data in `Brand Settings`.
  - [ ] Verify that no "stale" data appears in the Network tab (status 200 from server, not "disk cache" with old data).
