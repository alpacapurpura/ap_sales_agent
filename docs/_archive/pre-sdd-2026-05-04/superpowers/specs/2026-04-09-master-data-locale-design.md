# Master Data: TenantLocale (Currency + Timezone)

**Date:** 2026-04-09
**Status:** Approved
**Scope:** Cross-cutting — shared, iam, analytics, offer, scheduling, sales_agent, frontend

---

## Problem

The application has tenant-level `default_currency` and `timezone` settings in the DB
(`tenants` table) but they are **not propagated** to the modules that need them. Instead,
39 locations across backend and frontend hardcode `"USD"` or `"UTC"` as fallbacks, or use
`datetime.utcnow()` (deprecated since Python 3.12). This means:

- A Peruvian tenant creating an offer sees USD as default instead of PEN
- A tenant who travels sees dates in their browser's timezone, not their configured one
- Cross-channel dashboards can't aggregate amounts into the tenant's preferred currency
- There's no enforcement mechanism to prevent future hardcoding

## Design Principles

1. **Store source truth, convert on read** — ETL data keeps its original currency/timezone.
   Conversion happens at the service/presentation layer.
2. **Explicit injection, not implicit globals** — Services receive `TenantLocale` as a
   parameter, not via hidden state.
3. **Frontend owns display conversion** — Backend stores UTC; frontend converts to tenant
   timezone for display. If tenant changes timezone, all dates adapt instantly.
4. **Dual display rules:**
   - Single-source metric: show source currency; if different from tenant currency, also show
     tenant currency equivalent
   - Multi-source aggregated metric: show tenant currency + USD equivalent
   - If source = tenant currency: show once
   - If tenant currency = USD: show once

## Architecture

### 1. Shared Domain: TenantLocale Value Object

**File:** `backend/src/shared/domain/locale.py` (NEW)

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class TenantLocale:
    """Immutable value object representing a tenant's locale preferences."""
    currency: str   # ISO 4217: "PEN", "USD", "MXN"
    timezone: str   # IANA: "America/Lima", "America/Bogota"
```

Used by backend services that need to know the tenant's display preferences. Constructed
from `TenantModel.default_currency` + `TenantModel.timezone`.

### 2. Shared Domain: Currency Utilities (EXTEND existing)

**File:** `backend/src/shared/domain/currency.py` (EXTEND)

Add bidirectional conversion:

```python
def convert_currency(amount: float, from_currency: str, to_currency: str) -> float | None:
    """Convert between any two supported currencies via USD pivot.
    Returns None if either currency has no known rate."""
    if from_currency == to_currency:
        return round(amount, 2)
    to_usd = EXCHANGE_RATES_TO_USD.get(from_currency)
    from_usd = EXCHANGE_RATES_TO_USD.get(to_currency)
    if to_usd is None or from_usd is None or from_usd == 0:
        return None
    return round(amount * to_usd / from_usd, 2)
```

Add display amount builder:

```python
@dataclass(frozen=True)
class MoneyDisplay:
    """Amounts ready for frontend dual display."""
    source_amount: float
    source_currency: str
    tenant_amount: float | None       # None if conversion unavailable
    tenant_currency: str
    usd_amount: float | None          # None if source or tenant is USD

def build_money_display(
    amount: float,
    source_currency: str,
    tenant_currency: str,
) -> MoneyDisplay:
    """Build display amounts following dual-display rules."""
    ...
```

Add aggregated amount builder:

```python
@dataclass(frozen=True)
class AggregatedMoneyDisplay:
    """Aggregated amounts from multiple sources, in tenant currency."""
    tenant_amount: float
    tenant_currency: str
    usd_amount: float | None

def build_aggregated_display(
    amounts: list[tuple[float, str]],  # [(amount, currency), ...]
    tenant_currency: str,
) -> AggregatedMoneyDisplay:
    """Sum amounts from different currencies into tenant currency + USD."""
    ...
```

### 3. Shared Domain: Datetime Utilities (NEW)

**File:** `backend/src/shared/domain/datetime_utils.py` (NEW)

```python
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

def utc_now() -> datetime:
    """Timezone-aware UTC now. Replaces deprecated datetime.utcnow()."""
    return datetime.now(UTC)

def to_tenant_tz(dt: datetime, tz_name: str) -> datetime:
    """Convert UTC datetime to tenant's local timezone."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(ZoneInfo(tz_name))

def ensure_utc(dt: datetime) -> datetime:
    """Normalize any datetime to UTC. Raises if naive and ambiguous."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)

