# T-be-6 Result — Vitalia Application Services

## Verdict: GREEN

**Ticket:** T-be-6 · Story 11 `luana-vitalia-bootstrap` · Session 4 W3

## Validators Passed

| Validator | Command | Result |
|---|---|---|
| V-F-2a pytest consent | `uv run pytest tests/unit/application/test_consent_service.py -v` | 10/10 PASS |
| V-F-2b pytest followup | `uv run pytest tests/unit/application/test_treatment_followup_service.py -v` | 7/7 PASS |
| V-F-2c pytest payment | `uv run pytest tests/unit/application/test_prepaid_payment_service.py -v` | 8/8 PASS |
| V-F-2d ruff check | `uv run ruff check <6 files>` | 0 errors |
| V-F-2e ruff format | `uv run ruff format --check <6 files>` | 0 files to reformat |

**Total: 25/25 tests PASS, 0 lint errors**

## Services Delivered

### ConsentService
- `request_consent(request, base_url)` → `ConsentUrlResult` (consent_url with HMAC token, expires_at=now+24h, is_new flag)
- `sign_consent(request)` → `SignConsentResult` (HMAC token verification → capture signed_name, IP, User-Agent)
- `build_consent_url(consent_id, base_url)` → signed URL
- `verify_consent_token(consent_id, token)` → bool (constant-time `hmac.compare_digest`)
- D2: idempotency on same `(booking_id, template_slug)` within TTL

### TreatmentFollowupService
- `start_followup(request)` → `StartFollowupResult` with `cron_ticks: {"D5": dt, "D14": dt, "D90": dt}`
- Ticks anchored at 09:00 tenant local time (zoneinfo), stored UTC
- LangGraph workflow registration stub (deferred to T-workflow-1)
- D2: idempotency on same `booking_id`

### PrepaidPaymentService
- `generate_payment_link(request)` → `GeneratePaymentLinkResult` with `gateway`, `checkout_url`, `external_ref_id`
- Gateway routing: LatAm countries → `mercadopago`, else → `stripe_connect`
- `preferred_gateway` from BrandConfig overrides country default
- Currency from request DTO — never hardcoded
- D2: idempotency key = `vitalia:payment:{booking_id}:{deposit_or_full}`

## Environment Variable Required
`VITALIA_CONSENT_URL_SECRET` — HMAC secret for consent URL tokens. Must be set in production environment. Development uses constructor param.

## Luana-platform commit path
`/home/chris/luana-platform` — committed to `main` branch (luana-platform repo)
