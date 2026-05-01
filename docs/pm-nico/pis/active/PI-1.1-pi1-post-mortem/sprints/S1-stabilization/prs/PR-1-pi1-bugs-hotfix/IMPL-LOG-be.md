# IMPL-LOG-be — PR-1-pi1-bugs-hotfix (BE surface)

Builder: `nicolify-backend` (Sonnet)
Date: 2026-04-30
Iteration: 1

## Bug Fixed

### Bug #1 (BE side) — Contacts list returns 404 when path has no trailing slash

**Root Cause (CF Tunnel):**

CloudFlare Tunnel `dev-app.nicolify.com` strips trailing slash on GET requests:
```
curl https://dev-app.nicolify.com/api/v1/contacts/?limit=5
HTTP/2 308  location: /api/v1/contacts?limit=5
```

Then the no-slash URL hits BE. With `redirect_slashes=False` (mandatory CLAUDE.md rule — prevents 307 POST body drop in Next.js), and `@router.get("/")` only registering the slash path, `/api/v1/contacts` returns 404.

**Fix Applied:**

Dual-decorator pattern following `backend/src/modules/brand/api/buyer_personas.py:46-47` precedent:

```python
@router.get(
    "",
    response_model=PaginatedResponse[ContactListItem],
    summary="Listar contactos",
    description=...,
)
@router.get(
    "/",
    response_model=PaginatedResponse[ContactListItem],
    include_in_schema=False,
)
async def list_contacts(...): ...
```

- `""` is the canonical path (visible in OpenAPI docs at `/api/v1/contacts`)
- `"/"` is the hidden alias (handles clients sending trailing slash directly)
- `redirect_slashes=False` is NOT modified (inviolable rule)

## Files Modified

| File | Change |
|---|---|
| `backend/src/modules/crm/api/contacts.py` | Lines 211-227: changed `@router.get("/")` → dual decorator `@router.get("") + @router.get("/", include_in_schema=False)` |
| `backend/tests/modules/crm/test_contacts_api.py` | Added section 9: two regression tests for CF tunnel slash handling |

## Tests Written

Two new regression tests in `test_contacts_api.py` section 9:

```
test_list_contacts_no_slash_returns_200  — RED before fix, GREEN after
test_list_contacts_slash_still_returns_200  — GREEN before (alias still works)
```

Both verify `200` response with `items` + `total_count` in body.

## TDD Flow

1. Added tests before fix → RED: `test_list_contacts_no_slash_returns_200` failed (404)
2. Applied dual-decorator fix → GREEN: both tests pass
3. All 33 existing tests still pass (31 original + 2 new = 33 total)

## Quality Gates Output

### Ruff lint
```
All checks passed! (crm/ module)
```

### Ruff format
```
1 file already formatted
```

### Mypy strict
```
Success: no issues found in 1 source file (src/modules/crm/api/contacts.py)
```

### Pytest CRM module
```
82 passed, 16 warnings (all crm/ tests, including existing + new)
```

### Architecture fitness
```
10 failed (pre-existing, all from parallel PI-5 session ajenas to this PR):
- test_folder_naming.py::test_all_python_files_snake_case (copilot/_dependencies.py)
- test_master_data.py::test_no_new_usd_defaults
- test_chat_orchestrator_loc_ratchet.py
- test_sales_agent_system_prompt_order.py (x2)
- test_sales_agent_anchors.py
- test_ddd_boundaries.py::test_no_new_cross_module_imports
- test_copilot_anchors.py
- test_system_prompt_order.py (x2)

VERIFIED: Same 10 failures before my changes (git stash confirm). No new failures introduced.
```

### Smoke verify (live container)
```
curl http://localhost:8000/api/v1/contacts  → 401 (not 404) ✓
curl http://localhost:8000/api/v1/contacts/ → 401 (not 404) ✓
```
401 = auth-required = endpoint reachable (bug fixed). Pre-fix: 404.

## Cross-Codebase Audit — @router.get("/") without companion @router.get("")

Grep audit: all `@router.get("/")` in modules, checked for companion `@router.get("")`.

### Already correctly configured (dual-decorator)
| File | Status |
|---|---|
| `brand/api/buyer_personas.py` | `""` L46 + `"/"` L47 include_in_schema=False |
| `social_proof/api/authority.py` | both |
| `social_proof/api/placements.py` | both |
| `social_proof/api/team_members.py` | both |
| `social_proof/api/testimonials.py` | both |
| `crm/api/contacts.py` | **FIXED in this PR** |

### Pending follow-up (NOT fixed in this PR — scope creep prevention)

| File | Effective path | Risk | Priority |
|---|---|---|---|
| `assets/api/router.py:65` | TBD | Low (assets list — not in critical path) | P3 |
| `brand/api/avatars.py:21` | `/api/v1/brand/avatars/` | Medium (brand studio) | P2 |
| `iam/api/routers/tenant_router.py:15` | `/api/v1/iam/tenants/` | Low (admin-only) | P3 |
| `landing/api/landing.py:39` | `/api/v1/landing/` | Medium (landing list) | P2 |
| `scheduling/api/agenda.py:37` | `/api/v1/scheduling/agenda/` | Medium | P2 |
| `tenant_domains/api/domain_router.py:88` | `/api/v1/tenant-domains/` | Low | P3 |

PM: these 6 paths are follow-up items. CF tunnel affects GET list endpoints. Recommend P2 items (avatars, landing, agenda) get dual-decorator treatment in PI-3 or next hotfix.

## Exit criteria

- [x] API responds 401 (auth-required) at `/api/v1/contacts` without slash (not 404)
- [x] API responds 401 at `/api/v1/contacts/` with slash (unchanged)
- [x] Tests green (33 passed including 2 new regression tests)
- [x] Ruff + mypy 0 errors
- [x] No new architecture fitness failures
- [x] Audit cross-codebase complete (findings documented above)

## Decisions

- Only `list_contacts` gets dual-decorator in this PR. Other list endpoints in same file (`_filter-schema`, detail, journey, campaigns) use path segments after base so CF stripping does not affect them.
- `include_in_schema=False` on `"/"` keeps OpenAPI docs clean (single entry at canonical `""` path).
- Pattern strictly follows `buyer_personas.py` precedent (same project).
