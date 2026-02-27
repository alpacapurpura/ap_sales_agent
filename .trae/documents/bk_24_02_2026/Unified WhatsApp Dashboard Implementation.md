I will implement a **Unified WhatsApp Dashboard** that allows simultaneous management of both Evolution API (QR) and Meta Cloud API connections.

### Backend Changes
1.  **Data Model**: Update `ChannelType` in `channel_connection.py` to include `WHATSAPP_CLOUD` as a distinct channel type, while keeping `WHATSAPP` for the Evolution/QR integration.
2.  **API Router (`routers/whatsapp.py`)**:
    -   Update `GET /status` to return the status of **both** providers:
        ```json
        {
          "evolution": { "status": "connected", "profile": {...} },
          "meta": { "status": "disconnected", "profile": null }
        }
        ```
    -   Update `POST /session` and `DELETE /session` to accept a `provider` query parameter (values: `evolution` or `meta`), defaulting to `evolution` to maintain backward compatibility.

### Frontend Changes
1.  **API Client (`lib/api/whatsapp.ts`)**: Update `getStatus`, `createSession`, and `deleteSession` to support the new response structure and `provider` parameter.
2.  **UX Redesign (`whatsapp-view.tsx`)**:
    -   Transform the view into a **Grid Dashboard** containing two permanent Cards.
    -   **Card 1: Evolution API (QR)**
        -   **Disconnected**: Shows the "Modo Sincronizado" description and a "Connect" button. Clicking "Connect" reveals the QR code *inside* this card (preserving context).
        -   **Connected**: Shows the active profile (Avatar, Name, Number) and a "Disconnect" button.
    -   **Card 2: Meta Cloud API**
        -   **Disconnected**: Shows the "API Oficial" description and a "Connect" button (placeholder for future config form).
        -   **Connected**: Shows the Meta business profile.
    -   This layout ensures users can see and manage both connections simultaneously, fulfilling the "Dual Connection UX" requirement.

### Verification
-   Verify that connecting via QR updates only the Evolution card.
-   Verify that the "Meta" card remains visible and actionable.
