# T-be-6 Impl Log — Vitalia Application Services (Consent + TreatmentFollowup + PrepaidPayment)

## Ticket
**T-be-6** · Story 11 `luana-vitalia-bootstrap` · Session 4 W3

## Scope
Three application services (TDD RED→GREEN) for Vitalia module:
1. `ConsentService` — HMAC-signed consent URL + signing with IP/UA capture
2. `TreatmentFollowupService` — D+5/14/90 cron tick scheduling in tenant TZ
3. `PrepaidPaymentService` — gateway routing (MercadoPago LatAm / Stripe US/EU)

## Files Created / Modified

### Tests (RED phase — created first)
- `vitalia/backend/tests/unit/application/test_consent_service.py` — 10 tests
- `vitalia/backend/tests/unit/application/test_treatment_followup_service.py` — 7 tests
- `vitalia/backend/tests/unit/application/test_prepaid_payment_service.py` — 8 tests

### Services (GREEN phase)
- `vitalia/backend/src/modules/vitalia/application/services/consent_service.py`
- `vitalia/backend/src/modules/vitalia/application/services/treatment_followup_service.py`
- `vitalia/backend/src/modules/vitalia/application/services/prepaid_payment_service.py`

## Decisions

### D1 — DI constructor pattern
All services accept `session`, `*_repo`, `tenant_id` via constructor. No direct DB session construction inside service. Follows `OnboardingService` precedent.

### D2 — Idempotency
- `ConsentService.request_consent`: checks `consent_repo.get_pending_by_booking()` first; returns existing if same `(booking_id, template_slug)`.
- `TreatmentFollowupService.start_followup`: checks `followup_repo.get_by_booking_id()` first; returns existing if found.
- `PrepaidPaymentService.generate_payment_link`: idempotency key = `f"vitalia:payment:{booking_id}:{deposit_or_full}"`; checks `payment_intent_repo.get_by_idempotency_key()` first.

### HMAC Implementation
- `ConsentService._sign()` uses `hmac.new(key, msg, hashlib.sha256).hexdigest()`
- `verify_consent_token()` uses `hmac.compare_digest()` for constant-time comparison (prevents timing attacks)
- Secret from `VITALIA_CONSENT_URL_SECRET` env var or constructor `hmac_secret` param (dev/test)
- URL format: `{base_url}/consent/sign?consent_id={id}&token={hmac}`

### Tenant TZ Morning Anchor
- `_compute_cron_ticks()` uses `zoneinfo.ZoneInfo(tenant_timezone)` to anchor ticks at 09:00 local
- Prevents WhatsApp follow-ups landing at midnight (e.g., 00:00 UTC = 21:00 AR previous day)
- Stored as UTC (timezone-aware), computed relative to tenant's morning
- Invalid TZ fallback: logs warning + uses UTC

### Gateway Routing
- `_LATAM_COUNTRIES_MP = frozenset({"AR","MX","BR","CL","CO","PE","UY","BO","PY","EC"})`
- LatAm → `mercadopago`, else → `stripe_connect`
- `preferred_gateway` from BrandConfig overrides country default if valid

### langchain_core Isolation
`luana_core_channels` imports `langchain_core` in its `__init__.py` chain; `langchain_core` is NOT installed in vitalia's venv. Solution: patch internal service methods (`_create_mp_preference`, `_create_stripe_session`) in tests rather than patching through external package. This isolates vitalia's unit tests from the langchain dependency.

### StripeConnectAdapter — Vitalia-local stub
No Stripe adapter exists in `luana-core-channels`. Created a minimal stub in `prepaid_payment_service.py` using `httpx.AsyncClient` (timeout=10s per graceful-degradation). Tagged `# vitalia-local stub` for lift to core in Story 11.bis.

### Currency — No hardcoded USD
`GeneratePaymentLinkRequest.currency` is required (no default). Pydantic `extra="forbid"` ensures no silent defaults. Tests verify `ValidationError` when currency omitted.

## Acceptance Criteria Coverage

| Criteria | Tests | Status |
|---|---|---|
| A1: HMAC verify + 24h expiry default | `test_hmac_verify`, `test_consent_url_expiry_24h_default` | GREEN |
| A2: D+5/14/90 cron ticks in tenant TZ | `test_cron_ticks_scheduled`, `test_cron_ticks_chronological_order`, `test_cron_ticks_tenant_tz_morning_anchor` | GREEN |
| A3: MercadoPago AR + Stripe US routing | `test_gateway_routing`, `test_gateway_routing_cl_uses_mercadopago`, `test_gateway_routing_preferred_gateway_overrides` | GREEN |

## Test Results
25/25 PASS (10 consent + 7 followup + 8 payment)

## Lint Results
- `ruff check`: All checks passed
- `ruff format --check`: All checks passed (after `ruff format` applied)

## Skills Consulted
- `backend-expert/references/runtime-quality-checklist.md` — anti-patterns (SQLA legacy, datetime.utcnow, tenant isolation, response_model)
- Patterns from `OnboardingService` + `test_onboarding_service.py` as DI/test style reference
