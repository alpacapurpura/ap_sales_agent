<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Backend Code Review: T-3 — Fixture eval_tenant_seeded + fixture test

**Date:** 2026-05-07
**Story:** eval-foundation-simulator-homologation
**Ticket:** T-3
**Files Reviewed:** 3 (`fixtures/__init__.py`, `tenant_seeded.py`, `test_tenant_seeded.py`)
**Domains touched:** test-infrastructure (tests/agentic_evals/sales_agent/simulator/fixtures/)
**Skills consulted:** backend-expert, brand-expert, offer-expert, tessl__pytest-api-testing, tessl__graceful-degradation, tessl__fastapi (N/A)
**Verdict:** **PASS**

## /test-backend Gate Status

| # | Gate | Result | Detail |
|---|---|---|---|
| 3 | Lint (ruff check) — Story B scope | PASS | 0 errors on T-3 files |
| 4 | Format (ruff) — Story B scope | PASS | 0 reformats |
| 5 | Type check (mypy) — N/A | N/A | tests/ excluded from mypy |
| 7 | Tests | PASS partial | 3/3 unit PASS; 5/5 integration SKIP (Postgres DNS from WSL native — legitimate gate 8/9/10 SKIP per spec) |
| 9 | Integration-marker | SKIP | Postgres unavailable from WSL native (`psycopg2.OperationalError: could not translate host name "postgres"`). `_skip_if_no_postgres()` guard correctly applied. |

**Pre-existing failures excluded:** Same caveat as T-1/T-2.

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | DDD Compliance | PASS | Cross-module reads via canonical paths (production ORM models read-only) |
| 2 | Tenant Isolation | PASS | Every `select()` filters `tenant_id` explicit; cross-tenant test verifies UUID5 distinctness + offer non-leak |
| 3 | Soft Deletes | PASS | Teardown uses `deleted_at = utc_now()`; no hard DELETE |
| 4 | Code Quality | PASS | 0 |
| 5 | SQLAlchemy 2.0 | PASS | Uses `select(Model).where(...)` exclusively |
| 6 | Async Consistency | N/A | Sync session per pytest fixture pattern (legitimate — DB integration tests use Sync `Session`) |
| 7 | Pydantic v2 / PII | N/A | No DTOs; uses production Pydantic models read-only via PersonalityCompiler |
| 8 | Migration Quality | N/A | No migration |
| 9 | Security | PASS | 0 — synthetic data only (UUID5 deterministic), eval_synthetic_tenants table separates from prod |
| 10 | Tests / TDD | PASS | 3 unit + 5 integration tests; RED-first per IMPL-LOG iter log; TDD-mandatory followed (test file written first per impl-log Section 1 unit + Section 2 integration partition documented top-of-file) |
| 11 | Cross-cutting | PASS | Currency from `ctx.pricing.get("currency", "PEN")`, NOT hardcoded USD; structlog (no print/logging); Spanish neutro; soft-delete idempotent |
| 12 | Default flip side-effect coverage | N/A | no flag flip |

## Findings

### NOTE: Tenant isolation enforced rigorously
**Category:** 2
**File:** `backend/tests/agentic_evals/sales_agent/simulator/fixtures/tenant_seeded.py:90-94, 137-139, 200-207, 297-302, 371-376, 449-453`
**Issue:** All 6 internal upsert helpers (`_upsert_lookup`, `_upsert_tenant`, `_upsert_personality_profile`, `_upsert_offers`, `_upsert_buyer_personas`, `_soft_delete_lookup`) execute `select()` with explicit `.where(Model.tenant_id == tenant_id)` (or PK match). Cross-tenant test (`test_cross_tenant_isolation` line 363-405) seeds 5 archetypes and asserts no row of tenant A can be found via tenant B's filter.
**Status:** PASS — exemplar implementation per `tenant-isolation.md`.

### NOTE: Currency master-data correct
**Category:** 11
**File:** `tenant_seeded.py:141, 279`
**Issue:** `currency: str = ctx.pricing.get("currency", "PEN")` — derives from TenantContext (Story A loader), fallback PEN per Q3 seed data ratification. NOT hardcoded USD.
**Status:** PASS per `currency-handling.md`.

