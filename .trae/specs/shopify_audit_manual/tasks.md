# Tasks

- [x] Task 1: Refactor Shopify API Router
  - [x] SubTask 1.1: Modify `backend/src/modules/connections/api/shopify.py` to expose a `public_router` for the callback endpoint.
  - [x] SubTask 1.2: Remove the callback endpoint from the protected `router`.
  - [x] SubTask 1.3: Update `backend/src/main.py` to mount `conn_shopify.public_router` separately without `get_tenant_context`.
- [x] Task 2: Create Shopify Configuration Manual
  - [x] SubTask 2.1: Create `docs/guides/shopify_setup.md`.
  - [x] SubTask 2.2: Document the App URL and Redirect URI patterns.
  - [x] SubTask 2.3: Document environment variables (`SHOPIFY_APP_URL`, `SHOPIFY_API_KEY`, `SHOPIFY_API_SECRET`).
  - [x] SubTask 2.4: Explain Development (Tunneling) vs Production setup.
