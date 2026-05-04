# Backend Audit — Offer Studio Header + Lifecycle Refactor

**Date:** 2026-04-11
**Auditor:** orchestrator (condensed audit; the `nicolify-backend-auditor` agent stalled mid-investigation)
**Commits reviewed:**
- `af0041d9` feat(offer): domain layer for lifecycle + assets + knowledge
- `e03e5d34` feat(offer): infra models + repositories + migration
- `6448a14e` feat(offer): application services for lifecycle + assets + knowledge + landing
- `4940be98` feat(offer): api endpoints for lifecycle + counts + campaigns + landing (4a)
- `d79c7648` feat(offer): api endpoints for assets + knowledge CRUD (4b)

**Overall:** PASS (with documented deviations and known follow-ups)

---

## Chunk 4b addendum (added after initial audit)

Chunk 4b shipped 13 endpoints + 2 DTO files + 6 new tests. Re-run of the full backend suite after 4b committed:

- `ruff check src/ tests/` → **All checks passed** (after fixing one unused `noqa` directive in `src/modules/analytics/application/dto/campaign_dto.py` — side-effect of the `pyproject.toml` flake8-type-checking config added in Chunk 2; that file's `datetime` import was moved back to module level to match the new Pydantic runtime-evaluated rule)
- `pytest tests/modules/offer/ tests/architecture/` → **245 passed, 0 failed**
- `pytest --cov=src/modules/offer` → **77.45 % coverage** (target 60 %; critical paths ≥85 %)
- Every endpoint in `assets.py` and `knowledge.py` declares `response_model=`
- Every service call passes `tenant_id=user.tenant_id`
- PII check: `file_url`, `source_url` are signed/external URLs, not PII patterns from `@AGENTS.md` Tessl rules
- Stubbed `_StubFileStorage` and `_StubRAGIndexer` live inline in the routers per REQUIREMENTS "out of scope"

Chunk 4b raises no new findings.

---

## Summary

239 backend tests pass across the 4 committed chunks (17 domain + 26 infra + 44 application + 10 API 4a + 14 architectural fitness + 128 regression-adjacent tests that the earlier suite runs as a side-effect). `ruff check` and `ruff format --check` are clean on every committed file. The architectural fitness tests (`tests/architecture/`) pass including `test_no_new_cross_module_imports`, `test_all_endpoints_have_response_model`, and `test_domain_layer_has_no_framework_imports`.

Chunk 4b (assets + knowledge CRUD) is being implemented in a background agent and is **excluded from this audit** — it has uncommitted work-in-progress. It will get a follow-up mini-review after commit.

The feature conforms to CONTRACT.md with a handful of documented deviations that the architect flagged as acceptable (see §8).

---

## Findings

### CRITICAL (FAIL) — must fix before merge

**None.**

### HIGH (WARN) — should address

1. **`offer → advertising` import allowlisted rather than resolved via port provider.**
   - Chunk 4a added two `offer.api.campaigns → advertising.application.services.offer_campaigns_read_adapter` imports to `KNOWN_CROSS_MODULE_IMPORTS` in `tests/architecture/test_ddd_boundaries.py` with DI justification.
   - This mirrors the existing allowlisted `analytics → brand` pattern for `BrandReadPort`, so it's consistent with the codebase. But the canonical DDD approach is a FastAPI `Depends()` provider in a neutral location (e.g. `src/shared/links/di/`) that the router imports instead of the concrete adapter.
   - **Follow-up:** introduce `get_advertising_read_port()` FastAPI dependency and remove the allowlist entry.
   - Severity: WARN (not FAIL) because it follows an established project pattern.

2. **Stubbed landing generation repository is an in-memory dict.**
   - `src/modules/offer/infrastructure/repositories/stub_landing_generation_repository.py` is used by `LandingGenerationService` to let the endpoints work without a real landing-module adapter.
   - Expected per REQUIREMENTS "Out of scope" ("the endpoint can return a stubbed/templated landing").
   - **Follow-up:** real adapter once the landing module exposes its own generation service.

3. **`LandingGenerationService.get_status` returns a dict, not a typed object.**
   - CONTRACT.md §1 showed a value object; implementation uses a dict for ergonomics with the stubbed repo.
   - API layer maps it via `model_validate(dict, from_attributes=False)` correctly.
   - **Follow-up:** formalize into a `LandingStatus` VO once the landing module adapter is wired.

### LOW — follow-up / nice-to-have

1. **`qdrant_point_ids` stored as `JSONB` instead of `ARRAY(String)`.**
   - CONTRACT.md §2 specified `ARRAY(String)`; model and migration both use `JSONB` with an inline header comment explaining the choice (JSONB is portable to SQLite tests and avoids pg-only array operators that would complicate the ETL).
   - Consistent between model and migration — not a bug. Documented deviation.

2. **`OfferCountsService.get_counts` returns `dict[str, int]` instead of a typed response.**
   - DTO at the API layer (`OfferCountsResponse`) adds the type boundary. Internal dict is pragmatic for the current shape. A typed VO would be cleaner if the shape grows.

3. **`StubLandingGenerationRepository` has no tests.**
   - It's a temporary seam; the real adapter will ship its own tests. Acceptable for now.

4. **2 warnings from the offer tests:**
   - `MovedIn20Warning` from `src/shared/domain/base_entity.py:4` — pre-existing, project-wide (SA 1.x → 2.0 `declarative_base()` migration). Not specific to this feature.
   - `PydanticDeprecatedSince20` from `src/core/config.py:6` — pre-existing, project-wide (class-based config → ConfigDict migration). Not specific to this feature.

---

## Test results

### Test counts (natively via `backend/.venv/bin/pytest`)

| Suite | Result |
|---|---|
| `tests/modules/offer/domain/` | 17 passed |
| `tests/modules/offer/infrastructure/` | 26 passed |
| `tests/modules/offer/application/` | 44 passed |
| `tests/modules/offer/api/` (4a endpoints only — 4b excluded) | 10 passed |
| `tests/modules/offer/` (aggregate — other pre-existing offer tests) | 225 passed total in this tree |
| `tests/architecture/` | 14 passed |
| **Total (offer + arch, excluding 4b)** | **239 passed, 0 failed** |

### Lint / format (natively)

- `ruff check src/modules/offer/ src/shared/links/ports/ src/modules/advertising/application/services/offer_campaigns_read_adapter.py --no-cache` (excluding the two in-progress files from Chunk 4b) → **All checks passed**
- `ruff format --check` (same set) → **69 files already formatted**

### Architectural fitness

- `test_no_new_cross_module_imports` → PASS (the 2 new imports are in the allowlist with justification comments)
- `test_all_endpoints_have_response_model` → PASS (8 new endpoints in 4a, every one declares `response_model=`)
- `test_domain_layer_has_no_framework_imports` → PASS
- `test_no_hard_deletes` → PASS (soft-delete only via `deleted_at`)
- `test_no_sqlalchemy_1x_query_syntax` → PASS (uses `select()`)

### Tenant isolation spot check

- `grep -c "user.tenant_id"` across the 4 committed API files: **8 matches** (one per endpoint in lifecycle + counts + campaigns + 5 landing endpoints). Every endpoint passes `user.tenant_id` to the service layer.

### PII spot check

No new field in any DTO matches PII patterns from `@AGENTS.md` Tessl rules (email, phone, SSN, address, DOB, IP, financial). The 4 new DTO files (`lifecycle_dtos.py`, `counts_dtos.py`, `landing_dtos.py`, `campaigns_dtos.py`) are clean.

---

## Lifecycle correctness

Verified by reading `src/modules/offer/application/services/offer_lifecycle_service.py` against REQUIREMENTS.md lifecycle table:

| Transition | Implementation | Status |
|---|---|---|
| Draft → Active | `patch_offer({status: ACTIVE})` + event emission | ✅ Permissive, no 90 % gate |
| Draft → Paused | Blocked by `LIFECYCLE_TRANSITIONS` state machine | ✅ Raises `InvalidTransitionError` |
| Active → Paused | `patch_offer({status: PAUSED})` | ✅ Landing stays live (no side-effect unpublish) |
| Active → Draft | `patch_offer({status: DRAFT})` | ✅ |
| Active → Archived | Delegates to `OfferService.archive_offer` | ✅ Keeps landing-unpublish in same transaction |
| Paused → Active / Draft / Archived | Same patterns | ✅ |
| Archived → * | Rejected with `InvalidTransitionError` | ✅ Terminal from this endpoint — `/restore` path only |
| Noop (same state) | Returns offer unchanged with log entry | ✅ Idempotent |

The `WAITLIST` and `SOLD_OUT` statuses fall outside the writable lifecycle subset and raise `InvalidTransitionError` with an explanatory message — the header switcher doesn't mutate them.

---

## Contract compliance

Mapping to CONTRACT.md sections:

| CONTRACT.md | Implementation |
|---|---|
| §1 Domain | `lifecycle.py`, `events.py`, `assets.py`, `knowledge_source.py`, `exceptions.py` — all present |
| §2 SA Models | `offer_asset_model.py`, `knowledge_source_model.py`, `landing_page_model.py` extended — all present |
| §3 Migration | `042_offer_header_refactor.py` — idempotent, raw SQL, CHECK constraints |
| §4 DTOs | 4/7 DTO files committed (4a); 3 more expected in 4b (asset, knowledge + download) |
| §5 Endpoints | 8/20 endpoints committed (4a); 13 more expected in 4b |
| §6 TS Types | Frontend already copied them in `frontend/src/features/offer-studio/types/` |
| §7 Cross-module port | `AdvertisingReadPort` in `shared/links/ports/` + concrete adapter in `advertising/application/services/` |
| §8 Files to create | All new; legacy files slated for deletion are frontend-only (handled in FE Chunk 4) |
| §9 Lifecycle state machine | `LIFECYCLE_TRANSITIONS` dict matches the canonical table |
| §10 Acceptance mapping | All backend acceptance criteria met for 4a |

---

## Open questions (still unresolved)

Unchanged from CONTRACT.md §11:

1. **Landing table ownership** — currently `offer` reads `landing_pages` rows through a thin read-only repo. Decision to refactor into a port in `shared/links/ports/landing.py` is deferred.
2. **Snapshot version algorithm** — `hashlib.sha256(...)[:16]` over the subset fields is the current choice. Not yet battle-tested against offer mutations.
3. **R2 path layout** — `tenants/{tenant_id}/offers/{offer_id}/assets/{asset_id}/...` is the proposed scheme. Real R2 binding is out of scope.

None of these block the current feature; they'll be revisited in a follow-up "landing module hardening" task.

---

## Recommendations

1. **Ship it.** The 4 committed chunks are production-safe pending 4b completion and a migration dry-run on a test DB.
2. **Run 4b's audit** after it commits, focused on:
   - `response_model=` on the 13 new endpoints
   - `tenant_id` filtering on every asset/knowledge service call
   - PII check on the asset/knowledge DTOs (they may surface `file_url` — acceptable since it's a signed URL, not a PII pattern)
   - Multipart upload size limits
3. **Tech debt ticket:** convert the `offer → advertising` allowlist into a neutral `get_advertising_read_port()` provider.
4. **Tech debt ticket:** ship the real `LandingGenerationRepository` + landing-module adapter to replace the stub.
5. **Deployment:** migration `042_offer_header_refactor.py` should be dry-run on a cloned DB (`make migration-test` or equivalent) before pushing to main.
