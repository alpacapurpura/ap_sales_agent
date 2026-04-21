---
globs: "{backend/src/shared/domain/locale*,backend/src/shared/domain/currency*,frontend/src/features/tenant/**/*.{ts,tsx},frontend/src/lib/format-date*,frontend/src/lib/format-money*}"
description: TenantLocale currency+timezone system — no hardcoded currencies or timezones
---

# Master Data: Currency & Timezone

Every module MUST use tenant locale prefs. No hardcoded.

## Architecture

```
TenantModel (DB)
  ├── default_currency: str   (ISO 4217)
  └── timezone: str            (IANA)

Backend: TenantLocale VO (shared/domain/locale.py)
  ├── Injected via get_tenant_locale() FastAPI dep
  └── Workers load from TenantModel

Frontend: useTenantLocale() hook (features/tenant/context/)
  ├── Returns { currency, timezone }
  └── From GET /api/v1/iam/settings/general
```

## Currency Rules

1. **Source truth:** ETL data keeps original currency (official_metrics.currency). No convert on write.
2. **No hardcoded "USD"** en DTOs/domain. Only allowed: `shared/domain/currency.py`, `iam/domain/tenant.py`, `shared/domain/locale.py`.
3. **Display:**
   - Single-source metric: source currency + tenant equivalent (si different)
   - Aggregated multi-source: tenant currency + USD equivalent
   - BE: `build_money_display()` / `build_aggregated_display()`
   - FE: `formatMoneyDual()` / `formatAggregatedMoney()`
4. **FE fallback:** `data.currency ?? useTenantLocale().currency`. Never `currency || 'USD'`.
5. **Bidirectional convert:** `convert_currency()` de `shared/domain/currency.py`. Old `convert_to_usd()` existe, prefer `convert_currency()`.

## Timezone Rules

1. **BE stores UTC always.** `utc_now()` de `shared/domain/datetime_utils.py`. Never `datetime.utcnow()`.
2. **All DateTime columns** `DateTime(timezone=True)`.
3. **FE convert display:** `formatTenantDate()` / `formatTenantDateTime()` / `formatTenantTime()` de `lib/format-date.ts`. Never `toLocaleDateString()`.
4. **Timezone source:** `useTenantLocale().timezone` (FE), `TenantLocale.timezone` (BE).

## Agregando monetary field

1. DTO incluir `currency: str` alongside amount
2. Service resuelve currency de data source o `TenantLocale`
3. FE usa `formatMoneyDual()` / `formatAggregatedMoney()`

## Agregando date display

1. BE returns ISO 8601 UTC strings
2. FE `formatTenantDate(iso, tz)` con `useTenantLocale().timezone`

## Prohibido

- `datetime.utcnow()`
- `DateTime()` sin `timezone=True`
- `= "USD"` Pydantic default (fuera allowed files)
- `toLocaleDateString()` / `toLocaleTimeString()` para data display
- `currency || 'USD'` en FE
- Hardcoded `"America/Bogota"` / timezone en services
