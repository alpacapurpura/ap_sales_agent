# Tasks

- [x] Task 1: Backend Database Schema Migration
  - [x] SubTask 1.1: Create `user_tenants` table model (SQLAlchemy).
  - [x] SubTask 1.2: Update `User` and `Tenant` models with M:N relationship.
  - [x] SubTask 1.3: Create Alembic migration script to create table and migrate existing `tenant_id` data.
  - [x] SubTask 1.4: Apply migration (remove `tenant_id` column from `users`).

- [x] Task 2: Backend Logic Updates
  - [x] SubTask 2.1: Update `dependencies.py` (`get_current_user`) to validate against `user.tenants` and handle `X-Tenant-ID`.
  - [x] SubTask 2.2: Update `routers/settings.py` (`get_user_profile`) to resolve tenant from context.
  - [x] SubTask 2.3: Create new endpoint `GET /api/v1/users/me/tenants` in `routers/users.py` (or `settings.py`).
  - [x] SubTask 2.4: Fix `admin/modules/users.py` to support M:N (list users by tenant via join, assign user to tenant).

- [x] Task 3: Frontend Implementation
  - [x] SubTask 3.1: Add `getTenants` method to `settingsApi` in `frontend/src/lib/api/settings.ts`.
  - [x] SubTask 3.2: Create `TenantSwitcher` component using shadcn DropdownMenu.
  - [x] SubTask 3.3: Replace static tenant name in `AppSidebar` with `TenantSwitcher`.
  - [x] SubTask 3.4: Implement switching logic (update localStorage `x-tenant-id`, reload).

# Task Dependencies
- Task 2 depends on Task 1.
- Task 3 depends on Task 2 (API availability).
