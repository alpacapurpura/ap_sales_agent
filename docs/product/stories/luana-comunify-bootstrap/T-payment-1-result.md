# T-payment-1 Result: Payment Channel Adapters — Comunify Overlay
<!-- voseo-allowed: technical result doc, no user-facing strings -->

**Story:** luana-comunify-bootstrap  
**Ticket:** T-payment-1  
**Status:** DONE  
**Date:** 2026-05-14  

## Deliverables

### 1. Core lifts (new files in `@luana/core/channels`)

| File | Description |
|---|---|
| `core/luana-core-channels/src/luana_core_channels/payment/stripe_connect_adapter.py` | Generic `StripeConnectAdapter` base class — `_compliance_metadata()` hook (empty default), `_application_fee_amount()` hook (None default), `subscriber_id`/`entity_id` terminology |
| `core/luana-core-channels/src/luana_core_channels/payment/tokenized_recurring_adapter.py` | Generic `TokenizedRecurringAdapter` base class — `idempotency_prefix` configurable (default `luana:recurring`), neutral `subscriber_id`/`entity_id` domain terms, no `plan_kind` (comunify-specific) |
| `core/luana-core-channels/src/luana_core_channels/payment/__init__.py` | Updated to export all three adapters + VOs |

**Story 11 lift status at T-payment-1 start:** `MercadoPagoAdapter` was already in core (Story 11 done). `StripeConnectAdapter` + `TokenizedRecurringAdapter` were vitalia-local. T-payment-1 lifted both per arch doc § 2 contract.

### 2. Comunify overlay adapters (new files)

| File | Description |
|---|---|
| `comunify/backend/src/modules/comunify/payment/stripe_connect_adapter.py` | `ComunifyStripeConnectAdapter` — `compliance_level=creator_economy` (D7), `application_fee` per plan_tier (5%/7%/10%), `APPLICATION_FEE_RATES` dict |
| `comunify/backend/src/modules/comunify/payment/mercadopago_adapter.py` | `ComunifyMercadoPagoAdapter` — AR-primary subscriber tokenization, HMAC-SHA256 webhook, `_extra_metadata()` injects creator_economy fields |
| `comunify/backend/src/modules/comunify/payment/tokenized_recurring_adapter.py` | `ComunifyTokenizedRecurringAdapter` — `plan_kind` (cohort_installments\|monthly_membership), `COHORT_INSTALLMENT_OPTIONS=(3,6,12)`, `idempotency_prefix=comunify:recurring` |
| `comunify/backend/src/modules/comunify/payment/__init__.py` | Package init exporting all adapters + constants |

### 3. Integration tests

File: `comunify/backend/tests/integration/test_payment_adapters.py`

| Test class | Tests | Covers |
|---|---|---|
| `TestComunifyOverlayApplicationFeePerTier` | 5 | Fee rates per tier, compliance metadata, Stripe payload shape |
| `TestCountryRoutingArgentinaUsesMercadoPago` | 8 | AR→MP routing, metadata, status mapping, HMAC webhook (valid/invalid/replay/empty-secret) |
| `TestTokenizedRecurring3MonthInstallment` | 12 | 3 charges created, idempotency key namespacing, retry dedup, invalid counts (8 cases), valid counts (3,6,12), monthly_membership no restriction |
| `TestComunifyStripeWebhook` | 8 | Webhook valid/invalid/replay/empty-secret + edge cases |

**Result: 33/33 PASS (0.07s)**

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| D7 compliance level | `creator_economy` | Comunify is not healthcare; hipaa_lite is Vitalia-only |
| APPLICATION_FEE_RATES source | brand.yaml plan_tiers cross-ref | creator=$29→5%, pro=$99→7%, agency=$299→10% |
| Idempotency prefix | `comunify:recurring:` | Namespaced to prevent collision with `vitalia:recurring:` if infra shared |
| Venv isolation | Self-contained adapters | `luana_core_channels/__init__.py` triggers langchain; comunify venv doesn't have it. Full inheritance active in uv workspace env. |
| country_routing | AR→MP metadata field | Routing metadata in MP preference; no hard runtime if-branch needed at adapter layer |

## Test Counts

| Suite | Before | After | Delta |
|---|---|---|---|
| comunify/backend full | 240 passed, 9 skipped | 273 passed, 9 skipped | +33 |
| core/luana-core-channels | 100 passed | 100 passed (unchanged) | 0 |

## Lint / Format

```
uv run ruff check comunify/backend/src/modules/comunify/payment/ → All checks passed!
uv run ruff format --check comunify/backend/src/modules/comunify/payment/ → 4 files already formatted
uv run ruff check core/luana-core-channels/src/luana_core_channels/payment/ → All checks passed!
```

## Files Modified (git stage list)

```
core/luana-core-channels/src/luana_core_channels/payment/__init__.py
core/luana-core-channels/src/luana_core_channels/payment/stripe_connect_adapter.py
core/luana-core-channels/src/luana_core_channels/payment/tokenized_recurring_adapter.py
comunify/backend/src/modules/comunify/payment/__init__.py
comunify/backend/src/modules/comunify/payment/stripe_connect_adapter.py
comunify/backend/src/modules/comunify/payment/mercadopago_adapter.py
comunify/backend/src/modules/comunify/payment/tokenized_recurring_adapter.py
comunify/backend/tests/integration/test_payment_adapters.py
docs/product/stories/luana-comunify-bootstrap/T-payment-1-result.md
```
