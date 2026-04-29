---
globs: "{backend/src/shared/domain/locale*,backend/src/shared/domain/currency*,frontend/src/features/tenant/**/*.{ts,tsx},frontend/src/lib/format-date*,frontend/src/lib/format-money*}"
description: Stub — invoca backend-expert skill
---

# Master Data: Currency + Timezone

Cada módulo usa tenant locale prefs. Sin hardcoded.
- BE store UTC siempre (`utc_now()`, `DateTime(timezone=True)`).
- BE: `TenantLocale` VO (shared/domain/locale.py), DI `get_tenant_locale()`.
- FE: `useTenantLocale()` → `{ currency, timezone }`. Display: `formatTenantDate*()`, `formatMoneyDual()`.
- Currency: ETL keeps source currency. No convert on write. FE fallback `data.currency ?? useTenantLocale().currency`.

Detalle (build_money_display, convert_currency, agregar monetary field/date) en `backend-expert` skill → `references/master-data.md`.

**Prohibido:** `datetime.utcnow()`, `DateTime()` sin `timezone=True`, `= "USD"` Pydantic default (fuera allowed files), `toLocaleDateString()`, `currency || 'USD'` FE, hardcoded timezone.
