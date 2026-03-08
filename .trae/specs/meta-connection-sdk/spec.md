# Meta Connection SDK Implementation Spec

## Why
The current Meta integration uses manual HTTP calls and requires per-tenant App ID/Secret configuration, which is not suitable for a SaaS model. The user needs to consolidate marketing data (Ads, Pages, Instagram) and requested validation using the official `META Business SDK` (`facebook-business` Python package).

## What Changes
- **Dependency**: Add `facebook-business` to `backend/requirements.txt`.
- **Configuration**: Move `app_id` and `app_secret` to global environment variables (`META_APP_ID`, `META_APP_SECRET`) instead of per-tenant database config.
- **Backend Refactor**:
  - Update `MetaAdapter` (`backend/src/modules/connections/infrastructure/channels/meta.py`) to initialize `FacebookAdsApi` from the SDK.
  - Use SDK methods for token exchange and fetching User Profile, Ad Accounts, and Pages.
  - Maintain `InstagramChannel` compatibility (it can continue using `httpx` for messaging if SDK doesn't cover Messenger API, but should share the authenticated session).
- **API Updates**:
  - `GET /auth-url`: Generate URL using global credentials.
  - `POST /callback`: Exchange code using SDK.
  - `PUT /config`: Deprecate or restrict to advanced use cases (we will use global config by default).
- **Frontend**:
  - Create a simplified "Connect" flow in `ConnectionsView`.
  - Remove the form asking for App ID/Secret.

## Impact
- **Affected Specs**: `module_connections.md`, `module_analytics.md` (future).
- **Affected Code**:
  - `backend/src/modules/connections/infrastructure/channels/meta.py`
  - `backend/src/modules/connections/api/meta.py`
  - `frontend/src/features/marketing-studio/components/ConnectionsView.tsx`

## ADDED Requirements
### Requirement: Global Meta App Configuration
The system SHALL use `META_APP_ID` and `META_APP_SECRET` from environment variables for all tenant connections by default.

#### Scenario: User connects Meta
- **WHEN** user clicks "Connect Meta"
- **THEN** the system generates an OAuth URL using the global App ID.
- **AND** redirects the user to Facebook.

### Requirement: SDK Integration
The system SHALL use `facebook_business.api.FacebookAdsApi` to interact with Meta Marketing API.

#### Scenario: Token Exchange
- **WHEN** the callback is received with a `code`
- **THEN** the system uses the SDK to exchange it for a long-lived access token.
- **AND** initializes the API session for subsequent calls.

## MODIFIED Requirements
### Requirement: Meta Adapter
The `MetaAdapter` class SHALL be refactored to wrap the `facebook-business` SDK.

### Requirement: Connection Status
The `ConnectionsView` SHALL display the connection status based on the existence of a valid token in the database, without requiring manual configuration input from the user.

### Requirement: Test Connection
The UI SHALL provide a "Test Connection" button for connected accounts.
- **WHEN** user clicks "Test Connection"
- **THEN** the system calls `POST /api/v1/connections/meta/test`.
- **AND** displays a success message with the connected user's profile name if valid, or an error if invalid.
