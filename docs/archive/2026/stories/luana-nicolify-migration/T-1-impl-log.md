# T-1 Implementation Log — Baseline capture + codemod scripts + arch tests

## Metadata

- ticket: T-1
- story: luana-nicolify-migration
- builder: claude-sonnet-4-6 (T-1 = Sonnet OK per 05-guidelines.md §0)
- started: 2026-05-12
- state: done
- decisions_honored: [D5, D1, D10]

## Step 1 — BE baseline capture

Command:
```bash
cd /home/chris/AISALESHT/backend && .venv/bin/pytest --json-report --json-report-file=../docs/product/stories/luana-nicolify-migration/baseline-be-tests.json --tb=short -q
```

Results:
- **Passed:** 10018
- **Failed:** 8
- **Skipped:** 148 (includes 2 deselected)
- **Total collected:** 10184 (12 deselected)
- **Duration:** 808.51s (0:13:28)
- **Output file:** `docs/product/stories/luana-nicolify-migration/baseline-be-tests.json`

Pre-existing failures (8 — captured verbatim from pytest output):
1. `tests/agentic_evals/sales_agent/test_goldens_coverage.py::test_all_cells_covered`
2. `tests/scripts/test_skill_sales_agent_audit.py::test_utility_verdicts_cover_all_skill_sections`
3. `tests/scripts/test_skill_sales_agent_audit.py::test_impl_log_has_required_sections`
4. `tests/modules/copilot/api/test_suggestions_endpoint_integration.py::TestSuggestionsIntegration::test_e2e_real_engine_real_offer_provider`
5. `tests/agentic_evals/sales_agent/simulator/test_runner_unit.py::test_db_session_propagated_to_agent_bridge_via_contextvar`
6. `tests/architecture/test_grader_public_api_surface.py::test_no_internal_symbols_leaked_on_grader`
7. `tests/scripts/test_validate_session_close.py::test_cap_violation_reported_with_count[developed-cap 2]`
8. `tests/scripts/test_promote_golden.py::TestPromoteRefusesCrashedSimulation::test_error_message_mentions_crash_reason`

Note: These are NOT the "40 sales_agent pre-existing failures" mentioned in Decisión 9B (03-arch.md §0). The current env has 8 pre-existing failures. Decisión 9B refers to failures that will appear after the imports rewrite (when luana-core packages are not yet installed in the AISALESHT backend venv). These are tracked as deferred to Story 14.

