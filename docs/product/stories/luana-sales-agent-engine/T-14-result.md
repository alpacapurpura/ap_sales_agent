# T-14 Result

**Status:** GREEN
**Commit (luana-platform):** `84c3377`
**Date:** 2026-05-12

## Summary

Lifted sales_agent observability/ verbatim from AISALESHT to luana-platform with mechanical sed (§1.4), EXCLUDING `observability/eval_simulator/` per Session 3 ratificación 2 (Luana v0.2.0 territory). 17 src files lifted. D-T6 anti-mirror cardinal verified across 4 evidence layers.

## Validators addressed

| Validator | Status | Evidence |
|---|---|---|
| V-NF-2 | ✅ | Zero `from src.*` / `import src.*` leaks in 17 src files |
| V-F-trace-cost | ✅ | SalesAgentCallbackHandler + SalesAgentObservabilityContext correctly subclass shared bases |
| V-F-pii | ✅ | `sanitize_payload` imports from `luana_core_observability.recording.sanitization` (shared) — verified via post-sed grep |

## D-T6 cardinal verifications (4 evidence layers)

1. **Source declaration** — `class SalesAgentCallbackHandler(BaseAgentCallbackHandler):` (line in callback_handler.py)
2. **Source declaration** — `class SalesAgentObservabilityContext(BaseObservabilityContext):` (line in turn_envelope.py)
3. **Anti-mirror sweep** — Zero declarations of FXResolver/CostCalculator/PricingResolver/BaseObservabilityContext/BaseAgentCallbackHandler in luana-core-sales-agent src/
4. **Runtime smoke** — `issubclass(SalesAgentCallbackHandler, BaseAgentCallbackHandler)` + `issubclass(SalesAgentObservabilityContext, BaseObservabilityContext)` both return True

## V-AG-5 preparation

- `test -d core/luana-core-sales-agent/src/luana_core_sales_agent/observability/eval_simulator` → False (NOT lifted)
- `tests/agentic_evals/` → NOT lifted (Luana v0.2.0)

## Tests

- ✅ 26 tests passed (callback handler inheritance, dual_write_reconciliation, domain_event_subscribers core)
- ⚠️ 10 failed = Story 4 luana-core-platform CRM `LeadModel.messages` FK references `MessageModel.lead_id` column that does not exist (inherited tech debt, same root cause as T-13 + T-12 payment_webhooks failures)

## Cardinal invariants honored

- ★ AISALESHT UNTOUCHED (V-NF-4)
- ★ eval_simulator NOT lifted (Luana v0.2.0 territory) — V-AG-5 prep
- ★ tests/agentic_evals NOT lifted (Luana v0.2.0 territory)
- ★ D-T6 anti-mirror cardinal verified across 4 evidence layers
- ★ D-T3 hexagonal cement preserved (zero PersonalityCompiler imports in observability)
- ★ Persistence subclass pattern preserved — sales-agent-scoped repos implement structural Protocols from luana-core-observability (Story 2 cement intact)
