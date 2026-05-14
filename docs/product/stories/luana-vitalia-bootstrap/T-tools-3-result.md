# T-tools-3 — Result

> Story: `luana-vitalia-bootstrap` · Sesion 4 W8 · Closed 2026-05-14.

## State

`done` — tests-passing.

## Acceptance criteria

| ID | Description | Verifier | Result |
|---|---|---|---|
| A1 | list_slots filters by appointment_type + treatment_room + max_concurrent | `tests/agentic_evals/tools/test_appointment_reschedule_with_doctor.py::test_list_slots_filters` | PASS |
| A2 | propose_and_book atomic with advisory lock | `tests/agentic_evals/tools/test_appointment_reschedule_with_doctor.py::test_atomic_book` | PASS |
| A3 | reschedule releases old slot + reserves new | `tests/agentic_evals/tools/test_appointment_reschedule_with_doctor.py::test_reschedule_atomic` | PASS |

Plus 12 defensive tests covering tenant isolation, action discriminator,
idempotency, validation, cancel action, observability resilience (audit + trace),
PII sanitization. Total: **15/15 PASS** in 0.31s.

## Files modified

```
luana-platform/vitalia/backend/src/modules/vitalia/agentic/tools/appointment_reschedule_with_doctor.py    (NEW, ~700 LOC)
luana-platform/vitalia/backend/tests/agentic_evals/tools/test_appointment_reschedule_with_doctor.py       (NEW, ~960 LOC)
```

## Validators executed

```
cd /home/chris/luana-platform/vitalia/backend && uv run pytest tests/agentic_evals/tools/test_appointment_reschedule_with_doctor.py -v --tb=short
→ 15/15 PASS in 0.31s

cd /home/chris/luana-platform/vitalia/backend && uv run ruff check ...
→ All checks passed!

cd /home/chris/luana-platform/vitalia/backend && uv run ruff format --check ...
→ 2 files already formatted

# Downstream regression (R3):
cd /home/chris/luana-platform/vitalia/backend && uv run pytest tests/agentic_evals/tools/ -v
→ 38/38 PASS (T-tools-1 + T-tools-2 unaffected)
```

## Validators referenced

V-AE-5 (per 06-tickets.yaml::Ttools3.validators_pass) — agentic eval tools
unit coverage including idempotency + observability resilience.

## Decisions honored

- D1 DDD: tool calls `BookingService` + repos via Protocol DI; no direct
  session in tool layer.
- D2 atomic via advisory_lock: `BookingService.create_booking` (T-be-5)
  holds `pg_advisory_lock(hash(doctor_id, slot_iso))` — tool DELEGATES.

## Skills consulted (R23 enforcement)

`copilot-expert`, `sales-agent-expert`, `tessl__graceful-degradation`,
`tessl__pytest-api-testing`. (`tessl__langgraph` skipped — no graph node;
`tessl__fastapi` skipped — no endpoint.) Detail in T-tools-3-impl-log.md
§ Skills Consulted.

## Anti-duplication audit

Passed Step 0 GATE pre-write. Cross-codebase grep showed ZERO collision
for `appointment_reschedule_with_doctor`/`propose_and_book`/`reschedule_existing`.
Per Q4=A spec ratification, "@luana/core/scheduling.calendar" maps to
per-vertical surface (BookingRepository + DoctorExtensionRepository +
BookingService) which the tool composes with vertical-medical filters.
NO new infrastructure layer; NO duplicate of pg_advisory_lock primitives.

REUSE chain documented in source docstring "Anti-duplication audit (Step 0
GATE pre-write)" section (lines 66-92).

## Halt triggers

None fired (H1-H13 clean).

## Last line

`done -> docs/product/stories/luana-vitalia-bootstrap/T-tools-3-result.md`