No halt triggers encountered (Trigger #5: env breakage — 8 < 100 threshold, non-env failures).

## Step 2 — FE baseline capture

Command:
```bash
cd /home/chris/AISALESHT/frontend && npx vitest run --reporter=json --outputFile=../docs/product/stories/luana-nicolify-migration/baseline-fe-tests.json
```

Results:
- **Total tests:** 2164
- **Passed:** 2164
- **Failed:** 0
- **Pending:** 0
- **Output file:** `docs/product/stories/luana-nicolify-migration/baseline-fe-tests.json`

FE baseline is completely clean (0 failures).

## Step 3 — Visual baselines

**Decision: DEFERRED to T-11** (Playwright smoke ticket).

Rationale:
- T-1 is pre-rewrite — no env changes needed yet.
- Playwright requires dev server + Clerk auth + live Vercel deployment.
- Running `make dev` (Docker) during T-1 conflicts with M3 rule (sequential Docker/CI, one session at a time).
- T-11 ticket is specifically designed for Playwright smoke E2E (Scenario 5.1-5.4) — it will capture visual baselines as part of its scope when the post-migration env is live.
- 06-tickets.yaml confirms T-11 = "Playwright smoke E2E (Chris journey + tenant isolation + cost regression)" which runs against live env.

## Step 4 — BE codemod script authored

**File:** `scripts/codemod_be_imports.py`

- LibCST-based AST transformer (NOT sed — handles aliases, multi-line imports, nested paths per 03-arch-be.md §2.1 rationale)
- MAPPING dict: 18 modules + 11 shared subsystems + per-consumer ports (37 entries total)
- Nicolify-local modules preserved: `scheduling`, `advertising`, `social_media` → `nicolify_backend.modules.*` (Phase 0 Option A per 03-arch-be.md §1.1)
- Idempotency: running twice produces identical output (verified in self-check)
- Self-check verified: `python scripts/codemod_be_imports.py --dry-run --self-check` → PASSED

Self-check assertions:
- `src.modules.brand.domain.models` → `luana_core_brand_studio.domain.models` ✓
- `src.modules.scheduling.*` → `nicolify_backend.modules.scheduling.*` (stay-local) ✓
- `src.shared.domain_events.outbox.*` → `luana_core_events.outbox.*` (specificity order) ✓
- `src.shared.infrastructure.llm.*` → `luana_core_llm.*` ✓
- `src.shared.domain.locale` → `luana_core_platform.domain.locale` ✓
- Idempotent: second pass = 0 changes ✓

luana-platform package verification (all MAPPING targets verified present):
- All 26 luana-core-* packages exist in `/home/chris/luana-platform/core/`
- `luana-core-assets`, `luana-core-llm`, `luana-core-platform`, `luana-core-channels`, `luana-core-extraction` all verified present
- No MAPPING reference to a missing package (Trigger #1 NOT triggered)

## Step 5 — FE codemod script authored

**File:** `scripts/codemod_fe_imports.ts`

- jscodeshift TypeScript transform skeleton
- MAPPING covers: @/components/ui → @luana/ui-kit, @/lib/api/fetchClient → @luana/api-client, @/lib/format → @luana/format, @/lib/tokens → @luana/design-tokens, @/lib/zod-schemas → @luana/schemas, @/hooks/useTenantLocale → @luana/hooks
- Stay-local explicitly documented: @/app/, @/features/, @/stores/, @/components/shared/
- NOTE: T-8 builder will verify and complete FE mapping during Phase 0 spike (pnpm workspace + @luana/* package exports). This is an initial template per spec.

## Step 6 — Delta check script authored

**File:** `scripts/test_delta_check.py`

- Parses pytest-json-report JSON (BE) + vitest reporter=json (FE)
- Computes new_failures = current_failures - baseline_failures
- `--max-new-failures=0` enforces D5 cap
- Exit 0 = PASS, exit 1 = FAIL, exit 2 = arg error / file not found
- Self-comparison test: `delta(baseline, baseline) = 0` ✓ (verified via arch fitness test)

## Step 7 — 4 new arch fitness tests authored

All tests in `backend/tests/architecture/`:

1. **`test_no_legacy_src_paths.py`** — SKIP until luana-platform/nicolify/backend/src/ exists. 2 tests (from src. + bare import src.). Becomes active gate post Story 10 merge.

2. **`test_no_legacy_src_mock_paths.py`** — 1 test ACTIVE NOW (AISALESHT tests have 0 stale mocks — verified baseline = 0 per 03-arch-be.md §1.3). 1 test SKIP until nicolify tests dir exists.

3. **`test_consolidated_migration_idempotent.py`** — SKIP until 001_initial_snapshot.py exists (T-10). 2 tests: DDL idempotency + op.execute pattern.

4. **`test_delta_zero_enforcement.py`** — ALL 5 TESTS PASS NOW (baselines exist post Step 1-2). Self-comparison delta = 0 verified.

Collection result: 11 tests collected, 6 passed, 5 skipped.
Full arch fitness suite: 1069 passed, 6 skipped, 0 failures.

## Step 8 — Quality gates

- Ruff lint on arch tests: 0 errors (after fixing F541, adding check=False, noqa: S603/S607)
- Ruff format on arch tests: applied, 0 reformats remaining
- All scripts/ files: exempt from BE ruff gate (path is `../scripts/` relative to backend)

## Known unmapped mocks

Per Halt Trigger #11 tracking — verified baseline:
- `grep -r "patch.*['\"](src\." backend/tests/ | wc -l` = **0**
- No stale mock paths in current AISALESHT test suite
- Trigger #11 NOT triggered in T-1 (pre-rewrite phase)
- If T-2+ encounters a stale mock path with no luana-core equivalent → halt and document here

## Decisions honored

- **D5 (fix-on-discovery cap delta=0):** baseline captured pre-rewrite, delta enforcement scripts authored
- **D1 (full big-bang scope):** MAPPING covers all 18 modules + 11 shared subsystems (no partial scope)
- **D10 (Session 5 pre-auth):** T-1 is tooling only — no production code modified, no auth changes
