I will implement the Multi-Tenant Telegram Connection system as follows:

## 1. Backend Architecture & Database
- **New Model `ChannelConnection`**: I will create a new SQLAlchemy model `ChannelConnection` in `backend/src/services/db/models/channel_connection.py`.
    - Fields: `tenant_id` (FK), `channel_type` ('telegram', 'whatsapp', etc.), `credentials` (JSONB), `config` (JSONB), `is_active`.
- **Refactor `TelegramChannel`**: I will modify `backend/src/channels/telegram.py` to remove the dependency on the global `TELEGRAM_BOT_TOKEN` and instead accept a `token` in its constructor.

## 2. API & Webhook Logic
- **Dynamic Webhook Endpoint**: I will update `backend/src/api/routes.py` to support `/webhooks/telegram/{tenant_id}`.
    - The handler will look up the `ChannelConnection` for the given `tenant_id`, instantiate `TelegramChannel` with the specific token, and process the message.
- **Management Endpoints**: I will create `backend/src/api/v1/endpoints/channels.py` with:
    - `POST /telegram/connect`: Saves token, validates with `getMe`, and sets the webhook url to `.../webhooks/telegram/{tenant_id}`.
    - `GET /telegram/status`: Returns bot info and connection status.
    - `POST /telegram/test`: Performs a live connection check.
    - `DELETE /telegram/disconnect`: Removes webhook and deletes connection record.

## 3. Frontend Implementation
- **New Page**: `frontend/src/app/(dashboard)/connections/telegram/page.tsx`.
- **UI Components**:
    - **Connect View**: Step-by-step guide (BotFather) and Token Input.
    - **Connected View**: Displays Bot Name/Username, Webhook Status, and Config options.
    - **Actions**: "Test Connection" and "Disconnect" buttons with visual feedback.

## 4. Verification
- I will verify the entire flow: entering a token -> saving -> testing connection -> receiving a mock webhook -> disconnecting.
