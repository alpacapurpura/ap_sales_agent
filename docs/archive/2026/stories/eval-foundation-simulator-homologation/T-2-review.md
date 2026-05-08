<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Backend Code Review: T-2 — Migration test + arch fitness gate eval_simulator_observability_invariants

**Date:** 2026-05-07
**Story:** eval-foundation-simulator-homologation
**Ticket:** T-2
**Files Reviewed:** 2 (1 migration test + 1 arch fitness gate)
**Domains touched:** test-infrastructure (production_code=false), arch fitness ratchet
**Skills consulted:** backend-expert, tessl__pytest-api-testing, brand-expert/offer-expert/metrics-expert (N/A per IMPL-LOG)
**Verdict:** **PASS**

## /test-backend Gate Status

| # | Gate | Result | Detail |
|---|---|---|---|
| 3 | Lint (ruff check) — Story B scope | PASS | 0 errors on T-2 files |
| 4 | Format (ruff) — Story B scope | PASS | 0 reformats |
| 5 | Type check (mypy) — N/A | N/A | tests/ excluded from mypy strict (pyproject.toml `exclude = ["tests/"]`) |
| 6 | Arch fitness | PASS | 43/43 PASS in `test_eval_simulator_observability_invariants.py` (verified locally 2026-05-07) |
| 7 | Tests | PASS | 38/38 PASS in `test_extend_eval_simulator_observability.py` (verified locally) |
| 10 | Migration idempotency clone | PASS via T-2 itself — `TestUpgradeIdempotency` (3 tests) verifies `IF NOT EXISTS` semantics by simulating double upgrade |

**Pre-existing failures excluded:** Same caveat as T-1. Pre-existing `test_arch_fitness_performance_budget` flake (timing-sensitive) is documented in T-2 IMPL-LOG, NOT a T-2 regression.

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | DDD Compliance | N/A | test-infra |
| 2 | Tenant Isolation | PASS | T-2 enforces tenant_id NOT NULL invariant via `TestTenantIsolation` 5 tests |
| 3 | Soft Deletes | N/A | test-infra |
| 4 | Code Quality | PASS | 0 |
| 5 | SQLAlchemy 2.0 | N/A | test-infra reads model file content via Path.read_text |
| 6 | Async Consistency | N/A | sync test bodies |
| 7 | Pydantic v2 / PII | N/A | no DTOs |
| 8 | Migration Quality | PASS | T-2 enforces invariants — `TestRevisionMetadata`, `TestUpgradeIdempotency` |
| 9 | Security | PASS | 0 — patches `op.execute` with side-effect collector, no live DB |
| 10 | Tests / TDD | PASS | TDD-mandatory: T-2 lands tests for T-1 deliverable; RED→GREEN evidence in IMPL-LOG iter log |
| 11 | Cross-cutting | PASS | 0 |
| 12 | Default flip side-effect coverage | N/A | no flag flip |

## Findings

### NOTE: TDD evidence — RED tests after GREEN code (T-1 → T-2 ordering)
**Category:** 10
**File:** `T-2-impl-log.md` § Iteration log
**Issue:** T-2 lands tests post-T-1 schema commit. Per `tdd-mandatory.md` § "feature existente sin tests: baseline (comportamiento actual) → RED cambio → GREEN", this is acceptable when test-infrastructure follows production code in same story (sequential tickets in `06-tickets.yaml`).
**Fix:** No fix required. T-2 acts as baseline-RED-GREEN: tests added codify migration 125 invariants, ratchet pattern shrink-only.
**Skill ref:** `tdd-mandatory.md` § "Aplica" — tests-first applies to **feature implementation**; arch fitness gates and migration regression tests legitimately follow when codifying invariants.

### NOTE: Architecture fitness — 43 ratchet tests with ZERO allowlist
**Category:** 6 (arch fitness)
**File:** `backend/tests/architecture/test_eval_simulator_observability_invariants.py`
**Issue:** Gate uses 7 test classes. NO allowlists added — pure ratchet (every assertion is a hard contract). Confirmed by inspection: no `KNOWN_*` constant, no skip markers.
**Status:** Pattern correct per `architectural-fitness.md` § "ratchet pattern — `KNOWN_*` allowlists shrink only"; not-applicable since gate has no allowlist.

