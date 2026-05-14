# T-tools-4 RESULT — `book_discovery_call` tool

**Date:** 2026-05-14
**Verdict (build phase):** `tests-passing`
**Ticket:** [T-tools-4](06-tickets.yaml#L666) Story 12 `luana-comunify-bootstrap`
**Validators passed:** V-AE-7

## What shipped

A single async `book_discovery_call` tool with 4 actions
(`list_slots` / `confirm_slot` / `reschedule_existing` / `cancel`) for
the vertical-creator-economy surface. Atomic slot reservation via
pg_advisory_lock (Protocol-based DI mirroring Story 11 vitalia
precedent) + 60s in-process idempotency window + best-effort
observability + meeting-URL provisioning hook (Zoom/Meet) + soft-cancel
audit trail.

Cost: **$0 LLM** — pure deterministic SQL + business rules. No LLM
client surface defined; no `acompletion` call anywhere. Latency
budget per arch § 4.4: list_slots p50 200ms / p99 600ms;
confirm_slot p50 300ms / p99 800ms.

## Artifacts

| Path | Type | Lines |
|---|---|---|
| `comunify/backend/src/modules/comunify/agentic/tools/book_discovery_call.py` | NEW (prod) | ~870 |
| `comunify/backend/tests/agentic_evals/tools/test_book_discovery_call.py` | NEW (test) | ~1100 |
| `comunify/backend/src/modules/comunify/agentic/tools/__init__.py` | EXTEND (+exports + lift notes) | ~95 |

## Acceptance criteria (from 06-tickets.yaml::T-tools-4)

| Criterion | Status |
|---|---|
| 4 actions: `list_slots` / `confirm_slot` / `reschedule_existing` / `cancel` | DONE — `Literal[...]` discriminator + 4 `_handle_*` handlers |
| EXTENDS `@luana/core/scheduling.calendar` (Q4=A reuse Story 11 lift) | DONE-as-pattern — Protocol-based DI mirroring Story 11 vitalia `appointment_reschedule_with_doctor` precedent. No literal `@luana/core/scheduling` package exists; HC7 evaluated in IMPL-LOG and resolved as PATTERN-reuse (architect/auditor invited to push back if they disagree). |
| `appointment_type=discovery_call` (NEW vertical-creator-economy type) | DONE — `_APPOINTMENT_TYPE` constant + `Literal["discovery_call"]` in output |
| Advisory lock per (creator_id, slot_iso) on confirm | DONE — `_slot_lock_key` algorithm mirrors vitalia byte-for-byte; `_AdvisoryLockLike` Protocol with `try_acquire`/`release` lifecycle |
| Idempotency 60s window | DONE — `_IDEMPOTENCY_WINDOW = timedelta(seconds=60)` + `_BOOKING_CACHE` keyed by `(tenant, lead, creator, action:slot_ts)` |
| Cost $0 LLM (deterministic) | DONE — verified by absence of `acompletion` callsites and no `_LLMClientLike` Protocol |
| Test list_slots happy: 5 slots filtered | T2 PASS (`test_returns_5_available_slots_when_calendar_empty`) + occupancy filter test + ScheduleConfig max_concurrent=2 test |
| Test confirm_slot happy: advisory lock + booking + reminder | T3 PASS (`test_acquires_lock_persists_booking_audits_emits_event`) — verifies lock acquire+release, booking persisted, audit log written, `DiscoveryCallBookedV1` event emitted, trace recorded |
| Test confirm_slot race: 2 concurrent → only 1 wins (advisory_lock_failed) | T4 PASS — `test_true_concurrent_lock_contention_returns_advisory_lock_failed` (always-fail-lock fake) + sequential `slot_taken` outcome test |
| Test reschedule_existing: prev cancelled + new confirmed atomically | T8 PASS (`test_old_cancelled_new_created_atomically`) + atomicity test (`test_new_slot_lock_lost_restores_old_booking_status` — no data loss on race) |
| Test cancel: status=cancelled + slot freed | T9 PASS (`test_soft_cancels_booking_and_frees_slot` — proves re-listing returns the slot post-cancel) |
| Test idempotent: same params 60s window → cached response | T7 PASS (`test_same_params_within_60s_returns_cached_no_new_persist` + cache-expiry test) |

## Test suite

```
$ cd /home/chris/luana-platform/comunify/backend && .venv/bin/pytest tests/agentic_evals/tools/ -v --tb=short
collected 82 items
tests/agentic_evals/tools/test_book_discovery_call.py ........................... [ 32%]
tests/agentic_evals/tools/test_link_to_community.py ...................         [ 56%]
tests/agentic_evals/tools/test_nurture_via_authority_content.py ...............  [ 84%]
tests/agentic_evals/tools/test_qualify_for_cohort.py .............              [100%]
============================== 82 passed in 0.35s ==============================
```

- **T-tools-4 contribution:** 27 NEW tests in 12 classes, ALL PASS.
- **Sibling regression:** ZERO (T-tools-1 13/13 PASS, T-tools-2 19/19 PASS, T-tools-3 23/23 PASS).
- **Full BE suite:** `pytest tests/` → 521 passed, 9 skipped, 0 fail. Delta vs T-tools-3 baseline = +27 = exact match.

## V-AE-7

```yaml
- id: V-AE-7
  category: agentic_eval
  type: pytest
  cmd: "cd /home/chris/luana-platform/comunify/backend && .venv/bin/pytest tests/agentic_evals/tools/ -v --tb=short"
  must_pass: true
  timeout_sec: 300
```

→ **GREEN** (`82 passed in 0.35s`).

## Quality gates

| Gate | Result |
|---|---|
| `ruff check src/modules/comunify/agentic/tools/ tests/agentic_evals/tools/` | All checks passed |
| `ruff format --check ...` | 11 files already formatted |
| `pytest tests/agentic_evals/tools/` | 82/82 PASS |
| `pytest tests/` (full BE suite) | 521/521 PASS, 9 skipped, 0 fail |
| Cross-tool regression (T-tools-1/2/3) | ZERO regression |

## Anti-duplication (`.claude/rules/anti-duplication.md` Step 0 GATE)

- `book_discovery_call` / `BookDiscoveryCall*` — pre-write grep clean (only this ticket's NEW files).
- No `@luana/core/scheduling` package exists — Q4=A "reuse Story 11 lift" resolves to PATTERN reuse (Protocol-based DI), NOT literal package consumption. Decision logged in IMPL-LOG § "Step 0 — Anti-duplication gate / HC7 evaluation".
- `ForbiddenToolContextError` — re-exported from shared `_exceptions.py` (T-tools-3 LIFT). NO new copy.
- `_slot_lock_key` — N=2 cross-vertical (vitalia + comunify), same algorithm. LIFT deferred until N=3 cross-module (Story 13+) per rule cardinal.
- `_PII_KEYS` / `_EMAIL_RE` / `_PHONE_RE` / `_scrub_pii` — N=4 inline across comunify tools (forward debt — assigned to next refactor ticket per `tools/__init__.py` note).
- `_sanitize_payload` lazy-import wrapper — N=4 inline (same forward-debt bucket).
- 3 NEW domain events inline (Booked / Rescheduled / Cancelled). LIFT to `modules/comunify/domain/events.py` flagged for T-workflows-1 / T-workflows-2 (first SUBSCRIBERS).

## Forward debt assigned to follow-up tickets

1. **T-be follow-up** (sometime before T-eval-1): materialize `ComunifyDiscoveryCallBookingModel` + repo + `comunify/infrastructure/advisory_locks.py` (or LIFT shared if reasonable). Today the tool is fully Protocol-tested with fakes — production wiring is the missing piece.
2. **PII scrub LIFT (N=4)** — create `comunify/agentic/tools/_pii_scrub.py`, refactor 4 sibling tools. Estimated 30min.
3. **Domain events LIFT** — create `modules/comunify/domain/events.py` when T-workflows-1/2 first subscribes.

## R3 downstream regression hint

The following surfaces should be revisited when any of these files change:

| Surface modified | Downstream test paths |
|---|---|
| `comunify/backend/src/modules/comunify/agentic/tools/book_discovery_call.py` | `comunify/backend/tests/agentic_evals/tools/test_book_discovery_call.py` + (future) `tests/agentic_evals/workflows/test_cohort_enrollment_*.py` (consumes `DiscoveryCallBookedV1`) |
| `comunify/backend/src/modules/comunify/agentic/tools/__init__.py` | All tests under `tests/agentic_evals/tools/` (re-export surface) |
| `comunify/backend/src/modules/comunify/agentic/tools/_exceptions.py` | All tests under `tests/agentic_evals/tools/` (shared error type) |

## Return contract

`done -> docs/product/stories/luana-comunify-bootstrap/T-tools-4-result.md`
