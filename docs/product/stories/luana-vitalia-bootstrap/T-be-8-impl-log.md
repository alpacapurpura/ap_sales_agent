# T-be-8 Implementation Log — BE Webhook Receivers

**Ticket:** T-be-8  
**Story:** luana-vitalia-bootstrap  
**Date:** 2026-05-14  
**Builder:** claude-sonnet-4-6  

## Skills Consulted

| Skill | Why | Decision |
|---|---|---|
| `tessl__fastapi` | response_model= mandatory, async routes, raw body read | `Request.body()` before JSON parse; response_model=WebhookAck on all 5 endpoints |
| `tessl__pytest-api-testing` | httpx ASGITransport pattern, fixture scoping | `test_app(monkeypatch)` fixture + `webhook_routes._seen_event_ids.clear()` reset |

## Scope

5 webhook endpoints in `vitalia/backend/src/modules/vitalia/api/webhook_routes.py`:
- `POST /api/v1/vitalia/webhooks/stripe`
- `POST /api/v1/vitalia/webhooks/mercadopago`
- `POST /api/v1/vitalia/webhooks/clerk`
- `POST /api/v1/vitalia/webhooks/whatsapp/inbound`
- `POST /api/v1/vitalia/webhooks/manychat/inbound`

Plus infrastructure adapters for Clerk (Svix) and ManyChat.

## Files Created/Modified

**New files:**
- `vitalia/backend/src/modules/vitalia/api/webhook_routes.py` — 5 webhook endpoints + WebhookAck DTO + inline HMAC helpers
- `vitalia/backend/src/modules/vitalia/infrastructure/adapters/__init__.py`
- `vitalia/backend/src/modules/vitalia/infrastructure/adapters/clerk_webhook_adapter.py` — Svix HMAC-SHA256 (whsec_ base64 secret)
- `vitalia/backend/src/modules/vitalia/infrastructure/adapters/manychat_webhook_adapter.py` — X-MC-Signature HMAC-SHA256
- `vitalia/backend/tests/integration/__init__.py`
- `vitalia/backend/tests/integration/test_stripe_webhook.py` — 7 tests (A1+A2 validators)
- `vitalia/backend/tests/integration/test_mercadopago_webhook.py` — 7 tests
- `vitalia/backend/tests/integration/test_clerk_webhook.py` — 7 tests

**Modified:**
- `vitalia/backend/src/main.py` — register webhook_router
- `vitalia/backend/tests/integration/conftest.py` — fix skip logic (get_closest_marker)

## Key Design Decisions

### 1. Inline Stripe HMAC (no adapter import)

`payment/__init__.py` imports `VitaliaMercadoPagoAdapter` → `luana_core_channels` → `langchain_core` (not installed in vitalia/.venv). Avoided by implementing `_verify_stripe_hmac()` as pure stdlib inline in webhook_routes.py. Same algorithm as `VitaliaStripeConnectAdapter.verify_webhook`.

### 2. Svix HMAC (Clerk)

Strips `whsec_` prefix, base64-decodes the secret bytes.  
Signed content: `"{svix-id}.{svix-timestamp}.{raw_body}"`.  
Supports multiple space-separated `v1,<b64>` signatures in header (Svix rotation).

### 3. MercadoPago dual-format

Accepts bare hex `<hex>` OR structured `ts=<ts>,v1=<hex>`.  
Structured format adds timestamp staleness check (>300s → 400).

### 4. Replay protection

In-memory `_seen_event_ids: set[str]` per process.  
Dedup keys: `stripe:<pi_id>`, `mercadopago:<mp_id>`, `clerk:<svix_id>`, `whatsapp:<msg_id>`, `manychat:<sub_id>:<msg_id>`.  
Replay → 200 `replay_skipped` (not 4xx — avoids gateway retry storms).  
HMAC failure → 400 (not 401 — avoids auth semantics leakage).

### 5. conftest.py fix

Original: `"integration" in item.keywords` — triggered for ALL tests in `tests/integration/` because pytest auto-assigns directory name as keyword.  
Fixed: `item.get_closest_marker("integration") is not None` — only explicit `@pytest.mark.integration` tests skipped.  
Webhook tests have NO `@pytest.mark.integration` (use ASGITransport, not Postgres).

## Validator Results

```
V-F-12: pytest tests/integration/test_stripe_webhook.py tests/integration/test_mercadopago_webhook.py tests/integration/test_clerk_webhook.py -v
21 passed in 0.30s — GREEN
```

A1 `test_hmac_verify_idempotent`: same payment_intent_id twice → second returns `replay_skipped` ✓  
A2 `test_replay_blocked`: replay attack (new valid sig, same pi_id) → `replay_skipped` ✓

## Commit

SHA: `d7b5fb9` — pushed to `origin/main` (`luana-platform` repo)
