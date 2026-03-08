# Tasks

- [x] Task 1: Update Shopify App Configuration
  - [ ] SubTask 1.1: Edit `shopify_app/shopify.app.toml`:
    - Set `application_url = "https://laptopchris.alpacapurpura.lat"`
    - Update `redirect_urls` to include `https://laptopchris.alpacapurpura.lat/api/auth/shopify/callback`
  - [ ] SubTask 1.2: Verify configuration syntax.

- [x] Task 2: Update Backend Logic
  - [ ] SubTask 2.1: Add `SHOPIFY_FRONTEND_URL` to backend configuration (or derive from `application_url` if strictly coupled).
  - [ ] SubTask 2.2: Modify `generate_auth_url` in `backend/src/modules/connections/api/shopify.py` to use the Frontend callback URL.
  - [ ] SubTask 2.3: Implement `POST /api/v1/connections/shopify/auth/exchange` in `shopify.py`:
    - Accept JSON payload: `{ code, shop, hmac, state, host }`
    - Verify HMAC.
    - Exchange code for token (using `ShopifyConnector.exchange_token`).
    - Save connection.
    - Return success status.

- [x] Task 3: Implement Frontend Proxy
  - [ ] SubTask 3.1: Create `frontend/src/app/api/auth/shopify/callback/route.ts`.
  - [ ] SubTask 3.2: Implement GET handler:
    - Extract query params (`code`, `shop`, `hmac`, `state`, `host`).
    - Call Backend `POST /exchange` endpoint.
    - Redirect to `/marketing-studio/connections?status=success` on success.
    - Redirect to `/marketing-studio/connections?status=error` on failure.

- [x] Task 4: Deployment & Verification
  - [ ] SubTask 4.1: Run `shopify app config push` (User action required if auth needed).
  - [ ] SubTask 4.2: Verify the connection flow from the Frontend UI.
