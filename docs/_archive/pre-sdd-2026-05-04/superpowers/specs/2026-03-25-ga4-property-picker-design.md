# GA4 Property Picker — Design Spec

**Date:** 2026-03-25
**Status:** Approved
**Goal:** After Google OAuth (both Workspace and Standalone flows), let the user select which GA4 property to monitor so the ETL pipeline can extract metrics.

## Problem

The GA4 ETL provider requires a `property_id` in connection credentials. Currently, neither OAuth flow saves it. Result: ETL runs "successfully" but extracts 0 metrics.

## UX Flow

```
User connects Google (any flow)
  → OAuth popup → grants access → popup closes
  → Backend fetches GA4 properties via Admin API
  → Frontend receives properties list in callback response
  → If 1 property → auto-select, show confirmation
  → If N properties → show dropdown "Selecciona tu sitio web"
  → If 0 properties → friendly message + manual input fallback
  → User confirms → property_id saved to encrypted credentials
  → Status: "Conectado a [Property Name]"
```

## Connection States

```
Not configured        → Config form (client_id/secret)
Configured, not OAuth → "Conectar" button
Connected, no property → Property Picker (NEW)
Connected + property   → "Conectado a [Name]" + "Cambiar" button
```

## Backend Changes

### 1. Modify OAuth callbacks to return properties

**Files:** `google_analytics.py` callback, `google_workspace.py` callback

**Critical refactoring:** The standalone GA callback currently raises `HTTPException(400)` if `get_account_summaries()` fails. This MUST be changed to a graceful fallback — save credentials and return `properties: []` instead of blocking the connection.

After successful token exchange, call `get_account_summaries()` and include flattened properties in the response:

```python
# Response shape from both callbacks
{
    "status": "connected",
    "properties": [
        {"property_id": "123456789", "display_name": "Mi Sitio Web", "account_name": "Mi Cuenta"},
        ...
    ]
}
```

**Flattening logic** (in adapter or utility):
- `property_id` = `propertySummary["property"].split("/")[1]`
- `display_name` = `propertySummary["displayName"]`
- `account_name` = parent `accountSummary["displayName"]`

**Workspace callback specifics:** The Workspace callback does NOT currently interact with the Analytics Admin API. To add it:
- Instantiate `GoogleAnalyticsAdapter` with shared app credentials: `client_config={"client_id": settings.GOOGLE_CLIENT_ID, "client_secret": settings.GOOGLE_CLIENT_SECRET}`
- Use the freshly exchanged credentials (which include `refresh_token`) to build the Admin API service
- Wrap in try/except — if it fails, return `properties: []` without blocking the Workspace connection

**Scope confirmation:** The `analytics.readonly` OAuth scope (already requested in both flows) covers Admin API read operations including `accountSummaries.list`. No scope changes needed.

### 2. New endpoint: `PUT /google-analytics/properties/select`

```python
# Request
{"property_id": "123456789"}

# Validation: verify property_id exists in user's account via Admin API
# Storage: property_id → credentials (encrypted), display_name + account_name → config (plaintext)
# Response
{"status": "ok", "property_id": "123456789", "display_name": "Mi Sitio Web"}
```

**Storage split rationale:**
- `property_id` goes in `credentials` (EncryptedJSON) because the ETL provider reads it from there
- `display_name` and `account_name` go in `config` (JSONB) for fast UI display without decryption

**Validation:** Call Admin API to verify the property_id belongs to the authenticated user's account. If validation fails (e.g., Admin API unavailable), allow saving anyway for the manual-input fallback case.

### 3. Enhance `/google-analytics/status`

Add `selected_property` to response (DB-only, no external API calls):

```python
{
    "is_connected": True,
    "is_configured": True,
    "selected_property": {"property_id": "123456789", "display_name": "Mi Sitio Web"} | None
}
```

`available_properties` is NOT included in status — use the separate `GET /properties` endpoint to avoid expensive API calls on every status check.

### 4. Enhance `/google-analytics/properties` (existing)

Already exists, already calls `get_account_summaries()`. Normalize response to return flat list of `{property_id, display_name, account_name}`.

### 5. Update DTOs

Update `GoogleAnalyticsStatusResponse` in `dto/google_analytics.py` to include `selected_property` field.

Add new DTOs: `PropertySummaryResponse`, `PropertySelectRequest`.

## Frontend Changes

### 1. `PropertyPicker` component

**Location:** `frontend/src/features/connections/components/property-picker.tsx` (FSD: connections feature)

- Simple dropdown with property names (format: "Property Name — Account Name")
- Auto-selects if only 1 property
- "Cambiar propiedad" link when property already selected
- Fallback: manual input field if properties list is empty

### 2. Integration in `google-analytics-view.tsx`

After OAuth succeeds:
- If callback returned properties → show picker inline
- If property already selected → show "Conectado a [Name]"
- "Cambiar" button → calls `GET /properties` and shows picker

### 3. Integration in Google Workspace view

After Workspace OAuth:
- Check if GA connection has property_id via status endpoint
- If not, show the PropertyPicker component for GA specifically

### 4. API client updates

Add to `frontend/src/lib/api/connections.ts`:
- `getGoogleAnalyticsProperties(token)` → `GET /properties`
- `selectGoogleAnalyticsProperty(propertyId, token)` → `PUT /properties/select`

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Admin API disabled/403 | Return empty properties, show manual input fallback |
| Token expired during property fetch | Auto-refresh via adapter, write refreshed token back to DB, retry once |
| User has 0 GA4 properties | "No encontramos propiedades GA4 en tu cuenta. Verifica que tengas Google Analytics configurado." |
| Network error | Toast error, retry button |
| User re-connects via different flow | Preserve existing property_id, prompt only if credentials changed |

## Scope

**In scope:**
- Property picker for both connection flows (Standalone GA + Google Workspace)
- Auto-select single property
- Change property after initial selection
- Manual fallback input
- Property validation on select

**Out of scope:**
- YouTube channel picker (separate feature)
- Google Ads customer_id picker (requires developer token)
- Modifying the OAuth scopes
