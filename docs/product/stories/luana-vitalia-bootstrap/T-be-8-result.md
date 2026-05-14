# T-be-8 Result — BE Webhook Receivers

**Ticket:** T-be-8  
**Status:** GREEN  
**Commit:** d7b5fb9 (luana-platform main)  
**Date:** 2026-05-14  

## Validator V-F-12

```
pytest tests/integration/test_stripe_webhook.py \
       tests/integration/test_mercadopago_webhook.py \
       tests/integration/test_clerk_webhook.py -v
21 passed in 0.30s
```

## Acceptance Criteria

- A1 `test_hmac_verify_idempotent`: PASS — same `payment_intent_id` twice → second call `status=replay_skipped`
- A2 `test_replay_blocked`: PASS — replay attack with re-signed payload blocked via `payment_intent_id` dedup

## Deliverables

| File | Description |
|---|---|
| `vitalia/backend/src/modules/vitalia/api/webhook_routes.py` | 5 endpoints + WebhookAck DTO + HMAC helpers |
| `vitalia/backend/src/modules/vitalia/infrastructure/adapters/clerk_webhook_adapter.py` | Svix HMAC-SHA256 adapter |
| `vitalia/backend/src/modules/vitalia/infrastructure/adapters/manychat_webhook_adapter.py` | ManyChat HMAC adapter |
| `vitalia/backend/tests/integration/test_stripe_webhook.py` | 7 tests |
| `vitalia/backend/tests/integration/test_mercadopago_webhook.py` | 7 tests |
| `vitalia/backend/tests/integration/test_clerk_webhook.py` | 7 tests |
| `vitalia/backend/src/main.py` | webhook_router registered |
| `vitalia/backend/tests/integration/conftest.py` | get_closest_marker fix |
