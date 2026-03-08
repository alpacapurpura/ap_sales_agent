# Tasks

- [x] Task 1: Fix OAuth Flow for Background Access
    - [x] SubTask 1.1: Modify `ShopifyConnector.get_auth_url` in `backend/src/modules/connections/infrastructure/marketing_connectors/shopify.py` to remove `grant_options[]="per-user"`. This enables **Offline Access Tokens** required for background jobs.
    - [x] SubTask 1.2: Verify `shopify.app.toml` `redirect_urls` matches the backend's expected callback URL (`DASHBOARD_DOMAIN` + `/api/auth/shopify/callback`).

- [x] Task 2: Verify Connection Persistence
    - [x] SubTask 2.1: Verify `ShopifyConnector.exchange_token` correctly returns the access token.
    - [x] SubTask 2.2: Ensure `ChannelConnectionModel` saves the `access_token` in the `credentials` field (encrypted).

- [x] Task 3: Documentation & Validation
    - [x] SubTask 3.1: Create a manual verification script (or instructions) to test the auth flow with the `visionarias.lat` store.
