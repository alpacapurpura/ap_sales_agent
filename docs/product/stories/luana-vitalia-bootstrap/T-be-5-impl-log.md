<!-- voseo-allowed: impl-log cites rules + decisions per R25 -->
---
ticket_id: T-be-5
story_id: luana-vitalia-bootstrap
title: "BE services Booking + advisory_locks + idempotency"
state: done
implementor: builder-backend (Sonnet)
session: Sesion 4 W3
date: 2026-05-13
---

# T-be-5 Implementation Log

## Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `backend-expert` | Mandatory gate per implementation flow. Read `references/runtime-quality-checklist.md`. | Anti-patterns confirmed: SQLA 2.0 select(), Annotated deps, SLF001 private access not blocked by project ruff config (only E,F,I selected). |
| `tessl__fastapi` | Mandatory — service consumes advisory lock functions (external infra calls). | Async pattern confirmed. `response_model=` mandatory; service layer thin — no direct FastAPI imports. |
| `tessl__pytest-api-testing` | Mandatory — tests written per this skill pattern. | factory fixture `_make_request()` pattern. MagicMock + AsyncMock for repos + idempotency store. patch() for advisory lock functions. |
| `tessl__graceful-degradation` | Advisory lock is an external Postgres call — timeout/fallback consideration. | pg_advisory_lock is session-scoped + blocking; Postgres is in-process DB (not HTTP). Finally block ensures lock release. No additional circuit breaker needed at service layer — DB-level timeout handles this at infra. |

## Step 0 Anti-duplication Grep

```bash
grep -rn "class BookingService" /home/chris/luana-platform/ /home/chris/AISALESHT/backend/src/
# → No match. NEW BookingService justified (T-be-5 scope).

grep -rn "SlotTakenError" /home/chris/luana-platform/ /home/chris/AISALESHT/backend/src/
# → No match. NEW exception justified.

grep -rn "pg_advisory_lock\|advisory_lock" /home/chris/luana-platform/vitalia/backend/src/
# → Only in advisory_locks.py (T-be-3 infra). Service CONSUMES existing advisory_locks module — no mirror.
```

Verdict: no blocking collisions. BookingService is new, extends existing advisory_locks.py + BookingRepository from T-be-3.

## Decisions Honored

Per 06-tickets.yaml `decisions_applicable: [D1, D2]`:

- **D1** (03-arch.md § 11): Vitalia subdir at `luana-platform/vitalia/` — all files land in vitalia/backend.
- **D2** (03-arch.md § 11 + spec Q4=A): Reuse `@luana/core/scheduling` — BookingService uses advisory_locks.py (T-be-3 infra) for pg_advisory_lock per slot conflict prevention. Service receives BookingRepo + session via DI (no tight coupling).

## Idempotency Design

- Key: `SHA-256(patient_id:doctor_id:slot_iso_utc_epoch)` hex digest → `vitalia:booking:<sha256>`.
- TTL: 60 seconds (per spec A2).
- Store interface: `IdempotencyStoreProtocol` (Protocol class — structural typing, no import of luana-core-idempotency to avoid dep complexity at this layer).
- Production: Redis-backed `luana-core-idempotency` injected via FastAPI DI at API layer (T-be-7).
- Tests: In-memory dict store + MagicMock.

## Advisory Lock Protocol

- Implemented in `infrastructure/advisory_locks.py` (T-be-3 — already exists, no change needed).
- `BookingService.create_booking()` calls `acquire_slot_advisory_lock()` then `release_slot_advisory_lock()` in a `finally` block.
- Idempotency check is BEFORE the advisory lock acquisition (short-circuit, no lock if cache hit).
- If `SlotTakenError` raised inside lock → lock still released (finally ensures it).

## Status Routing Logic

```
requires_consent=True → "awaiting_consent" (highest priority — consent before payment)
requires_prepay=True  → "pending_payment"
neither              → "confirmed_deposit"
```

Both flags True → "awaiting_consent" (consent takes priority over prepay per spec § 3.4).

## Files Modified

| File | Status | Notes |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/application/services/booking_service.py` | NEW | BookingService + CreateBookingRequest + BookingResult + SlotTakenError + IdempotencyStoreProtocol |
| `vitalia/backend/tests/unit/application/test_booking_service.py` | NEW | 9 unit tests — A2 + A3 + slot_taken + lock_release + tenant isolation |
| `vitalia/backend/tests/integration/test_booking_service_advisory_lock.py` | NEW | 3 integration tests (skip Postgres unavailable) |
| `vitalia/backend/tests/e2e/test_slot_race_double_booking_e2e.py` | NEW | 3 e2e race tests (skip Postgres unavailable) |

## Test Results

| Test suite | Outcome | Notes |
|---|---|---|
| Unit: `tests/unit/application/test_booking_service.py` | 9/9 PASS | A2 idempotency + A3 status routing + SlotTakenError + lock release |
| Integration: `test_booking_service_advisory_lock.py` | 3/3 SKIP | Postgres unavailable — T-be-1+T-be-3 precedent |
| E2E: `test_slot_race_double_booking_e2e.py` (V-F-8) | 3/3 SKIP | Postgres unavailable — same precedent |
| Ruff check | PASS | 0 errors |
| Ruff format | PASS | 4/4 files formatted |

## Cross-module reads

- Read `advisory_locks.py` (T-be-3 infra layer) for lock function signatures and key derivation logic.
- Read `booking_repository.py` (T-be-3 infra repos) for `find_by_doctor_slot()` signature.
- Read `onboarding_service.py` (T-be-4) for pattern reference (Protocol store, structlog, _utc_now).
- Read `VitaliaBookingModel` fields from `booking_model.py` (T-be-3 models).

## Out-of-scope (per 06-tickets.yaml)

- `PrepaidPaymentService` (T-be-6) — payment_url generation not wired here.
- Endpoints / FastAPI DI wiring (T-be-7) — `IdempotencyStoreProtocol` will be satisfied by Redis-backed store injected there.
- ConsentRequestedV1 event emission (T-be-6) — `consent_url` field in BookingResult is None until wired.

## Parallel sessions WIP (untouched)

Files `M` in `git status` belong to parallel sessions — left untouched per parallel-safety.md M8:
- `core/DEFERRED-FILES.md`, `core/luana-core-platform/...`, `core/tests/architecture/...`, `pyproject.toml`
- `vitalia/backend/tests/unit/application/test_consent_service.py`
- `vitalia/backend/tests/unit/application/test_prepaid_payment_service.py`
- `vitalia/backend/tests/unit/application/test_treatment_followup_service.py`
- `vitalia/backend/src/modules/vitalia/application/services/consent_service.py`
- `vitalia/backend/src/modules/vitalia/application/services/treatment_followup_service.py`
