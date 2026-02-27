# Tasks

- [x] Task 1: Backend Database Migration
  - [x] SubTask 1.1: Generate Alembic migration to drop unique constraint on `users.email`.
  - [x] SubTask 1.2: Add composite unique constraint `(email, tenant_id)` to `users` table.
  - [x] SubTask 1.3: Add `clerk_org_id` column to `tenants` table (nullable).
  - [x] SubTask 1.4: Apply migration to local database.

- [x] Task 2: Backend Auth Logic Update
  - [x] SubTask 2.1: Update `get_current_user` in `src/api/dependencies.py` to accept `X-Tenant-ID` header.
  - [x] SubTask 2.2: Modify user lookup query to filter by `tenant_id` if header is present.
  - [x] SubTask 2.3: Implement strict validation: if resolved user's tenant != header tenant, raise 403.
  - [x] SubTask 2.4: Update `get_tenant_context` to rely on the strictly resolved user.

- [x] Task 3: Frontend API Client Update
  - [x] SubTask 3.1: Modify `src/lib/http-client.ts` (or equivalent) to retrieve `tenant_id` from Clerk session/metadata.
  - [x] SubTask 3.2: Inject `X-Tenant-ID` header into all `fetchClient` requests.
  - [x] SubTask 3.3: Verify `OrganizationSwitcher` (if used) updates the local storage/session correctly.

- [x] Task 4: Verification & Testing
  - [x] SubTask 4.1: Create a test user in Tenant A and Tenant B with the same email.
  - [x] SubTask 4.2: Verify login to Tenant A shows Tenant A data.
  - [x] SubTask 4.3: Verify login to Tenant B shows Tenant B data.
  - [x] SubTask 4.4: Verify cross-tenant request (Token A + Header B) is blocked.

# Task Dependencies
- Task 2 depends on Task 1 (Schema change needed for query update).
- Task 4 depends on Task 2 and Task 3.
