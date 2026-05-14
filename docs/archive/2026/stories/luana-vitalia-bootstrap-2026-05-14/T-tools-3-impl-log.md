# T-tools-3 — `appointment_reschedule_with_doctor` implementation log

> Story: `luana-vitalia-bootstrap` · Sesion 4 W8 · R23 Opus 4.7 EXCLUSIVE.
> Closed 2026-05-14 · Owner: builder-agentic Opus 4.7.

## Skills Consulted

| Skill | Why invoked | Decision applied |
|---|---|---|
| `copilot-expert` | AGENTIC tool touches `modules/vitalia/agentic/tools/`. Anti-duplication cardinal + best-effort observability + PII sanitization + tool dispatcher tenant_id injection. | (a) Cross-codebase grep verified ZERO collision for `appointment_reschedule_with_doctor` / `propose_and_book` / `reschedule_existing`. (b) `audit_log_repo.save` + `trace_event_repo.add` wrapped try/except + structlog warn — NEVER break turn (R23). (c) `sanitize_payload` from `luana_core_observability.recording.sanitization` — REUSE shared (anti-duplication.md). |
| `sales-agent-expert` | AGENTIC tool extends BookingService + matches T-tools-2 shape. § 0 anti-duplication cardinal mandate. | (a) Confirmed `BookingService` (T-be-5) is the canonical advisory-lock + 60s idempotency surface — REUSE. (b) Tool delegates `propose_and_book` to `BookingService.create_booking`; never replicates pg_advisory_lock at tool layer. (c) Output schema fields + Protocol-typed dependency injection mirror T-tools-2 patterns (decoupled from concrete repo classes). |
| `tessl__langgraph` | N/A — this is a `@tool` not a graph node. No StateGraph / edge / state schema changes. | Skipped per mapping table — only invoked when modifying graphs. |
| `tessl__graceful-degradation` | External call (DB + advisory lock indirectly via BookingService). | (a) Audit + trace writes wrap try/except (Rule 6 log failures with context). (b) `SlotTakenError` from BookingService surfaces as `booking_status="slot_taken"` instead of raising — sales_agent re-lists slots per § 5.2 failure branch (Rule 2 fallback). (c) BookingService internally enforces 60s idempotency window — short-circuit retries (Rule 3 idempotent-by-design). |
| `tessl__pytest-api-testing` | New pytest fixtures async + factory pattern + in-memory fakes. | (a) `_FakeBookingRepository` + `_FakeDoctorExtensionRepository` + `_FakeBookingServiceCalls` follow factory-fixture pattern; tenant-scoped at construction. (b) Asyncio mode AUTO already configured in pyproject.toml. (c) Capturing + Raising fakes for audit_log_repo + trace_event_repo (§ 8 testing both happy + degradation paths). |
| `tessl__fastapi` | N/A — no new FastAPI endpoint. | Skipped. |

## Cross-module audit (NO-NEW-LAYER)

ANTES de write, performed grep + inventory check per `.claude/rules/anti-duplication.md`:

```bash
grep -rln "appointment_reschedule_with_doctor|propose_and_book|reschedule_existing" \
  /home/chris/luana-platform/ /home/chris/AISALESHT/backend/src/
# → only matches in spec docs + extensions.py registration stub. NO source collision.

find /home/chris/luana-platform/core -path '*scheduling*' -o -path '*calendar*'
# → core/luana-core-platform/src/luana_core_platform/links/ports/scheduling.py
#   (Nicolify-specific port — NOT applicable to vertical-medical booking)
# → core/luana-core-sales-agent/src/luana_core_sales_agent/application/tools/scheduling/
#   (S8 booking_link tools — Nicolify-domain, NOT slot reservation per (doctor, slot))
# → No core/luana-core-platform "scheduling.calendar" Calendar class exists.
```

**Conclusion (per Q4=A spec ratification):** "@luana/core/scheduling.calendar"
referenced in spec § 6.4 maps to the PER-VERTICAL surface registered in
T-be-2 (BookingRepository + DoctorExtensionRepository) + T-be-5 (BookingService).
Tool EXTENDS this surface by composing it with vertical-medical filters
(appointment_type compat + treatment_room_assignment + max_concurrent_per_doctor)
+ idempotent action discriminator. NO new infrastructure layer. NO duplicate
of pg_advisory_lock primitives.

