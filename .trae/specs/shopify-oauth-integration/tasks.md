# Tasks

- [x] Task 1: Backend OAuth Implementation (MUST use `backend-expert` skill)
  - [x] SubTask 1.1: Add `SHOPIFY_API_KEY`, `SHOPIFY_API_SECRET`, `SHOPIFY_APP_URL` (backend URL) and `SHOPIFY_SCOPES` (read_products,read_orders,etc) to `src/core/config.py` (or environment loading logic).
  - [x] SubTask 1.2: Update `ShopifyConnector` class in `infrastructure/marketing_connectors/shopify.py` to include methods for:
    - Generating the authorization URL.
    - Verifying the HMAC signature.
    - Exchanging the authorization code for an access token.
  - [x] SubTask 1.3: Update `api/shopify.py` to add:
    - `GET /auth/login`: Accepts `shop_url` and `tenant_id` (via query or auth context), generates state, and redirects.
    - `GET /auth/callback`: Accepts `code`, `shop`, `state`, `hmac`. Verifies, exchanges token, and stores it in `ChannelConnectionModel.credentials` (automatically encrypted by `EncryptedJSON`).
    - Remove the existing `POST /connect` endpoint that accepts manual tokens.
    - Redirects to frontend success page after successful connection.

- [x] Task 2: Frontend UI Updates (MUST use `frontend-expert` skill)
  - [x] SubTask 2.1: Modify `frontend/src/features/connections/components/shopify-view.tsx`.
  - [x] SubTask 2.2: Remove the "Access Token" field from the form.
  - [x] SubTask 2.3: Change the "Connect" action to redirect the browser to `${API_URL}/api/v1/connections/shopify/auth/login?shop=${shopUrl}&token=${authToken}` (Need a way to pass auth context, or rely on cookie/param. Since this is a browser redirect, we might need to pass a short-lived token or sign the state with the user's session). 
    - *Correction*: The backend endpoint `/auth/login` should be protected (require Auth header). If we redirect the browser directly, we can't easily send the Bearer header. 
    - *Better Approach*: Frontend calls an API endpoint `POST /generate-auth-url` (protected) -> returns `{ url: string }` -> Frontend does `window.location.href = url`.
  - [x] SubTask 2.4: Handle the return from Shopify. The backend callback will likely redirect to a frontend route like `/connections/shopify?status=success`. Ensure the frontend displays a success message.

- [x] Task 3: Verification & Cleanup
  - [x] SubTask 3.1: Verify the flow with a test store (if credentials available) or mock the Shopify responses.
  - [x] SubTask 3.2: Ensure error handling is robust (e.g., user denies permissions).

# Task Dependencies
- Task 2 depends on Task 1.3 (API availability).
