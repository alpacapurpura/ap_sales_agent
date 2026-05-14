# T-be-9 Implementation Log — Webhook Receivers (5 Sources)

**Story:** luana-comunify-bootstrap
**Ticket:** T-be-9 — 5 webhook receivers with HMAC signature verification + idempotency
**Validator:** V-F-15 — `pytest tests/integration/test_{stripe,mercadopago,clerk}_webhook.py -v`
**Status:** tests-passing

---

## Skills Consulted

| Skill | Why | Decision |
|---|---|---|
| `backend-expert` | Quality gate pre-impl: anti-patterns FastAPI/SQLA/tests | Verified: `response_model=` mandatory, `Request.body()` before JSON parse for HMAC, inline verify functions over import chain |
| `tessl__fastapi` | Async patterns, `response_model=`, Header dependency injection | Used `Header(alias=...)` for case-sensitive webhook headers (Stripe-Signature, svix-id, X-Hub-Signature-256) |
| `tessl__pytest-api-testing` | `httpx.AsyncClient` + `ASGITransport`, fixture scoping, `monkeypatch.setenv` | Used `pytest_asyncio.fixture` + `_seen_event_ids.clear()` in each fixture for test isolation |
| `tessl__graceful-degradation` | External calls timeout + fallback | Webhooks are inbound (no external calls in T-be-9 scope); no HTTP client needed. Noted for future service dispatch integration |

---

## Files Created / Modified

### Created (new)

1. `luana-platform/comunify/backend/src/modules/comunify/infrastructure/adapters/__init__.py`
   — Module marker for adapters package

2. `luana-platform/comunify/backend/src/modules/comunify/infrastructure/adapters/clerk_webhook_adapter.py`
   — `ClerkWebhookAdapter` with Svix HMAC-SHA256 verify (base64-decoded secret, multi-sig support, 300s tolerance)
   — `ClerkWebhookEvent(frozen=True)` dataclass

3. `luana-platform/comunify/backend/src/modules/comunify/infrastructure/adapters/manychat_webhook_adapter.py`
   — `ManychatWebhookAdapter` with HMAC-SHA256 bare hex verify + optional timestamp check
   — `ManychatInboundEvent(frozen=True)` dataclass

4. `luana-platform/comunify/backend/src/modules/comunify/api/webhook_routes.py`
   — `webhook_router = APIRouter(prefix="/api/v1/comunify/webhooks")`
   — `WebhookAck(BaseModel)` with `response_model=` on all 5 endpoints
   — Inline `_verify_stripe_hmac()`, `_verify_mercadopago_hmac()`, `_verify_whatsapp_hmac()` (avoids payment/__init__ import chain)
   — `_seen_event_ids: set[str]` in-process idempotency store (production: DB query)
   — 5 endpoints: /stripe, /mercadopago, /clerk, /whatsapp/inbound, /manychat/inbound

5. `luana-platform/comunify/backend/tests/integration/test_stripe_webhook.py`
   — 7 tests: valid payment_intent.succeeded, valid subscription.created, valid subscription.updated, invalid HMAC, replay, missing header 422, timestamp too old

6. `luana-platform/comunify/backend/tests/integration/test_mercadopago_webhook.py`
   — 6 tests: valid bare hex, valid structured ts=,v1=, invalid HMAC, replay, no sig + no secret 200, invalid JSON

7. `luana-platform/comunify/backend/tests/integration/test_clerk_webhook.py`
   — 6 tests: valid user.created, invalid HMAC, replay, missing svix headers 422, non-user event, timestamp too old

8. `luana-platform/comunify/backend/tests/integration/test_whatsapp_webhook.py`
   — 6 tests: valid inbound, invalid HMAC, replay, no sig + secret warns 200, no sig + no secret 200, invalid JSON

9. `luana-platform/comunify/backend/tests/integration/test_manychat_webhook.py`
   — 5 tests: valid inbound, invalid HMAC, replay, no sig + no secret 200, invalid JSON

### Modified (existing)

10. `luana-platform/comunify/backend/src/main.py`
    — Added `from src.modules.comunify.api.webhook_routes import webhook_router`
    — Added `app.include_router(webhook_router)`

---

## Design Decisions

### D1 — Import chain avoidance (Stripe)
`payment/stripe_connect_adapter.py` imports `langchain_core` transitively. Inlined `_verify_stripe_hmac()` in `webhook_routes.py` to avoid the import chain. Same algorithm, no duplication of business logic.

### D2 — Tenant isolation note
Webhooks are unauthenticated by Clerk (no JWT). `X-Tenant-ID` header NOT used. Tenant resolved from payload metadata. Noted in module docstring per D11.

### D3 — MercadoPago permissive mode
Legacy IPN may not include `X-Signature`. When `mp_secret` is empty (dev/test), allow through. When secret is configured but header absent, log `webhook_hmac_missing_header` warning + continue. Mirrors Vitalia pattern.

### D4 — ManyChat timestamp fix
Test payload had hardcoded `timestamp: 1685395200` (old epoch). ManychatWebhookAdapter enforces ±5 min tolerance when payload contains `timestamp`. Fixed test to use `int(time.time())` for fresh payload.

### D5 — In-memory idempotency (T-be-9 scope)
`_seen_event_ids: set[str]` process-level. Production replaces with DB query on `comunify_community_audit_log` with 7-day window. Comment in code notes the SQL query pattern.

---

## Quality Gates

| Gate | Result |
|---|---|
| `ruff check` (owned files) | PASS — 0 errors |
| `ruff format --check` (owned files) | PASS |
| V-F-15 (stripe + mercadopago + clerk) | PASS — 19/19 |
| WA + ManyChat tests | PASS — 11/11 |
| Architecture fitness | PASS — 17/17 |

Total integration tests added: 30 (5 files × avg 6 tests)

---

## Default-flip pre-audit (Step 0.5)

No `core/config.py` defaults touched. Not applicable.

---

## Cross-module reads

- READ `/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/api/webhook_routes.py` (pattern reference — read-only)
- READ `/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/infrastructure/adapters/clerk_webhook_adapter.py` (pattern reference)
- READ `/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/infrastructure/adapters/manychat_webhook_adapter.py` (pattern reference)
- READ `/home/chris/luana-platform/comunify/backend/src/modules/comunify/payment/stripe_connect_adapter.py` (import chain audit)
