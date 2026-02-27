# Add Webhook Tab for External Agent Integration

## 1. Database Migration (Backend)

* Create a script `backend/scripts/add_webhook_secret.py` to add a `webhook_secret` column to the `tenants` table.

* This secret will act as the authentication token for external systems (n8n, ManyChat, Flowise).

## 2. Backend Implementation

### Core Logic

* **Schema**: Update `backend/src/core/schema.py` to include `WebhookSettings` and ensure `IncomingMessage` supports generic channels.

* **Model**: Update `Tenant` model in `backend/src/services/db/models/tenant.py`.

### API Endpoints

* **New Router**: Create `backend/src/api/routers/webhook.py`.

  * `POST /api/v1/webhook/chat`:

    * **Headers**: `X-Webhook-Secret` (Mandatory).

    * **Body**: Standard JSON `{"user_id": "...", "message": "...", "metadata": {...}}`.

    * **Logic**: Validates secret, finds tenant, invokes `ChatOrchestrator`.

* **Settings Router**: Update `backend/src/api/routers/settings.py`.

  * `GET /api/v1/settings/webhook`: Retrieve the current secret and construction of the public URL.

  * `POST /api/v1/settings/webhook/regenerate`: Generate a new secure secret.

### Main Application

* Register the new `webhook` router in `backend/src/main.py`.

## 3. Frontend Implementation

### API Client

* Update `frontend/src/lib/api/settings.ts` to include methods for fetching and regenerating webhook settings.

### UI Components

* **New Component**: `frontend/src/components/settings/webhook-view.tsx`.

  * Display the **Webhook URL** (e.g., `https://api.visionarias.ai/api/v1/webhook/chat`).

  * Display the **Secret Key** with a "Reveal/Copy" feature.

  * "Regenerate Secret" button with confirmation dialog.

  * **Documentation Section**: Provide JSON examples for n8n and ManyChat to guide the user.

### Settings Page

* Update `frontend/src/app/(dashboard)/settings/page.tsx` to add the "Webhook" tab and render `WebhookView`.

## 4. Verification

* Run the migration script.

* Verify the endpoint using `curl` or a test script simulating an n8n request.

* Verify the Frontend UI allows copying and regenerating the key.

