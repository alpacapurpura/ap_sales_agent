# T-be-4 Impl Log — Application Services (Onboarding + ComplianceEvent + PiiScanner)

## Ticket
**T-be-4**: Create 3 application services + unit tests + V-F-17 integration tests.

## Skills Consulted

| Skill | Why invoked | Decision |
|---|---|---|
| `backend-expert` | Runtime quality checklist — anti-patterns FastAPI/SQLA/tests | Followed best-effort write pattern, lazy sanitize_payload import, DI constructor injection |
| `tessl__fastapi` | Pydantic v2 ConfigDict, response_model mandatory | Applied throughout service layer |
| `tessl__pytest-api-testing` | Fixture scoping, async test patterns | asyncio_mode=auto; all async def tests; fixtures properly scoped |

## Step 0 — Default-flip detection
No changes to `core/config.py`. No flag flips. Step 0.5 N/A.

## R10 Anti-duplication grep
```bash
grep -rn "PiiScannerService\|ComplianceEventService\|OnboardingService" /home/chris/luana-platform/comunify/backend/src/ 2>/dev/null
# → NO existing implementations found in comunify module pre-T-be-4
grep -rn "class PiiScannerService\|class ComplianceEventService" /home/chris/luana-platform/ 2>/dev/null
# → Found in luana-platform/vitalia — PATTERN SOURCE (not duplicate; vertical-specific implementations)
```
Decision: Vitalia services are vertical-specific (medical PII, HIPAA surfaces). Comunify services are creator-economy specific (offer descriptions, testimonials, voice samples, LATAM national IDs). Not duplicates — same pattern, distinct domains.

## Implementation

### Files created
1. `src/modules/comunify/application/__init__.py` — empty package
2. `src/modules/comunify/application/services/__init__.py` — empty package
3. `src/modules/comunify/application/services/pii_scanner_service.py` — PiiScannerService + PiiScanResult + BLOCKING_CATEGORIES
4. `src/modules/comunify/application/services/compliance_event_service.py` — ComplianceEventService + local sanitize_payload wrapper
5. `src/modules/comunify/application/services/onboarding_service.py` — OnboardingService + ALLOWED_NICHES + ALLOWED_PLAN_TIERS + 3 exception classes
6. `tests/unit/__init__.py` — empty package
7. `tests/unit/application/__init__.py` — empty package
8. `tests/unit/application/test_pii_scanner_service.py` — 19 tests + parametrize (C1-C13)
9. `tests/unit/application/test_compliance_event_service.py` — 8 tests (B1-B5)
10. `tests/unit/application/test_onboarding_service.py` — 24 tests (A1-A6)
11. `tests/integration/test_pii_scanner.py` — 6 integration tests (V-F-17 part 1)
12. `tests/integration/test_voice_samples_pii_sanitized.py` — 8 integration tests (V-F-17 part 2)

### Key patterns applied

**PiiScannerService:**
- `_PATTERN_SPECS` dict with 6 compiled regexes: email, phone (intl +CC), dni_ar, rut_cl, rfc_mx, curp_mx
- `BLOCKING_CATEGORIES` frozenset — all 6 categories are blocking
- `PiiScanResult` frozen dataclass: `detected`, `masked_text`, `needs_review`, `blocked` (alias)
- 3 convenience methods: `scan_offer_description()`, `scan_testimonial()`, `scan_voice_sample()`
- Email regex fix: negative lookahead `(?![a-zA-Z0-9])` (not `(?![a-zA-Z0-9.])`) — trailing period in sentences was blocking email detection

**ComplianceEventService:**
- Local `sanitize_payload()` wrapper: lazy try-import from `luana_core_observability`, fallback = truncate >4000 chars
- `log_event()` wraps `try/except Exception` + `structlog.warning` — NEVER raises
- DI: `__init__` receives `audit_repo: CommunityAuditLogRepository`

**OnboardingService:**
- `ALLOWED_NICHES` frozenset (20 creator-economy LATAM niches)
- `ALLOWED_PLAN_TIERS` frozenset: `{"creator", "pro", "agency"}`
- `DuplicateHandleError`, `InvalidNicheError`, `InvalidPlanTierError` domain exceptions
- Idempotency TTL = 1 second (spec § 4.2)
- Validation order: idempotency → niche → plan_tier → handle_uniqueness → persist

### Bug found and fixed during testing
Email regex `(?![a-zA-Z0-9.])` used `.` in negative lookahead — caused emails followed by sentence-ending period (`"x@y.com."`) to NOT be detected. Fixed by removing `.` from negative lookahead: `(?![a-zA-Z0-9])`.

## Validators status

| Validator | Command | Result |
|---|---|---|
| V-F-2 | `pytest tests/unit/application/` | 51/51 PASS |
| V-F-17 | `pytest tests/integration/test_pii_scanner.py tests/integration/test_voice_samples_pii_sanitized.py` | 14/14 PASS |
| V-NF-1 | `ruff check src/ tests/ --no-cache` | 0 errors |
| V-AE-25 | `pytest tests/architecture/` | 17/17 PASS |

## Cross-module reads (read-only)
- `/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/application/services/compliance_event_service.py` — pattern source
- `/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/application/services/pii_scanner_service.py` — pattern source
- `/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/application/services/onboarding_service.py` — pattern source
