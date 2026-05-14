---
ticket: T-be-4
title: "BE services Onboarding + ComplianceEvent + PiiScanner"
story: luana-vitalia-bootstrap
session: 4
iteration: 1
state: tests-passing
author: builder-backend (Sonnet)
date: 2026-05-13
---

# T-be-4 Implementation Log

## Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `backend-expert` | Mandatory per role step 0 — anti-patterns FastAPI/SQLA/tests/migrations | Read runtime-quality-checklist.md patterns: Annotated dep, best-effort writes, DI constructor pattern, structlog |
| `brand-expert` | Loaded per system prompt (invoking skills BEFORE code) | N/A — no brand surfaces in T-be-4 |
| `offer-expert` | Loaded per system prompt | N/A — no offer surfaces in T-be-4 |
| `tessl__fastapi` | Mandatory — async patterns, DI via Annotated | Used Annotated/Protocol pattern for IdempotencyStoreProtocol; response_model not applicable (services layer) |
| `tessl__pytest-api-testing` | Mandatory — test patterns with mocked repos | Used AsyncMock for repo.save, MagicMock for session, function-scoped fixtures, parametrize for PII categories |
| `tessl__graceful-degradation` | External calls pattern (audit log best-effort writes) | Applied: try/except catches ALL exceptions in ComplianceEventService.log_event, structlog.warning on failure — user flow never broken |

## Step 0 Anti-Duplication Gate

```bash
grep -rn "class.*OnboardingService\|class.*ComplianceEventService\|class.*PiiScannerService" \
  /home/chris/AISALESHT/backend/src/ /home/chris/luana-platform/ 2>/dev/null | grep -v __pycache__
# → (no output) — 0 matches. NEW services justified, NOT mirrors.

grep -rn "sanitize_payload" /home/chris/luana-platform/ 2>/dev/null | grep -v __pycache__
# → Found in luana_core_observability.recording.sanitization — CONSUMED, not re-implemented.
```

**Result:** All 3 service classes are new. `sanitize_payload` consumed from `luana_core_observability` (anti-duplication: EXTEND shared, NEVER mirror).

## Step 0.5 Default-Flip Detection

No `core/config.py` defaults touched. Not applicable.

## Scope Verification

T-be-4 touches business modules only:
- `/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/application/services/` (3 new files)
- `/home/chris/luana-platform/vitalia/backend/tests/unit/application/` (3 new test files)
- `/home/chris/luana-platform/vitalia/backend/tests/agentic_evals/smoke/smoke_pii_detection.py` (V-AE-2)

No copilot/sales_agent/frontend touched.

## TDD Order (Inside-Out)

Per `.claude/rules/tdd-mandatory.md` RED → GREEN → REFACTOR:

1. **RED**: Created all 3 test files FIRST (test_onboarding_service.py, test_compliance_event_service.py, test_pii_scanner_service.py). Confirmed ImportError (modules did not exist).
2. **GREEN**: Implemented PiiScannerService (stateless, simplest), then ComplianceEventService, then OnboardingService. Fixed RUT/DNI regex conflict (lookahead adjustment).
3. **REFACTOR**: ruff auto-fix + ruff format. No behavior changes.

## Decisions Made

### D1 (DDD inside-out)
- All services receive repos via constructor DI — no direct `AsyncSession` construction inside service body
- `OnboardingService(session, audit_repo, idempotency_store)` — session passed for ORM model flush
- `ComplianceEventService(audit_repo)` — pure repo DI, no session
- `PiiScannerService()` — stateless, no deps

### D7 (HIPAA-lite)
- `ComplianceEventService.log_event` calls `sanitize_payload(payload)` BEFORE creating `VitaliaMedicalAuditLogModel`
- Best-effort pattern: `except Exception as exc: logger.warning(...)` — NEVER re-raises

### Idempotency (A1 spec)
- `IdempotencyStoreProtocol` defined (typing.Protocol) — duck-typed interface
- Key: `vitalia:onboarding:{clerk_user_id}`, TTL: 1 second
- Cache hit → returns existing result with `is_new=False`, session.add NOT called
- Cache miss → creates new tenant, calls `session.add`, stores in idempotency store

### PII Scanner regex (A3 + V-AE-2)
- DNI_AR and RUT_CL share overlapping digit patterns
- Fixed: `dni_ar` lookahead `(?![\d.-])` excludes hyphen-suffix (prevents false-positive on RUT)
- `rut_cl` requires dots in format `\d{1,2}\.\d{3}\.\d{3}-[\dkK]` to avoid bare-number matches
- All 6 categories in `BLOCKING_CATEGORIES` — any detection triggers `blocked=True`

## Files Created

```
luana-platform/vitalia/backend/
  src/modules/vitalia/application/
    __init__.py
    services/
      __init__.py
      onboarding_service.py        # OnboardingService + CreateClinicProfileRequest + OnboardingResult + IdempotencyStoreProtocol
      compliance_event_service.py  # ComplianceEventService (best-effort) + utc_now helper
      pii_scanner_service.py       # PiiScannerService + PiiScanResult + BLOCKING_CATEGORIES
  tests/unit/application/
    __init__.py
    test_onboarding_service.py     # 5 tests (A1 idempotency + DI + DTO validation)
    test_compliance_event_service.py  # 6 tests (A2 never-raises + sanitize_payload + DI)
    test_pii_scanner_service.py    # 24 tests (A3 + V-F-14 + V-AE-2 unit coverage)
  tests/agentic_evals/smoke/
    __init__.py
    smoke_pii_detection.py         # 11 tests (10 PII cases + count sanity — V-AE-2)
```

## Cross-module reads

None (services are self-contained within vitalia module).

## Validators Passed

| Validator | Command | Result |
|---|---|---|
| V-F-2 | `pytest tests/unit/application/ -v` | 35/35 PASS |
| V-F-14 | covered by test_pii_scanner_service.py::test_offer_description_scan_blocks_on_pii | PASS |
| V-AE-2 | `pytest tests/agentic_evals/smoke/smoke_pii_detection.py -v` | 11/11 PASS |
| V-NF-1 (lint) | `ruff check ... --no-cache` | 0 errors |
| V-NF-2 (format) | `ruff format --check` | 10 files clean |
| Full unit suite | `pytest tests/unit/ -v` | 107/107 PASS |

## Acceptance Tests

| # | Test | Result |
|---|---|---|
| A1 | `test_onboarding_service.py::test_idempotency` | PASS |
| A2 | `test_compliance_event_service.py::test_never_raises` | PASS |
| A3 | `test_pii_scanner_service.py::test_detects_all_pii_categories` | PASS |

## Warnings

- `DeprecationWarning: There is no current event loop` in async tests using `asyncio.get_event_loop().run_until_complete()`. This is a Python 3.12 issue with sync test runner + async coroutines. The tests pass. For future sessions: prefer `asyncio_mode = "auto"` with `async def test_*` signatures (pytest-asyncio). Not breaking.
- `OnboardingService` uses a placeholder ORM object for `session.add()` in T-be-4 scope. Full `TenantModel` wiring (luana_core_iam.tenants FK) deferred to T-be-7/8 (API layer). Documented in service docstring.

## Partial flag §11 (CONTEXT-BRIEF.md not used — CONTRACT.md read directly)

N/A — no CONTEXT-BRIEF.md provided for this ticket. Read spec files directly per instructions.
