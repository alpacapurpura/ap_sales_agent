# Frontend-Backend Connection Fix Spec

## Why
The backend has been refactored into a Domain-Driven Design (DDD) structure with modular API routes (e.g., `/api/v1/iam/...`, `/api/v1/connections/...`). The frontend is still using the old flat API structure (e.g., `/api/v1/settings/...`, `/api/v1/whatsapp/...`), causing connection failures. Additionally, some backend routers have redundant prefixes (e.g., `/leads/leads`) that need cleaning.

## What Changes

### Backend Refactoring (Clean up API Paths)
- **Remove Redundant Prefixes**: Modify `APIRouter` definitions to remove internal prefixes that are already handled by `main.py` mounting.
  - `src/modules/connections/api/calendar.py`: Remove `prefix="/calendar"`.
  - `src/modules/connections/api/gmail.py`: Remove `prefix="/gmail"`.
  - `src/modules/crm/api/leads.py`: Remove `prefix="/leads"`.
  - `src/modules/scheduling/api/event_types.py`: Remove `prefix="/event-types"`.
- **Standardize Telegram Routes**:
  - `src/modules/connections/api/telegram.py`: Rename endpoints to remove `/channels/telegram` path segments, aligning with the `/api/v1/connections/telegram` mount point.
    - `GET /channels/telegram` -> `GET /status`
    - `POST /channels/telegram/connect` -> `POST /connect`
    - `POST /channels/telegram/test` -> `POST /test`
    - `DELETE /channels/telegram` -> `DELETE /disconnect`

### Frontend Updates (Point to New API Paths)
- **`src/lib/api/assets.ts`**:
  - Verify `upload` endpoint matches `/api/v1/assets/gallery/upload`.
- **`src/lib/api/avatar.ts`**:
  - Update base URL to `/api/v1/brand/avatars`.
- **`src/lib/api/settings.ts`**:
  - `getTenants` -> `/api/v1/iam/users/me/tenants`
  - `getTeam`, `createTeamMember` -> `/api/v1/iam/settings/team`
  - `getGeneralSettings`, `updateGeneralSettings` -> `/api/v1/iam/settings/general`
  - `getProfile` -> `/api/v1/iam/settings/profile`
  - `getAISettings`, `updateAISettings` -> `/api/v1/iam/settings/ai`
  - `getWebhookSettings` -> `/api/v1/iam/settings/webhook`
  - `regenerateWebhookSecret` -> `/api/v1/iam/settings/webhook/regenerate`
  - `getBrandSettings` -> `/api/v1/brand/settings`
- **`src/lib/api/whatsapp.ts`**:
  - Update base URL to `/api/v1/connections/whatsapp`.
- **`src/lib/api/public.ts`**:
  - Update base URL to `/api/v1/scheduling/public`.
- **`src/lib/api/leads.ts`**:
  - Update `search` to `/api/v1/crm/leads/search`.
- **`src/lib/api/event-types.ts`**:
  - Update base URL to `/api/v1/scheduling/event-types`.
- **`src/lib/api/connections.ts`**:
  - Telegram: `/api/v1/connections/telegram` (endpoints: `/status`, `/connect`, `/test`, `/disconnect`).
  - Calendar: `/api/v1/connections/calendar` (endpoints: `/status`, `/auth-url`, `/callback`, `/disconnect`, `/test`, `/appointments`, `/link`).
  - Gmail: `/api/v1/connections/gmail` (endpoints: `/status`, `/auth-url`, `/callback`, `/disconnect`, `/test`).
- **`src/lib/api/booking-links.ts`**:
  - Update `create` to `/api/v1/connections/calendar/personalized-link`.
- **`src/lib/api/availability.ts`**:
  - Update base URL to `/api/v1/connections/calendar/schedules`.
- **`src/lib/api/offer-gallery.ts`**:
  - Update base URL to `/api/v1/assets/offers/{offerId}/gallery`.
- **`src/lib/api/admin.ts`**:
  - Update `getTenants` to `/api/v1/iam/tenants`.
  - Update `updateTenantPermissions` to `/api/v1/iam/tenants/{tenantId}/permissions`.

## Impact
- **Affected Specs**: None.
- **Affected Code**: Frontend API client library (`src/lib/api/*.ts`) and Backend API Routers (`backend/src/modules/*/api/*.py`).
- **Breaking Changes**: Yes, API paths are changing. Both frontend and backend must be updated simultaneously.

## ADDED Requirements
### Requirement: API Consistency
The system SHALL use consistent RESTful paths structured by domain (e.g., `/api/v1/{domain}/{resource}`).

### Requirement: Global Versioning Strategy
The system SHALL use `/api/v1/{module}` (Global Versioning) as the standard URL structure, as confirmed by the architectural decision record. This simplifies frontend configuration and maintains consistency across the modular monolith.

## MODIFIED Requirements
### Requirement: Backend Router Configuration
**Reason**: Remove redundant path prefixes to ensure clean URLs.
**Migration**: Update frontend clients to match new paths.
