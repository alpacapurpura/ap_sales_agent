# IMPL-LOG — PR-10-crm-contacts-api-forward-compat

> Owner: nicolify-backend (Sonnet) builder + PM main session (Opus 4.7) bug-resolution.

## Sub-deliverables shipped

| # | Deliverable | Status | Lines |
|---|---|---|---|
| 1 | `modules/crm/api/dto/contact_filters.py` (18 canonical fields) | ✅ | 119 |
| 2 | `modules/crm/api/dto/contacts.py` (4 DTOs: ListItem, Detail, Identity, Deferred) | ✅ | 153 |
| 3 | `modules/crm/application/services/contact_query_service.py` (2 methods + helpers) | ✅ | 554 |
| 4 | `modules/crm/api/contacts.py` (5 endpoints) | ✅ | 410 |
| 5 | `main.py` mount router `/api/v1` prefix + tenant dependency | ✅ | +6 |
| 6 | `tests/modules/crm/test_contacts_api.py` (31 integration sin mocks) | ✅ | 980 |
| 7 | `tests/architecture/test_contacts_filter_params_forward_compat.py` (2 arch tests ratchet) | ✅ | 54 |

Total: 2224 insertions across 7 files.

## EXTEND vs NEW decision (CONTRACT § 1)

NEW `/api/v1/contacts/` endpoint group. Justificación documentada en CONTRACT § 1:
- Scope semántico distinto al legacy `/leads/search` (limited POST)
- Source unificada: `CustomerProfileModel + LEFT JOIN LeadModel` (CDP pattern)
- Forward-compat: PI-3 expande sub-resources sobre `/contacts/{id}` sin breaking
- Cero deuda: legacy `/leads` minimal queda intact

## Filters implementados (18 canonical)

| Field | Mapping |
|---|---|
| lifecycle_stage_in | CustomerProfileModel.lifecycle_stage IN |
| score_min/max | CustomerProfileModel.lead_score BETWEEN |
| source_in | CustomerProfileModel.lead_source IN |
| has_email/phone | primary_email/phone IS NOT NULL |
| has_telegram_id/whatsapp_id/instagram_id/tiktok_id | EXISTS LeadModel.{col} NOT NULL |
| created_after/before | CustomerProfileModel.created_at |
| last_activity_after/before | CustomerProfileModel.last_activity_at |
| is_inactive | CustomerProfileModel.is_inactive |
| has_campaign_engagement | 2-step batch via CampaignsLookupPort (90d window) |
| country_in | EXISTS LeadModel.country IN |
| q | ILIKE OR(name, email, phone) |

## Bugs resueltos durante implementación

PM main session (Opus 4.7) resolvió tras builder Sonnet pause mid-fix:

| # | Bug | Fix |
|---|---|---|
| 1 | `ContactQueryServiceDep = Annotated[...]` type alias falla FastAPI dependency resolution con AsyncSession | Removido alias; inline `Annotated[ContactQueryService, Depends(...)]` per call site |
| 2 | Override fixture `_fake_svc(session: AsyncSession = None)` — `session` sin `Depends()` → FastAPI introspect AsyncSession como Pydantic field → 500 error | Removido session param (no usado en factory closure) |
| 3 | Tests `client_a` + `client_tenant_b` fixtures sobreescribían `app.dependency_overrides` globalmente, segundo wins → tenant A ve datos B | Refactor: single `app_with_overrides` fixture con `_fake_user(x_tenant_id: Header(...))`. Cada client httpx envía header propio |
| 4 | Stub 501 endpoints con `response: Response` param → 422 (mismo introspection issue) | Refactor: return `JSONResponse(status_code=501, headers={"Retry-After": "PI-3"})` directo |
| 5 | Tests `?created_after={iso}` raw f-string URL → `+00:00` interpretado como espacio, 400 invalid | Endpoint accepts `datetime` query type direct (FastAPI native parse). Tests usan `client.get(url, params={...})` httpx encoding |
| 6 | Helper `_apply_channel_exists` con `channel_col: Any` (ANN401 prohibido) | `noqa: ANN401` con justificación legacy SQLA Column |
| 7 | mypy strict reportó 9 errors por SQLA legacy `Column[T]` types | Targeted `# type: ignore` per line + `bool()` / `str()` casts donde aplica |

## Skill consultations

- backend-expert (FastAPI + SQLA 2.0 + Pydantic v2 strict patterns)
- nicolify-backend agent built initial scaffolding; PM Opus completó tras pause mid-fix

## Quality gates locales NATIVE (cd backend)

| Gate | Result |
|---|---|
| ruff check | ✅ All checks passed |
| ruff format | ✅ 6 files already formatted |
| mypy strict (4 source files PR-10) | ✅ Success: no issues |
| pytest integration | ✅ 31 passed |
| pytest arch | ✅ 2 passed |

Total: **33 tests verde nativo**.

## Architecture invariants verified

- ✅ Tenant isolation cada query (incluso get_by_id) — `WHERE tenant_id == :tid` PRIMER predicate
- ✅ response_model en cada endpoint (PII rule)
- ✅ SQLA 2.0 async (no `session.query()`)
- ✅ Pydantic v2 `ConfigDict(extra="forbid")` strict
- ✅ structlog (no print/logging)
- ✅ Spanish neutro LATAM en docstrings + descriptions
- ✅ Cross-module read via `CampaignsLookupPort` (NO import directo `modules/campaigns`)
- ✅ Cero migration
- ✅ Files M ajenos (PI-2 S4 PR-1 LLM config) NO TOCADOS

## Commits

- `c0cad8de` — `feat(crm): PR-10 contacts API forward-compat (S4 PI-1)`

## Surface entregada (consumible por PR-11)

API ready en `/api/v1/contacts/*`. FE PR-11 puede consumir directo via `fetchClient` (auto X-Tenant-ID).

DTOs Pydantic mirrored exactamente en TS PR-11 CONTRACT § 2 (`CONTACT_FILTER_FIELDS` arch test enforces).

---

<!-- @pm: PR-10 implement done. Tests verde nativo. Builder Sonnet paused mid-fix; PM main session completó. -->
