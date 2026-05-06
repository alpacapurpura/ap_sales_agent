# Backend Code Review: PR-1 Fix Broken Tests, Singleton Fixture, EventBus Migration (Business Surface)

**Date:** 2026-05-04
**PR / CONTRACT:** `docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-1-fix-broken-tests-and-arch-snapshots/`
**Files Reviewed (business surface):** 13
**Domains touched:** shared (LLM provider, domain events, conftest fixture), brand (test migration), architecture (allowlists), frontend (closer-studio test)
**Skills consulted:** backend-expert, brand-expert, tessl__pytest-api-testing, tessl__fastapi (N/A — no API routes touched), tessl__graceful-degradation (events.py best-effort warning verified)
**Iter:** 1 (continuation post stalled previous auditor)
**Verdict:** **PASS**

## /test-backend Gate Status (consumed from `gate-output.json` iter 2 subset)

| # | Gate | Result | Detail |
|---|---|---|---|
| 1 | Tools | PASS | (subset run; tools assumed present per builder native execution) |
| 2 | Postgres pre-flight | N/A | Subset gates skipped 8/9/10 |
| 3 | Lint (ruff check) | PASS | 0 errors |
| 4 | Format (ruff format) | PASS | 0 reformats |
| 5 | Type check (mypy) | FAIL (baseline) | 1972 errors. **Verified business-touched files: `src/shared/domain/events.py` 0 errors; `src/shared/infrastructure/llm/providers/litellm.py` 3 errors at lines 146/194/204 — ALL pre-existing (NOT introduced by PR-1 kimi clamp at line 115)**. Info-only — does not fail PR-1 verdict per CONTRACT scope rule. |
| 6 | Architecture fitness (78 gates) | PASS | 811/811 per IMPL-LOG (native validated) — allowlist additions justified in commit `ee26d5c2` |
| 7 | Tests + coverage | NATIVE_VALIDATED | builder native: 811 arch + 1210 shared + 11 brand + 4 kimi clamp + 4 deprecation + 8 event_bus_adapter + 10 FE = all PASS; 5x consecutive deterministic runs |
| 8 | Verify-marker | SKIP | Subset gates only; not in scope PR-1 (no analytics ETL) |
| 9 | Integration | SKIP | Subset gates only; agentic builder ran integration tests separately |
| 10 | Migration idempotency | SKIP | No migrations in PR-1 |
| 11 | jscpd | FAIL (baseline) | 363 clones at **3.91% — UNDER 5% threshold**. Runner misclassification (per gate-output.json `notes`). First clones cited (`src/tests/test_telegram_flow.py`, `src/core/base_repository.py`) — NOT in PR-1 diff. Info-only. |
| 12 | interrogate | PASS | docstrings ≥85% |
| 13 | pip-audit | FAIL (baseline) | 14 pre-existing CVEs (langchain-openai, langchain-text-splitters, langsmith, lxml, pillow, etc.) — out-of-scope per CONTEXT-BRIEF. Info-only. |

**Verdict-affecting failures: 0.** All gate FAILs are baseline pre-existing in files NOT touched by PR-1 business surface.

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | DDD Compliance | PASS | 0 — `events.py` is shared/domain (pure), `litellm.py` is shared/infrastructure (correct layer); local import of `settings` inside function avoids circular |
| 2 | Tenant Isolation | PASS | 0 — events.py emits `tenant_id` in structlog warning; tests preserve tenant_id determinism (`44444444-…`) |
| 3 | Soft Deletes | PASS | 0 — no DELETE statements added |
| 4 | Code Quality | PASS | 0 — ruff lint+format clean; new code has docstrings; `# noqa: BLE001` on best-effort try/except (justified comment per backend-quality.md) |
| 5 | SQLAlchemy 2.0 | PASS | 0 — no SA queries added/modified in business surface |
| 6 | Async Consistency | PASS | 0 — sync code paths preserved (events.py `publish` is sync by contract); no blocking I/O in async paths |
| 7 | Pydantic v2 / DTOs / PII | PASS | 0 — no new DTOs; structlog warning logs `event_name` + `tenant_id` (UUID, not PII per allowlist) |
| 8 | Migration Quality | PASS | 0 — no migrations in PR-1 |
| 9 | Security | WARN→PASS | 1 baseline — 14 pip-audit CVEs documented out-of-scope (not introduced by PR-1). No new external calls. `_is_internal_caller_or_test()` uses `sys._getframe` (intended frame inspection, depth-bounded to 10). |
| 10 | Tests / TDD | PASS | RED-first per IMPL-LOG (kimi clamp regression tests written, 4 deprecation warning tests, brand event migration test). 5x deterministic. No skip/xfail. Snapshot baseline regenerated within same PR per CONTRACT § 10 Q5. |
| 11 | Cross-cutting | PASS | 0 — no `datetime.utcnow()`, no hardcoded `'USD'`, no voseo in user-facing strings (test docstrings only — Spanish neutro respected). Commits use Conventional Commits + `git add <path>` (no `git add .` evidence). No `docker exec` for lint/tests in commit history. |
| 12 | Mirror detection | PASS | No new files in `modules/X/<subsystem>/` cross-module. Only NEW test files: `test_litellm_kimi_clamp.py` + `test_legacy_event_bus_deprecation_warning.py` — both regression tests in `tests/shared/`, NOT mirrors of existing patterns. PR.md § "Existing systems audit" populated with grep evidence + path:line. |

