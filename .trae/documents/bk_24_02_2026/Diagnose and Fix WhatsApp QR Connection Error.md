I will perform the following steps to diagnose and fix the WhatsApp connection error, ensuring strict adherence to the **multi-tenant architecture**:

1. **Analyze Runtime Logs**:

   * Execute `docker logs visionarias_brain_dev` to see the specific Python exception.

   * Execute `docker logs visionarias_whatsapp` to see if the Evolution API is rejecting the `tenant_id` (UUID) as an instance name or failing to create the worker.

2. **Verify Multi-Tenant Context Flow**:

   * Confirm that `get_current_tenant_id` is correctly extracting the tenant UUID from the user's token in `routers/whatsapp.py`.

   * Verify that the Evolution API `instanceName` payload matches this unique `tenant_id`.

3. **Implement Robust Session Management (Backend)**:

   * **Zombie Instance Cleanup**: In `create_whatsapp_session`, if the instance "already exists" but connection fails (or QR cannot be fetched), automatically trigger a `DELETE /instance/delete/{tenant_id}` and retry the creation. This prevents tenants from being stuck with broken sessions.

   * **Initialization Delay**: Add a short `asyncio.sleep(1)` after sending the Create command to allow Evolution API to allocate resources for the new tenant worker before we ask for the QR code.

4. **Frontend Feedback**:

   * Enhance `whatsapp-view.tsx` to log specific API error details (404, 500, timeout) to the console to distinguish between "Backend Error" and "Evolution API Error".

5. **Verify**:

   * Restart backend.

   * Attempt connection with the current user (tenant) and verify the QR code loads.

