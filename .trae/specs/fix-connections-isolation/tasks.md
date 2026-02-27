# Tasks

- [x] Task 1: Frontend - Fix Multi-tenancy Isolation (Use `frontend-expert`)
  - [x] SubTask 1.1: Edit `frontend/src/features/connections/components/ConnectionsView.tsx` to add `key={tenantId}` to all tab content.
  - [x] SubTask 1.2: Create a Cypress/Playwright test OR a manual verification script with Mock Data to confirm that switching tenants updates the view. (Since we don't have Cypress setup in context, we will use a manual verification component or log).
  - [x] SubTask 1.3: Verify `fetchClient` behavior with the new key approach.

- [x] Task 2: Backend - Refactor to Integration Module (Use `backend-expert`)
  - [x] SubTask 2.1: Create `backend/src/modules/integration` structure (api, domain, application, infrastructure).
  - [x] SubTask 2.2: Move `communication/infrastructure/channels` to `integration/infrastructure/channels`.
  - [x] SubTask 2.3: Move `communication/api/whatsapp.py` to `integration/api/whatsapp.py`.
  - [x] SubTask 2.4: Update `main.py` to include `integration` router.
  - [x] SubTask 2.5: Fix all broken imports in the backend.
  - [x] SubTask 2.6: Verify that the `ChatOrchestrator` (in communication) can still access `WhatsAppChannel` (now in integration).

- [x] Task 3: Final Verification
  - [x] SubTask 3.1: Start the stack and verify that WhatsApp connection status loads correctly.
  - [x] SubTask 3.2: Verify that switching tenants updates the status.
