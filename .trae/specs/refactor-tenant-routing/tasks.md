# Tasks

- [ ] Task 1: Route Restructuring
  - [ ] Create directory `src/app/(main)/[tenantId]`.
  - [ ] Move `src/app/(main)/(dashboard)/layout.tsx` to `src/app/(main)/[tenantId]/layout.tsx`.
  - [ ] Move all route directories (e.g., `brand-settings`, `offer-studio`, `admin`, `sales`, `settings`, `audit`, `authority`, `avatars`, `connections`, `onboarding`) from `src/app/(main)/(dashboard)/` to `src/app/(main)/[tenantId]/`.
  - [ ] Create a root page `src/app/(main)/page.tsx` that redirects to the user's tenant dashboard.

- [ ] Task 2: Update Sidebar & Navigation
  - [ ] Modify `src/components/shared/layout/app-sidebar.tsx` to accept `tenantId` (from params or context).
  - [ ] Update all `Link` components in the sidebar to prefix URLs with `/${tenantId}`.
  - [ ] Ensure the `SidebarProvider` or context exposes the current `tenantId`.

- [ ] Task 3: Update Tenant Switcher
  - [ ] Modify `src/components/shared/layout/tenant-switcher.tsx`.
  - [ ] Update `handleTenantChange` to use `router.push` to the new tenant's URL (preserving the sub-path if possible, or defaulting to dashboard).
  - [ ] Remove `window.location.reload()`.

- [ ] Task 4: Update API Client & Cache Safety
  - [ ] Modify `src/lib/http-client.ts`.
  - [ ] Implement logic to extract `tenantId` from `window.location.pathname` (regex matching `^/([^/]+)/`).
  - [ ] Retain `localStorage` logic as a fallback.
  - [ ] Append `?_t=${tenantId}` to GET requests to guarantee browser cache isolation.

- [ ] Task 5: Verify & Fix Imports
  - [ ] Check for broken imports after moving files.
  - [ ] Verify that `layout.tsx` in `[tenantId]` correctly wraps the content.
