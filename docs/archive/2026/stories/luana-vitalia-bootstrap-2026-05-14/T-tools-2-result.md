# T-tools-2 — Result

**Ticket:** Tool `medical_consent_request` (consent capture + URL HMAC sign + channel dispatch + audit log)
**State:** developing → developed
**R23:** production_code=true AGENTIC tool, Opus 4.7 (Sonnet ban absolute) — honored
**Builder:** Claude Opus 4.7 (1M context)
**Date:** 2026-05-14
**Sesion:** /pm Sesion 4 W7

---

## Summary

Implemented vertical-medical AGENTIC tool `medical_consent_request` per 02-design § 6.3 + 03-arch-agentic § 4.3. Tool validates `offer.requires_informed_consent=true` (A2 gate), delegates consent_record persistence + HMAC-signed URL generation to T-be-6 ConsentService (which provides D2 idempotency for A3), appends audit_log consent_requested event with PII-sanitized payload (A1), and dispatches WhatsApp + email channels asynchronously (fire-and-forget, per-dependency error isolation per `tessl__graceful-degradation` Rule 5).

Single iteration to GREEN: 13/13 tests pass + lint clean + format clean. No iteration cap concern (cap was 3, used 1). NO halt triggers fired. NO downstream regression (121 tests still GREEN across `tests/agentic_evals/tools/`, `tests/unit/repositories/`, `tests/unit/application/`).

## Files created

| Path | Purpose | Lines |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/agentic/tools/medical_consent_request.py` | Pydantic schemas + async handler + 4 helper functions + 4 dependency Protocols | 396 |
| `vitalia/backend/tests/agentic_evals/tools/test_medical_consent_request.py` | 13 unit tests (TDD RED → GREEN) | 521 |

## Acceptance verification

| ID | Description | Test | Result |
|---|---|---|---|
| A1 | Tool persists consent_record + audit_log consent_requested | `test_persists_audit_logs` | ✅ PASS — verifies ConsentService.request_consent invoked + MedicalAuditLogModel saved with event_type="consent_requested" + sanitized payload (consent_template_slug + delivery_channel + consent_id + is_new) |
| A2 | Tool returns error if offer.requires_informed_consent=false | `test_offer_validation_returns_error_when_not_required` | ✅ PASS — status="offer_does_not_require_consent" + error_code populated + NO consent_record persisted + NO channel dispatched |
| A3 | Idempotency 1h window same (booking_id, slug) returns existing consent_id | `test_idempotency_returns_existing_consent_id` | ✅ PASS — same consent_id returned twice + only 1 record materialized in fake store + 2nd audit event flagged is_new=False |

Plus 10 defensive tests (security boundary + observability + best-effort + PII + URL format + 24h expiry).

## Validators

| ID | Description | Status |
|---|---|---|
| V-AE-5 | 4 tools tests — happy/edge/error per tool (02-design § 6) | ✅ GREEN — 13/13 PASS for medical_consent_request, 10/10 still GREEN for prepaid_payment_check (T-tools-1) — total 23 tests in `tests/agentic_evals/tools/` |
| V-AE-18 | copilot_trace_event records present + cost_usd > 0 + tokens accounted + PII sanitized | N/A for this tool — tool is $0 LLM (deterministic). PII sanitization assertion covered locally via `test_no_patient_pii_in_trace_payload`. Full V-AE-18 wiring (real Postgres + cost assertion for tools that DO call LLMs) deferred to future observability integration ticket. |
| V-NF-1 (lint) | Ruff check on tool + test files | ✅ GREEN — `All checks passed!` |
| V-NF-2 (format) | Ruff format --check on tool + test files | ✅ GREEN — `2 files already formatted` |

## Patterns honored (R23 + 05-guidelines.md § 1.10)

- ✅ `try/except + structlog.warning` on ALL observability writes (audit_log, trace_event, channel dispatch)
- ✅ `sanitize_payload(...)` BEFORE persist (defense-in-depth, even on safe identifiers)
- ✅ `tenant_id` kwarg-only, NEVER in input schema (test enforces via Pydantic introspection)
- ✅ Idempotency natural via ConsentService.request_consent D2 (no Redis needed, no duplication)
- ✅ Async throughout
- ✅ Pydantic v2 ConfigDict (frozen + extra="forbid")
- ✅ Structural Protocols for all 4 deps (testable in isolation)
- ✅ Fire-and-forget channel dispatch — per-dependency error isolation
- ✅ Structlog (no `print()` / `logging.*`)
- ✅ NO mirror — `sanitize_payload`, `BaseTraceEventRepoProtocol`, ConsentService HMAC SSoT all consumed from canonical paths
- ✅ NO HMAC duplication — delegated to ConsentService.build_consent_url
- ✅ NO offer model assumption — accepts callable injected by caller (forward-compatible)

## Decisions honored

- **D1** Vitalia subdir at `luana-platform/vitalia/`
- **D7** HIPAA-lite — 24h default URL expiry + medical_audit_log immutable + payload PII sanitized

## Halt triggers — none fired

- ✅ H4 spec drift: tool surface honors 02-design § 6.3 verbatim
- ✅ H5 tenant isolation: kwarg-only, NEVER from input
- ✅ H6 PII leak: sanitize_payload defense-in-depth, forbidden keys absent (test verifies)
- ✅ H10 anti-duplication: zero mirrors

## Tech debt / follow-ups (out-of-scope this ticket)

1. **extensions.py wiring** — placeholder `_not_implemented_yet("EP-3 vitalia.medical_consent_request", "T-tools-2")` in extensions.py (line 260) intentionally LEFT UNTOUCHED. Real wiring requires sales_agent tool dispatcher to construct tenant-scoped deps — separate ticket (T-extensions-2 / future).
2. **Real channel adapters** — currently consumed via callable Protocol. WhatsApp + email implementations land in future payment integration ticket.
3. **OfferRepository wiring** — currently `offer_requires_consent` is callable injected by caller. When OfferRepository materializes, wire via `lambda offer_id: offer_repo.get_by_id(offer_id).requires_informed_consent`. Tool surface stable.
4. **V-AE-18 full integration** — real Postgres + cost-bucket assertion deferred. PII assertion covered locally.
5. **Audit log 7-year retention** — separate purge job ticket (out-of-scope).

## Commit

```
feat(story-11/T-tools-2): vitalia medical_consent_request AGENTIC tool (R23 Opus)
```

Files staged at `/home/chris/luana-platform/`:
- `vitalia/backend/src/modules/vitalia/agentic/tools/medical_consent_request.py`
- `vitalia/backend/tests/agentic_evals/tools/test_medical_consent_request.py`

Branch: `main`. Pushed to `origin/main`.

---

**Verdict:** done. T-tools-2 complete in single iteration. Ready for /auditor (Sesion 5).

`done -> docs/product/stories/luana-vitalia-bootstrap/T-tools-2-result.md`
