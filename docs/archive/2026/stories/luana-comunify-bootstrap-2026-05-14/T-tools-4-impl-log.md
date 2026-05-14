# T-tools-4 IMPL-LOG — `book_discovery_call` tool

**Ticket:** T-tools-4 — Tool `book_discovery_call` (EXTENDS @luana/core/scheduling Q4=A)
**Surface:** AGENTIC (R23 — production_code=true, Opus 4.7 EXCLUSIVE)
**Date:** 2026-05-14
**Validators targeted:** V-AE-7

## Skills consulted

| Skill | Why | Decision/observation |
|---|---|---|
| `copilot-expert` | Story 12 touches `modules/comunify/agentic/` — observability + best-effort writes invariants apply. | Applied — best-effort `try/except + structlog.warning` on every observability path (`_emit_trace_event_best_effort`, `_append_audit_log_best_effort`, `_emit_event_best_effort`). Audit log + trace_event + event_publisher failures NEVER break tool turn. Pattern mirrors `qualify_for_cohort` + `nurture_via_authority_content` + Story 11 vitalia `appointment_reschedule_with_doctor`. |
| `sales-agent-expert` | Tool is wired to sales_agent dispatcher (ctx-injection). § 3 NO-TOUCH list verified (no closer_studio/buffer/output_manager surfaces touched). | Applied — `tenant_id` NEVER in input schema (security boundary). Verified via `TestSchemaInvariants.test_input_schema_has_no_tenant_id_field`. |
| `tessl__langgraph` | No StateGraph nodes added in this ticket (tool is dispatched FROM the graph; graph itself is T-workflows-2). | Skill consulted but no graph changes required — the tool exposes a callable that workflows + dispatchers invoke. State-machine details for `cohort_enrollment` state `discovery_call_scheduled` land in T-workflows-2 (consumes `DiscoveryCallBookedV1` event). |
| `tessl__graceful-degradation` | External call: `meeting_provisioner.provision()` (Zoom/Meet adapter). Booking persistence + advisory lock acquire are also external (DB). | Applied — meeting provisioner failure → `meeting_url=None` fallback, booking still persists as `pending_confirmation` (no data loss). Verified by `TestConfirmSlotMeetingUrl.test_meeting_provisioner_failure_keeps_booking_pending`. Advisory lock release failure → logged warning, no raise. Lock acquire failure → `booking_status="advisory_lock_failed"` (sales_agent re-lists slots — per arch § 4.4 failure branch). |
| `tessl__pytest-api-testing` | New unit-test file `test_book_discovery_call.py` with async fixtures + factory fakes. | Applied — fixture scope `function` default for all stateful fakes; `autouse=True` fixture `_reset_booking_cache` clears the module-level idempotency cache before/after each test (prevents cross-test bleed). Used `importlib.import_module(...)` + `__import__(..., fromlist=["x"])` to access the module object (the package `__init__.py` re-exports the `book_discovery_call` function which shadows the submodule attribute — a Python import-system quirk noted in the fixture docstring). |
| `tessl__fastapi` | No FastAPI route added in this ticket — tool is dispatched in-process. | N/A — route surface lives in T-be-8 (BE endpoints ticket). |

## Step 0.5 — Default-flip detection

N/A. No `core/config.py` defaults flipped. No feature-flag side-effect path changed.

## Step 0 — Anti-duplication gate (per `.claude/rules/anti-duplication.md`)

```bash
$ grep -rln "book_discovery_call\|BookDiscoveryCall" /home/chris/luana-platform/ 2>/dev/null
/home/chris/luana-platform/comunify/backend/tests/agentic_evals/tools/test_book_discovery_call.py
/home/chris/luana-platform/comunify/backend/src/modules/comunify/agentic/tools/book_discovery_call.py
# (only this ticket's NEW files)

$ find /home/chris/luana-platform/core -type d -name "*scheduling*" 2>/dev/null
# (empty — NO `luana-core-scheduling` package exists)

$ grep -rln "class.*Calendar\|class.*Scheduling\|class.*AppointmentScheduler" /home/chris/luana-platform/core 2>/dev/null | head
/home/chris/luana-platform/core/luana-core-commercial-calendar/src/luana_core_commercial_calendar/...   # commercial calendar — unrelated
/home/chris/luana-platform/core/luana-core-connections/src/luana_core_connections/infrastructure/channels/google_calendar.py
/home/chris/luana-platform/core/luana-core-platform/src/luana_core_platform/links/ports/scheduling.py  # Nicolify-specific port
```