def is_valid_timezone(tz_name: str) -> bool:
    """Check if a timezone string is a valid IANA timezone."""
    try:
        ZoneInfo(tz_name)
        return True
    except (KeyError, ValueError):
        return False
```

### 4. Backend Dependency Injection

**File:** `backend/src/modules/iam/api/dependencies.py` (EXTEND)

New dependency that piggybacks on the existing `get_current_user` flow:

```python
def get_tenant_locale(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TenantLocale:
    """Load TenantLocale for the current request's tenant.
    Cost: 1 SELECT on tenants table (lightweight, same row already cached by SA session).
    """
    from src.shared.domain.locale import TenantLocale

    tenant = db.execute(
        select(TenantModel).where(TenantModel.id == user.tenant_id)
    ).scalars().first()

    if tenant:
        return TenantLocale(
            currency=tenant.default_currency or "USD",
            timezone=tenant.timezone or "UTC",
        )
    return TenantLocale(currency="USD", timezone="UTC")
```

**Usage in route handlers:**

```python
@router.get("/dashboard", response_model=DashboardDTO)
async def get_dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    locale: TenantLocale = Depends(get_tenant_locale),
):
    service = DashboardService(db, user.tenant_id, locale)
    return service.get_dashboard()
```

**For workers/ETL** (no request context):

```python
# Workers load TenantLocale directly from TenantModel
tenant = db.execute(select(TenantModel).where(TenantModel.id == tenant_id)).scalars().first()
locale = TenantLocale(
    currency=tenant.default_currency or "USD",
    timezone=tenant.timezone or "UTC",
)
```

### 5. Frontend: TenantLocale Context

**File:** `frontend/src/features/tenant/context/tenant-locale-context.tsx` (NEW)

```typescript
"use client"

interface TenantLocale {
  currency: string   // ISO 4217
  timezone: string   // IANA
}

const TenantLocaleContext = createContext<TenantLocale>({
  currency: "USD",
  timezone: "UTC",
})

export function TenantLocaleProvider({ children }: { children: ReactNode }) {
  // Fetches from GET /api/v1/iam/settings/general on mount
  // Uses React Query with long staleTime (settings change rarely)
  // Returns children wrapped in context provider
}

export function useTenantLocale(): TenantLocale {
  return useContext(TenantLocaleContext)
}
```

**Injection point:** Inside `app/providers.tsx`, after `QueryClientProvider` (needs React Query).

**Settings API extension:** The `GeneralSettings` response already returns `default_currency`
and `timezone`. The frontend `GeneralSettings` interface needs to add the `timezone` field
(currently only has `default_currency`).

### 6. Frontend: Currency Formatting (EXTEND existing)

**File:** `frontend/src/lib/format-money.ts` (EXTEND)

```typescript
// NEW: Single-source dual display
export function formatMoneyDual(
  amount: number,
  sourceCurrency: string,
  tenantCurrency: string,
  tenantAmount?: number | null,
): string {
  // source === tenant → "S/ 500"
  // source !== tenant → "S/ 500 (~ S/ 135 PEN)" or with USD
}

// NEW: Multi-source aggregated display
export function formatAggregatedMoney(
  tenantAmount: number,
  tenantCurrency: string,
  usdAmount?: number | null,
): string {
  // tenant === USD → "$1,350"
  // tenant !== USD → "S/ 1,350 (~ $365 USD)"
}
```

### 7. Frontend: Date Formatting Utility (NEW)

**File:** `frontend/src/lib/format-date.ts` (NEW)

```typescript
import { formatInTimeZone } from "date-fns-tz"
import { es } from "date-fns/locale"

export function formatTenantDate(
  isoDate: string,
  timezone: string,
  format?: string,
): string {
  return formatInTimeZone(
    new Date(isoDate),
    timezone,
    format ?? "d MMM yyyy",
    { locale: es },
  )
}

export function formatTenantDateTime(
  isoDate: string,
  timezone: string,
): string {
  return formatInTimeZone(
    new Date(isoDate),
    timezone,
    "d MMM yyyy, HH:mm",
    { locale: es },
  )
}

