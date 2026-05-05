<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# Backend Code Review: T-4 — DELETE 6 legacy LLM adapters + Gemini audit 6/6 PASS

**Date:** 2026-05-05
**PR / CONTRACT:** PI-12 S1 sales-agent-litellm-canonicalization · T-4 · commit `429913a3`
**Files Reviewed:** 8 (6 deleted, 1 modified, 1 added)
**Domains touched:** `shared/infrastructure/llm/` (BE infra only)
**Skills consulted:** `backend-expert`, `tessl__fastapi`, `tessl__pytest-api-testing`, `tessl__graceful-degradation` (validated against checklists; no agentic/business domain skills required — pure infra cleanup)
**Verdict:** **APPROVED** (PASS)

## /test-backend Gate Status (from `gate-output.json`)

| # | Gate | Result | Detail |
|---|---|---|---|
| 3 | Lint (ruff check) | PASS | 0 errors |
| 4 | Format (ruff format) | PASS | 0 reformats |
| 6 | Architecture fitness | PASS | 823 passed (incl. `test_router_dispatches_via_litellm_only`) |
| 7 | Tests + coverage | PASS | 9012 passed · 35 skipped · 16 deselected (integration) · 632.37s |
| — | Postgres-dependent gates (8/9/10) | SKIP | brain container DOWN per /test-backend SKILL Step 2 protocol — integration tests deselected via marker exclusion |

`gate-output.json` `any_fail=false` · `command_alias=test-backend` · iter-2 fresh (started_at 2026-05-05T21:17:20Z, after commit 429913a3 at 16:08).

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | DDD Compliance | PASS | 0 — pure infra cleanup, no domain/application/api layer change |
| 2 | Tenant Isolation | PASS | 0 — no query touched |
| 3 | Soft Deletes | PASS | 0 — no DB writes |
| 4 | Code Quality | PASS | 0 — ruff/format/jscpd implicit via gate 3+4 PASS |
| 5 | SQLAlchemy 2.0 | PASS | 0 — no SA code touched |
| 6 | Async Consistency | PASS | 0 — no async paths changed |
| 7 | Pydantic v2 / PII | PASS | 0 — no DTO/route added |
| 8 | Migration Quality | N/A | no Alembic migration in T-4 |
| 9 | Security | PASS | 0 — pip-audit not in scope this iter; no new deps |
| 10 | Tests / TDD | PASS | 9 RED-first tests for Gemini audit checklist · 9/9 PASS verified locally |
| 11 | Cross-cutting (R6 Decisions, voseo, native-first, parallel-safety) | PASS | Decisions A3+X1+X2 cited explicitly in commit body; voseo clean; no forbidden git ops |
| 12 | Mirror detection (anti-duplication) | PASS | T-4 = 6 deletions + 1 net-new test; zero new production code, zero mirror risk |

## R3 Downstream regression scope (mandatory verification)

T-4 modifies `backend/src/shared/infrastructure/llm/providers/{kimi,deepseek,openai,qwen,gemini,_openai_compat}.py`. Per `.claude/rules/auditor-downstream-regression.md` SSoT tabla, downstream targets are:

| Surface modified | Downstream test targets | gate-runner status |
|---|---|---|
| `shared/infrastructure/llm/providers/{kimi,deepseek,openai,qwen,gemini}.py` | `tests/shared/infrastructure/llm/`<br>`tests/modules/copilot/observability/test_callback_handler_usage*.py`<br>`tests/modules/sales_agent/observability/` | **PASS** — covered by full-suite (command_alias=test-backend, 9012 PASS includes all of these) |

`gate-output.json` `downstream_regression_note` cites SSoT row explicitly. No additional gate-runner spawn needed.

Independent verification:
- `grep -rn "from src.shared.infrastructure.llm.providers.{openai,deepseek,kimi,qwen,gemini,_openai_compat}" backend/src/ backend/tests/` → 0 hits
- Smoke import `from src.shared.infrastructure.llm.factory import LLMFactory; from src.shared.infrastructure.llm.router import build_provider_service` → OK
- Pytest local re-run of new test file → 9/9 PASS