REUSE inventory cited:
- `BookingService.create_booking` (T-be-5) — atomic + 60s idempotency cache.
- `acquire/release_slot_advisory_lock` (T-be-2) — held by BookingService internal.
- `BookingRepository.{get_by_id, find_by_doctor_slot, list_by_doctor, save}` (T-be-3).
- `DoctorExtensionRepository.get_by_doctor_id` (T-be-3).
- `VitaliaMedicalAuditLogModel` (T-be-2) — audit row schema.
- `sanitize_payload` from `luana_core_observability.recording.sanitization` (canonical).
- `BaseTraceEventRepoProtocol` from `luana_core_observability.persistence` (structural Protocol).

## TDD RED → GREEN cycle

1. Wrote `test_appointment_reschedule_with_doctor.py` first (15 tests covering
   A1-A3 acceptance + 12 defensive tests).
2. RED confirmed: `ModuleNotFoundError` at import.
3. Wrote `appointment_reschedule_with_doctor.py` implementation.
4. Iteration 1: 14/15 PASS; `test_reschedule_atomic` failed because
   `_FakeBookingServiceCalls` hardcoded `status="pending_payment"` while real
   BookingService returns `confirmed_deposit` for default flags. Fixed FAKE
   to mirror `_determine_booking_status` semantics.
5. Iteration 2: same test failed because original design tried to
   "stable booking_id" (mutate `existing.id = new_result.booking_id`)
   creating dual-write race. Refined design: tool returns NEW booking_id
   from BookingService; old row preserved as cancelled (audit trail
   intact); `audit_log` payload includes `old_booking_id` linking old→new.
   Updated test to assert NEW booking_id semantics + `old_booking_id`
   in audit payload.
6. Iteration 3 (final): all 15 PASS in 0.31s.

No iteration cap reached.

## Implementation summary

### File 1 — `src/modules/vitalia/agentic/tools/appointment_reschedule_with_doctor.py` (~700 LOC)

- `WindowSpec` Pydantic model — start date + days span (1-60 cap).
- `AppointmentRescheduleInput` — Literal action discriminator, doctor_id required,
  per-action optional fields (booking_id / offer_id / patient_id / preferred_window
  / target_slot / appointment_type). `frozen=True` + `extra="forbid"`.
- `AppointmentRescheduleOutput` — available_slots + booking_id + booking_status
  + payment_url + appointment_type + treatment_room_assigned.
- `appointment_reschedule_with_doctor` async handler — 4-action dispatcher.
- 4 `_handle_*` action functions (list_slots / propose_and_book /
  reschedule_existing / cancel) — each owns its branch logic.
- 5 dependency Protocols (`_BookingRepoLike`, `_DoctorExtensionRepoLike`,
  `_BookingServiceLike`, `_AuditLogRepoLike`, `_TraceEventRepoLike`,
  `_SchedulerQueryLike`) — decoupled from concrete classes.
- Helpers: `_list_active_doctor_bookings` (union active statuses),
  `_append_audit_log` (best-effort + sanitize_payload),
  `_emit_trace_event` (best-effort + sanitize_payload + skip when correlation
  IDs absent).

### File 2 — `tests/agentic_evals/tools/test_appointment_reschedule_with_doctor.py` (~960 LOC)

15 tests across 4 acceptance criteria + defensive coverage:

