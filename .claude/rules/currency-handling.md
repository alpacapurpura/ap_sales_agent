---
globs: "{backend/src/modules/analytics/**/*.py,frontend/src/lib/format-money*}"
description: Currency from data source — never hardcoded
---

# Currency Handling

**Every monetary value displayed in the UI MUST use the currency from the data source, never hardcoded.**

## Data Flow

```
Provider API (Meta, Shopify, etc.) → official_metrics.currency (DB)
  → Service detects currency via SELECT currency FROM official_metrics WHERE channel_slug=:slug LIMIT 1
    → DTO includes currency: str | None field
      → Frontend receives currency and passes to formatMoney(amount, currency)
```

## Backend Rules

1. **Every DTO that contains monetary fields** (spend, cpc, cpm, cpa, cost_per_*, revenue) MUST include a `currency: str | None = None` field.
2. **Every service that builds monetary DTOs** MUST query the actual currency from `official_metrics` for the tenant+channel.
3. **Never assume USD.** Different tenants use different currencies (PEN, USD, MXN, COP, etc.)
4. Currency is stored per-row in `official_metrics.currency` and is set during ETL extraction from the provider's ad account settings.

## Frontend Rules

1. **Never hardcode 'USD' in `formatMoney()` calls.** Always use the currency from the API response.
2. **Fallback chain:** `response.currency ?? parentData.currency ?? 'USD'` — only use 'USD' as last resort.
3. Use `formatMoney(amount, currency)` from `lib/format-money.ts` — it handles all ISO 4217 codes via `Intl.NumberFormat`.
4. For dual display (local + USD): use `formatDualCurrency(amount, currency, usdAmount)`.

## MetricKpiDTO Pattern

When `unit == "currency"` in the metric catalog, the KPI MUST include the channel's currency:

```python
MetricKpiDTO(
    ...,
    unit=unit,
    currency=channel_currency if unit == "currency" else None,
)
```

## Common Currencies in Nicolify

| Currency | Country | Example Tenant |
|----------|---------|---------------|
| PEN | Perú | Visionarias |
| USD | USA / International | — |
| MXN | México | — |
| COP | Colombia | — |

## Prohibited

- `formatMoney(value, 'USD')` without checking if the data's currency is actually USD
- DTOs with monetary fields but no `currency` field
- Services that skip currency detection for monetary responses
