# Tasks

* [x] Task 1: Database & Backend Model Updates

  * [x] SubTask 1.1: Add `clerk_id` column to `User` model in `backend/src/services/db/models/user.py`.

  * [x] SubTask 1.2: Generate/Run migration or update schema (ensure `clerk_id` is indexable).

* [x] Task 2: Clerk Service Upgrade

  * [x] SubTask 2.1: Add `update_user_metadata(user_id, public_metadata)` method to `ClerkService` in `backend/src/services/clerk.py`.

  * [x] SubTask 2.2: Verify `create_user` returns the Clerk ID correctly.

* [x] Task 3: Streamlit Admin Enhancement

  * [x] SubTask 3.1: Update `render_tenant_manager` in `backend/src/admin/app.py` to store `clerk_id` when creating a user.

  * [x] SubTask 3.2: Add logic to call `clerk.update_user_metadata` with `tenant_id` and `role` immediately after creation.

* [x] Task 4: Backend API for Team Management

  * [x] SubTask 4.1: Create `TeamService` or add logic to `UserService` to handle user creation requests from Tenant Admins.

  * [x] SubTask 4.2: Implement `POST /api/v1/tenant/users`:

    * Check requester's Tenant.

    * Count existing users (Max 3 total).

    * Create in Clerk + Update Metadata + Create in DB.

* [x] Task 5: Frontend Security & Pages

  * [x] SubTask 5.1: Create `/no-permission` page (Standalone layout, contact info).

  * [x] SubTask 5.2: Update `middleware.ts` to check `auth().sessionClaims.metadata.tenant_id`. Redirect if missing.

  * [x] SubTask 5.3: Update `types/globals.d.ts` to type Clerk Custom Claims.

* [x] Task 6: Frontend Team Management UI

  * [x] SubTask 6.1: Create `TeamSettings` component in `/dashboard/settings`.

  * [x] SubTask 6.2: List current users.

  * [x] SubTask 6.3: Form to add new user (Name, Email, Password). Handle errors and limits.

* [x] Task 7: Production Access Documentation

  * [x] SubTask 7.1: Create `backend/src/admin/PRODUCTION_ACCESS.md` with step-by-step SSH and Streamlit usage guide.