| # | Test | Acceptance |
|---|---|---|
| 1 | `test_tenant_id_not_in_schema` | Security boundary (ctx-injected) |
| 2 | `test_action_discriminator` | Pydantic Literal enforcement |
| 3 | `test_list_slots_filters` | **A1** — appointment_type + treatment_room + max_concurrent |
| 4 | `test_list_slots_respects_max_concurrent` | A1 edge: max_concurrent=2 with 1 vs 2 active bookings |
| 5 | `test_list_slots_no_doctor_extension_returns_empty` | A1 defensive |
| 6 | `test_atomic_book` | **A2** — atomic with advisory lock (race detection) |
| 7 | `test_propose_and_book_idempotency` | A2 60s idempotency window |
| 8 | `test_propose_and_book_missing_required_fields_returns_error` | A2 validation surface |
| 9 | `test_reschedule_atomic` | **A3** — releases old + reserves new + audit links old→new |
| 10 | `test_reschedule_missing_booking_returns_error` | A3 defensive |
| 11 | `test_cancel_releases_slot_and_audit` | Cancel action coverage |
| 12 | `test_audit_log_failure_does_not_break_turn` | R23 best-effort observability |
| 13 | `test_trace_event_recorded_on_propose_and_book` | Trace event happy path |
| 14 | `test_trace_event_failure_does_not_break_turn` | R23 best-effort observability |
| 15 | `test_pii_sanitized_in_audit_payload` | PII defense (no @ / +5 patterns) |

In-memory fakes (`_FakeBookingRepository`, `_FakeDoctorExtensionRepository`,
`_FakeBookingServiceCalls`, `_CapturingAuditRepo`, `_RaisingAuditRepo`,
`_CapturingTraceRepo`, `_RaisingTraceRepo`) mirror real T-be-3 / T-be-5
surfaces. `_FakeBookingServiceCalls` mirrors real `_determine_booking_status`
semantics + 60s idempotency cache + SlotTakenError raising.

## Validators result

| Command | Result |
|---|---|
| `uv run pytest tests/agentic_evals/tools/test_appointment_reschedule_with_doctor.py -v` | **15/15 PASS** in 0.31s |
| `uv run ruff check src/...appointment_reschedule_with_doctor.py tests/...` | All checks passed |
| `uv run ruff format --check ...` | 2 files already formatted |
| Downstream regression: `uv run pytest tests/agentic_evals/tools/` | **38/38 PASS** (T-tools-1 + T-tools-2 unaffected) |

## Decisions honored

- D1 (DDD): tool lives in `agentic/tools/`; calls `BookingService` (application
  service) + repos via DI Protocols. No direct session construction in tool layer.
- D2 (atomic via advisory_lock): pg_advisory_lock per `(doctor_id, slot_iso)`
  enforced by `BookingService.create_booking` (T-be-5). Tool delegates rather
  than re-implementing — REUSE shared infrastructure (anti-duplication.md).

## Halt triggers

None fired (H1-H13 clean):
- H1 cost variance: $0 LLM (deterministic SQL only) — within budget.
- H2 validators blocked: NO — passed first GREEN iteration.
- H3 arch fitness: NO new violation introduced (no new shared/* layer).
- H4 spec drift: NO — implementation matches § 6.4 + § 5.2 verbatim.
- H5 tenant isolation: tenant_id NEVER in input schema (security boundary
  test asserts this explicitly).
- H6 PII leak: `sanitize_payload` invoked BEFORE every persist; assertion
  test verifies no @/+5 patterns in audit payload.
- H7 Spanish neutro: N/A (tool returns structured data, no user-facing strings).
- H8 alembic conflict: N/A.
- H9 cross-module import boundary: only consumes T-be-2/3/5 within vitalia
  module + `luana_core_observability.recording.sanitization` (allowed shared).
- H10 anti-duplication: passed Step 0 GATE pre-write — verified REUSE strategy.
- H11/H12/H13: N/A.

## Anti-default-flip-audit

N/A — no `core/config.py` defaults touched.

## Files committed (Sesion 4 W8)

```
luana-platform/vitalia/backend/src/modules/vitalia/agentic/tools/appointment_reschedule_with_doctor.py
luana-platform/vitalia/backend/tests/agentic_evals/tools/test_appointment_reschedule_with_doctor.py
```

Docs (this story):
```
AISALESHT/docs/product/stories/luana-vitalia-bootstrap/T-tools-3-impl-log.md
AISALESHT/docs/product/stories/luana-vitalia-bootstrap/T-tools-3-result.md
```

## State

`done -> docs/product/stories/luana-vitalia-bootstrap/T-tools-3-result.md`
