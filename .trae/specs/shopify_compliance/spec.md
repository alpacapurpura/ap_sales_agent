# Shopify Mandatory Webhooks Spec

## Why
To comply with Shopify's App Store requirements and GDPR regulations, every public app must handle three mandatory webhook topics: `customers/data_request`, `customers/redact`, and `shop/redact`. Failure to implement these endpoints leads to app rejection or removal. Currently, these are missing.

## What Changes
- **New Endpoints**: Add a new router `backend/src/modules/connections/api/shopify_compliance.py` with endpoints for:
  - `POST /api/v1/connections/shopify/compliance/customers/data_request`
  - `POST /api/v1/connections/shopify/compliance/customers/redact`
  - `POST /api/v1/connections/shopify/compliance/shop/redact`
- **Security**: These endpoints must verify the HMAC signature using `verify_shopify_signature`.
- **Logic**: 
  - For now, they will log the request and return 200 OK (Compliance requirement).
  - In the future, they should trigger actual data deletion/export workflows.
- **Main App**: Mount this new router in `main.py`.

## Impact
- **Affected Specs**: `shopify_audit_manual/spec.md`
- **Affected Code**: `backend/src/main.py`, new file `backend/src/modules/connections/api/shopify_compliance.py`

## ADDED Requirements
### Requirement: GDPR Compliance Endpoints
The system SHALL provide the three mandatory GDPR webhooks required by Shopify, verifying the HMAC signature and returning a 200 OK status.