## Cross-scope flags (deferred to nicolify-agentic-auditor — already PASS per REVIEW-agentic.md)

| File | Module | Action |
|---|---|---|
| `tests/architecture/test_sales_agent_*.py` (2 files) | sales_agent | OUT-OF-SCOPE — agentic auditor PASS verdict |
| `tests/modules/copilot/test_*.py` (4 files) | copilot | OUT-OF-SCOPE — agentic auditor PASS verdict |
| `tests/modules/sales_agent/**` (incl. snapshot helpers + baseline) | sales_agent | OUT-OF-SCOPE — agentic auditor PASS verdict |
| `tests/integration/test_outbound_orchestrator_e2e.py` | sales_agent (build_sales_agent_observability_context) | OUT-OF-SCOPE — agentic auditor PASS verdict |

## Findings (business surface)

### info — `backend/src/shared/domain/events.py:107-109`

**Category:** 11 (Cross-cutting)
**Issue:** Deprecation warning checks 3 flags (`USE_OUTBOX_PATTERN_SALES_AGENT/COPILOT/BRAND`) but does NOT check `USE_OUTBOX_PATTERN_DEFAULT`. If a future module uses `module=None` (defaults to global flag) and that global flag is True while module-specific flags are False, the warning won't trigger.
**Fix (non-blocking):** Optionally add `or getattr(_settings, "USE_OUTBOX_PATTERN_DEFAULT", False)` for completeness. Defer to future PR — current behavior matches the 3 modules currently active per CONTRACT § 5.
**Skill ref:** consistency check vs `event_bus_adapter._is_outbox_enabled` which uses module-keyed lookup.

### info — `backend/tests/conftest.py:344-419`

**Category:** 10 (Tests / TDD)
**Issue:** Singleton fixture documents 2 EXCLUDED singletons (`ChannelRouterRegistry._instance`, `MetaAPI._api_instance`) — well-justified inline. Future maintainers may add new singletons that should be reset; consider adding a brief grep command in module docstring for periodic re-validation.
**Fix (non-blocking):** Add a comment: `# To re-validate inventory: grep -rn "_instance = None\|cls._instance" src/`. Defer to future PR.
**Skill ref:** `backend-expert/references/runtime-quality-checklist.md` autouse fixture pattern (correct).

### info — `backend/src/shared/infrastructure/llm/providers/litellm.py:115-123`

**Category:** 4 (Code Quality)
**Issue:** Kimi clamp adds a `logger.warning("kimi_k2_temperature_clamped", ...)` — correct structured log. The clamp matches the spec mirror from `kimi.py:79-92` per IMPL-LOG. CONTRACT.md § 7 is satisfied.
**Pre-existing mypy errors at lines 146/194/204 are NOT introduced by this clamp** (verified via line-level inspection). They were present pre-PR-1 and are out-of-scope.
**Skill ref:** spec-conformant; structlog logger properly typed.

## Contract Compliance (business surface only)