### NOTE: Migration test pattern paridad existing precedent
**Category:** 8
**File:** `backend/tests/migrations/test_extend_eval_simulator_observability.py`
**Issue:** Pattern follows `tests/migrations/test_119_llm_eval_gate.py` (importlib.util module load + `patch.object(module.op, "execute", side_effect=executed.append)` collector). Idiomatic for migration tests without live DB.
**Status:** PASS.

## Contract Compliance (test-infrastructure surface)

- [x] Migration test (38 tests) covers: revision metadata × 2, table creation × 4 (3 explicit + 1 count assertion), index creation × 8 (7 expected indexes + count), schema shape × 10, idempotency × 3, downgrade × 5, spec registration × 6
- [x] Arch fitness gate (43 tests) covers: spec registration × 5, ORM models exist × 6, eval_metadata JSONB × 4, tenant isolation × 5, timestamp timezone × 5, campaign parity × 14 (10 fields + 4 extras), R5 schema-mirror boundary × 4
- [x] Tests cite spec sections (D-BE-1, D-BE-2, H5, H6, H7, R5)
- [x] Arch fitness tests verify R5 boundary explicitly: `test_llm_call_model_does_not_import_sales_agent_domain`, `test_llm_call_model_does_not_import_sales_agent_application`, `test_llm_call_model_imports_from_shared_base_entity`, `test_spec_imports_eval_simulator_llm_call_model`. ✓
- [x] T-2 corrected initial 6→7 indexes mismatch (caught `ix_eval_synthetic_tenants_slug` partial-index oversight). Iteration log entry 5.

## Allowlist Movement
- [x] Did any allowlist GROW? **NO** — gate has NO allowlist (pure ratchet)
- [x] Did any allowlist shrink? Not applicable (new gate)

## Native-First Audit
- [x] No `docker exec ... ruff|pytest|tsc|vitest|mypy|eslint` in commit body
- [x] Commit `e6f3ca7b` uses scoped `git add` (no `-A`/`-u`)
- [x] Push to `development`, not `main`

## Cross-cutting verification

- **Spanish neutro:** Test docstrings use Spanish neutro ("Migration declara correct revision chain", "upgrade() emits CREATE TABLE IF NOT EXISTS"). Some docstrings English; all neutral. No voseo. ✓
- **Test isolation:** Each test class re-loads migration module via `_load_migration_module()` (no shared state across tests).
- **No DB dependency:** Migration test uses `patch.object(module.op, "execute", side_effect=executed.append)` — runs on any environment without Postgres. Arch fitness gate reads file source via `Path.read_text` — also DB-agnostic. Excellent.
- **TDD layering:** T-2 codifies invariants ABOUT T-1 deliverables. Per `tdd-mandatory.md` flow `domain → infrastructure → application → API arch+E2E`, arch fitness is the architecture E2E layer.

## Anti-duplication §0 verification (Cat 12)

- T-2 IMPL-LOG cites Step 0 grep: `grep -rn "test_eval_simulator\|test_extend_eval_simulator" backend/tests/` → 0 results (first-time creation).
- Pattern PRECEDENT explicit: `tests/migrations/test_119_llm_eval_gate.py` and `tests/architecture/test_sales_agent_observability_invariants.py`. NOT a mirror — adapted with story-specific assertions.
- No subsystem in `anti-duplication.md` inventory matches arch fitness test files (each module owns its own gates).

## Verdict Math
- Cat 1/2/8/9/12: all PASS or N/A
- Cat 4 (Code Quality), Cat 6 (arch fitness), Cat 8 (Migration Quality), Cat 10 (Tests/TDD): PASS
- /test-backend gate scoped run: 38+43 = 81/81 PASS verified locally
- Allowlist movement: no growth (no allowlist exists)
- IMPL-LOG cites baseline skills

## Verdict
**APPROVED**

## Findings
- 0 FAIL
- 0 WARN
- 3 NOTE (TDD ordering rationale + ratchet pattern + migration test pattern paridad)

## Cited paths
- `backend/tests/migrations/test_extend_eval_simulator_observability.py:1-410`
- `backend/tests/architecture/test_eval_simulator_observability_invariants.py:1-436`
- `backend/tests/migrations/test_119_llm_eval_gate.py` (precedent)
- `backend/tests/architecture/test_sales_agent_observability_invariants.py` (precedent)
- `T-2-result.md`, `T-2-impl-log.md`
