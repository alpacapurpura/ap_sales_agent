---
globs: "{backend/src/modules/analytics/**/*.py,frontend/src/lib/format-money*}"
description: Stub — invoca backend-expert skill
---

# Currency Handling

Monetary value en UI usa data source currency, nunca hardcoded.

Flow: provider → `official_metrics.currency` → service detecta → DTO `currency: str | None` → FE `formatMoney(amount, currency)`.

- BE: cada DTO con monetary fields incluye `currency: str | None = None`. Service queries currency de `official_metrics` for tenant+channel.
- FE: nunca hardcode 'USD'. Fallback `response.currency ?? parentData.currency ?? 'USD'`.
- KPI `unit == "currency"` MUST include `currency` from channel.

Detalle + tabla currencies LatAm (PEN/USD/MXN/COP) en `backend-expert` skill → `references/currency-handling.md`.

**Prohibido:** `formatMoney(value, 'USD')` sin verify. DTOs monetary sin `currency`. Skip currency detection.
