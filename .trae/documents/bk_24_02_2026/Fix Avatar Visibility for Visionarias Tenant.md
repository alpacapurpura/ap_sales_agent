I will resolve the issue by fixing the data, ensuring future integrity, and improving the backend design as requested.

### 1. Immediate Fix (Data)
I will manually update the "Valeria" avatar in the database to assign it to the "Visionarias" tenant. This will immediately make it visible in the Client Dashboard.
*   **Action**: Execute SQL `UPDATE avatar_definitions SET tenant_id = '...' WHERE name = 'Valeria';`

### 2. Prevent Recurrence (Script Fix)
I identified that the tenant initialization script (`backend/scripts/init_tenant_data.py`) updates `tenant_id` for many tables but is missing `avatar_definitions`. I will add it to the list.
*   **Action**: Edit `backend/scripts/init_tenant_data.py` to include `"avatar_definitions"` in `tables_to_update`.

### 3. Improve Design (Backend Logic)
To support "System Templates" (Global Avatars) in the future without errors, I will implement the robust "Read-Global / Write-Tenant" pattern in the repository.
*   **Action**: Modify `backend/src/services/db/repositories/avatar.py`:
    *   **Read**: Allow `list_avatars` and `get_by_id` to return avatars where `tenant_id` is User's Tenant **OR** `NULL`.
    *   **Write**: Enforce that `update`, `delete`, and `set_default` ONLY operate on avatars where `tenant_id` matches the User's Tenant.
