# T-be-5 Impl Log — Cohort Services (CohortService + CohortBroadcastService)

## Ticket
**T-be-5**: Create CohortService (enroll_member + advisory lock + idempotency) + CohortBroadcastService (WhatsApp rate-limit pre-flight + dispatch + recipient tracking). 2 unit test files + 1 E2E enrollment test. Validators V-F-2, V-F-8, V-F-16.

## Skills Consulted

| Skill | Why invoked | Decision |
|---|---|---|
| `backend-expert` | Runtime quality checklist — anti-patterns FastAPI/SQLA/tests/migrations | DI constructor injection; no cross-module imports; structlog only; SQLA 2.0 select() |
| `tessl__fastapi` | Pydantic v2 ConfigDict, response_model | Applied `ConfigDict(from_attributes=True, extra="forbid")` on all input DTOs |
| `tessl__pytest-api-testing` | Fixture scoping, async test patterns, mock injection | asyncio_mode=auto; all `async def` tests; `AsyncMock` for repo + advisory_lock_fn |

## Step 0 — Default-flip detection
No changes to `core/config.py`. No flag flips. Step 0.5 N/A.

## R10 Anti-duplication grep
```bash
grep -rn "class CohortService\|class CohortBroadcastService" /home/chris/luana-platform/ 2>/dev/null
# → NO existing implementations found in any vertical pre-T-be-5
grep -rn "enroll_member\|send_broadcast" /home/chris/luana-platform/comunify/backend/src/ 2>/dev/null
# → No results (new surface)
```
Decision: cohort enrollment + broadcast are Comunify-specific (creator-economy group cohorts, WhatsApp tier quota). No duplication with Vitalia booking_service (medical slot + availability grid).

## Implementation

### Files created/modified

**New files:**
1. `src/modules/comunify/application/services/cohort_service.py` — CohortService + 3 exception classes + IdempotencyStoreProtocol + CreateCohortRequest/Result + EnrollMemberRequest/Result
2. `src/modules/comunify/application/services/cohort_broadcast_service.py` — CohortBroadcastService + BroadcastRateLimitError + SendBroadcastRequest/Result
3. `tests/unit/application/test_cohort_service.py` — 8 unit tests (RED→GREEN)
4. `tests/unit/application/test_cohort_broadcast_service.py` — 6 unit tests (RED→GREEN)
5. `tests/e2e/__init__.py` — empty package
6. `tests/e2e/test_cohort_enrollment_e2e.py` — 5 E2E tests (V-F-8)

**Modified files:**
7. `src/modules/comunify/infrastructure/repositories/cohort_broadcast_repository.py` — added `count_sent_today(tenant_id)` method (needed by CohortBroadcastService for rate-limit pre-flight)

### Key patterns applied

**CohortService — advisory lock injection:**
- `advisory_lock_fn: Callable[[uuid.UUID], Coroutine[Any, Any, bool]]` injected at construction
- Production: wraps `try_acquire_cohort_enrollment_lock(session, cohort_id)` from T-be-3
- Tests: `AsyncMock(return_value=True/False)` — no DB required for unit tests
- Lock not acquired → `CohortEnrollmentRaceError` (HTTP 409 in router)

**CohortService — idempotency:**
- `IdempotencyStoreProtocol` local Protocol (same pattern as vitalia booking_service, onboarding_service)
- Key: SHA-256 hex of `f"{cohort_id}:{subscriber_id}"`, TTL=86400s (24h per spec)
- Cache hit → return `EnrollMemberResult(is_idempotent_hit=True)` without DB write
- DB fallback: `find_by_cohort_and_subscriber()` → existing member also returns idempotent result

**CohortService — capacity routing:**
- `capacity_filled < capacity_max` → `status='active'`, `update_capacity(filled_delta=+1)`
- `capacity_filled >= capacity_max` → `status='waitlisted'`, `waitlist_position=capacity_waitlist+1`, `update_capacity(waitlist_delta=+1)`

**CohortBroadcastService — WhatsApp rate limit:**
- `_resolve_whatsapp_daily_limit()`: graceful degradation — returns `_DEFAULT_WHATSAPP_DAILY_LIMIT=1000` when PlanTierConfig not found or `whatsapp_daily_limit` attr absent
- `remaining <= 0` → `BroadcastRateLimitError(daily_limit, already_sent)` (HTTP 429)
- `remaining < len(members)` → partial delivery: dispatch `remaining`, queue rest, `status='partial'`
- Recipient records created for dispatched members only; `delivery_at` left null (populated by agentic callback per spec)

**count_sent_today:**
- Filter: `status IN ('sent', 'partial')` + `sent_at >= midnight UTC today` + `deleted_at IS NULL` + `tenant_id`
- Uses `func.count().select_from(Model).where(...)` — SQLA 2.0 scalar count pattern

### TDD flow
Tests written RED (all failing — service modules not yet created), then GREEN after implementation. `ruff format` applied after implementation.

## Validators status

| Validator | Command | Result |
|---|---|---|
| V-F-2 | `pytest tests/unit/application/ -v` | 70/70 PASS (includes 14 new) |
| V-F-8 | `pytest tests/e2e/test_cohort_enrollment_e2e.py -v` | 5/5 PASS |
| V-F-16 | `pytest tests/integration/test_cohort_enrollment_advisory_lock.py -v` | 4 SKIP (no Postgres) — tests exist from T-be-3 |
| V-NF-1 | `ruff check src/ tests/ --no-cache` | 0 errors |
| V-NF-1 format | `ruff format --check src/ tests/` | 0 files to reformat |

## Cross-module reads (read-only)
- `/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/application/services/booking_service.py` — advisory lock + idempotency Protocol pattern source
- `/home/chris/luana-platform/comunify/backend/src/modules/comunify/application/services/onboarding_service.py` — IdempotencyStoreProtocol pattern (T-be-4 precedent)
- `/home/chris/AISALESHT/backend/src/shared/idempotency/` — reviewed; chose local Protocol to avoid cross-repo dependency in luana-platform
- `/home/chris/luana-platform/comunify/backend/tests/integration/test_cohort_enrollment_advisory_lock.py` — confirmed V-F-16 already covered by T-be-3 integration tests
