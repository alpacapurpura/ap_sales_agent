# T-guards-1 — community_safety_no_spam (input+output Haiku classifier)

**Ticket**: T-guards-1 — Guardrail community_safety_no_spam.
**R23**: AGENTIC production_code=true → Opus 4.7 EXCLUSIVE.
**Estimate vs actual**: 3h estimate / ~50min actual (batched with sibling guards).

## Skills Consulted

- **copilot-expert**: best-effort observability invariant (try/except + structlog.warning + audit_log NEVER breaks decision). Tenant isolation cardinal applied — every `_emit_audit_log` carries `tenant_id`. Sanitize_payload deferred to `ComplianceEventService.log_event` consumer (single source of truth; double-sanitize avoided).
- **sales-agent-expert**: anti-duplication cardinal §0 — grep verified ZERO existing `class CommunitySafetyNoSpam` / `community_safety_no_spam` outside EP-13 placeholder; NEW vertical-creator-economy surface; no mirror risk.
- **tessl__langgraph**: N/A — guardrails are pre/post-LLM middleware, not graph nodes.
- **tessl__graceful-degradation**: Rule 1 — `_CLASSIFIER_TIMEOUT_SEC = 5.0` hard timeout on Haiku classifier. Rule 2 — outage degrades to pass-through (`_consult_classifier_input` returns None on raise; caller treats None as "no information"). Audit_log raising NEVER breaks block decision (`_emit_audit_log` try/except + structlog).
- **tessl__pytest-api-testing**: function-scoped fixtures (audit_log / classifier_negative / classifier_positive / classifier_failing); `@pytest.mark.parametrize` for 9 spam vectors + 6 benign queries; in-memory `_FakeLLMClassifier` + `_FakeAuditLog` with `raise_on_call` / `raise_on_log` toggles for outage testing.

## Step 0 GATE — Anti-duplication audit (verified 2026-05-14)

```bash
grep -rln "class CommunitySafetyNoSpam\|community_safety_no_spam" \
  /home/chris/luana-platform/comunify/backend/src /home/chris/luana-platform/core
```

Returns ONLY:
- `extensions.py` EP-13 placeholder registration (T-extensions-1, CC-2 cement says T-guards-* replace via direct edit)
- `community_moderation_service.py` classifier dispatch stub (T-be-6, ContentClassifierProtocol)

No mirror risk. NEW vertical-creator-economy guard surface. `_LLMClassifierLike` Protocol is structural typing — concrete impl wires LiteLLM Proxy adapter at sales_agent runtime (Story 13+).

## Step 0.5 — Default flip detection

N/A. No `core/config.py` flag flips in this ticket.

## Files created

1. `/home/chris/luana-platform/comunify/backend/src/modules/comunify/agentic/guardrails/community_safety_no_spam.py` (~410 lines source)
2. `/home/chris/luana-platform/comunify/backend/tests/agentic_evals/guardrails/test_community_safety_no_spam.py` (~290 lines, 27 test cases)

Also: `__init__.py` package marker + `guardrails/__init__.py` consolidator (re-exports per anti-duplication.md sibling convention from vitalia).

## Implementation summary

- **INPUT layer** (`community_safety_no_spam_input_check`): cheap regex first (3 patterns: promo+TLD, click-bait+URL, affiliate/MLM/crypto/casino) → cost-guard skip classifier on regex hit. Regex miss → Haiku score classifier > 0.85 fires → action='pending_moderation'.
- **OUTPUT layer** (`community_safety_no_spam_output_check`): anti-pivot defense — same INPUT regex catalog applied to LLM response. Block + retry hint (`regenerate_with_no_spam_instruction`) on first failure; `use_fallback_response` after retry_attempted=True (cement Spanish-neutro `FALLBACK_RESPONSE`).
- **Audit log**: severity medium, event_type `community_safety_no_spam_fired`, includes layer (input/output) + detection_source (regex/classifier) + classifier_score when applicable.
- **Graceful degradation**: classifier timeout → pass-through (V-AE-11 adversarial pass^5 ≥0.95 cement catches paraphrased spam end-to-end).

## Validators

- **V-AE-2** (10 spam vectors — 8+ caught high-precision): 9 spam vectors all caught at regex layer + 6 benign community queries pass clean. Total: 15 parametrize cases at regex layer + 8 async end-to-end cases. All GREEN.
- **V-AE-11** (audit_log fires + chain order enforced): verified by 4 audit_log assertions across input fire + output fire + cross-tenant isolation + payload schema. Severity=medium cement asserted.

## Quality gates run

```
cd /home/chris/luana-platform/comunify/backend
.venv/bin/pytest tests/agentic_evals/guardrails/test_community_safety_no_spam.py -v
27/27 PASS

.venv/bin/ruff check src/modules/comunify/agentic/guardrails/community_safety_no_spam.py \
                    tests/agentic_evals/guardrails/test_community_safety_no_spam.py
All checks passed

.venv/bin/ruff format --check ...
Already formatted
```

## Deferred / gaps

- Real Haiku 4.5 classifier wiring (sales_agent runtime LiteLLM Proxy adapter): Story 13+.
- EP-13 extensions.py wiring (replace `_block_handler_placeholder` with real `community_safety_no_spam_input_check` adapter): deferred to wiring story (BrandContext bridging + sales_agent orchestrator integration).
- V-AE-11 end-to-end chain order enforcement (input pipeline 1→2→3→4→5→6 sequencing): cross-ticket — verified at orchestrator integration tests (Story 13+).
