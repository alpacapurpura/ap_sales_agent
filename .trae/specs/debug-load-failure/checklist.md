# Debugging Checklist

## 1. Environment & Network
- [ ] `NEXT_PUBLIC_API_URL` is set to `http://localhost:8000` (for local dev) or a valid HTTPS URL.
- [ ] Browser console shows NO "Network Error" or "CORS Policy" errors for API requests.
- [ ] Browser network tab shows requests to `/api/v1/...` with status `200 OK`.

## 2. Authentication (Frontend)
- [ ] LocalStorage contains `x-tenant-id` after login.
- [ ] Network requests include `Authorization: Bearer eyJ...` header.
- [ ] Network requests include `X-Tenant-ID: <uuid>` header.

## 3. Backend Data (Postgres Verification)
- [x] User `christian.revilla.m@gmail.com` exists in `users` table. (Verified)
- [ ] User has a corresponding entry in `user_tenants` table linking to a valid tenant.
- [ ] The linked tenant exists in `tenants` table.

## 4. API Response
- [ ] `/api/v1/iam/settings/profile` returns JSON with `tenant` object.
- [ ] `/api/v1/iam/users/me/tenants` returns array with at least one tenant.
- [ ] `/api/v1/brand/settings` returns valid JSON (not 500 error).

## 5. UI Logic
- [ ] `TenantGuard` allows rendering for authenticated user.
- [ ] Sidebar displays user name "Christian Revilla".
