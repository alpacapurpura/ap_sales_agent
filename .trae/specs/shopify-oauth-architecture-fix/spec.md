# Shopify OAuth Architecture Fix Spec

## Why
The current configuration causes a "Host Mismatch" error because Shopify enforces that the `redirect_uri` host matches the `application_url` host for Embedded Apps using the Authorization Code Grant.
- **Current State**: `application_url` points to Backend (API), but the user interacts with the Frontend. If we change `application_url` to Frontend (as required for Embedded Apps), the Backend-based `redirect_uri` becomes invalid due to cross-domain restrictions in the strict OAuth flow.
- **Goal**: Align the architecture with Shopify best practices for decoupled apps (Next.js Frontend + Python Backend) by making the Frontend the primary OAuth entry/exit point.

## What Changes
### 1. Configuration (`shopify_app/shopify.app.toml`)
- **Update `application_url`**: Set to the Frontend URL (`https://laptopchris.alpacapurpura.lat`). This ensures the app loads correctly in the Shopify Admin iframe.
- **Update `redirect_urls`**: Add the Frontend Callback URL (`https://laptopchris.alpacapurpura.lat/api/auth/shopify/callback`). This satisfies the "matching hosts" requirement.

### 2. Backend (`backend/src/modules/connections/api/shopify.py`)
- **Modify `generate_auth_url`**: Construct the `redirect_uri` using the Frontend base URL (`SHOPIFY_FRONTEND_URL` or derived).
- **Add `POST /exchange` Endpoint**: Create a new endpoint (or update existing) to accept the OAuth `code` payload from the Frontend proxy. This keeps the Client Secret secure on the Backend.

### 3. Frontend (`frontend/src/app/api/auth/shopify/callback/route.ts`)
- **Create Proxy Route**: Implement a Next.js API route that:
  1. Receives the OAuth callback from Shopify.
  2. Forwards the `code`, `shop`, `hmac`, `state` to the Backend.
  3. Handles the Backend response and redirects the user to the App UI.

## Impact
- **Architecture**: Shifts the OAuth callback responsibility to the Frontend (as a proxy), aligning with the "BFF" (Backend for Frontend) pattern for this specific flow.
- **Security**: Maintains security by keeping the `client_secret` and token exchange on the Backend.
- **User Experience**: Fixes the "Invalid Request" error and enables successful store connection.

## ADDED Requirements
### Requirement: Frontend Callback Handler
The system SHALL provide a Frontend API route (`/api/auth/shopify/callback`) that intercepts the Shopify OAuth redirect and proxies the authorization code to the Backend.

### Requirement: Backend Code Exchange
The system SHALL provide a Backend endpoint that accepts the authorization code via JSON payload (from the Frontend proxy) and performs the token exchange with Shopify.

## MODIFIED Requirements
### Requirement: App Configuration
The `shopify.app.toml` SHALL be configured with the Frontend URL as the `application_url` to support Embedded App behavior.

### Requirement: Redirect URI Generation
The Backend SHALL generate authorization URLs with a `redirect_uri` pointing to the Frontend's callback route.