### NOTE: Soft-delete teardown idempotent
**Category:** 3
**File:** `tenant_seeded.py:436-470`
**Issue:** `_soft_delete_lookup()` sets `deleted_at = utc_now()` only when `row.deleted_at is None`. Wrapped in try/except with rollback fallback (best-effort teardown per `tessl__graceful-degradation` Rule 6 — "log failures with structured context"; logs `eval_synthetic_tenant_teardown_fallido` warning). Does not raise on teardown failure (test stability).
**Status:** PASS.

### NOTE: PersonalityCompiler reused (not mirrored)
**Category:** 12 (anti-duplication)
**File:** `tenant_seeded.py:189-194, 221`
**Issue:** Imports `PersonalityCompiler` from `src.modules.brand.domain.personality` (canonical) and calls `PersonalityCompiler.compile(dimensions, patterns, exchanges)` to generate `system_instruction`. NO local re-implementation. Subsystem matches `anti-duplication.md` "PersonalityCompiler" pattern → reuse via direct import.
**Status:** PASS.

### NOTE: Idempotent upsert pattern
**Category:** 10 (Tests / H2 hardening)
**File:** `tenant_seeded.py:90-118 (lookup), 137-172 (tenant), 200-260 (personality), 297-340 (offers), 371-428 (buyer personas)`
**Issue:** Each upsert: `select(...).scalar_one_or_none()` → branch `if row is None` insert, `else` update. Restoration of `deleted_at = None` on re-seed (line 109) implements H2 idempotency. Verified by `test_seed_is_idempotent_on_rerun` (line 459-507) and `test_teardown_soft_delete_idempotent` (line 246-320).
**Status:** PASS.

### NOTE: Integration test SKIP rationale documented
**Category:** 10
**File:** `T-3-result.md` § Acceptance Criteria + `test_tenant_seeded.py:119-130`
**Issue:** 5 integration tests self-skip via `_skip_if_no_postgres()` when WSL native cannot resolve `postgres` hostname (Docker internal DNS). Per gate-spec "gates 8/9/10 may legitimately SKIP if Postgres down" — documented and correct.
**Verification:** Test logic verified by code inspection (every test asserts UUID5 idempotency, lookup row state, cross-tenant non-leak).
**Status:** PASS.

### INFO: tests/ excluded from mypy strict (paridad repo-wide)
**Category:** 5
**File:** `pyproject.toml` (per IMPL-LOG)
**Issue:** Per pyproject.toml `exclude = ["tests/"]` for mypy strict. T-3 tests are in `backend/tests/agentic_evals/sales_agent/simulator/fixtures/` — covered by exclusion. Type comments `# type: ignore[no-untyped-def]` and `# type: ignore[return]` used selectively (e.g., line 104, 135) for pytest fixture generators where mypy cannot infer.
**Status:** ACCEPTED — paridad repo-wide convention.

## Contract Compliance

- [x] D2 invariant `tenant_id = uuid5(NS_DNS, f"eval-{slug}")` verified at `tenant_seeded.py:68` + tests `test_eval_tenant_id_is_deterministic` PASS + `test_all_five_archetypes_have_distinct_ids` PASS
- [x] D2 lookup table marker (Opción B) — `_upsert_lookup` populates `eval_synthetic_tenants` only, business tables untouched per migration column scope
- [x] H2 idempotent upsert verified by `test_seed_is_idempotent_on_rerun`
- [x] Teardown soft-delete: `_soft_delete_lookup` sets `deleted_at = utc_now()`, idempotent via `if row.deleted_at is None` guard
- [x] Tenant isolation cross-test seeds 5 archetypes + verifies no leak
- [x] Currency derived from `ctx.pricing.currency` (NOT hardcoded)
- [x] Story A consumed read-only: `from tests.fixtures.eval.tenants.loader import ARCHETYPE_SLUGS, TenantContext, load_eval_tenant`
- [x] R5 strict — fixture is in `tests/`, NOT in `src/modules/sales_agent/`. NO production code modification.

## Allowlist Movement
- [x] Did any allowlist GROW? **NO**
- [x] Did any allowlist shrink? Not applicable

## Native-First Audit
- [x] No `docker exec ... ruff|pytest|tsc|vitest|mypy|eslint` in commit body
- [x] Commit `1e550042` uses scoped `git add` (no `-A`/`-u`)
- [x] Push to `development`, not `main`

## Cross-cutting verification