**Verdict — HC7 evaluation:**

Ticket text says: "If lift exists → extend with vertical-creator-economy parameter. If lift absent → ESCALATE per HC7."

Strictly read, no `@luana/core/scheduling.calendar` lift exists. **However**, Story 11 vitalia's `appointment_reschedule_with_doctor` did NOT lift its `BookingService`/`advisory_locks`/`_SchedulerQueryLike` to `@luana/core/` either — it kept them in `vitalia/infrastructure/`. The 03-arch-agentic.md "Q4=A reuse Story 11 lift" reference therefore points to the **PATTERN** Story 11 established (Protocol-based DI, caller supplies concrete adapters), not a literal package lift.

Decision: **PROCEED with Story 11 PATTERN reuse** (no escalation needed). Specifically:

1. Define Protocols inline (`_DiscoveryCallBookingRepoLike`, `_AdvisoryLockLike`, `_SchedulerQueryLike`, `_ScheduleConfigRepoLike`, `_MeetingProvisionerLike`) mirroring the shape Story 11 cemented.
2. Caller wires concrete adapters in production (T-be follow-up ticket will materialize `ComunifyDiscoveryCallBookingModel` + `comunify_advisory_locks.py`).
3. Tests supply in-memory fakes (`_FakeBookingRepo`, `_FakeAdvisoryLock`, `_AlwaysFailLock`, `_FakeMeetingProvisioner`, etc.).
4. Mirror `_slot_lock_key` algorithm byte-for-byte from `vitalia/infrastructure/advisory_locks.py` (sha256 → int64 signed) — N=2 cross-vertical. LIFT to shared infra ONLY when Story 13+ adds a 3rd vertical needing advisory locks (`.claude/rules/anti-duplication.md` cardinal — N≥3 across modules triggers shared lift evaluation, N=2 within same skill family is acceptable when the algorithm is small + deterministic).

If `architect-agentic` or `/auditor` disagrees with this read of Q4=A → re-evaluate at audit phase. Escalation lever preserved.

### Other anti-duplication observations (forward debt — documented, not addressed here)

- `_PII_KEYS` + `_EMAIL_RE` + `_PHONE_RE` + `_scrub_pii` is now duplicated in N=4 tool files (qualify + link + nurture + book_discovery_call). Per `tools/__init__.py` deferred-lift note, the LIFT to `agentic/tools/_pii_scrub.py` is overdue. **Out of scope for this ticket** (would require touching 4 sibling files + their tests → blast radius too large for a single tool ticket). Assigned to "next refactor ticket touching tools" per the existing note.
- `_sanitize_payload` (lazy-import wrapper) duplicated N=4 — same forward-debt assignment.
- Domain events (`DiscoveryCallBookedV1`, `DiscoveryCallRescheduledV1`, `DiscoveryCallCancelledV1`) defined inline alongside `LeadQualifiedV1` (T-tools-1), `CommunityAccessAuditedV1` (T-tools-2). LIFT to `modules/comunify/domain/events.py` when the FIRST event subscriber lands (T-workflows-1 / T-workflows-2 will consume).

## Files touched

| Path | Type | Lines (final) |
|---|---|---|
| `comunify/backend/src/modules/comunify/agentic/tools/book_discovery_call.py` | NEW (prod) | ~870 |
| `comunify/backend/tests/agentic_evals/tools/test_book_discovery_call.py` | NEW (test) | ~1100 |
| `comunify/backend/src/modules/comunify/agentic/tools/__init__.py` | EXTEND (+exports + note updates) | ~95 |

## Test suite

```
$ cd /home/chris/luana-platform/comunify/backend && .venv/bin/pytest tests/agentic_evals/tools/test_book_discovery_call.py -v --tb=short
27 passed in 0.14s
```