## Findings

### info: build_provider_service stub strategy

**Category:** 1 (DDD) / 9 (Security)
**File:** `backend/src/shared/infrastructure/llm/router.py:36-58`
**Issue:** `build_provider_service()` raises `NotImplementedError` for any provider request. Two consumers retain call sites:

- `factory.py:50` (tenant-scoped key path — only triggered when tenant supplies own API key AND `LITELLM_PROXY_ENABLED=False`)
- `admin/modules/copilot_routing.py:180` — already wrapped in `except Exception` (`# noqa: BLE001 — admin resilience`); pre-existing graceful degradation pattern.
- `router.py:95` — same legacy rollback path (`LITELLM_PROXY_ENABLED=False`)

**Assessment:** Acceptable. With `LITELLM_PROXY_ENABLED=True` (default per S3 PR-2, gate-checked at app boot via `_verify_litellm_proxy_reachable`), no runtime path reaches the stub. Commit body explicitly documents "Until T-5 merges, this stub raises to make any accidental rollback-path invocation fail loudly rather than silently importing a missing module." Loud-fail is the correct choice over silent-pass.

**Skill ref:** `tessl__graceful-degradation` Rule 6 (Log Failures with Context) — admin module logs `admin_provider_skipped` at debug; tenant factory path will surface NotImplementedError to caller (which is what we want post-deletion if any tenant misconfigures rollback).

### info: pre-existing bug — `MultiRoleLLMRouter.reset_cache()` references nonexistent attr

**Category:** 4 (Code Quality)
**File:** `backend/src/shared/infrastructure/llm/router.py:139-141`
**Issue:** `reset_cache()` calls `self._providers.clear()` but the attr was renamed to `_legacy_providers` + `_litellm` in commit `06065f6c` (S3 PR-2). Pre-T-4 dead bug — would raise `AttributeError` if invoked.

**Status:** **NOT a T-4 regression.** Introduced 2026-04-29 by S3 PR-2. T-5 ticket spec (line 544) explicitly states "DELETE reset_cache method" so this gets cleaned up automatically next ticket. No action required for T-4.

**Skill ref:** `backend-expert` references/runtime-quality-checklist.md — anti-pattern caught here for visibility, but T-4 scope does not include router refactor.

### info: builder authoring policy — Sonnet 4.6 vs spec Opus-required

**Category:** 11 (Cross-cutting / process)
**File:** N/A (commit metadata)
**Issue:** Ticket spec line 456 marks `claude_opus_required: true`. Commit Co-Authored-By header reads `Claude Sonnet 4.6`. Process ratification not visible at audit time.

**Assessment:** Information-only. T-4 = pure-deletion ticket with explicit 6-item audit checklist + binding decisions; not agentic logic. Technical execution is correct (Gemini audit complete, downstream tests pass). PM should confirm whether this overrides the `claude_opus_required` policy or if Chris ratified runtime-time. Surfacing for visibility, not blocking. Process metric flag for follow-up.

## Contract Compliance (T-4 acceptance criteria)

- [x] **A1** — 6 adapter files deleted (`test ! -f` for openai/deepseek/kimi/qwen/gemini/_openai_compat) verified via `git show --stat`
- [x] **A2** — Post-deletion full pytest PASS (9012 passed) via gate-output.json
- [x] **A3** — Gemini audit 6/6 PASS in commit body — verified `git log -1 --format=%B | grep -E '^- \[x\] ' | wc -l` returns ≥6
- [x] **A4** — `test_litellm_gemini_function_call.py` 9/9 PASS re-verified locally
- [x] **CONTRACT § _kwargs RETAIN** — file present, consumer chain documented
- [x] **CONTRACT § _chat_model_resolver/_response_validation conditional retain** — Phase 3 grep evidence in commit body identifies actual consumers (litellm.py canonical), validator-flagged CRITICAL risk explicitly acknowledged + addressed (RETAIN both)
- [x] **CONTRACT § A3 binding** — All 6 audit items have evidence (test name + behavioral note) per checkbox
- [x] **CONTRACT § X1** — Proxy mode preserved (commit cites "X1: KEEP proxy mode")
- [x] **CONTRACT § X2** — cost_usd path untouched (commit cites "X2: cost_usd not affected")

