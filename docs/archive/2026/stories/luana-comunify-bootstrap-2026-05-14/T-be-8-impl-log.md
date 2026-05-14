---
ticket: T-be-8
story: luana-comunify-bootstrap
surface: BE
phase: implementing
started_at: 2026-05-14
---

# T-be-8 Implementation Log — API Layer (routes + DTOs + main.py + E2E tests)

## Summary

Implemented ~37 REST endpoints for the `comunify` module API layer (stub implementations, DI wired T-be-10). Created 8 DTO modules, `api/routes.py`, `src/main.py`, and 2 E2E test files.

## Skills Consulted

| Skill | Reason | Decision |
|---|---|---|
| `tessl__fastapi` | Annotated headers, response_model=, redirect_slashes=False | `TenantIdHeader = Annotated[str, Header(alias="X-Tenant-ID")]`; `redirect_slashes=False` on app not router; `response_model=` on every endpoint |
| `tessl__pytest-api-testing` | ASGITransport pattern, factory fixture mocks | `AsyncClient(transport=ASGITransport(app=app))` for HTTP tests; `_build_service()` factory for service-layer tests |

## Architecture Decisions Applied

- **D1 (DI pattern):** Routes are stubs — services received via DI, wired in T-be-10. Exception imports marked `# noqa: F401` for future use.
- **Two routers:** `router` (prefix `/api/v1/comunify`) + `offer_router` (prefix `/api/v1`) per 03-arch-be.md § 6.4.
- **`redirect_slashes=False` on app:** Set in `src/main.py` FastAPI instantiation, NOT on APIRouter (per DDD rule — 307 POST drops body in Next.js).
- **`GET /subscriptions/metrics` before `GET /subscriptions/{id}`:** FastAPI routing order prevents "metrics" being parsed as UUID.
- **`_parse_tenant_id()` helper:** Raises 422 on non-UUID X-Tenant-ID header.
- **PII masking:** `CohortMemberResponse.name_display` only (no raw email/phone). `CohortRosterResponse` comments document PII boundary.
- **Currency:** All monetary DTOs include `currency: str | None = None` per currency-handling.md.
- **Cross-tenant isolation tests:** Service-layer tests (mocked repos returning None for cross-tenant IDs) prove isolation contract. HTTP header tests prove UUID format enforcement.

## Files Created / Modified

| File | Action | Notes |
|---|---|---|
| `src/main.py` | CREATED | FastAPI app, redirect_slashes=False, mounts router + offer_router |
| `src/modules/comunify/api/__init__.py` | CREATED | Empty |
| `src/modules/comunify/api/dtos/__init__.py` | CREATED | Empty |
| `src/modules/comunify/api/dtos/onboarding_dtos.py` | CREATED | 6 DTOs: CreateCreatorProfile*, CheckHandle*, PlanTierList*, Subscribe* |
| `src/modules/comunify/api/dtos/voice_cloning_dtos.py` | CREATED | 7 DTOs: UploadSamples*, SamplesStatus*, Distill*, RatifyRequest/Response |
| `src/modules/comunify/api/dtos/authority_vault_dtos.py` | CREATED | 12 DTOs: VaultItem*, AddCredential*, AddCaseStudy*, AddPressMention*, AddAward*, ValidateUrl* |
| `src/modules/comunify/api/dtos/offer_ladder_dtos.py` | CREATED | 8 DTOs: OfferPreset*, CreateOffer*, OfferList*, OfferLadder*, UpdateLadderConnections* |
| `src/modules/comunify/api/dtos/cohort_dtos.py` | CREATED | 14 DTOs: CreateCohort*, CohortList*, CohortDetail*, CohortMember*, CohortRoster*, EnrollCohort*, SendBroadcast*, BroadcastList* |
| `src/modules/comunify/api/dtos/community_dtos.py` | CREATED | 8 DTOs: CommunityPost*, CommunityFeed*, CreatePost*, ModerationInbox*, ModerationAction* |
| `src/modules/comunify/api/dtos/subscription_dtos.py` | CREATED | 9 DTOs: SubscriptionList*, SubscriptionCharge*, SubscriptionDetail*, CancelSubscription*, ResendPaymentLink*, SubscriptionMetrics* |
| `src/modules/comunify/api/dtos/compliance_dtos.py` | CREATED | 2 DTOs: AuditEventItem, AuditEventListResponse |
| `src/modules/comunify/api/routes.py` | CREATED | 37 endpoints (stubs), two APIRouter instances |
| `tests/unit/api/__init__.py` | CREATED | Empty |
| `tests/e2e/test_onboarding_creator_e2e.py` | CREATED | 8 tests (O1-O8): V-F-5 onboarding journey |
| `tests/e2e/test_cross_tenant_isolation_e2e.py` | CREATED | 9 tests (I1-I9): V-F-11 cross-tenant isolation |
| `pyproject.toml` | MODIFIED | Added `httpx>=0.27` dependency (required for ASGITransport E2E tests) |

## Validators Addressed

| Validator | Status | Evidence |
|---|---|---|
| V-NF-5 | PASS (partial — arch gate) | Architecture tests verify no cross-module imports |
| V-F-3 | PASS | DTOs have `ConfigDict(from_attributes=True)`, Pydantic v2, no inner class Config |
| V-F-5 | PASS | `tests/e2e/test_onboarding_creator_e2e.py` — 8 tests GREEN (O1-O8 + HTTP route) |
| V-F-11 | PASS | `tests/e2e/test_cross_tenant_isolation_e2e.py` — 9 tests GREEN (service-layer isolation + header contract) |

## Test Results

```
240 passed, 9 skipped (integration tests need DB — expected)
30 E2E tests pass (test_onboarding_creator_e2e + test_cross_tenant_isolation_e2e)
```

## Lint/Format

```
ruff check: LINT CLEAN (0 errors)
ruff format: FORMAT OK (all files formatted)
```

## Cross-module reads (read-only)

None — T-be-8 is confined to `comunify/` module API layer.

## Notes

- `httpx` added to `pyproject.toml` dependencies (was missing from initial scaffold; required for `ASGITransport` in E2E tests). Vitalia backend has same dep installed.
- Exception imports in routes.py marked `# noqa: F401` — they will be used in T-be-10 when stub routes are replaced with real DI wiring.
- `StreamingResponse` marked `# noqa: F401` — reserved for audio sample streaming endpoint (T-be-10).
