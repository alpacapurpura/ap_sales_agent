---
globs: "{backend/src/modules/analytics/**/*.py,frontend/src/lib/format-money*}"
description: Currency from data source — never hardcoded
---

# Currency Handling

Every monetary value en UI MUST use data source currency, nunca hardcoded.

## Data Flow

```
Provider API (Meta, Shopify) → official_metrics.currency (DB)
  → Service detecta via SELECT currency FROM official_metrics WHERE channel_slug=:slug LIMIT 1
    → DTO includes currency: str | None
      → FE passes to formatMoney(amount, currency)
```

## Backend Rules

1. Every DTO con monetary fields (spend, cpc, cpm, cpa, cost_per_*, revenue) MUST include `currency: str | None = None`.
2. Every service building monetary DTOs MUST query currency de `official_metrics` for tenant+channel.
3. **Never assume USD.** Tenants usan PEN/USD/MXN/COP/etc.
4. Currency per-row en `official_metrics.currency`, set en ETL from provider ad account.

## Frontend Rules

1. **Never hardcode 'USD'** en `formatMoney()`. Use currency from API response.
2. **Fallback:** `response.currency ?? parentData.currency ?? 'USD'` — 'USD' last resort.
3. Use `formatMoney(amount, currency)` de `lib/format-money.ts` — handles all ISO 4217 via `Intl.NumberFormat`.
4. Dual display (local + USD): `formatDualCurrency(amount, currency, usdAmount)`.

## MetricKpiDTO Pattern

`unit == "currency"` en catalog → KPI MUST include channel currency:

```python
MetricKpiDTO(
    ...,
    unit=unit,
    currency=channel_currency if unit == "currency" else None,
)
```

## Common Currencies Nicolify

| Currency | Country | Tenant |
|---|---|---|
| PEN | Perú | Visionarias |
| USD | USA/Int'l | — |
| MXN | México | — |
| COP | Colombia | — |

## Prohibido

- `formatMoney(value, 'USD')` sin check si data es USD
- DTOs con monetary fields sin `currency`
- Services que skip currency detection para monetary responses
