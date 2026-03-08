# Tasks

- [ ] Task 1: Update Shopify App Configuration
  - [ ] SubTask 1.1: Modify `shopify_app/shopify.app.toml` to set `application_url` to `https://laptopchris.alpacapurpura.lat`.
  - [ ] SubTask 1.2: Add `https://laptopchris.alpacapurpura.lat/api/auth/shopify/callback` to `redirect_urls` in `shopify.app.toml`.
  - [ ] SubTask 1.3: Verify `shopify.app.toml` syntax and consistency.

- [ ] Task 2: Implement Backend Token Exchange Logic
  - [ ] SubTask 2.1: Update `backend/src/modules/connections/api/shopify.py` to add `POST /exchange` endpoint.
  - [ ] SubTask 2.2: Refactor `auth_callback` logic into a shared service method or reuse it in the new endpoint to avoid duplication.
  - [ ] SubTask 2.3: Update `generate_auth_url` in `shopify.py` to use the Frontend callback URL.
  - [ ] SubTask 2.4: Ensure `SHOPIFY_APP_URL` or a new env var correctly points to the Frontend for the redirect generation.

- [ ] Task 3: Implement Frontend Callback Proxy
  - [ ] SubTask 3.1: Create `frontend/src/app/api/auth/shopify/callback/route.ts`.
  - [ ] SubTask 3.2: Implement GET handler to receive Shopify params.
  - [ ] SubTask 3.3: Implement logic to POST params to Backend `/exchange` endpoint.
  - [ ] SubTask 3.4: Handle success/error redirects to the application UI.

- [ ] Task 4: Deployment and Verification
  - [ ] SubTask 4.1: Run `shopify app config push` (or instruct user if auth required) to update Shopify settings.
  - [ ] SubTask 4.2: Verify the flow by initiating a connection from the Frontend.