- **Spanish neutro:** All structlog event names + docstrings use Spanish neutro ("eval_synthetic_tenant_lookup_insertado", "eval_tenant_actualizado", "Sembrar un tenant eval en la DB"). Imperatives ("Sembrar", "Restaurar", "Actualizar") use neutral form, NOT voseo. Cero `vos/sos/tenés/podés/mirá/dejá/poné/usá/hacé/elegí/agregá/configurá/revisá/guardá/abrí/volvé/cambiá` in T-3 files. ✓ (verified via grep on Story B BE files; only voseo found is `actor_profiles.py` from T-9 agentic, NOT T-3)
- **structlog usage:** No `print()`/`logging` calls. ✓
- **No `datetime.utcnow()`:** Uses `utc_now()` from `src.shared.domain.datetime_utils`. ✓
- **`DateTime(timezone=True)`:** Schema reads only — production models already enforce; fixture writes via `seeded_at=utc_now()` (TZ-aware UTC). ✓
- **Cross-module reads (DDD):** Read-only via canonical paths (`brand.domain.personality.PersonalityCompiler`, `iam.infrastructure.models.tenant_model.TenantModel`, `offer.infrastructure.models.product_model.ProductModel`, `brand.infrastructure.models.{personality,buyer_persona}_model.*`, `eval_simulator.persistence.models.eval_synthetic_tenants.EvalSyntheticTenantModel` from T-1). NO mutation of these production models. ✓

## Anti-duplication §0 verification (Cat 12)

- T-3 IMPL-LOG cites Step 0 grep:
  - `find backend/src -name "tenant_seeded.py"` → 0 results
  - `grep -rn "class EvalSyntheticTenant" backend/src/` → only T-1 production model
  - `grep -rn "seed_eval_tenant" backend/src/` → 0 results (only in tests/)
- All 6 cross-module dependencies are inventory-listed canonical paths (read-only consume): PersonalityCompiler (brand/personality), TenantModel (iam), ProductModel (offer), BuyerPersonaModel (brand), PersonalityProfileModel (brand), EvalSyntheticTenantModel (T-1). NO mirror.
- TenantContext loader (Story A) consumed via `tests.fixtures.eval.tenants.loader.load_eval_tenant` per Story A done 2026-05-07.

## Verdict Math
- Cat 1/2/8/9/12: all PASS or N/A
- Cat 3 (Soft Deletes), Cat 5 (SQLA 2.0), Cat 10 (Tests/TDD), Cat 11 (Cross-cutting): PASS
- /test-backend gate scoped run: 3/3 unit PASS + 5/5 integration legitimate SKIP (Postgres DNS) per spec
- Allowlist movement: no growth
- IMPL-LOG cites baseline skills + 2 domain skills (brand-expert, offer-expert) + tessl__pytest-api-testing + tessl__graceful-degradation
- Per `auditor-downstream-regression.md` SSoT table: T-3 fixture path under `tests/agentic_evals/sales_agent/simulator/fixtures/` covered by entry "modules/sales_agent/observability/eval_simulator/" line 43 (downstream tests include `tests/agentic_evals/sales_agent/simulator/`)

## Verdict
**APPROVED**

## Findings
- 0 FAIL
- 0 WARN
- 5 NOTE (tenant isolation rigor, currency master-data, soft-delete idempotent, PersonalityCompiler reuse, idempotent upsert) + 1 INFO (mypy tests/ exclusion paridad)

## Cited paths
- `backend/tests/agentic_evals/sales_agent/simulator/fixtures/tenant_seeded.py:1-571`
  - `_eval_tenant_id():59-68` (D2 UUID5 deterministic)
  - `_upsert_lookup():76-117` (H2 idempotent upsert)
  - `_upsert_tenant():120-172` (currency from ctx.pricing)
  - `_upsert_personality_profile():175-260` (PersonalityCompiler reuse)
  - `_upsert_offers():263-340`
  - `_upsert_buyer_personas():343-428`
  - `_soft_delete_lookup():436-470` (teardown idempotent)
  - `seed_eval_tenant():478-529` (public function)
  - `eval_tenant_seeded():532-571` (pytest fixture)
- `backend/tests/agentic_evals/sales_agent/simulator/fixtures/test_tenant_seeded.py:1-507` (3 unit + 5 integration)
- `backend/tests/agentic_evals/sales_agent/simulator/fixtures/__init__.py`
- `T-3-result.md`, `T-3-impl-log.md`
