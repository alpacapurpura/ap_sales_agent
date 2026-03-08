# Shopify OAuth Integration Spec

## Why

The current manual integration method (copy-pasting Access Token) is error-prone and provides a poor user experience. Users expect a seamless "Log in with Shopify" flow similar to Google OAuth. Switching to the standard Shopify OAuth 2.0 flow will simplify the onboarding process and reduce support friction.

## What Changes

* **Backend**: Implement Shopify OAuth 2.0 flow endpoints.

  * `GET /auth/login`: Initiates the OAuth flow, redirecting the user to Shopify's authorization page.

  * `GET /auth/callback`: Handles the redirect from Shopify, validates the HMAC, exchanges the temporary code for a permanent `access_token`, and stores it.

  * Use the `state` parameter to securely pass the `tenant_id` through the OAuth flow.

* **Frontend**: Update the Shopify connection UI.

  * Remove the "Access Token" input field.

  * Keep the "Shop URL" input.

  * Add a "Connect with Shopify" button that triggers the OAuth flow.

* **Configuration**: Requires `SHOPIFY_API_KEY` and `SHOPIFY_API_SECRET` in environment variables.

## Impact

* **Affected Specs**: Connection capabilities.

* **Affected Code**:

  * `backend/src/modules/connections/api/shopify.py`: Add OAuth endpoints.

  * `backend/src/modules/connections/infrastructure/marketing_connectors/shopify.py`: Add token exchange logic.

  * `frontend/src/features/connections/components/shopify-view.tsx`: Update UI to use OAuth.

## ADDED Requirements

### Requirement: OAuth 2.0 Flow

The system SHALL provide an OAuth 2.0 based connection mechanism.

#### Scenario: User connects store

* **WHEN** user enters their Shop URL and clicks "Connect"

* **THEN** the system redirects them to Shopify's permission approval screen.

* **WHEN** user approves permissions

* **THEN** they are redirected back to the application, and the connection is established automatically without manual token entry.

## REMOVED Requirements
### Requirement: Manual Token Connection
**Reason**: The manual copy-pasting of Access Tokens is insecure, error-prone, and provides a poor user experience. It is being fully replaced by the OAuth 2.0 flow.
**Migration**: Existing connections will continue to work (as the stored token format is compatible), but new connections can only be made via OAuth. The manual input form and corresponding API endpoint (`POST /connect` with manual token) will be removed.

## Security Considerations
- **Data Encryption**: The `access_token` and any other sensitive credentials MUST be stored in the `credentials` field of `ChannelConnectionModel`. This field uses the `EncryptedJSON` type, which automatically encrypts data at rest using the tenant-specific or global encryption key. The implementation MUST ensure that the `credentials` dictionary is passed to the model, allowing the `EncryptedJSON` type decorator to handle the encryption process transparently.
- **CSRF Protection**: The `state` parameter MUST be used to prevent CSRF attacks and to persist the `tenant_id` across the redirect chain.
- **HMAC Verification**: The system MUST verify the `hmac` signature on the callback to ensure the request is genuinely from Shopify.

