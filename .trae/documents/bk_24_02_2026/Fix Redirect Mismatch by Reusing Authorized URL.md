
# Fix Google OAuth Redirect Mismatch

The error `Error 400: redirect_uri_mismatch` confirms that the new "Popup Callback" URL (`.../google-callback`) is **not registered** in your Google Cloud Console, and since we cannot easily register it without access, we must revert to using the **already authorized** URL (`.../connections`) while maintaining the popup experience.

## The Solution: "Hybrid" Popup Callback

We will use the existing authorized page (`/connections`) as the popup callback, but we'll add logic to detect when it's opened inside a popup so it behaves like a lightweight callback handler instead of loading the full dashboard.

### 1. Modify `ConnectionsPage` (Frontend)
*   **File**: `frontend/src/app/(dashboard)/connections/page.tsx`
*   **Action**: Add a `useEffect` hook at the top level.
*   **Logic**:
    *   Check if `window.opener` exists (meaning it's a popup).
    *   Check if URL params contain `code` or `error`.
    *   If true:
        *   Send `postMessage` to the opener with the code.
        *   Show a simple "Authenticating..." loading screen (return early).
        *   Close the window automatically.
    *   If false: Render the normal dashboard (sidebar, tabs, etc.).

### 2. Revert Redirect URI in `GoogleCalendarView`
*   **File**: `frontend/src/components/connections/google-calendar-view.tsx`
*   **Action**: Change `redirectUri` back to `window.location.origin + "/connections"`.
*   **Why**: This matches what is already whitelisted in Google Console, so the error 400 will disappear.

### 3. Cleanup
*   **File**: `frontend/src/app/google-callback/page.tsx`
*   **Action**: Delete this file since we are no longer using it.

## Expected Outcome
1.  You click "Connect".
2.  Popup opens -> Google Login -> Redirects to `/connections?code=...` (inside the popup).
3.  The `/connections` page inside the popup detects it's a popup, sends the code to the main window, and closes itself.
4.  The main window receives the code and completes the connection.
5.  **No error 400** because we are using the whitelisted URL.
