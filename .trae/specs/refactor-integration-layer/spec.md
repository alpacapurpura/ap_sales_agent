# Refactor Integration Layer Spec

## Why
Currently, external integration logic is scattered across `communication` and `marketing` modules. The user requires a strict Anti-Corruption Layer (ACL) where ALL external communication (webhooks, API keys, HTTP clients) resides in `backend/src/modules/integration`. This ensures a single point of responsibility for "talking to the outside world".

## What Changes
- **Move Webhook Handlers**: Move `communication/api/webhooks_cdp.py` (Shopify/MailerLite) to `integration/api/marketing_webhooks.py`.
- **Move API Connectors**: Move `marketing/infrastructure/connectors/` (MailerLite/Shopify clients) to `integration/infrastructure/marketing_connectors/`.
- **Update Router Registration**: Update `backend/src/main.py` to import the new webhook router from `integration`.
- **Update References**: Update any internal imports in `marketing` to point to the new connector locations.

## Impact
- **Affected specs**: Integration, Communication, Marketing.
- **Affected code**: 
  - `backend/src/modules/communication/api/webhooks_cdp.py` (Deleted)
  - `backend/src/modules/integration/api/marketing_webhooks.py` (Created)
  - `backend/src/modules/marketing/infrastructure/connectors/*` (Moved)
  - `backend/src/main.py` (Modified)

## ADDED Requirements
### Requirement: Centralized Webhooks
The system SHALL handle all external webhooks (Shopify, MailerLite, etc.) within `src/modules/integration/api`.

### Requirement: Centralized API Clients
The system SHALL place all external API clients (Marketing Connectors) within `src/modules/integration/infrastructure`.

## REMOVED Requirements
### Requirement: Communication Module Webhooks
**Reason**: `communication` module should only handle internal message orchestration, not raw external HTTP requests.
**Migration**: Logic moved to `integration`.

### Requirement: Marketing Module Connectors
**Reason**: `marketing` module should define *what* it needs (Ports), but `integration` should implement *how* to connect (Adapters).
**Migration**: Implementation moved to `integration`.
