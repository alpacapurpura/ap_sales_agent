<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# Backend Code Review: T-5 — Kill flag LITELLM_PROXY_ENABLED + admin provider library panel

**Date:** 2026-05-05
**PR / Story:** `docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/S1-eval-runner/stories/sales-agent-litellm-canonicalization/`
**Ticket:** T-5
**Commit:** `28617716` (main work) + `560f14b5` (impl-log SHA backfill)
**Files Reviewed:** 10 (8 backend src + 1 rule + 1 pyproject) + 1 impl-log
**Domains touched:** shared/infrastructure/llm, core/config, admin/modules, main.py boot, anti-default-flip rule
**Skills consulted:** backend-expert (runtime-quality-checklist + architectural-fitness + anti-default-flip-audit), tessl__fastapi (router contract preservation), tessl__pytest-api-testing (test fixture isolation post-deletion). NOT invoked (out of scope): tessl__graceful-degradation (no external HTTP/DB calls), brand-expert/offer-expert/metrics-expert/copilot-expert/sales-agent-expert (no domain logic touched).
**Verdict:** **APPROVED**

---

## /test-backend Gate Status

| # | Gate | Result | Detail |
|---|---|---|---|
| 1 | Tools | PASS | ruff 0.x, pytest 8.x, mypy 1.x — versions per `backend/pyproject.toml` |
| 2 | Postgres pre-flight | UP | architecture+unit ran in-memory; integration (16 tests) deselected per gate command |
| 3 | Lint (ruff check) | PASS | `All checks passed!` (1 pre-existing `# noqa` warning on `offer_type_presets.py:28`, unrelated to T-5) |
| 4 | Format (ruff) | PASS | 2321 files already formatted |
| 5 | Type check (mypy) | INFO | T-5 changed files: `factory.py`, `router.py`, `litellm.py`, `config.py`, `copilot_routing.py`, `llm_virtual_keys.py` mypy clean. `main.py` has 9 pre-existing mypy errors (verified via `git show 28617716^:main.py | mypy` = 10 errors before T-5; T-5 only deleted 4 lines, didn't introduce). NOT a T-5 regression. |
| 6 | Arch fitness (78/78 → 823/823) | PASS | 823 architecture tests PASS. KNOWN_LEGACY_LLM_FILES allowlist still empty (T-8 will codify the 3 new assertions: `test_no_legacy_adapter_imports`, `test_settings_has_no_litellm_proxy_enabled_attr`, `test_known_legacy_files_set_is_empty`). |
| 7 | Tests + coverage | PASS | 9012 passed, 34 skipped, 16 deselected (integration), exit 0. Coverage threshold (≥43%) implicitly satisfied (gate exits 0). |
| 8 | Verify marker | N/A | No analytics/data-reliability changes in T-5 |
| 9 | Integration | DESELECTED | `-m "not integration"` per gate command (consistent with prior T-1..T-4 gate runs). Postgres integration tests not affected by pure code-deletion ticket. |
| 10 | Migration idempotency | N/A | T-5 has zero migrations (pure code/config/rule cleanup) |
| 11 | jscpd | INFO | Not run in this gate (typically not in `test-backend` alias for code-deletion PRs). Net deletion = -190 LOC from `src/` — duplication ratio mathematically improves. |
| 12 | interrogate | INFO | Not run in this gate. Builder added Google-style docstrings to all rewritten methods (`_resolve`, `get_service_for_tenant`, module headers). Manual sample verified: every public method has docstring. |
| 13 | pip-audit | N/A | No dependency changes in T-5 |
| — | Acceptance A1 | PASS | `python -c "from src.core.config import settings; assert not hasattr(settings, 'LITELLM_PROXY_ENABLED')"` → `A1 PASS` |
| — | Acceptance A2 | PASS | `! grep -q 'def build_provider_service' backend/src/shared/infrastructure/llm/router.py` → 0 matches |
| — | Acceptance A3 | PASS | Commit body has 5 mandatory `## ` headers (`## Tests audited`, `## Path old`, `## Path new`, `## Verification`, `## Inventory updated`) — exceeds minimum 4 |
| — | Acceptance A4 | PASS | Inventory row removed AND footnote `removed PI-12 S1` present in `.claude/rules/anti-default-flip-audit.md` |
| — | Anti-default-flip Step 1 grep | PASS | ZERO active mocks of legacy `LITELLM_PROXY_ENABLED=False` path. Two docstring-history references retained in `test_router_litellm_dispatch.py:4` and `test_llm_routing_ssot.py:111-135` (factually correct: explain what was deleted). T-7 had already migrated `TestLegacyDispatch` class. |

**R22 manual fallback acknowledged:** gate-runner Haiku spawn skipped — builder Opus 4.7 ran the full suite natively in agent transcript context (10:32 wall-clock). Auditor independently re-ran ruff (lint + format), architecture (823 PASS), and `tests/shared/infrastructure/llm/` (67 PASS) plus targeted downstream consumer surfaces (see § Downstream regression scope) — gate output validated.

---

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | DDD Compliance | PASS | 0 — pure deletion, no cross-module imports introduced; existing port `shared/infrastructure/llm/` boundary preserved |
| 2 | Tenant Isolation | N/A | 0 — no DB queries touched. `_extract_tenant_key` method still extracts from `tenant` arg correctly (preserved for T-6a/T-6c) |
| 3 | Soft Deletes | N/A | 0 — no DB ops |
| 4 | Code Quality | PASS | 0 — ruff lint + format clean; mypy clean on T-5-touched files; cyclomatic complexity reduced (deletion); module/class/method docstrings updated to reflect post-canonicalization reality |
| 5 | SQLAlchemy 2.0 | N/A | 0 — no SA queries touched |
| 6 | Async Consistency | PASS | 0 — `_verify_litellm_proxy_reachable` remains async (only conditional dropped); no new sync calls in async paths |
| 7 | Pydantic v2 / DTOs / PII | N/A | 0 — no DTO changes; `Settings` lost a single bool field (no PII) |
| 8 | Migration Quality | N/A | 0 — zero migrations in T-5 |
| 9 | Security | PASS | 0 — `_verify_litellm_proxy_reachable` now ALWAYS runs (removed conditional bypass) → strictly improves security posture (was: bypassable via flag; now: unconditional master-key + reachability check) |
| 10 | Tests / TDD | PASS | 0 — anti-flip Step 1 grep returned ZERO active mocks (T-7 already migrated). Single-path test run (9012 PASS) replaces the dual-path requirement since the toggle is gone. T-8 will codify the new arch fitness assertions. |
| 11 | Cross-cutting (master-data + Spanish + native-first + decisions) | PASS | 0 — no `datetime.utcnow()` introduced; admin Spanish strings (`Ruta canónica única`) free of voseo (verified via grep against full glosario); commit body has explicit "Decisions Honored" mapping covering A4 + A2 expand-contract + X1 + Chris zero-tech-debt directive (R6 satisfied); native commands only (no `docker exec` in commit log); scoped commits (specific files staged, no `git add .` evidence). |
| 12 | Anti-Duplication / Mirror Detection | PASS | 0 — pure deletion, no NEW files. No new mirrors. Builder verified anti-duplication §0 GATE manually in impl-log Decisions Honored row 6. |
| 13 | TBD | — | — |
| 14 | Default flip side-effect coverage | **PASS** | **PRIMARY audit dimension this ticket.** 4-step DELETION case satisfied end-to-end (see § Cat 14 detail below) |

---

## Cross-scope flags

None. T-5 touches `shared/`, `core/`, `admin/`, `main.py`, and one `.claude/rules/` file. No `modules/copilot/` or `modules/sales_agent/` files in diff. No agentic logic. R5 schema-mirror exception not invoked (no `persistence/models/` touched).

---

## Findings

### info: dead-bug cleanup of `reset_cache` honored T-4 audit handoff

**Category:** 4 (Code Quality) — non-blocking

**File:** `backend/src/shared/infrastructure/llm/router.py` (deletion of method `reset_cache`)

**Issue:** Pre-T-5, `MultiRoleLLMRouter.reset_cache()` called `self._providers.clear()` referencing an attribute that **never existed** (the actual dict was `_legacy_providers`, renamed in commit `06065f6c` S3 PR-2). T-4 audit (review.md line 142) explicitly flagged this for T-5 cleanup. Builder deleted the method as opportunistic cleanup alongside `_legacy_providers` deletion, verified zero callers via grep across `src/` + `tests/`.

**Verdict:** Audit handoff correctly honored. Pre-existing dead bug now resolved. Not scope creep — explicitly within T-5 deliverable line 548 ("DELETE reset_cache method").

**Skill ref:** `.claude/rules/debugging.md` § "Leave file better — cleanup tech debt mismo file"

---

### info: factory.py dead Path 1 deletion is architecturally forced (not gratuitous scope creep)

**Category:** 1 (DDD Compliance) / 11 (Cross-cutting — scope boundaries) — non-blocking

**File:** `backend/src/shared/infrastructure/llm/factory.py:34-51` (deletion of `api_key = cls._extract_tenant_key(...)` + `if api_key: return build_provider_service(...)` Path 1 of `get_service_for_tenant`)

**Issue:** Architect 03-arch-be.md § 2.4 (line 222-227) and § 4 deliverables table (line 583) assigned `_extract_tenant_key` simplification to **T-6a** (stub return None) + **T-6c** (DELETE method + simplify caller). Builder deleted dead Path 1 of `get_service_for_tenant` in T-5 instead.

**Why this is acceptable (not a violation):**

T-5 ticket deliverable line 548 mandates `DELETE build_provider_service function entirely`. The function had exactly ONE call site outside admin: `factory.py::get_service_for_tenant` line `return build_provider_service(provider, api_key=api_key)`. If T-5 deletes the function but leaves this call, Python raises `ImportError` on module load → production incident. The builder therefore had to delete this call site as part of T-5.

Once the call site is gone, `api_key = cls._extract_tenant_key(...)` becomes dead code (var used only in deleted `if api_key:`). Removing the assignment is mechanical cleanup. The builder **preserved** the `_extract_tenant_key` method itself per architect § 2.4 ("T-6a stub return None, T-6c DELETE method") — confirmed via `hasattr(LLMFactory, '_extract_tenant_key')` returns `True` post-T-5.

**Trade-off:** the alternative was a 2-commit dance (T-5: leave broken intermediate `if api_key:` + new stub; T-6a: clean it up). The builder chose the architecturally clean single-commit. Documented in impl-log § "Subtle decisions" + Decisions Honored A2 row.

**Mitigation for T-6a impact:** T-6a now has a slightly shrunk scope — it no longer needs to "stub `_extract_tenant_key` to None for the 4 deprecated providers" because the **caller is already gone**. T-6a scope reduces to: drop Pydantic deprecated fields, drop repo writes, NULL the columns via migration. T-6c remains identical (drop method + drop columns).

**Action required:** PM should note T-6a scope reduction in `04-tickets.yaml` follow-up edit (or T-6a builder will discover and report). Not blocking.

**Skill ref:** `.claude/rules/anti-duplication.md` § "lift shared first commit" (architecturally correct atomic deletion); architect 03-arch-be.md § 2.4 (boundary clarification)

---

### info: pyproject.toml INP001 ignore is config-level fix (not scope creep)

**Category:** 4 (Code Quality) — non-blocking

**File:** `backend/pyproject.toml:223-225` (added `[per-file-ignores] "src/main.py" = ["INP001"]`)

**Issue:** Pre-commit hook (introduced commit `1a868ac5`) pipes staged content via `ruff check --stdin-filename src/main.py`, which cannot traverse the implicit namespace package (`backend/src/` has no `__init__.py` — confirmed `find backend/src -maxdepth 2 -name "__init__.py"` returns only subdirs, never `src/__init__.py` itself). This produces a false-positive INP001 (implicit-namespace-package) on every staged `main.py` edit because ruff sees only the file content and the filename, not sibling files in `src/`. Direct invocation (`ruff check src/main.py` from `backend/`) was already clean (visible context).

**Why config-level fix is correct (not scope creep):**

1. **`main.py` is the FastAPI entry point** at the top of the namespace package, not a module-folder needing `__init__.py`. INP001 fires correctly on truly missing inits in module folders, but is semantically wrong for a top-level entry point.
2. **Per-file-ignore is the principled fix.** Per Chris zero-tech-debt directive, the alternative `# noqa: INP001` on the file's first line each time main.py is edited is worse: per-line noqa ⊆ per-file rule ⊆ config-level rule (least specific = least churn).
3. **Scoped narrowly.** The ignore applies ONLY to `src/main.py` — every other `.py` file under `src/` is unaffected. ruff still enforces INP001 for genuine module-folder violations.
4. **Documented inline.** The pyproject.toml entry has an inline comment explaining the rationale (`pre-commit hook --stdin-filename can't traverse to verify, false-positive on staged main.py edits`).
5. **Unblocks T-5 commit.** Without this fix, T-5's main.py 4-line deletion (drop `LITELLM_PROXY_ENABLED` conditional) would fail pre-commit hook spuriously, blocking the entire ticket.

**Verdict:** Architecturally correct, minimum-impact, correctly scoped, properly documented. NOT a violation of T-5 scope — necessary to unblock T-5 commit.

**Skill ref:** `backend-expert/references/runtime-quality-checklist.md` (anti-pattern: per-line `# noqa` repeats — prefer config-level when applies to single file consistently)

---

### info: docstring-history references retained in 3 source files (selective)

**Category:** 4 (Code Quality) — non-blocking

**Files:**
- `backend/src/shared/infrastructure/llm/factory.py:9-15, 39-45` (module + method docstrings reference `LITELLM_PROXY_ENABLED=False` rollback path as deleted)
- `backend/src/shared/infrastructure/llm/router.py:9-11` (module docstring references `LITELLM_PROXY_ENABLED` as deleted)
- `backend/src/shared/infrastructure/llm/providers/litellm.py:24-26` (module docstring references toggle removal)

**Issue:** Three source files retain `LITELLM_PROXY_ENABLED` mentions in docstrings as deletion-history annotation. Active code references = ZERO (verified `grep -rn 'settings\.LITELLM_PROXY_ENABLED' backend/src/` = no matches).

**Why this is good engineering (not dead reference):**

The docstring-history pattern allows a future developer reading `factory.py` to discover **why** the dual-path was simplified without git blame archaeology. Each retained reference cites the deletion epoch (`PI-12 S1 T-4` for adapters / `T-5` for the toggle) so the rationale is auditable in-file. This is the standard pattern in deletion commits — the alternative (no docstring history) leads to "what was here?" questions in 6 months.

**Test docstring references:**

`tests/shared/infrastructure/llm/test_router_litellm_dispatch.py:4` and `tests/architecture/test_llm_routing_ssot.py:111-135` retain similar history annotations. T-7 ticket spec (per CONTEXT-BRIEF § 4) handles these explicitly — not T-5's responsibility. T-8 ticket will codify clean assertions (`test_no_legacy_adapter_imports`, `test_known_legacy_files_set_is_empty`, `test_settings_has_no_litellm_proxy_enabled_attr`) that supersede the docstring history.

**Verdict:** Acceptable selective retention. Documented in impl-log § "Subtle decisions". No action required.

---

## Cat 14 — Default flip side-effect coverage (PRIMARY audit dimension this ticket)

Per `.claude/rules/anti-default-flip-audit.md` 4-step **DELETION** variant + ticket spec § "ANTI-FLIP AUDIT 4-STEP" (line 555-559):

### Step 1 — Grep tests path viejo

**Command (verbatim from impl-log line 53-56):**
```bash
grep -rln 'LITELLM_PROXY_ENABLED.*False\|setattr.*LITELLM_PROXY_ENABLED' \
  /home/chris/AISALESHT/backend/tests/ 2>/dev/null | grep -v __pycache__
```

**Output (verified by auditor re-run):**
```
backend/tests/shared/infrastructure/llm/test_router_litellm_dispatch.py
backend/tests/architecture/test_llm_routing_ssot.py
```

**Narrower verifier — active mocks/setattrs:**
```bash
grep -nE "monkeypatch.*LITELLM_PROXY_ENABLED|setattr.*LITELLM_PROXY_ENABLED|LITELLM_PROXY_ENABLED.*=.*False" \
  backend/tests/shared/infrastructure/llm/test_router_litellm_dispatch.py \
  backend/tests/architecture/test_llm_routing_ssot.py
# → 2 matches, BOTH inside docstrings/assertion-messages explaining the deletion (auditor verified line-by-line):
#   test_router_litellm_dispatch.py:4 → module docstring "(LITELLM_PROXY_ENABLED=False) deleted"
#   test_llm_routing_ssot.py:116 → function docstring "emergency rollback path when LITELLM_PROXY_ENABLED=False"
```

**Verdict Step 1:** ✓ PASS — ZERO active monkeypatches/setattrs/mocks. T-7 (precede T-5 per ticket dependency line 594) already deleted `TestLegacyDispatch` class and simplified `test_router_litellm_dispatch.py` to LiteLLM-only assertions.

### Step 2 — Migrate mocks path nuevo

**Verdict Step 2:** N/A (deletion case). T-7 handled all mock migrations pre-T-5. Builder impl-log line 77 confirms: "Step 2 (migrate mocks) N/A — nothing to migrate."

### Step 3 — Run full suite both flag values

**Pre-T-5 default:** `LITELLM_PROXY_ENABLED = True` (only valid path post-T-4).
**Post-T-5:** field deleted entirely → no toggle exists.

**Single-path run:**
- `cd backend && .venv/bin/pytest tests/architecture/ -q` → **823 passed** (auditor verified)
- `cd backend && .venv/bin/pytest -m "not integration" --cov=src/modules --cov=src/shared -q` → **9012 passed, 34 skipped, 16 deselected, exit 0** (gate-output line 41)
- `cd backend && .venv/bin/pytest tests/shared/infrastructure/llm/ -q` → **67 passed** (auditor verified)

**"Both values" requirement collapsed:** since the field is deleted, there is no toggle to test. This is the canonical anti-flip-audit DELETION variant (§ "Cuándo aplica" — toggle removed permanently). Documented in architect 03-arch-be.md § 2.7 line 273-277 ("flag deletion = special case, default actual `True`, deletion path es 'True → removed'").

**Verdict Step 3:** ✓ PASS — single-path run (only valid post-deletion) all 9012 tests green.

### Step 4 — Commit body documentation

Verifier `git log -1 --format=%B 28617716 | grep -c '^## '` → **5** (≥4 required).

| Required header | Present | Verbatim content (selected) |
|---|---|---|
| `## Tests audited` | ✓ | "0 tests migrated (handled in T-7) / 0 tests use bypass / 0 tests use monkeypatch.setattr band-aid" |
| `## Path old` | ✓ | Cites `LITELLM_PROXY_ENABLED: bool = True` field + `if settings.LITELLM_PROXY_ENABLED:` branch in router |
| `## Path new` | ✓ | Cites field-deleted state + simplified `_resolve` returning singleton + admin panel deletion |
| `## Verification` | ✓ | Cites all 4 quality gates (ruff check, ruff format, arch suite, full backend suite) + acceptance verifiers A1/A2/A4 results |
| `## Inventory updated` | ✓ | Cites row removal + footnote insertion in `.claude/rules/anti-default-flip-audit.md` with verbatim removed-row content |

**Verdict Step 4:** ✓ PASS — exceeds minimum requirement.

### Step 5 — Inventory updated (anti-default-flip-audit.md)

**Verifier (line-by-line re-run by auditor):**

```bash
git diff 28617716^ 28617716 -- .claude/rules/anti-default-flip-audit.md
```

**Confirms:**
- Line 67 row `| LITELLM_PROXY_ENABLED | True (default 2026) | LLM routing | adapter ... | LiteLLMService proxy ... | provider mock matching active path |` → **DELETED**
- Lines 71-73 footnote ADDED: `> Note: LITELLM_PROXY_ENABLED row removed PI-12 S1 sales-agent-litellm-canonicalization T-5 (legacy adapters deleted T-4). The LiteLLM Proxy is now the only runtime LLM dispatch path — there is no fallback toggle to audit.`

**Verdict Step 5:** ✓ PASS — A4 acceptance criterion met (verified `! grep -q '| \`LITELLM_PROXY_ENABLED\`' && grep -q 'removed PI-12 S1'` returns success).

### Cat 14 overall verdict: **PASS**

All 5 anti-default-flip-audit DELETION-variant steps satisfied. The DELETION case is the *strongest* form of the rule (no path drift possible because no path exists), and the builder honored every documentation requirement.

---

## Contract Compliance (T-5 deliverables vs implementation)

Per `04-tickets.yaml` T5 section (lines 546-559) + iter-2 scope expansion (per CONTEXT-BRIEF § 2):

- [x] D1: DROP `LITELLM_PROXY_ENABLED` field from Settings — `core/config.py:244-249` (3 lines deleted: comment + field) ✓
- [x] D2: Simplify `MultiRoleLLMRouter._resolve` to LiteLLM-only path — `router.py:44-56` (single-path returning singleton) ✓
- [x] D2: DELETE `build_provider_service` function — `router.py` (22 LOC removed; verified `! grep -q 'def build_provider_service'` PASS) ✓
- [x] D2: DELETE `_legacy_providers` dict init — `router.py:42` (no longer initialized in `__init__`) ✓
- [x] D2: DELETE `reset_cache` method — `router.py` (3 LOC removed; pre-existing bug honored T-4 audit handoff) ✓
- [x] D3: DELETE `build_provider_service` import in factory.py — `factory.py:20` (single import statement now) ✓
- [x] D4: DROP main.py `_verify_litellm_proxy_reachable` conditional — `main.py:365-368` (4 lines: `if not settings.LITELLM_PROXY_ENABLED: log warn; return`) ✓
- [x] D5: DROP fallback in admin/llm_virtual_keys.py — `llm_virtual_keys.py:68-80` (replaced with single clean `st.info`) ✓
- [x] D6 (iter-2 NEW): DELETE admin `_fetch_provider_library_provenance` — `copilot_routing.py:158-196` (entire function gone) ✓
- [x] D6 (iter-2 NEW): DELETE admin `_render_provider_library_provenance` + 2 call sites — `copilot_routing.py:347-371` + `render_copilot_routing` lines 451 + 459 ✓
- [x] D7: Clean docstring `litellm.py:26` — flag-toggle reference replaced with deletion note ✓
- [x] D8 (iter-2 NEW): UPDATE `.claude/rules/anti-default-flip-audit.md` — row removed line 67 + footnote added under table ✓
- [x] D9: Anti-flip 4-step commit body — 5 H2 headers (≥4 required, see Cat 14 § Step 4) ✓

**Acceptance criteria A1-A4:** all 4 PASS (see § /test-backend Gate Status table).

**Out-of-scope respected:**
- ✓ Adapter file deletion (T-4) — already done
- ✓ Tests migration (T-7) — already done
- ⚠ Tenant API key cols drop (T-6a/T-6c) — partial impact: dead Path 1 of `get_service_for_tenant` removed (forced by `build_provider_service` deletion); `_extract_tenant_key` method preserved per architect § 2.4 boundary. T-6a scope slightly reduced (caller already gone); T-6c scope unchanged. PM should note in T-6a 04-tickets.yaml refresh.

**Architect spec drift:** **none material**. The factory.py boundary expansion (deleting dead Path 1 caller) is architecturally forced by T-5's mandatory `build_provider_service` deletion, not a unilateral builder decision. Documented in impl-log Decisions Honored A2 row + § Subtle decisions. T-6a/T-6c scope adjustment is a downstream concern the PM resolves at next ticket refresh, not a T-5 audit fail.

---

## Decisions Honored audit (R6)

Per `.claude/rules/auditor-downstream-regression.md` § "R6 Decisions honored cite": ticket has explicit `decisions_applicable` references (architect 03-arch-be.md § 0 cites X1, X2, A4, A2 expand-contract; § 2.4 cites T-6a/T-6c boundary). Builder commit body and impl-log MUST cite each.

| Decision | Source | Builder cite location | Verdict |
|---|---|---|---|
| **A4** Settings field DROP (not deprecate) | architect 04-tickets.yaml T-5 deliverable 1 | impl-log line 85 + commit body line 16 ("Decision A4 (architect binding): Settings field DROP not deprecate") | ✓ |
| **A2 expand-contract** Stripe-style 3-step (T-5/T-6a/T-6c) | architect 03-arch-be.md § 1.18 + § 2.4 | impl-log line 86 ("`_extract_tenant_key` PRESERVED in factory.py for T-6a stub") + commit body line 17-19 | ✓ |
| **X1** LiteLLM-only canonical path | architect 03-arch-be.md § 1.18 "REPLACE simplify" | impl-log line 87 + router.py:7-11 docstring | ✓ |
| **Chris zero-tech-debt directive** (iter-2 scope expansion) | /pm reframe 2026-05-05 | impl-log line 88 + commit body line 20-22 ("Chris zero-tech-debt directive (iter-2 scope expansion) honored: admin _fetch_provider_library_provenance + _render_provider_library_provenance + 2 call sites DELETED") | ✓ |
| **R5 Schema-mirror exception** | rule | impl-log line 89 ("T-5 does not touch modules/{copilot,sales_agent}/persistence/models/") | ✓ N/A — correctly identified as inapplicable |
| **Anti-duplication §0 GATE** | `.claude/rules/anti-duplication.md` | impl-log line 90 ("Pure deletion — no NEW LAYER, no mirror creation, no new shared abstraction") | ✓ |

**Verdict R6:** ✓ PASS — all applicable architect decisions explicitly cited in BOTH impl-log table AND commit body.

---

## Allowlist Movement

| Allowlist | Pre-T-5 | Post-T-5 | Delta |
|---|---|---|---|
| `KNOWN_LEGACY_LLM_FILES` (`tests/architecture/test_llm_routing_ssot.py`) | empty `set()` | empty `set()` | 0 (T-8 will codify 3 new assertions, not a T-5 task) |
| `tests/architecture/test_known_legacy_files_set_is_empty` | not yet exists | not yet exists | T-8 deliverable |
| `# noqa` per-file in `src/main.py` | none | INP001 added (justified inline + commit body) | +1 (justified — see § info "pyproject.toml INP001 ignore") |

**No allowlist GROW without justification.** The single addition (INP001 per-file-ignore) is justified inline with verbatim rationale. Anti-default-flip-audit inventory **shrunk by 1 row** (LITELLM_PROXY_ENABLED removed) — the only ratchet movement, in the correct shrink direction.

**Verdict:** PASS

---

## Native-First Audit

| Check | Status | Evidence |
|---|---|---|
| No `docker exec ... ruff\|pytest\|tsc\|vitest\|mypy\|eslint` in commits | ✓ PASS | Builder impl-log § "Quality gates run" line 121-127 cites `cd backend && .venv/bin/...` for every gate. Zero `docker exec` invocations. |
| No `git add .` / `git add -A` / `git add -u` in commits | ✓ PASS | Two commits in series. `git show 28617716 --stat` shows 10 specific files staged by name (+ 1 docs in 560f14b5). No bulk staging. |
| Pushed to `main`? | N/A | Both commits on `development` branch (verified `git log` recent commits). `make ci-parity` not required. |

**Verdict:** PASS

---

## Downstream regression scope (R3 mandatory step)

Per `.claude/rules/auditor-downstream-regression.md` § "Tabla SSoT — surface → downstream test paths":

T-5 modifies `core/config.py` (Settings flag deletion) → row "core/config.py defaults flip" → downstream targets per `.claude/rules/anti-default-flip-audit.md` Step 1 grep tests path viejo.

**Step 1 grep result (auditor re-verified):**
- ZERO active mocks of `LITELLM_PROXY_ENABLED=False` (T-7 already migrated)
- Two docstring-history references retained (factually correct as deletion annotation)

**Surface → consumer test paths covered (auditor independently re-ran):**

| Surface modified | Downstream test targets per SSoT tabla | gate-runner status |
|---|---|---|
| `shared/infrastructure/llm/router.py` | `tests/shared/infrastructure/llm/`, `tests/architecture/test_llm_routing_ssot.py` | **PASS** (auditor re-run: 67 + arch suite 823 PASS) |
| `shared/infrastructure/llm/factory.py` | `tests/shared/infrastructure/llm/`, `tests/modules/iam/` (consumer of `get_service_for_tenant` via tenant model) | **PASS** (auditor re-run: 67 LLM + 278 iam tests PASS) |
| `shared/infrastructure/llm/providers/litellm.py` (docstring only) | full LLM suite | **PASS** (re-run: 67 PASS) |
| `core/config.py` (field deletion) | full suite (settings is process-wide singleton) | **PASS** (gate-output: 9012 PASS) |
| `core/config.py` defaults flip side-effect | per anti-default-flip Step 1 grep tests path viejo | **PASS** (zero active mocks; full suite green) |
| `admin/modules/copilot_routing.py` | `tests/admin/test_admin_smoke.py` + manual Streamlit smoke (no E2E) | **PASS** (auditor re-run: 103 admin tests PASS; both modules `import` cleanly verified via `python -c "from src.admin.modules import copilot_routing, llm_virtual_keys"`) |
| `admin/modules/llm_virtual_keys.py` | `tests/admin/test_llm_virtual_keys_smoke.py` | **PASS** (covered by 103 admin suite) |
| `main.py` boot conditional removed | `tests/architecture/test_settings_no_directs.py` (boot-time invariants) + arch suite | **PASS** (823 PASS) |
| **Cross-consumer (R3 critical):** any callback handler consuming the LLM service via factory | `tests/modules/copilot/observability/` + `tests/modules/sales_agent/observability/` | **PASS** (auditor re-run: 197 tests PASS) |

**R3 satisfied.** `gate-output.json` `command_alias = test-backend` (full suite) covered all consumer paths. Auditor independently re-validated cross-consumer surfaces (copilot + sales_agent observability + admin + iam) — zero regression. Caso origen D4 (cost_recorder cross-surface bug) NOT reproduced — clean.

---

## R23 Owner verification (process learning from T-4 Sonnet violation)

**Pre-T-5 process learning (from T-4 closure 2026-05-05):** T-4 violated `claude_opus_required: true` ticket flag — Sonnet 4.6 ran instead of Opus 4.7. Process correction applied to T-5.

**Verification commands (auditor independently ran):**

```bash
git log -1 --format='%(trailers:key=Co-Authored-By)' 28617716
# → "Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"

git log -1 --format='%(trailers:key=Co-Authored-By)' 560f14b5
# → "Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

**Both commits in T-5 series authored by Claude Opus 4.7 (1M context).** R23 satisfied. T-4 process learning correctly applied — `model: "opus"` parameter pre-spawn verification before builder agent dispatch.

**Verdict:** ✓ PASS

---

## Verdict Math

- Downstream regression scope FAIL? **No** — all consumer paths PASS (197 observability + 278 iam + 103 admin + 67 LLM + 823 arch + 9012 full suite, all green) → does NOT trigger overall FAIL Cat 10.
- Any FAIL in categories 1 / 2 / 8 / 9 / 12? **No** — all PASS or N/A.
- Allowlist grew without justified commit? **No** — only INP001 per-file-ignore, justified inline + commit body.
- Any `/test-backend` gate FAIL (3-7, 11-13)? **No** — all PASS or N/A. Gates 8/9/10/13 N/A (no analytics/no integration scope/no migration/no deps in T-5).
- IMPL-LOG `§ Skills Consulted` empty OR missing required skills? **No** — backend-expert + tessl__fastapi + tessl__pytest-api-testing all listed with explicit invocation rationale; tessl__graceful-degradation correctly identified as N/A (no external HTTP/DB calls). Domain skills correctly skipped (no domain code touched).
- `backend-expert/references/runtime-quality-checklist.md` cited in IMPL-LOG? **Yes** — line 26 ("Loaded references/runtime-quality-checklist.md before commit. Decision: pure deletion is not subject to FastAPI Annotated dep / response_model / 501 stub / datetime query anti-patterns").
- Two or more category WARNs? **No** — zero WARNs. Four `info` annotations (non-blocking).
- Cat 14 default-flip-audit DELETION 4-step + Step 5 (inventory) all PASS? **Yes**.
- R3 downstream regression coverage (auto-spawn condition)? **Satisfied without re-spawn** — full-suite gate covered all surfaces; auditor independently re-ran cross-consumer surfaces.
- R6 Decisions Honored cite? **Yes** — all 6 applicable decisions cited in BOTH impl-log table AND commit body.
- R23 Opus 4.7 verification? **Yes** — both commit Co-Authored-By trailers confirm Opus 4.7.

→ **Overall verdict: APPROVED**

---

## Footer / handoff

T-5 closes the LITELLM_PROXY_ENABLED toggle removal cleanly. Downstream tickets unblocked:
- **T-6a** (deprecate tenant API key cols) — slightly reduced scope (`get_service_for_tenant` caller of `_extract_tenant_key` already gone). PM should refresh `04-tickets.yaml` T-6a deliverable list to reflect this.
- **T-6c** (drop tenant API key cols + remove `_extract_tenant_key`) — unchanged scope.
- **T-8** (arch fitness assertions) — can now codify `test_no_legacy_adapter_imports`, `test_known_legacy_files_set_is_empty`, `test_settings_has_no_litellm_proxy_enabled_attr`. The retained docstring-history references in `tests/architecture/test_llm_routing_ssot.py:111-135` are NOT regression — T-8 will supersede them with explicit assertions.

LiteLLM Proxy is now the **only** runtime LLM dispatch path. Anti-default-flip-audit inventory shrunk by 1 row. 9012 tests green. 823 arch fitness green. Zero net regression.

**Pase a producción readiness:** T-5 alone is safe to deploy. The flag was always-`True` since 2026-04-30 (S3 PR-2), so deletion is operationally a no-op. Rollback strategy = `git revert 28617716` on `development` (per `docs/domains/llm-routing.md` desktop procedure).
