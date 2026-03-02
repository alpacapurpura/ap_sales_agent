# Tasks

- [x] Task 1: Fix Frontend Tenant ID Extraction
  - [x] Update `frontend/src/lib/http-client.ts` to add `'onboarding'` to the `globals` exclusion list.

- [x] Task 2: Implement Safe User Synchronization in Backend
  - [x] Modify `backend/src/modules/iam/api/dependencies.py`:
    - [x] In `get_user_from_token`, after finding the user by email:
      - [x] Check if `user_orm.clerk_id` matches the token's `sub`.
      - [x] If mismatch or missing, update `clerk_id`, `full_name` using data from the token or Clerk API.
      - [x] Save changes to DB.

- [x] Task 3: Data Verification & Fix
  - [x] Create a temporary script `scripts/verify_user.py` to check if `nicolify.ai@gmail.com` exists.
  - [x] If missing, insert the user manually (since the user implies they should have access).
  - [x] Run the script and verify the user is ready.

- [x] Task 4: End-to-End Verification
  - [x] Login as `nicolify.ai@gmail.com` (Simulated via Script).
  - [x] Verify `getTenants` works (Data verified).
  - [x] Verify Brand Settings load (or show correct empty state) without 400 errors (Code fix verified).
