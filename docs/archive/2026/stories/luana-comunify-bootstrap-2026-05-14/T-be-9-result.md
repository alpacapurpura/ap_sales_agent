# T-be-9 Result — Webhook Receivers (5 Sources)

**Story:** luana-comunify-bootstrap
**Ticket:** T-be-9
**State:** tests-passing
**Validator V-F-15:** PASS — 19/19 (stripe + mercadopago + clerk)
**All integration tests:** PASS — 30/30

---

## Delivered

5 webhook endpoints at `/api/v1/comunify/webhooks/`:

| Endpoint | HMAC | Idempotency key | Env var |
|---|---|---|---|
| `POST /stripe` | `Stripe-Signature: t=,v1=` | `evt_*` or `pi_*/sub_*` | `COMUNIFY_STRIPE_WEBHOOK_SECRET` |
| `POST /mercadopago` | `x-signature: <hex>` or `ts=,v1=` | `mp:<data.id>` | `COMUNIFY_MERCADOPAGO_WEBHOOK_SECRET` |
| `POST /clerk` | `svix-id/svix-timestamp/svix-signature` | `clerk:<svix-id>` | `COMUNIFY_CLERK_WEBHOOK_SECRET` |
| `POST /whatsapp/inbound` | `X-Hub-Signature-256: sha256=<hex>` | `wa:<message_id>` | `COMUNIFY_WHATSAPP_WEBHOOK_SECRET` |
| `POST /manychat/inbound` | `X-MC-Signature: <hex>` | `mc:<sub_id>:<msg_id>` | `COMUNIFY_MANYCHAT_WEBHOOK_SECRET` |

## Files (new)

- `src/modules/comunify/infrastructure/adapters/__init__.py`
- `src/modules/comunify/infrastructure/adapters/clerk_webhook_adapter.py`
- `src/modules/comunify/infrastructure/adapters/manychat_webhook_adapter.py`
- `src/modules/comunify/api/webhook_routes.py`
- `tests/integration/test_stripe_webhook.py` (7 tests)
- `tests/integration/test_mercadopago_webhook.py` (6 tests)
- `tests/integration/test_clerk_webhook.py` (6 tests)
- `tests/integration/test_whatsapp_webhook.py` (6 tests)
- `tests/integration/test_manychat_webhook.py` (5 tests)

## Files (modified)

- `src/main.py` — mounted `webhook_router`

## Contract

- HMAC failure → 400
- Replay → 200 `{"status": "replay_skipped"}`
- Success → 200 `{"status": "received"}`
- `response_model=WebhookAck` mandatory on all 5 endpoints
- `redirect_slashes=False` on `FastAPI` app (arch test enforces)

## Impl-log

`/home/chris/AISALESHT/docs/product/stories/luana-comunify-bootstrap/T-be-9-impl-log.md`
