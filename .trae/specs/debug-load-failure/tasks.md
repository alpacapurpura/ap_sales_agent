# Debugging Tasks

- [ ] **Task 1: Verify Authentication & Token Propagation**
  - [ ] Check if `fetchClient` is correctly appending `Authorization: Bearer <token>`.
  - [ ] Check if `fetchClient` is correctly appending `X-Tenant-ID`.
  - [ ] Verify that `middleware.ts` is not stripping headers.

- [ ] **Task 2: Verify Backend Accessibility (Network)**
  - [ ] Confirm `NEXT_PUBLIC_API_URL` is reachable from the browser (CORS check).
  - [ ] Verify that the Cloudflare tunnel (if used) is routing traffic to the correct container.

- [ ] **Task 3: Verify Data Integrity for User**
  - [ ] Confirm user `christian.revilla.m@gmail.com` has a valid `tenant_id` in `publicMetadata` (Clerk).
  - [ ] Confirm user exists in Postgres `users` table (Verified: Yes).
  - [ ] Confirm user is linked to a tenant in `user_tenants` table.
  - [ ] Confirm that tenant exists in `tenants` table.

- [ ] **Task 4: Verify API Endpoints**
  - [ ] Test `GET /api/v1/iam/settings/profile` manually with a valid token.
  - [ ] Test `GET /api/v1/iam/users/me/tenants` manually.
  - [ ] Test `GET /api/v1/brand/settings` manually.

- [ ] **Task 5: Frontend Component Logic**
  - [ ] Audit `TenantGuard` to ensure it doesn't block valid users with missing metadata (fallback logic).
  - [ ] Check `AppSidebar` error handling (does it crash if profile fails?).