export function formatTenantTime(
  isoDate: string,
  timezone: string,
): string {
  return formatInTimeZone(
    new Date(isoDate),
    timezone,
    "HH:mm",
    { locale: es },
  )
}
```

### 8. Enforcement: Claude Code Rule (NEW)

**File:** `.claude/rules/master-data.md` (NEW)

Defines the rules for any code that touches currency or timezone:
- Every monetary amount must carry its currency — no bare numbers
- Currency fallbacks must use `useTenantLocale().currency` (frontend) or
  `TenantLocale.currency` (backend), never hardcoded `"USD"`
- All `datetime.utcnow()` replaced with `utc_now()` from `shared/domain/datetime_utils.py`
- All `DateTime()` columns must use `timezone=True`
- Frontend date display must use `formatTenantDate()` with tenant timezone, not
  `toLocaleDateString()`
- Backend stores UTC; frontend converts for display

### 9. Enforcement: Architecture Fitness Test (NEW)

**File:** `backend/tests/architecture/test_master_data.py` (NEW)

Tests:
- No `datetime.utcnow()` or `datetime.datetime.utcnow()` in any Python file
- No `DateTime()` columns without `timezone=True` (except known legacy allowlist)
- No `= "USD"` as Pydantic field default outside of `shared/domain/currency.py` and
  `iam/domain/tenant.py` (the settings model)
- No `toLocaleDateString` or `toLocaleTimeString` in frontend (except calendar.tsx)
- `TenantLocale` imported in services that handle monetary or temporal data
- `SUPPORTED_CURRENCIES` and `EXCHANGE_RATES_TO_USD` only defined in one place

---

## Migration: Violations to Fix

### Backend — Currency Hardcodes (7 files)

| # | File | Line | Current | Fix |
|---|------|------|---------|-----|
| 1 | `offer/domain/offer.py` | 106 | `currency: str = "USD"` | `currency: str` (required, set from tenant at creation) |
| 2 | `offer/api/dto/products.py` | 40 | `currency: str \| None = "USD"` | `currency: str \| None = None` (service injects tenant default) |
| 3 | `shared/domain/ports.py` | 57 | `currency: str = "USD"` | `currency: str` (remove default) |
| 4 | `crm/domain/sale.py` | 19 | `currency: str = "USD"` | `currency: str` (required) |
| 5 | `analytics/dto/sales_dto.py` | 190 | `shopify_currency: str = "USD"` | `shopify_currency: str` (from shop config) |
| 6 | `analytics/dto/adoption_dto.py` | 38 | `refund_currency: str = "USD"` | `refund_currency: str` (from tenant) |
| 7 | `analytics/providers/google_ads_provider.py` | 167,225,271,408 | `account_currency: str = "USD"` | `account_currency: str` (required param) |

Also: `shopify_provider.py` (lines 148, 197) and `tiktok_provider.py` (lines 118, 240)
use `credentials.get("currency", "USD")` — acceptable as provider fallback but should log
a warning when falling back.

### Backend — datetime.utcnow() (8 files)

| # | File | Lines | Fix |
|---|------|-------|-----|
| 1 | `shared/links/service.py` | 31, 52, 92, 100 | `utc_now()` from datetime_utils |
| 2 | `copilot/tools/analytics_tools.py` | 38 | `utc_now()` |
| 3 | `assets/repos/asset_repository.py` | 100 | `utc_now()` |
| 4 | `assets/repos/gallery_repository.py` | 88 | `utc_now()` |
| 5 | `connections/channels/google_calendar.py` | 49 | `utc_now()` |
| 6 | `brand/repos/avatar_repository.py` | 84 | `utc_now()` |
| 7 | `sales_agent/repos/state_repository.py` | 48, 70 | `utc_now()` |
| 8 | `sales_agent/domain/events.py` | 11 | `lambda: utc_now()` |

### Backend — DateTime columns missing timezone=True (1 model, 6 columns)

| File | Columns |
|------|---------|
| `sales_agent/models/agent_state_checkpoint_model.py` | `paused_at`, `frozen_at`, `last_human_message_at`, `deleted_at`, `created_at`, `updated_at` |

**Requires Alembic migration** to alter column types (PostgreSQL: `ALTER COLUMN ... TYPE TIMESTAMPTZ`).

### Backend — Hardcoded timezone strings (2 files)

| # | File | Line | Current | Fix |
|---|------|------|---------|-----|
| 1 | `scheduling/domain/availability_schema.py` | 31 | `timezone: str = "UTC"` | Remove default; inherit from tenant |
| 2 | `scheduling/services/availability_service.py` | 94, 167 | `"America/Bogota"` | Read from `tenant.timezone` |

### Frontend — Currency fallbacks (5 files)

| # | File | Line | Current | Fix |
|---|------|------|---------|-----|
| 1 | `offer-studio/components/.../pricing-form.tsx` | 346 | `currency \|\| "USD"` | `currency \|\| tenantLocale.currency` |
| 2 | `offer-studio/api/adapter.ts` | 184, 189 | `\|\| "USD"` | `\|\| tenantLocale.currency` |
| 3 | `offer-studio/components/dashboard/offer-card.tsx` | 88 | `\|\| 'USD'` | `\|\| tenantLocale.currency` |
| 4 | `growth-studio/.../CostosTab.tsx` | 99 | `\|\| 'USD'` | `\|\| tenantLocale.currency` |
| 5 | `growth-studio/.../utils/format.ts` | 25 | `\|\| 'USD'` | Accept tenant currency param |

### Frontend — Browser timezone assumptions (12 files)

| # | File | Current pattern | Fix |
|---|------|----------------|-----|
| 1 | `settings/components/team-view.tsx` | `toLocaleDateString()` | `formatTenantDate()` |
| 2 | `audit/components/context-panel.tsx` | `toLocaleDateString()` | `formatTenantDate()` |
| 3 | `audit/components/node-details-panel.tsx` | `toLocaleTimeString()` | `formatTenantTime()` |
| 4 | `growth-studio/.../MetricSidebar.tsx` | `toLocaleDateString('es-ES')` | `formatTenantDate()` |
| 5 | `growth-studio/.../SidebarContent.tsx` | `toLocaleDateString('es-MX')` | `formatTenantDate()` |
| 6 | `growth-studio/.../MetaAdsDashboard.tsx` | `toLocaleDateString('es')` | `formatTenantDate()` |
| 7 | `growth-studio/.../CampaignsTab.tsx` | `toLocaleDateString('es')` | `formatTenantDate()` |
| 8 | `growth-studio/.../ChannelDetailSidebar.tsx` | `toLocaleDateString('es-ES')` | `formatTenantDate()` |
| 9 | `growth-studio/.../ChannelRowHeader.tsx` | `toLocaleDateString('es-ES')` | `formatTenantDate()` |
| 10 | `growth-studio/.../NurtureOpportunityDetail.tsx` | `toLocaleTimeString('es-ES')` | `formatTenantTime()` |
| 11 | `growth-studio/.../utils/format.ts` | `toLocaleDateString('es-ES')` | `formatInTimeZone()` |
| 12 | `components/ui/calendar.tsx` | `toLocaleDateString()` | Keep (UI control, not data display) |

---

## Testing Plan

### New Test Files

#### `backend/tests/shared/test_locale.py` (NEW)
- `test_tenant_locale_frozen` — TenantLocale is immutable
- `test_tenant_locale_equality` — Value equality semantics

#### `backend/tests/shared/test_currency_conversion.py` (EXTEND existing test_currency.py)
- `test_convert_currency_same` — PEN → PEN returns same amount
- `test_convert_currency_pen_to_usd` — Known rate, expected result
- `test_convert_currency_usd_to_pen` — Reverse direction
- `test_convert_currency_pen_to_mxn` — Cross via USD pivot
- `test_convert_currency_unknown` — Returns None
- `test_build_money_display_same_currency` — No dual display needed
- `test_build_money_display_different_currency` — Dual display with conversion
- `test_build_money_display_tenant_is_usd` — Source + USD only
- `test_build_aggregated_display_single_currency` — Simple sum
- `test_build_aggregated_display_mixed_currencies` — Cross-currency aggregation
- `test_build_aggregated_display_tenant_is_usd` — No duplicate USD

#### `backend/tests/shared/test_datetime_utils.py` (NEW)
- `test_utc_now_is_aware` — Has tzinfo, is UTC
- `test_utc_now_not_naive` — tzinfo is not None
- `test_to_tenant_tz_lima` — UTC midnight → Lima (UTC-5)
- `test_to_tenant_tz_bogota` — UTC midnight → Bogota (UTC-5)
- `test_to_tenant_tz_naive_input` — Naive datetime assumed UTC
- `test_ensure_utc_from_aware` — Converts non-UTC aware to UTC
- `test_ensure_utc_from_naive` — Adds UTC tzinfo
- `test_is_valid_timezone_valid` — "America/Lima" → True
- `test_is_valid_timezone_invalid` — "Narnia/Castle" → False
- `test_is_valid_timezone_utc` — "UTC" → True

#### `backend/tests/modules/iam/test_tenant_locale_dependency.py` (NEW)
- `test_get_tenant_locale_returns_tenant_values` — PEN + America/Lima
- `test_get_tenant_locale_fallback_when_null` — Null fields → USD + UTC
- `test_get_tenant_locale_missing_tenant` — Returns default locale

#### `backend/tests/architecture/test_master_data.py` (NEW)
- `test_no_utcnow_usage` — Scan all .py for `utcnow()`, fail if found outside allowlist
- `test_no_datetime_without_timezone` — Scan models for `DateTime()` without `timezone=True`
- `test_no_hardcoded_usd_defaults` — Scan DTOs/domains for `= "USD"` outside allowed files
- `test_no_toLocaleDateString_in_frontend` — Scan .tsx/.ts for browser date methods

#### `frontend/src/features/tenant/__tests__/tenant-locale-context.test.tsx` (NEW)
- `test_provides_default_locale` — Without fetch, defaults to USD/UTC
- `test_provides_fetched_locale` — After settings fetch, returns PEN/America_Lima
- `test_hook_outside_provider_throws` — useTenantLocale outside provider

#### `frontend/src/lib/__tests__/format-money.test.ts` (EXTEND)
- `test_formatMoneyDual_same_currency` — Single display
- `test_formatMoneyDual_different_currency` — Dual display
- `test_formatAggregatedMoney_tenant_is_usd` — Single display
- `test_formatAggregatedMoney_tenant_is_pen` — Dual with USD

#### `frontend/src/lib/__tests__/format-date.test.ts` (NEW)
- `test_formatTenantDate_utc` — UTC timezone
- `test_formatTenantDate_lima` — America/Lima
- `test_formatTenantDate_custom_format` — Custom date format
- `test_formatTenantDateTime` — Date + time
- `test_formatTenantTime` — Time only
- `test_formatTenantDate_day_boundary` — 23:30 UTC = previous day in Lima

### Updated Existing Tests

- `backend/tests/modules/analytics/test_ad_performance.py` — Update any hardcoded USD
  assertions to use tenant locale
- `backend/tests/modules/analytics/test_campaign_repository.py` — Same
- `backend/tests/modules/analytics/test_campaign_sync_pipeline.py` — Same
- `backend/tests/modules/offer/` — Update product creation tests to pass currency explicitly
- `backend/tests/shared/test_currency.py` — Add convert_currency tests

### Migration Test

- `test_agent_checkpoint_datetime_migration` — Verify `ALTER COLUMN ... TYPE TIMESTAMPTZ`
  succeeds and existing data is preserved (run against cloned DB per migration rules)

---

## Files Changed Summary

### New Files (8)
1. `backend/src/shared/domain/locale.py`
2. `backend/src/shared/domain/datetime_utils.py`
3. `backend/tests/shared/test_datetime_utils.py`
4. `backend/tests/modules/iam/test_tenant_locale_dependency.py`
5. `backend/tests/architecture/test_master_data.py`
6. `frontend/src/features/tenant/context/tenant-locale-context.tsx`
7. `frontend/src/lib/format-date.ts`
8. `.claude/rules/master-data.md`

### Extended Files (6)
1. `backend/src/shared/domain/currency.py` — Add convert_currency, MoneyDisplay, etc.
2. `backend/src/modules/iam/api/dependencies.py` — Add get_tenant_locale
3. `frontend/src/lib/format-money.ts` — Add formatMoneyDual, formatAggregatedMoney
4. `frontend/src/app/providers.tsx` — Wrap with TenantLocaleProvider
5. `backend/tests/shared/test_currency.py` — Add conversion tests
6. `frontend/src/lib/__tests__/format-money.test.ts` — Add dual display tests

### Migration Files (1)
1. `backend/alembic/versions/xxx_add_timezone_to_checkpoint_columns.py`

### Migrated Files (~27)
- 7 backend files: currency hardcode removal
- 8 backend files: utcnow() → utc_now()
- 1 backend model: DateTime → DateTime(timezone=True)
- 2 backend files: hardcoded timezone strings
- 5 frontend files: currency fallback → tenantLocale
- 11 frontend files: toLocaleDateString → formatTenantDate

---

## Out of Scope

- Real-time exchange rates (keep static rates for now; can add API later)
- Per-user timezone override (tenant-level is sufficient for now)
- Locale/language setting (Spanish only for now)
- Historical exchange rate tracking
