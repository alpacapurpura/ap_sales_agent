# Fix Connections Multi-tenancy Isolation & Refactor Integration Spec

## Why
1. **Isolation Issue**: Users see the same connection information across different tenants due to frontend state persistence.
2. **Architecture Issue**: Integration logic (WhatsApp, Telegram, etc.) is currently mixed within the `communication` module. The user requests moving all integration-related code to a dedicated `integration` module to align with the "Connections" domain.

## What Changes
### Frontend (Scope: `frontend-expert`)
- **Fix Isolation**: Add `key={tenantId}` to `ConnectionsView` components to force re-initialization on tenant switch.
- **Testing**: Implement a mock data verification step to ensure the UI updates correctly when `tenantId` changes.

### Backend (Scope: `backend-expert`)
- **Refactor**: Move all Channel/Integration logic from `modules/communication` to `modules/integration`.
    - Move `communication/infrastructure/channels/*` -> `integration/infrastructure/channels/*`.
    - Move `communication/api/whatsapp.py` -> `integration/api/whatsapp.py`.
    - Move `communication/domain/channel_connection.py` -> `integration/domain/connection.py` (if applicable).
- **Update References**: Update all imports in the codebase to point to the new `integration` module.
- **Router**: Register the new `integration` router in `main.py`.

## Impact
- **Breaking Changes**: API endpoints might move if the router prefix changes (though we will keep `/api/v1/whatsapp` for compatibility if possible, or update frontend).
- **Affected Specs**: Connections, Communication.

## MODIFIED Requirements
### Requirement: Connections View Isolation
- The view MUST refresh data when `tenantId` changes.
- Verified via Mock Data test.

### Requirement: Integration Module
- All logic for managing external connections (WhatsApp, Telegram) MUST reside in `backend/src/modules/integration`.
