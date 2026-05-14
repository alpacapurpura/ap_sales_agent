---
ticket: T-be-8
story: luana-comunify-bootstrap
surface: BE
status: tests-passing
completed_at: 2026-05-14
---

# T-be-8 Result — API Layer (routes + DTOs + main.py + E2E tests)

## Deliverables

| Deliverable | Status | Path |
|---|---|---|
| All REST endpoints per 03-arch-be.md § 6 (37 stubs excl. webhooks) | DONE | `src/modules/comunify/api/routes.py` |
| 8 DTO modules (Pydantic v2, response_model=) | DONE | `src/modules/comunify/api/dtos/*.py` |
| `src/main.py` (FastAPI app + router mounts) | DONE | `src/main.py` |
| `tests/e2e/test_onboarding_creator_e2e.py` | DONE | `tests/e2e/test_onboarding_creator_e2e.py` |
| `tests/e2e/test_cross_tenant_isolation_e2e.py` | DONE | `tests/e2e/test_cross_tenant_isolation_e2e.py` |
| `T-be-8-impl-log.md` | DONE | `docs/product/stories/luana-comunify-bootstrap/T-be-8-impl-log.md` |

## Validators

| Validator | Result | Notes |
|---|---|---|
| V-NF-5 | PASS | `redirect_slashes=False` on app; `response_model=` on all endpoints |
| V-F-3 | PASS | Pydantic v2 `ConfigDict(from_attributes=True)`; no inner `class Config`; monetary fields have `currency: str \| None = None` |
| V-F-5 | PASS | 8 tests GREEN — onboarding journey O1-O8 (service layer + HTTP via ASGI) |
| V-F-11 | PASS | 9 tests GREEN — cross-tenant isolation I1-I9 (service + header contract) |

## Test Run Summary

```
.venv/bin/pytest tests/ -v --tb=short
240 passed, 9 skipped in 1.07s
(9 skipped = integration tests requiring live Postgres — expected)
```

## Key Design Decisions

- Two APIRouters: `router` (`/api/v1/comunify`) + `offer_router` (`/api/v1`) — per arch § 6.4 offer paths
- `redirect_slashes=False` set on FastAPI app (not router) — mandatory per DDD rule
- `_parse_tenant_id()` raises 422 on non-UUID header — validates at route boundary
- Stub routes return well-formed DTOs with `response_model=` enforced — PII gate satisfied
- Exception imports kept with `# noqa: F401` for T-be-10 wiring
- `httpx>=0.27` added to `pyproject.toml` (required for `ASGITransport` E2E pattern)

## Acceptance Criteria Check

- [x] All DTOs use Pydantic v2 `ConfigDict(from_attributes=True)`
- [x] Every endpoint has `response_model=` annotation
- [x] `X-Tenant-ID` header required on all endpoints
- [x] `FastAPI(redirect_slashes=False)` in `main.py`
- [x] `GET /subscriptions/metrics` placed before `GET /subscriptions/{id}` (routing order)
- [x] V-F-5 onboarding E2E test GREEN (8/8)
- [x] V-F-11 cross-tenant isolation E2E test GREEN (9/9)
- [x] Lint clean (0 errors), format clean
- [x] 240/240 tests pass (9 skipped integration — expected)
