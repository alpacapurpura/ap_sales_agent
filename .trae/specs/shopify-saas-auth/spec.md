# Shopify SaaS Integration Spec

## Why
The user is building a multi-tenant SaaS that needs to connect to client Shopify stores to extract marketing data in the background. The current implementation uses "online" access tokens (per-user), which expire and are unsuitable for background synchronization (cron jobs). Additionally, the user needs clarification on the App Type (Public vs Custom) for a SaaS model.

## What Changes
- **Backend Auth Flow**: Change the OAuth request to request **Offline Access Tokens** instead of Online (per-user) tokens. This ensures the token remains valid for background data extraction even when the user is not logged in.
- **Configuration Verification**: Ensure `shopify.app.toml` and `.env` are synchronized regarding Client ID and Redirect URIs.
- **Documentation**: Clarify that for a Multi-tenant SaaS, the correct Shopify App type is **Public App** (even if unlisted/custom distribution via link), as "Custom Apps" (Shopify Admin created) do not support OAuth, and Partner Dashboard Custom Apps have limitations.

## Impact
- **Affected Code**: 
    - `backend/src/modules/connections/infrastructure/marketing_connectors/shopify.py` (OAuth URL generation).
- **Affected Specs**: None directly, but enables the "Data Extraction" capability.

## ADDED Requirements
### Requirement: Offline Access Token
The system SHALL request an **Offline Access Token** during the OAuth handshake.
#### Scenario: Background Sync
- **WHEN** the SaaS backend runs a cron job to fetch orders
- **THEN** the stored `access_token` MUST be valid without requiring user re-authentication.

## MODIFIED Requirements
### Requirement: OAuth URL Generation
The `get_auth_url` method SHALL NOT include `grant_options[]=per-user` to ensure the default (Offline) token is returned.
