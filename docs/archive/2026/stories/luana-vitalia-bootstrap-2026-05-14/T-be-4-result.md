---
ticket: T-be-4
title: "BE services Onboarding + ComplianceEvent + PiiScanner"
story: luana-vitalia-bootstrap
session: 4
state: tests-passing
verdict: GREEN
date: 2026-05-13
---

# T-be-4 Result

## Status: tests-passing (GREEN)

## Acceptance Tests

| # | Acceptance criteria | Test | Result |
|---|---|---|---|
| A1 | OnboardingService idempotent same clerk_user_id within 1s | `test_onboarding_service.py::test_idempotency` | PASS |
| A2 | ComplianceEventService never raises on persist failure | `test_compliance_event_service.py::test_never_raises` | PASS |
| A3 | PiiScannerService detects AR DNI / CL RUT / MX RFC / email / phone | `test_pii_scanner_service.py::test_detects_all_pii_categories` | PASS |

## Validator Results

| Validator | Description | Result |
|---|---|---|
| V-F-2 | Application services unit tests with mocked repos | 35/35 PASS |
| V-F-14 | PII scanner — offer description + testimonial inputs | PASS (via unit tests) |
| V-AE-2 | 10 PII inputs detected (AR DNI / CL RUT / MX RFC / email / phone) | 11/11 PASS |
| V-NF-1 | ruff check 0 errors | PASS |
| V-NF-2 | ruff format clean | PASS |

## Commands Run

```bash
# V-F-2 (unit application tests)
cd /home/chris/luana-platform/vitalia/backend && .venv/bin/pytest tests/unit/application/ -v --tb=short
# → 35 passed in 0.29s

# V-AE-2 (agentic eval smoke — PII detection)
cd /home/chris/luana-platform/vitalia/backend && .venv/bin/pytest tests/agentic_evals/smoke/smoke_pii_detection.py -v
# → 11 passed in 0.03s

# Full unit suite regression check
cd /home/chris/luana-platform/vitalia/backend && .venv/bin/pytest tests/unit/ -v --tb=short
# → 107 passed in 0.33s

# Lint
cd /home/chris/luana-platform/vitalia/backend && .venv/bin/ruff check src/modules/vitalia/application/services/ tests/unit/application/ tests/agentic_evals/smoke/ --no-cache
# → All checks passed!

# Format
cd /home/chris/luana-platform/vitalia/backend && .venv/bin/ruff format --check src/modules/vitalia/application/services/ tests/unit/application/ tests/agentic_evals/smoke/
# → 10 files already formatted
```

## Files Delivered

### Source (luana-platform)
- `vitalia/backend/src/modules/vitalia/application/__init__.py`
- `vitalia/backend/src/modules/vitalia/application/services/__init__.py`
- `vitalia/backend/src/modules/vitalia/application/services/onboarding_service.py`
- `vitalia/backend/src/modules/vitalia/application/services/compliance_event_service.py`
- `vitalia/backend/src/modules/vitalia/application/services/pii_scanner_service.py`

### Tests (luana-platform)
- `vitalia/backend/tests/unit/application/__init__.py`
- `vitalia/backend/tests/unit/application/test_onboarding_service.py`
- `vitalia/backend/tests/unit/application/test_compliance_event_service.py`
- `vitalia/backend/tests/unit/application/test_pii_scanner_service.py`
- `vitalia/backend/tests/agentic_evals/smoke/__init__.py`
- `vitalia/backend/tests/agentic_evals/smoke/smoke_pii_detection.py`

### Docs (AISALESHT)
- `docs/product/stories/luana-vitalia-bootstrap/T-be-4-impl-log.md`
- `docs/product/stories/luana-vitalia-bootstrap/T-be-4-result.md`

## Key Design Decisions

1. **PiiScannerService**: Stateless synchronous hot-path service. Regex patterns derived from shared AISALESHT `_pii_patterns.py` catalog but compiled locally for performance. Fixed RUT/DNI conflict: `dni_ar` lookahead `(?![\d.-])` prevents matching when followed by hyphen (RUT suffix).

2. **ComplianceEventService**: Best-effort writes — `except Exception` catches ALL failures, structlog.warning logs them, user flow never interrupted. `sanitize_payload` from `luana_core_observability` called BEFORE any persist.

3. **OnboardingService**: `IdempotencyStoreProtocol` (typing.Protocol) for duck-typed idempotency store — tests use MagicMock, production uses Redis-backed store. Cache hit returns `is_new=False` with NO `session.add` call (verified by test).

4. **T-be-4 scope boundary**: `OnboardingService._build_tenant_placeholder()` creates a lightweight placeholder for `session.add()` call. Full `TenantModel` (luana_core_iam.tenants FK) wired in T-be-7/8. This is deliberate — T-be-4 scope is services layer only.

## Warnings / Notes

- `DeprecationWarning: There is no current event loop` in 2 async tests using sync `asyncio.get_event_loop().run_until_complete()`. Passes cleanly. Future tickets: use `async def test_*` with pytest-asyncio `asyncio_mode = "auto"`.
- V-F-14 full integration test (`tests/integration/test_pii_scanner.py`) deferred — that validator requires live Postgres (integration marker). The unit-level coverage in `test_pii_scanner_service.py` satisfies the functional validation for T-be-4.

## Next Ticket

T-be-5: `BookingService` + advisory locks + idempotency (depends on T-be-4).
