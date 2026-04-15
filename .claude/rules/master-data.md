---
globs: "{backend/src/shared/domain/locale*,backend/src/shared/domain/currency*,frontend/src/features/tenant/**/*.{ts,tsx},frontend/src/lib/format-date*,frontend/src/lib/format-money*}"
description: TenantLocale currency+timezone system — no hardcoded currencies or timezones
---

# Master Data: Currency & Timezone

**Every module MUST use the tenant's locale preferences. No hardcoded currencies or timezones.**

## Architecture

```
TenantModel (DB)
  ├── default_currency: str   (ISO 4217)
  └── timezone: str            (IANA)

Backend: TenantLocale value object (shared/domain/locale.py)
  ├── Injected via get_tenant_locale() FastAPI dependency
  └── Workers load directly from TenantModel

Frontend: useTenantLocale() React hook (features/tenant/context/)
  ├── Returns { currency, timezone }
  └── Loaded from GET /api/v1/iam/settings/general
```

## Currency Rules

1. **Store source truth:** ETL data keeps its original currency (official_metrics.currency).
   Never convert on write.
2. **No hardcoded "USD" defaults** in DTOs or domain models.
   Only allowed in: `shared/domain/currency.py`, `iam/domain/tenant.py`, `shared/domain/locale.py`.
3. **Display rules:**
   - Single-source metric: source currency + tenant currency equivalent (if different)
   - Aggregated multi-source: tenant currency + USD equivalent
   - Use `build_money_display()` or `build_aggregated_display()` (backend)
   - Use `formatMoneyDual()` or `formatAggregatedMoney()` (frontend)
4. **Frontend fallback chain:** `data.currency ?? useTenantLocale().currency`
   Never `currency || 'USD'`.
5. **Bidirectional conversion:** Use `convert_currency()` from `shared/domain/currency.py`.
   Old `convert_to_usd()` still available but prefer `convert_currency()` for any new code.

## Timezone Rules

1. **Backend stores UTC always.** Use `utc_now()` from `shared/domain/datetime_utils.py`.
   Never `datetime.utcnow()` (deprecated).
2. **All DateTime columns** must use `DateTime(timezone=True)`.
3. **Frontend converts for display** using `formatTenantDate()` / `formatTenantDateTime()` /
   `formatTenantTime()` from `lib/format-date.ts`. Never `toLocaleDateString()`.
4. **Timezone source:** `useTenantLocale().timezone` (frontend), `TenantLocale.timezone` (backend).

## When Adding New Monetary Fields

1. DTO must include a `currency: str` field alongside the amount
2. Service must resolve currency from data source or `TenantLocale`
3. Frontend must use `formatMoneyDual()` or `formatAggregatedMoney()`

## When Adding New Date Displays

1. Backend returns ISO 8601 UTC strings
2. Frontend uses `formatTenantDate(isoString, timezone)` with `useTenantLocale().timezone`

## Prohibited

- `datetime.utcnow()` anywhere
- `DateTime()` without `timezone=True` in models
- `= "USD"` as Pydantic field default (outside allowed files)
- `toLocaleDateString()` or `toLocaleTimeString()` for data display
- `currency || 'USD'` in frontend components
- `"America/Bogota"` or any hardcoded timezone in services