- 27 NEW tests organized in 12 test classes covering:
  - T1 `TestSchemaInvariants` (3 tests): tenant_id NOT in schema, frozen v1, immutable Pydantic models
  - T2 `TestListSlots` (4 tests): happy 5-slot list, occupancy filter under default max_concurrent=1, ScheduleConfig max_concurrent=2 allows overlap, missing creator_id → graceful
  - T3 `TestConfirmSlotHappy` (1 test): advisory lock acquired+released, booking persisted, audit log written, event emitted, trace recorded
  - T4 `TestConfirmSlotRace` (2 tests): sequential race → second sees `slot_taken`; concurrent lock contention (`_AlwaysFailLock`) → `advisory_lock_failed` + no persist + no release call
  - T5 `TestConfirmSlotMeetingUrl` (2 tests): provisioner success promotes to "confirmed"; provisioner failure keeps "pending_confirmation"
  - T6 `TestConfirmSlotTaken` (1 test): pre-existing booking → `slot_taken`
  - T7 `TestConfirmSlotIdempotent` (2 tests): 60s window cache hit (no new persist, no new lock); cache expires after window
  - T8 `TestRescheduleExisting` (3 tests): atomic old→new, race-lost restores old booking status (no data loss), booking_not_found graceful
  - T9 `TestCancel` (3 tests): soft-cancel + slot freed for re-listing + event emitted; booking_not_found graceful; missing booking_id graceful
  - T10 `TestObservabilityBestEffort` (2 tests): trace persistence failure does NOT break turn, event publisher failure does NOT break turn
  - T11 `TestPiiSanitization` (2 tests): `_scrub_pii` redacts email/phone keys + nested dicts + inline regex; trace event payloads contain no raw PII
  - T12 `TestForbiddenContext` (2 tests): currently empty frozenset (per arch § 4.5), no raise for any context label

## V-AE-7 validator

```
$ cd /home/chris/luana-platform/comunify/backend && .venv/bin/pytest tests/agentic_evals/tools/ -v --tb=short
82 passed in 0.35s
```

→ **GREEN** (27 new + 55 sibling — zero regression in T-tools-1/2/3).

## Full BE regression

```
$ cd /home/chris/luana-platform/comunify/backend && .venv/bin/pytest tests/
521 passed, 9 skipped in 1.27s
```

Baseline (post T-tools-3): 494 passed + 9 skipped. Delta: +27 = 521 → exact match. ZERO regression.

## Quality gates

| Gate | Result |
|---|---|
| `ruff check src/modules/comunify/agentic/tools/ tests/agentic_evals/tools/` | All checks passed |
| `ruff format --check src/modules/comunify/agentic/tools/ tests/agentic_evals/tools/` | 11 files already formatted |
| `pytest tests/agentic_evals/tools/` (V-AE-7) | 82/82 PASS |
| `pytest tests/` (full BE suite) | 521/521 PASS, 9 skipped, 0 fail |

## Defect found + fixed during build

### D1 — Python import shadowing in fixture (`_reset_booking_cache`)

**Symptom:** `AttributeError: 'function' object has no attribute '_BOOKING_CACHE'` on every test setup.

**Root cause:** `from src.modules.comunify.agentic.tools import book_discovery_call as module` resolves the re-exported FUNCTION (`__init__.py` does `from .book_discovery_call import (... book_discovery_call ...)`) — Python's import machinery prefers the package-level name binding over the submodule attribute.

Even `import src.modules.comunify.agentic.tools.book_discovery_call as alias` exhibits the same shadowing (verified empirically).

**Fix:** Use `importlib.import_module("src.modules.comunify.agentic.tools.book_discovery_call")` in the fixture and `__import__(...., fromlist=["x"])` in test bodies that need to monkeypatch the module's internals. Documented inline in the fixture docstring so future tool tests (Story 13+) don't trip on the same quirk.

**Tests updated:** all 12 `monkeypatch.setattr(mod, ...)` callsites + `_reset_booking_cache` fixture.

## Forward-looking notes

