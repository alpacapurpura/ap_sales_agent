---
ticket_id: T-payment-1
story_id: luana-vitalia-bootstrap
state: developed
verdict_builder: PASS
verdict_auditor: pending
production_code: true
decisions_applicable: [D4]
completed_at: 2026-05-14T02:54:03Z
iter_count: 1
files_count: 9
loc_added: ~1110
tests_added: 38
tests_passed: 38
---

# T-payment-1 result — MercadoPago adapter LIFT SHARED to @luana/core/channels + vitalia EXTEND

## TL;DR

`MercadoPagoAdapter` lifted to **NEW** `core/luana-core-channels/payment/` (subdir didn't exist — D4 LIFT branch). `VitaliaMercadoPagoAdapter` EXTENDS via subclass + `_extra_metadata` override only (compliance_level=hipaa_lite + brand_slug=vitalia + contains_phi=False). 38/38 tests PASS. Zero nicolify modifications. Zero `luana-core-sales-agent` modifications (sales-agent's MP closer-tool unchanged — different concern).

## Files in scope

| Path | Status | LOC |
|---|---|---|
| `core/luana-core-channels/src/luana_core_channels/payment/__init__.py` | NEW | 32 |
| `core/luana-core-channels/src/luana_core_channels/payment/mercadopago_adapter.py` | NEW | 305 |
| `core/luana-core-channels/tests/payment/__init__.py` | NEW | 0 |
| `core/luana-core-channels/tests/payment/test_mercadopago_adapter.py` | NEW | 472 |
| `vitalia/backend/src/modules/vitalia/payment/__init__.py` | NEW | 12 |
| `vitalia/backend/src/modules/vitalia/payment/mercadopago_adapter.py` | NEW | 50 |
| `vitalia/backend/tests/architecture/test_vitalia_payment_inherits_core_base.py` | NEW | 89 |
| `vitalia/backend/tests/unit/payment/__init__.py` | NEW | 0 |
| `vitalia/backend/tests/unit/payment/test_mercadopago_adapter.py` | NEW | 153 |
| `vitalia/backend/conftest.py` | EDIT (+1 line) | n/a |

**Total:** 9 NEW files + 1 EDIT (append-only sys.path tuple) = ~1110 LOC + 38 new tests.

## Test summary

| Suite | Tests | Result |
|---|---|---|
| `core/luana-core-channels/tests/payment/test_mercadopago_adapter.py` | 27 | 27/27 PASS |
| `core/luana-core-channels/tests/` (full regression) | 100 | 100/100 PASS (no pre-existing regression) |
| `vitalia/backend/tests/architecture/test_vitalia_payment_inherits_core_base.py` | 8 | 8/8 PASS |
| `vitalia/backend/tests/unit/payment/test_mercadopago_adapter.py` | 3 | 3/3 PASS |
| **TOTAL NEW** | **38** | **38/38 PASS** |

Coverage breakdown (27 core tests):
- 9 `create_preference` happy/edge cases (init_point return, idempotency header, auth bearer, cents→major-units, 7 LATAM currencies, external_reference, back_urls + auto_return, payer optional, http error propagation)
- 8 `verify_payment` parametrized status mappings (approved/pending/in_process/rejected/cancelled/refunded/charged_back/unknown)
- 2 override hooks (`_extra_metadata` + `_status_overrides`)
- 5 HMAC webhook signature paths (valid, tampered, missing-secret, malformed, no-request-id)
- 3 environment/defaults (timeout default 10s, env fallback, provider_id stable)

Coverage breakdown (8 arch tests):
- `issubclass` check
- 3 no-override checks (`create_preference`, `verify_payment`, `verify_webhook_signature`)
- 1 has-override check (`_extra_metadata`)
- 1 hipaa_lite metadata content assertion
- 1 no-httpx-in-vertical sourcecode scan
- 1 constants exposure check

## Decisions honored

- **D4** (03-arch.md § 11, 2026-05-13) — MercadoPago adapter LIFT SHARED to `@luana/core/channels/payment/` since subdir didn't exist. Vitalia EXTENDS with `compliance_level=hipaa_lite` per Q6=B.

## R3 downstream regression — SSoT row to append

(handled by orchestrator / `/dev-team` post-spawn — append to `.claude/rules/auditor-downstream-regression.md`):

```markdown
| `core/luana-core-channels/src/luana_core_channels/payment/mercadopago_adapter.py` | `core/luana-core-channels/tests/payment/test_mercadopago_adapter.py` (27)<br>`vitalia/backend/tests/architecture/test_vitalia_payment_inherits_core_base.py` (8)<br>`vitalia/backend/tests/unit/payment/test_mercadopago_adapter.py` (3) | Story 11 D4 lift — MercadoPagoAdapter for booking-deposit (HMAC + idempotency_key=booking_id + compliance metadata). Verticals subclass via `_extra_metadata`. Distinct from sales-agent CLOSER tool. |
```

## Anti-duplication audit

`grep -rln "class.*MercadoPago" /home/chris/luana-platform/core/` returned 2 hits in `luana-core-sales-agent` BEFORE write. Diagnosis: those are sales-agent CLOSER tools (chat-flow checkout link, sig `create_payment_link(tenant_id, lead_id, offer_id, amount, currency, metadata)`) — DIFFERENT concern from booking-deposit channel adapter (sig `create_preference(items, payer, back_urls)` per arch-be § 11.2). Coexist intentionally. Future Comunify+Lupulo verticals EXTEND `luana-core-channels/payment/MercadoPagoAdapter`; sales-agent closer flow keeps its own provider unchanged.

## Acceptance verification

- **A1 (anti-duplication grep verified):** ✓ — § 1 of impl-log captures grep output verbatim. Commit body cites § 1 + diagnosis.
- **A2 (vitalia EXTENDS core base):** ✓ — `test_vitalia_payment_inherits_core_base.py` 8/8 PASS — verifies `issubclass` + no-override of `create_preference`/`verify_payment`/`verify_webhook_signature` (security-critical) + only `_extra_metadata` override.
- **A3 (nicolify downstream still GREEN):** ✓ (non-blocking) — Pre-existing nicolify env-level breakage UNRELATED to T-payment-1; we did NOT modify nicolify (zero file touched) NOR `luana-core-sales-agent/.../tools/payment/providers.py`. Our new package is greenfield with no existing consumer.

## Halt triggers

None fired (H1-H13 all clean).

## Builder verdict

`PASS` (tests-passing state per R30). Auditor-agentic + gate-runner spawn handled by orchestrator post-spawn — independent verdict pending.

---

`done -> docs/product/stories/luana-vitalia-bootstrap/T-payment-1-result.md`
