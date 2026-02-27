
# Google Calendar Auth: Transition to Popup Flow

The current redirect-based flow is causing UX issues (losing tab state, "double-submission" errors) and persistent authentication failures. A **Popup Flow** is the standard best practice for Single Page Applications (SPAs) like this dashboard, as it preserves the application state and provides a seamless "widget-like" experience.

## Why Popup?
1.  **Preserves Context**: User stays on the "Connections" page; no page reload/redirect to wipe out the active tab or scroll position.
2.  **Solves "Double Submit"**: The popup handles the auth code, passes it to the main window, and closes. The main window never reloads with the `?code=` param, eliminating the race condition.
3.  **Better Error Handling**: Errors happen in the popup or are caught by the opener, allowing for cleaner UI feedback (toasts) without page transitions.

## Implementation Plan

### 1. Frontend: Implement `useGoogleAuthPopup` Hook
Create a robust hook to handle the `window.open` -> `postMessage` flow.
*   **Trigger**: Button click opens `width=500,height=600` popup centered on screen.
*   **Popup Logic**: The popup will be redirected by Google to a new simple route `/google-callback`.
*   **Callback Page**: A minimal page that parses the URL code/error and sends `window.opener.postMessage(...)` then closes itself.
*   **Listener**: The main page listens for the message, calls the backend `connectGoogle` API, and updates state.

### 2. Frontend: Create Callback Route
*   New file: `src/app/google-callback/page.tsx`
*   Logic: Client component that extracts `code`, sends to opener, and `window.close()`.

### 3. Backend: Verify Redirect URI
*   **Crucial Fix**: The `redirect_uri` passed to Google **MUST** match the route where the user lands.
*   We will change the backend validation to expect `.../google-callback` instead of `.../connections`.
*   No complex backend code changes needed, just ensuring the `redirect_uri` param sent from frontend matches the new popup callback URL.

### 4. Verification
*   User clicks "Connect".
*   Popup opens -> Google Login -> Redirect to `/google-callback`.
*   Popup closes automatically.
*   "Connections" page shows "Connected" toast and updates UI immediately without reload.