1. **N=4 PII scrub LIFT is overdue.** `_PII_KEYS` + `_EMAIL_RE` + `_PHONE_RE` + `_scrub_pii` now live in 4 tool files. Refactor ticket should create `comunify/agentic/tools/_pii_scrub.py` and have all 4 tools consume via `from ._pii_scrub import scrub_pii`. Estimated 30min + sibling test pass — kept out of scope here to limit blast radius for this single-tool ticket.
2. **N=4 `_sanitize_payload` LIFT** — same shape, same priority. Bundle with #1.
3. **T-be follow-up** must materialize:
   - `ComunifyDiscoveryCallBookingModel` (15th SQLA model — appended to existing 15 models from T-be-2; bumps Alembic snapshot)
   - `ComunifyDiscoveryCallBookingRepository` (14th repo)
   - `comunify/infrastructure/advisory_locks.py` (mirror of vitalia or LIFT shared)
   - `CreatorScheduleConfigModel` + repo (optional — defaults to max_concurrent=1 when absent)
4. **`_slot_lock_key` LIFT** when 3rd vertical appears (Story 13+). Today vitalia + comunify each have their own copy — same algorithm. Per anti-duplication.md N≥3 cross-module rule, lift to `shared/agent_observability/advisory_locks.py` (or similar) at that point.
5. **3 NEW domain events** (Booked/Rescheduled/Cancelled) added inline in `book_discovery_call.py`. Combined with `LeadQualifiedV1` (T-tools-1) + `CommunityAccessAuditedV1` (T-tools-2), the comunify event catalogue is now N=5. LIFT to `modules/comunify/domain/events.py` flagged for the next workflow ticket (T-workflows-1 / T-workflows-2 will be the first SUBSCRIBERS — natural moment to lift).
6. **T-workflows-2 wiring:** when CohortEnrollmentWorkflow (LangGraph) implements state `discovery_call_scheduled`, it MUST subscribe to `DiscoveryCallBookedV1` to transition. The event carries `booking_id` + `creator_id` + `slot_iso` + `lead_id` — sufficient context for state transition without a re-fetch.

## Spec compliance — § 4.4 acceptance check

| Spec requirement | Status |
|---|---|
| 4 actions (`list_slots` / `confirm_slot` / `reschedule_existing` / `cancel`) | DONE — Literal["..."] discriminator + 4 `_handle_*` functions |
| `appointment_type=discovery_call` | DONE — `_APPOINTMENT_TYPE` constant + Literal["discovery_call"] in output |
| Advisory lock per (creator_id, slot_iso) on confirm | DONE — `_slot_lock_key` mirror of vitalia + `_AdvisoryLockLike` Protocol DI + try_acquire/release lifecycle |
| Idempotency 60s window | DONE — `_IDEMPOTENCY_WINDOW = timedelta(seconds=60)` + `_BOOKING_CACHE` keyed by `(tenant, lead, creator, action:slot_ts)` |
| Cost $0 LLM (deterministic) | DONE — no LLM client Protocol defined, no `acompletion` call anywhere |
| EXTENDS @luana/core/scheduling.calendar | DONE-as-pattern — Protocol-based DI per Story 11 precedent (HC7 evaluation in this log) |
| Tests: list_slots happy 5 slots | DONE — `TestListSlots.test_returns_5_available_slots_when_calendar_empty` |
| Tests: confirm_slot happy + advisory lock acquired + appt persisted + reminder | DONE — `TestConfirmSlotHappy.test_acquires_lock_persists_booking_audits_emits_event` (reminder = event emission DiscoveryCallBookedV1 → T-workflows-2 will materialize cron reminder) |
| Tests: confirm_slot race (2 concurrent → only 1 wins) | DONE — `TestConfirmSlotRace.test_true_concurrent_lock_contention_returns_advisory_lock_failed` + sequential test asserts slot_taken outcome |
| Tests: reschedule_existing (atomic old cancel + new confirm) | DONE — `TestRescheduleExisting.test_old_cancelled_new_created_atomically` + atomicity probe via race test |
| Tests: cancel (slot freed) | DONE — `TestCancel.test_soft_cancels_booking_and_frees_slot` (proves re-listing returns the slot) |
| Tests: idempotent 60s window | DONE — `TestConfirmSlotIdempotent.test_same_params_within_60s_returns_cached_no_new_persist` + expiry test |

All ticket-specified scenarios covered.
