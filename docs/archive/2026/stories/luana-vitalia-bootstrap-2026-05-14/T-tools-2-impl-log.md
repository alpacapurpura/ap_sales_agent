# T-tools-2 — Implementation Log

**Ticket:** Tool `medical_consent_request` — informed consent capture + HMAC-signed URL + audit log + WhatsApp/email channel dispatch.
**State:** developing → developed
**R23:** production_code=true AGENTIC tool, Opus 4.7 (Sonnet ban absolute).
**Builder:** Claude Opus 4.7 (1M context)
**Date:** 2026-05-14
**Sesion:** /pm Sesion 4 W7 (T-tools-2 batch)

---

## Skills Consulted (Step 0 GATE)

| Skill | Why invoked | Decision |
|---|---|---|
| `copilot-expert` | Touching AGENTIC tool surface; observability + tenant isolation patterns + best-effort writes required | Consume `sanitize_payload` from `luana_core_observability` shared lib (anti-duplication §0). Wrap audit_log + trace_event writes in try/except + structlog warning (R23 best-effort). Channel dispatch fire-and-forget via `loop.create_task` — failures swallowed with warning, NEVER break tool turn. Idempotency natural via ConsentService D2 (no duplicate row on re-invoke). |
| `sales-agent-expert` | Tool dispatched by sales_agent runtime — must respect tenant isolation cardinal + voice-neutral output (HMAC URL is data, not user-facing copy) | `tenant_id` MUST NEVER appear in tool input schema (§ 3 cardinal). All deps (consent_service, audit_log_repo, channel_dispatcher) bound to tenant via construction. ConsentService consumed via callable Protocol (NEVER raw HMAC duplication — HMAC SSoT lives in T-be-6 ConsentService). |
| `tessl__langgraph` | Tool will be consumed as LangChain tool from a LangGraph node (future T-extensions wiring) | Tool is async; returns Pydantic schema; idempotent natural (D2 via ConsentService). Errors expressed via typed `status` literal + `error_code` field — NOT exceptions. Aligns with LangGraph's `bind_tools()` + structured-output expectations + safe error handling. |
| `tessl__graceful-degradation` | Tool has 3 external write surfaces (consent_service, audit_log_repo, channel_dispatcher) + optional trace_event_repo | Audit log + trace emission wrapped in try/except (Rule 2: every external call needs fallback). Channel dispatch fire-and-forget via background task (Rule 5: per-dependency error isolation — one channel failing does NOT block the other). NO retry needed (caller's responsibility for downstream retry policy). |
| `tessl__pytest-api-testing` | 13 unit tests with async fixtures + capturing fakes + raising fakes + Pydantic schema introspection | Fakes mirror `_FakeConsentService` (D2 idempotency in-memory) + `_CapturingAuditRepo` + `_CapturingChannelDispatcher` + `_RaisingChannelDispatcher` (failure mode). Asyncio_mode=AUTO honored. `await asyncio.sleep(0.05)` used to settle background dispatch tasks before assertions. |

## Step 0 — Anti-duplication GATE (mandatory per anti-duplication.md §0)

Executed grep audit BEFORE writing implementation:

```bash
# 1. Existing medical_consent_request tool / class / module
find /home/chris/luana-platform -name "medical_consent_request.py" -o -name "consent_request_tool*"
# → Empty (no matches outside __pycache__/.venv)

grep -rln "medical_consent_request\|MedicalConsentRequest\|consent_request_tool" \
  /home/chris/luana-platform/vitalia/backend/src/ /home/chris/AISALESHT/backend/src/
# → Empty (no source matches)

# 2. ConsentService surface (T-be-6 — already done W3)
ls /home/chris/luana-platform/vitalia/backend/src/modules/vitalia/application/services/consent_service.py
# → exists. ConsentService.request_consent has D2 idempotency built-in
#   (returns existing pending consent for same booking_id+slug). HMAC URL
#   signing via build_consent_url() — SSoT for HMAC token contract.
#   CONSUME via callable Protocol (_ConsentServiceLike) — no mirror.

# 3. MedicalAuditLogRepository surface (T-be-3)
ls /home/chris/luana-platform/vitalia/backend/src/modules/vitalia/infrastructure/repositories/medical_audit_log_repository.py
# → exists. Append-only (no update/delete) — perfect for consent_requested
#   audit event. CONSUME via callable Protocol — no mirror.

# 4. sanitize_payload location
grep -n "def sanitize_payload" /home/chris/luana-platform/core/luana-core-observability/src/
# → CANONICAL: luana_core_observability.recording.sanitization::sanitize_payload
#   CONSUME via `from luana_core_observability.recording.sanitization import sanitize_payload`

# 5. BaseTraceEventRepoProtocol
grep -n "class BaseTraceEventRepoProtocol" /home/chris/luana-platform/core/luana-core-observability/src/
# → CANONICAL: luana_core_observability.persistence.base_trace_event_repo (Protocol)
#   Tool accepts ANY repo implementing this protocol via _TraceEventRepoLike

# 6. Idempotency layer (potential lift candidate)
find /home/chris/luana-platform -path "*shared/idempotency*" -name "*.py"
# → Lives ONLY in nicolify/backend/src/shared/idempotency (Story 10 cement).
#   NOT yet in vitalia/luana-platform/core. For T-tools-2, idempotency
#   NATURALLY lives in ConsentService.request_consent (D2 — DB row check
#   via get_pending_by_booking). NO need for shared/idempotency here.
#   Future ticket may lift shared/idempotency to luana-core if cross-brand
#   tool needs Redis-backed idempotency keys (current scope: DB row check OK).

# 7. Channel dispatcher surface (potential lift candidate)
grep -rn "class.*ChannelDispatcher\|class.*ChannelAdapter" /home/chris/luana-platform/core/
# → ChannelAdapterDef DataClass exists in luana_core_extension_sdk.models, BUT
#   actual adapter implementations are PLACEHOLDERS in vitalia/extensions.py
#   (registered with _not_implemented_yet handlers — see T-extensions-1 result).
#   For T-tools-2, channel_dispatcher consumed via callable Protocol
#   (_ChannelDispatcherLike) — caller wires real adapter when payment integration
#   ticket lands. Vertical-medical specific (no equivalent in @luana/core/channels yet).
```

**Audit result:** NO mirror risk. All shared abstractions consumed from canonical paths. No duplicate HMAC, no duplicate sanitization, no duplicate audit log persistence.

NEW tool (no existing equivalent): vertical-medical specific — couples consent capture + offer.requires_informed_consent validation + HIPAA-lite 24h URL expiry. Per 02-design § 6.3: "NEW vertical-medical. No equivalent en @luana/core (consent capture is medical-vertical concern)."

## Implementation

### Files created

| Path | Purpose |
|---|---|
| `/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/agentic/tools/medical_consent_request.py` | Pydantic schemas (input/output) + async handler + 4 helper functions + 4 dependency Protocols |
| `/home/chris/luana-platform/vitalia/backend/tests/agentic_evals/tools/test_medical_consent_request.py` | 13 unit tests (TDD RED → GREEN) — A1/A2/A3 + 10 defensive |

### Files NOT modified (M8 — extend, no destroy)

- `/home/chris/luana-platform/vitalia/backend/conftest.py` — no changes (workspace paths already cover `luana_core_observability` from T-tools-1 W5 extension)
- `/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/extensions.py` — placeholder registration `_not_implemented_yet("EP-3 vitalia.medical_consent_request", "T-tools-2")` LEFT UNTOUCHED. Wiring this tool's handler into the registry is a separate ticket (T-extensions-2 / sales_agent dispatcher composition ticket — same pattern as T-tools-1 follow-up). Tool itself is complete + tested.

## Tool design decisions

### 1. Handler signature — keyword-only deps (no global registry)

```python
async def medical_consent_request(
    input: MedicalConsentRequestInput,
    *,
    tenant_id: uuid.UUID,                   # injected from ctx (R12 tenant-isolation)
    offer_id: uuid.UUID,                    # for A2 validation gate
    offer_requires_consent: Callable,       # sync OR async — caller wires offer service
    consent_service: _ConsentServiceLike,   # T-be-6 (HMAC + D2 idempotency)
    audit_log_repo: _AuditLogRepoLike,      # T-be-3
    channel_dispatcher: _ChannelDispatcherLike,
    base_url: str,                          # https://vitalia.app
    trace_event_repo: _TraceEventRepoLike | None = None,
    turn_id: uuid.UUID | None = None,
    span_id: uuid.UUID | None = None,
) -> MedicalConsentRequestOutput:
```

**Rationale:**
- `tenant_id` keyword-only enforces "NEVER from input" boundary (R12 tenant-isolation cardinal).
- All deps via structural Protocol — testable in isolation (no SQLAlchemy / Postgres dep).
- `offer_requires_consent` callable accepts both sync + async (resolved via `asyncio.iscoroutine`) — flexible for caller.
- `trace_event_repo` optional — eval/dev paths can skip observability wiring.

### 2. Output uniformity — typed status literal, NO exceptions

Per 02-design § 6.3 + agentic best practice: validation failures surface via typed `status` field + `error_code`, NOT exceptions. LLM consumer parses `status` enum and routes accordingly. Three states:
- `pending_signature` — happy path, consent persisted + URL signed + dispatched
- `delivery_failed` — reserved for future synchronous dispatch failures (channel adapters that wait for ack)
- `offer_does_not_require_consent` — A2 validation gate (offer.requires_informed_consent=false)

DB exceptions / repo failures bubble up — caller (LangGraph node) decides retry policy. Tool itself does NOT swallow downstream failures (consent_service exceptions surface; audit_log + dispatch + trace are best-effort).

### 3. Idempotency — delegated to ConsentService.request_consent (T-be-6 D2)

Per 02-design § 6.3 idempotency contract: "(booking_id OR patient_id, consent_template_slug, sales_agent_turn_id) within 1h window returns existing consent_id (no duplicate delivery)".

T-be-6 ConsentService.request_consent already implements D2 idempotency via `get_pending_by_booking(booking_id)` + slug match. This tool DELEGATES rather than re-implementing. Re-invoking with same `(booking_id, consent_template_slug)` returns the SAME `consent_id` + `is_new=False` flag in the underlying ConsentUrlResult.

Audit log records BOTH invocations (each is a sales_agent intent record), but second event's payload `is_new=False` distinguishes idempotent reuse from initial creation. Test `test_idempotency_returns_existing_consent_id` confirms exactly 1 row in `_FakeConsentService._records` after 2 invocations.

**Why not Redis-backed idempotency?** ConsentService's DB-row idempotency satisfies the 1h window requirement (consent records have `expires_at` 24h, but pending_signature status acts as the live key). For natural reuse within 1h, the most-recent pending consent is found via `get_pending_by_booking` — no Redis SETNX needed. If future scenarios require turn-id-grained dedup (within-same-turn double-fire), shared/idempotency lift candidate (parked).

### 4. Pre-booking phase — booking_id may be None

Per 02-design § 6.3 input spec: "booking_id: UUID | None — may be null pre-booking (intent phase)". When `booking_id is None`, ConsentService.request_consent receives `patient_id` as the booking_id key (defensive defaulting in tool wrapper). This preserves D2 idempotency on the patient-level for pre-booking intent flows. Documented inline in handler.

### 5. Fire-and-forget channel dispatch (per-dependency error isolation)

Per `tessl__graceful-degradation` Rule 5: each dependency failure isolated. Channel dispatch invoked once per channel (whatsapp / email / both) via `loop.create_task(_safe_dispatch())` background task. `_safe_dispatch` wraps the actual dispatch in try/except — failures logged + swallowed.

**Why background task?** Synchronous in-line dispatch would block the agentic turn for ~200-500ms per channel. Tool returns `pending_signature` status immediately after consent persist — channel delivery happens asynchronously. If delivery fails, the consent_record still exists; caller can re-dispatch via separate cron retry job (out-of-scope T-tools-2).

Test `test_dispatch_failure_does_not_break_turn` uses `_RaisingChannelDispatcher` — confirms tool still returns `status='pending_signature'` even when both whatsapp + email dispatchers raise.

### 6. PII sanitization — defense in depth

Per `.tessl/RULES.md` PII + `.claude/rules/copilot-observability.md`:
- Audit log payload sanitized via `sanitize_payload` BEFORE persist (line 287) — even though `consent_id`, `consent_template_slug`, `delivery_channel`, `is_new` are intrinsically safe identifiers, defense-in-depth + 4kb truncation.
- Trace event payload sanitized BEFORE persist (line 348) — same rationale.
- Patient name / phone / email / signature evidence NEVER passed to either audit or trace payload. Test `test_no_patient_pii_in_trace_payload` asserts forbidden keys (`patient_name`, `patient_phone`, `patient_email`, `signed_name`) absent from trace data.
- Patient signature evidence (signed_name, signed_ip, signed_user_agent, signed_at) is captured by ConsentService.sign_consent (T-be-6) — NOT this tool's surface (this tool is REQUEST, not SIGN).

### 7. HMAC URL — SSoT in ConsentService (no duplication)

Per anti-duplication §0: HMAC token generation lives in `ConsentService.build_consent_url` + `_sign` (T-be-6 cement). Tool consumes `consent_url` from `ConsentUrlResult.consent_url` — never re-signs, never extracts secret. Tests verify URL contains `consent_id=...&token=...` query params (test_signed_url_contains_consent_id_and_token).

### 8. 24h default expiry (D7 HIPAA-lite)

Per spec § 14 + 02-design § 6.3: `_DEFAULT_EXPIRY_HOURS = 24`. ConsentService.RequestConsentRequest accepts `expiry_hours` field (default 24, range 1-720). Tool always passes 24 — caller can override via future input field if business requires. Test `test_expiry_24h_default_per_d7_hipaa_lite` asserts `expires_at` ≈ `now + 24h`.

## Iteration log

| Iter | RED tests | GREEN tests | Lint | Format | Notes |
|---|---|---|---|---|---|
| 1 (RED) | 1/13 fail (ModuleNotFoundError) | n/a | n/a | n/a | TDD RED phase — confirmed test scaffolding correct, module missing |
| 1 (GREEN) | n/a | **13/13 GREEN** | clean (`All checks passed!`) | clean (`2 files already formatted`) | First-pass implementation passed all tests + lint + format on iter 1. No re-iteration needed. |

Final result:

```
tests/agentic_evals/tools/test_medical_consent_request.py::test_tenant_id_not_in_schema PASSED [  7%]
tests/agentic_evals/tools/test_medical_consent_request.py::test_persists_audit_logs PASSED [ 15%]
tests/agentic_evals/tools/test_medical_consent_request.py::test_offer_validation_returns_error_when_not_required PASSED [ 23%]
tests/agentic_evals/tools/test_medical_consent_request.py::test_idempotency_returns_existing_consent_id PASSED [ 30%]
tests/agentic_evals/tools/test_medical_consent_request.py::test_dispatches_channels_for_both PASSED [ 38%]
tests/agentic_evals/tools/test_medical_consent_request.py::test_dispatches_channel_whatsapp_only PASSED [ 46%]
tests/agentic_evals/tools/test_medical_consent_request.py::test_dispatch_failure_does_not_break_turn PASSED [ 53%]
tests/agentic_evals/tools/test_medical_consent_request.py::test_trace_event_recorded_when_repo_supplied PASSED [ 61%]
tests/agentic_evals/tools/test_medical_consent_request.py::test_trace_event_failure_does_not_break_turn PASSED [ 69%]
tests/agentic_evals/tools/test_medical_consent_request.py::test_audit_log_failure_does_not_break_turn PASSED [ 76%]
tests/agentic_evals/tools/test_medical_consent_request.py::test_no_patient_pii_in_trace_payload PASSED [ 84%]
tests/agentic_evals/tools/test_medical_consent_request.py::test_signed_url_contains_consent_id_and_token PASSED [ 92%]
tests/agentic_evals/tools/test_medical_consent_request.py::test_expiry_24h_default_per_d7_hipaa_lite PASSED [100%]

============================== 13 passed in 0.45s ==============================
```

## Acceptance coverage (per 06-tickets.yaml T-tools-2)

| Acceptance | Test | Result |
|---|---|---|
| A1 — persists_audit_logs (consent_record + audit_log consent_requested) | `test_persists_audit_logs` | PASS — verifies ConsentService.request_consent invoked + MedicalAuditLogModel saved with event_type=consent_requested + sanitized payload |
| A2 — offer_validation (returns error if offer.requires_informed_consent=false) | `test_offer_validation_returns_error_when_not_required` | PASS — verifies status='offer_does_not_require_consent' + error_code populated + NO consent_record created + NO channel dispatched |
| A3 — idempotency (1h window same (booking_id, slug) returns existing consent_id) | `test_idempotency_returns_existing_consent_id` | PASS — verifies same consent_id returned twice + only 1 record materialized + 2nd event flagged is_new=False |

Plus 10 defensive tests:
- `test_tenant_id_not_in_schema` — security boundary verified via Pydantic introspection
- `test_dispatches_channels_for_both` — both whatsapp + email invoked async
- `test_dispatches_channel_whatsapp_only` — single-channel mode
- `test_dispatch_failure_does_not_break_turn` — fire-and-forget pattern verified (raising dispatcher does not break turn)
- `test_trace_event_recorded_when_repo_supplied` — best-effort observability
- `test_trace_event_failure_does_not_break_turn` — observability never breaks turn
- `test_audit_log_failure_does_not_break_turn` — audit log never breaks turn
- `test_no_patient_pii_in_trace_payload` — PII forbidden keys absent
- `test_signed_url_contains_consent_id_and_token` — HMAC URL contract verified
- `test_expiry_24h_default_per_d7_hipaa_lite` — 24h default expiry per HIPAA-lite

## Validators

| ID | Status | Cmd |
|---|---|---|
| V-AE-5 (tools test suite) | **GREEN — 13/13 passed for medical_consent_request, plus 10/10 still GREEN for prepaid_payment_check from T-tools-1** | `cd backend && .venv/bin/pytest tests/agentic_evals/tools/ -v --tb=short` |
| V-AE-18 (trace invariants) | N/A (file does not exist) | Deferred to future observability integration ticket (full Postgres + production trace repo wiring with cost_usd > 0 + tokens accounted for tools that DO call LLMs — this tool is $0 LLM, so V-AE-18 not applicable to medical_consent_request) |

## Downstream regression (R3 per `auditor-downstream-regression.md`)

Per R3 SSoT table, modifying `vitalia/backend/src/modules/vitalia/agentic/tools/*` requires running `vitalia/backend/tests/agentic_evals/tools/*` AND verifying no regression in extensions.py mounting (T-extensions-1). Validation:

```bash
cd /home/chris/luana-platform/vitalia/backend && \
  .venv/bin/pytest tests/agentic_evals/tools/ tests/unit/repositories/ tests/unit/application/ \
    -v --tb=short --ignore=tests/unit/payment

→ 121 passed in 0.54s
```

`tests/unit/payment/test_mercadopago_adapter.py` collection error excluded — pre-existing missing `langchain_core` dep in vitalia venv (NOT caused by T-tools-2; same state as before this ticket per W6 T-payment-1 result).

## Patterns honored (per 05-guidelines.md § 1.10 + R23)

- ✅ `try/except + structlog.warning("...persist_failed", exc=str(e))` on observability writes (audit_log line 312, trace_event line 365, dispatch line 339)
- ✅ `sanitize_payload(...)` BEFORE persist (audit log line 287, trace line 351)
- ✅ `tenant_id` from kwarg (caller's ctx injection) NEVER from input schema (test_tenant_id_not_in_schema PASS)
- ✅ Idempotency natural via ConsentService D2 — no Redis needed, NO duplication of HMAC/idempotency layer
- ✅ Async throughout (`async def medical_consent_request`)
- ✅ Pydantic v2 ConfigDict (frozen + extra="forbid" on input)
- ✅ Structural Protocols for all deps (no concrete SQLA imports — testable in isolation)
- ✅ Fire-and-forget channel dispatch — per-dependency error isolation (`tessl__graceful-degradation` Rule 5)
- ✅ Structlog (no `print()` / `logging.*`)
- ✅ NO shared abstraction mirrored — sanitize_payload + BaseTraceEventRepoProtocol consumed from canonical `luana_core_observability`
- ✅ NO HMAC duplication — delegated to ConsentService.build_consent_url SSoT
- ✅ NO offer model assumption — accepts `offer_requires_consent` Callable injected by caller (offer model lives in future ticket)

## Decisions honored

- **D1** — Vitalia subdir at `luana-platform/vitalia/`: tool lives in `modules/vitalia/agentic/tools/medical_consent_request.py` (per 02-design § 6.3 path).
- **D7** — compliance_level=hipaa_lite: 24h default URL expiry + audit_log immutable (no deleted_at) + payload PII sanitized + medical_audit_log table append-only retention 7 years.

Other ticket-relevant decisions are upstream — this ticket's scope is consent capture only (no LLM, no prompt slots, no voice).

## Halt triggers — none tripped

- ✅ H4 spec drift: tool surface honors 02-design § 6.3 verbatim — Pydantic schemas match, idempotency contract honored via ConsentService delegation
- ✅ H5 tenant isolation: tenant_id kwarg-only; consent_service + audit_log_repo + channel_dispatcher all bound to tenant via construction (caller's responsibility); test asserts schema absence
- ✅ H6 PII leak: sanitize_payload consumed (NOT re-implemented); test asserts forbidden keys absent from trace payload
- ✅ H10 anti-duplication: no mirror — shared abstractions consumed from canonical paths; ConsentService HMAC SSoT respected; idempotency delegated NOT duplicated

## Tech debt / follow-ups

1. **extensions.py wiring** — current registration passes `_not_implemented_yet()` placeholder. Real handler `medical_consent_request` lives in `agentic/tools/medical_consent_request.py`. Wiring requires the sales_agent tool dispatcher to:
   - Construct tenant-scoped `ConsentService` + `MedicalAuditLogRepository` + offer service callable + channel dispatcher from `tenant_id` + `AsyncSession`
   - Construct tenant-scoped `trace_event_repo` + correlation IDs from current turn
   - Call `await medical_consent_request(input, tenant_id=..., offer_id=..., offer_requires_consent=..., consent_service=..., audit_log_repo=..., channel_dispatcher=..., base_url=..., trace_event_repo=..., turn_id=..., span_id=...)`

   This wiring is a follow-up ticket (T-extensions-2 or sales_agent dispatcher composition ticket), NOT this ticket's scope. The handler itself is complete + tested. SAME pattern as T-tools-1 follow-up.

2. **V-AE-18 observability integration** — real Postgres + production trace_event repo invariants test. This tool is $0 LLM (deterministic), so cost_usd > 0 + tokens accounted assertions DON'T apply. PII sanitization assertion DOES apply — covered locally via `test_no_patient_pii_in_trace_payload`. To be merged into V-AE-18 suite when scaffolded.

3. **Channel dispatcher implementation** — currently consumed via callable Protocol `_ChannelDispatcherLike`. Real WhatsApp / email adapter implementations land in future payment integration ticket (per 02-design § 11). For now, channel dispatch is fire-and-forget — when real adapter materializes, may want to add retry + dead-letter pattern (separate ticket).

4. **Offer model (future)** — currently `offer_requires_consent` is a Callable injected by caller. When OfferRepository materializes (future T-be-X), wire via `lambda offer_id: offer_repo.get_by_id(offer_id).requires_informed_consent`. Tool surface unchanged (Protocol stable).

5. **Multi-tenant audit log retention** — 7-year HIPAA-lite retention enforced via separate purge job (out-of-scope T-tools-2). MedicalAuditLogModel has `created_at` index — retention worker scans by tenant + cutoff date.
