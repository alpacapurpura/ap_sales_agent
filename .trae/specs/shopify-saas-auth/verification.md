# Shopify Integration Verification Steps

## Prerequisites
- Ensure the backend is running (`docker compose up api_dev`).
- Ensure the frontend is running (`docker compose up client_dashboard_dev`).
- Ensure the tunnel is active and pointing to the frontend (e.g. `https://laptopchris.alpacapurpura.lat`).
- Ensure `shopify.app.toml` has been pushed to Shopify (`shopify app config push`).

## Manual Verification Flow

1. **Trigger Auth Flow**:
   - Make a POST request to `https://laptopchris.alpacapurpura.lat/api/v1/connections/shopify/generate-auth-url`
   - Body: `{ "shop_url": "visionarias.lat" }`
   - Headers: Authorization (Bearer token for a valid user/tenant).

2. **Follow Redirect**:
   - Open the returned `auth_url` in a browser.
   - Log in to `visionarias.lat` (if prompted).
   - Click "Install App".

3. **Verify Callback**:
   - Shopify should redirect you back to `https://laptopchris.alpacapurpura.lat/api/v1/connections/shopify/auth/callback`.
   - The browser should then redirect you to `/marketing-studio/connections?status=success`.

4. **Verify Database**:
   - Connect to the database (`docker exec -it visionarias_postgres psql -U postgres -d visionarias_logs`).
   - Run: `SELECT * FROM channel_connections WHERE channel_type = 'shopify';`
   - Confirm `is_active` is true and `credentials` contains an `access_token`.

## Troubleshooting
- If you get a "Redirect URI mismatch" error from Shopify, ensure you ran `shopify app config push` after the code changes.
- If you get a 404 on callback, ensure the Next.js proxy is working for `/api/v1/*`.