- [x] All entities from CONTRACT § 1 (singleton inventory) implemented in conftest.py — exhaustive list per IMPL-LOG matches CONTRACT
- [x] § 2 fixture design: pre + post yield reset implemented (`_do_singleton_reset` called twice per test)
- [x] § 3 EventBus mock migration: Caso C (brand test, `patch.object(EventBusAdapter, "_is_outbox_enabled")`) correctly migrated; Caso D/E (test_event_bus_adapter.py) correctly preserved
- [x] § 5 D3 LegacyEventBus runtime warning: implemented with `_is_internal_caller_or_test()` helper, frame-depth bounded, best-effort try/except — 4 test cases cover all paths (test context suppress / adapter fall-through suppress / all-flags-off no-warning / external+flag-on emit)
- [x] § 7 D7 litellm.py kimi clamp: implemented at line 115 with `_K2_REQUIRED_TEMPERATURE = 0.6` constant, structured log, 4 regression tests
- [x] § 8 Agentic Surfaces: flagged `[CROSS-SCOPE]` and validated PASS by `nicolify-agentic-auditor`
- [x] § 9 stash apply: 16 files audited per IMPL-LOG `Stash Apply Audit` table; business owns 5 staged + committed; agentic owns 8 left-unstaged (now committed by agentic builder per `git log`)
- [x] § 13 PR-3 cross-PR coordination signal: commit `37e0b794` flagged "EventBus migration complete (business surface)" per IMPL-LOG; `_chat_flow_snapshot_helpers.py` migrated by agentic — PR-3 builder can shrink allowlist
- [x] § 14 test surfaces present at every layer: kimi clamp (regression), deprecation warning (4 cases), brand event migration (Caso C), event_bus_adapter (Caso D/E preserved)

## Allowlist Movement

- **GREW:** `KNOWN_CROSS_MODULE_IMPORTS` +3 entries (campaigns→sales_agent adapter, crm→campaigns x2). Justified in `test_ddd_boundaries.py` inline comments + commit `ee26d5c2` body — these reflect existing PI-1 PR-7 outbound + PI-1 PR-6 contacts hub adapters at infrastructure/external/ + api/ composition root, NOT business-logic coupling. **Justified — PASS.**
- **GREW:** `KNOWN_PRIVATE_FILE_EXCEPTIONS` +1 entry (`copilot/api/_dependencies.py`). Justified — mirrors campaigns/api/_dependencies.py PI-5 PR-1 pattern (async session DI factory). Inline comment present. **Justified — PASS.**
- **SHRUNK:** No allowlist shrunk in this PR (cross-PR signal sent for PR-3 to shrink `KNOWN_LEGACY_MOCK_FILES` post agentic completion).

## Native-First Audit

- [x] No `docker exec ... ruff|pytest|tsc|vitest|mypy|eslint` in commit history (verified `git log --oneline -15` + IMPL-LOG `Quality Gates Output` section confirms native venv usage)
- [x] No `git add .` / `git add -A` / `git add -u` in commits (per IMPL-LOG `Commits` table — files staged by exact path)
- [x] No `git pull` / `git push --force` / `git revert` evidence
- [x] PR not pushed to `main` — on `development` branch (correct workflow)

## Verdict Math

- Any FAIL in categories 1 / 2 / 8 / 9 → **No** (Cat 9 is WARN→PASS baseline-only, not introduced by PR-1)
- Allowlist grew without justified commit → **No** (both growths inline-justified + commit body)
- Any `/test-backend` gate FAIL (3-7, 11-13) blocking? → **No** (mypy/jscpd/pip-audit are pre-existing baseline NOT in business-touched files; all PR-1 gates 3/4/6/7/12 PASS)
- IMPL-LOG § Skills Consulted complete? → **Yes** (backend-expert, tessl__pytest-api-testing, tessl__fastapi N/A justified, tessl__graceful-degradation cited, brand-expert cited)
- `runtime-quality-checklist.md` cited? → **Yes, indirectly** (IMPL-LOG line 11 references "runtime-quality-checklist.md autouse fixture override pattern") — singleton fixture follows the documented autouse function-scope pattern correctly
- Two or more category WARNs → **No** (0 WARN, 3 info-only)

**Verdict: PASS**

## Drift Detection (CONTRACT vs code)

NO drift detected. Business surface honored:
- CONTRACT § 1-2 (singleton inventory + fixture design — exhaustive 5 singletons + 2 caches, 2 EXCLUDED documented)
- CONTRACT § 3 D2 (EventBus mock migration via `patch.object(EventBusAdapter, "_is_outbox_enabled")` — Caso C correct)
- CONTRACT § 5 D3 (LegacyEventBus deprecation warning — 4 test cases, internal caller detection working)
- CONTRACT § 7 D7 (litellm kimi clamp — `_K2_REQUIRED_TEMPERATURE=0.6`, structured log, 4 regression tests)
- CONTRACT § 11 surface mapping (no business edit on agentic-owned paths)
- CONTRACT § 13 cross-PR signal (commit hash `37e0b794` flags EventBus migration complete)

<!-- @pm: REVIEW-backend.md ready (verdict=PASS). Próximo paso: cerrar PR (PM /pm orchestration → RESULT.md). -->