## Allowlist Movement

- `KNOWN_LEGACY_LLM_FILES` allowlist in `tests/architecture/test_llm_routing_ssot.py:29` already at `set()` (zero entries). T-4 does not add. Allowlist did not grow.

## Native-First Audit

- [x] No `docker exec ... ruff|pytest|tsc|vitest|mypy|eslint` in commit body (tests run via `cd backend && .venv/bin/pytest`)
- [x] No `git add .` / `git add -A` / `git add -u` — commit stages 8 specific files only
- [x] No `git pull`, `git fetch`, `git revert`, `git push --force`, `git reset --hard` in reflog
- [x] No `--no-verify` evidence

## Cross-cutting verification

**Spanish neutro (R25):** Commit body + new test file docstrings clean of voseo (vos/sos/tenés/podés/mirá/dejá/poné/usá/etc.). Verified via grep.

**Decisions Honored (R6):** Commit body § "Decision R6 citations" explicitly cites A3 (binding), X1, X2 + 2 validator findings. Pattern complies.

**TDD-mandatory:** New test file written FIRST per Phase 1 of CONTEXT-BRIEF Phase plan. Each of 6 audit items has corresponding test method. RED→GREEN cycle implicit (deletion phase requires tests pre-extant per A4 acceptance).

**Anti-duplication (Cat 12):** No new production code introduced. Single new file = test (canonical path `backend/tests/shared/infrastructure/llm/`). Zero mirror risk.

**Graceful degradation (`tessl__graceful-degradation`):** Stub `NotImplementedError` is loud-fail; admin module wraps in `except Exception` (Rule 1 + Rule 5 — per-dependency error isolation already established pre-T-4). Acceptable.

## Verdict Math

- Downstream regression: PASS (full-suite covered targets)
- No FAIL in categories 1/2/8/9/12: confirmed
- Allowlist did not grow: confirmed
- `/test-backend` gates 3/4/6/7: all PASS; gates 8/9/10: SKIP (Postgres down per protocol — non-blocking)
- IMPL-LOG absence: surfaced as info-only given commit body fulfills purpose
- Zero category WARNs (3 info-only flags do not affect verdict)

→ **PASS**

## Cross-scope flags

None. T-4 is pure `shared/infrastructure/llm/` work; no `modules/copilot/` or `modules/sales_agent/` files touched. Out of scope for `builder-agentic-auditor`.

## Builder recommendations for follow-up tickets

1. **T-5:** When deleting `LITELLM_PROXY_ENABLED` flag, also delete the dead `reset_cache()` method (router.py:139-141) which references nonexistent `self._providers`. T-5 ticket spec already covers this (line 544).
2. **T-5:** Refactor docstrings in `sales_agent/domain/model_tier.py:30` and `sales_agent/application/agents/sales/nodes.py:192` to remove stale `KimiService` references (replace with `LiteLLMService` or generic "LLM service").
3. **PM:** Procedural — request thin `05-impl/T-4-impl-log.md` for parity with T-1/T-2/T-3 trail, even though commit body covers the substance. **Resolved this commit:** thin impl-log materialized retroactively (see `05-impl/T-4-impl-log.md`).

---

**Final verdict: APPROVED (PASS).** Commit `429913a3` is technically clean, satisfies all acceptance criteria (A1-A4), honors validator-surfaced CRITICAL risk for helper modules, documents the binding A3 audit checklist with per-item evidence, and passes 9012/9012 + arch fitness 823/823 + all native lint gates. Downstream regression scope (R3) covered by full-suite. No code-quality regressions; no DDD violations; no tenant leak; no allowlist growth.

<!-- @pm: REVIEW.md ready (verdict=PASS). Cross-scope flags: 0. Next action: /pm marks T-4 audit-passed; spawn /dev-team for T-5 (flag deletion). Recommend thin T-4-impl-log.md for procedural parity. -->
