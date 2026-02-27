I will implement the fix for the "Unknown" email issue and add the "Test Connection" feature for Gmail.

**Backend Implementation:**

1. **Modify** **`backend/src/channels/gmail.py`:**

   * Update `get_profile` method to properly inspect the Gmail API response structure. The API returns `{'emailAddress': 'user@example.com', ...}` directly.

   * Add error logging if the response doesn't contain the expected key.

2. **Modify** **`backend/src/api/routers/gmail.py`:**

   * **Fix "Unknown" email:** In `oauth_callback`, improve error handling. If `get_profile` fails, retry or fail gracefully, but ensure the error is logged clearly.

   * **Add** **`/test`** **endpoint:** Create a new endpoint `POST /api/v1/gmail/test` that:

     * Retrieves the connection from the DB.

     * Re-instantiates the `GmailAdapter`.

     * Calls `get_profile()` to verify the token is still valid.

     * Returns a success message with the profile data, or an error if the token is expired/invalid.

**Frontend Implementation:**

1. **Update** **`frontend/src/lib/api/connections.ts`:**

   * Add `testGmail` method to the `connectionsApi` object, calling the new backend endpoint.

2. **Update** **`frontend/src/components/connections/gmail-view.tsx`:**

   * **Add "Probar Conexión" button:** Replicate the UI pattern from `TelegramView`.

   * **Add** **`handleTest`** **function:** Call `connectionsApi.testGmail` and display the result (Success/Error) using an `Alert` component, similar to Telegram's implementation.

   * **Display more info:** Show the email address more prominently if available.

**Validation:**

* User will be able to click "Probar Conexión" to verify the Gmail integration.

* The "Cuenta Conectada" field should display the correct email address instead of "Unknown" after a successful connection or test.

