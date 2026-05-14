# T-be-5 Result — Cohort Services

## Status: DONE

## Artifacts

| File | Type | Notes |
|---|---|---|
| `src/modules/comunify/application/services/cohort_service.py` | Service | CohortService: enroll_member (advisory lock + idempotency + capacity routing) + create_cohort |
| `src/modules/comunify/application/services/cohort_broadcast_service.py` | Service | CohortBroadcastService: WhatsApp rate-limit pre-flight + dispatch + recipient tracking |
| `src/modules/comunify/infrastructure/repositories/cohort_broadcast_repository.py` | Repo (extended) | Added `count_sent_today(tenant_id)` |
| `tests/unit/application/test_cohort_service.py` | Unit tests | 8 tests — enroll_member + create_cohort |
| `tests/unit/application/test_cohort_broadcast_service.py` | Unit tests | 6 tests — send_broadcast rate-limit scenarios |
| `tests/e2e/__init__.py` | Package | New e2e test package |
| `tests/e2e/test_cohort_enrollment_e2e.py` | E2E tests | 5 tests — V-F-8 enrollment journey |

## Validator results

| Validator | Result | Detail |
|---|---|---|
| V-F-2 (unit tests) | 70/70 PASS | All unit tests green including 14 new |
| V-F-8 (E2E enrollment) | 5/5 PASS | Happy path, waitlist, idempotency, race, not-found |
| V-F-16 (advisory lock integration) | 4 SKIP | Tests exist from T-be-3; require Postgres |
| V-NF-1 (ruff lint) | 0 errors | `ruff check src/ tests/ --no-cache` |
| V-NF-1 (ruff format) | 0 files to reformat | `ruff format --check src/ tests/` |

## Key design decisions

- **Advisory lock injection**: `advisory_lock_fn: Callable` at construction (not hard-imported) — keeps unit tests DB-free
- **Local IdempotencyStoreProtocol**: avoids cross-repo dependency on AISALESHT shared idempotency module; same Protocol pattern as onboarding_service (T-be-4) and vitalia booking_service
- **WhatsApp default 1000/day**: graceful degradation when PlanTierConfig not found — broadcasts allowed, warning logged
- **Partial broadcast**: `min(remaining, member_count)` dispatched + `queue_count` tracked in result; `delivery_at` null until agentic callback (per spec § 3.5.B)
