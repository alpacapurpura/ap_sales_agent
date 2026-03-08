# Shopify Redirect URI Mismatch Spec

## Why
The user is encountering an "Oauth error invalid_request: The redirect_uri and application url must have matching hosts" error. This indicates a mismatch between the `SHOPIFY_APP_URL` configured in the backend environment and the App URL/Redirect URIs configured in the Shopify Partner Dashboard. This usually happens when the development tunnel URL changes (e.g., restarting ngrok/cloudflared) but is not updated in one of the two places.

## What Changes
- **Verify & Update `.env`**: Ensure `SHOPIFY_APP_URL` matches the currently active public URL (tunnel).
- **Documentation**: Update `docs/guides/shopify_setup.md` to explicitly warn about keeping these values in sync.
- **Code**: No code changes required in the logic, but we will add a log to print the generated `redirect_uri` to help debugging.

## Impact
- **Affected Specs**: `shopify_audit_manual/spec.md`
- **Affected Code**: `backend/src/modules/connections/api/shopify.py` (Adding debug log)

## ADDED Requirements
### Requirement: Debug Logging
The system SHALL log the generated `redirect_uri` during the `/generate-auth-url` call to assist in verifying the mismatch.

## MODIFIED Requirements
### Requirement: Configuration Consistency
The `SHOPIFY_APP_URL` environment variable MUST exactly match the "App URL" configured in Shopify Partners.
