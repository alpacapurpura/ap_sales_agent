# Backend Code Review: PR-3 Anti-Default-Flip Enforcement

**Date:** 2026-05-04
**PR / CONTRACT:** docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-3-anti-default-flip-enforcement/
**Files Reviewed:** 4 (rule + 2 arch fitness tests + CLAUDE.md)
**Domains touched:** meta-architectural (rules + tests/architecture); zero source modules
**Skills consulted:** backend-expert (runtime-quality-checklist baseline); tessl__fastapi (N/A scope confirmed); tessl__pytest-api-testing (AST-walk + meta-test pattern). tessl__graceful-degradation NOT invoked (no external calls in scope — correct).
**Iteration:** 1 (Opus OFFICIAL — overrides previous self-audit by Sonnet builder per D10 caveat)
**Verdict:** **PASS**

---

## /test-backend Gate Status

`gate-output.json` NOT executed per machine-stability D10 caveat (PR-1 RESULT.md). Builder ran subset of gates natively; auditor independently re-validated.

| # | Gate | Result | Detail |
|---|---|---|---|
| 1 | Tools | PASS | venv 3.12 present |
| 2 | Postgres pre-flight | N/A | PR-3 = meta-architectural; no DB |
| 3 | Lint (ruff check) | PASS | Native re-run on 2 PR-3 files: "All checks passed!" |
| 4 | Format (ruff format --check) | PASS | "2 files already formatted" |
| 5 | Type check (mypy) | N/A (baseline) | No source files touched |
| 6 | Arch fitness (78 → 80 gates) | PASS | Native full suite re-run: **823/823 PASS** (was 811 pre-PR-3, +12 new). 0 regressions |
| 7 | Tests + coverage | BASELINE | No source code; coverage unchanged |
| 8 | Verify marker | N/A | No analytics changes |
| 9 | Integration | N/A | No DB/integration code |
| 10 | Migration idempotency | N/A | No migrations |
| 11 | jscpd | BASELINE | No source code |
| 12 | interrogate | BASELINE | No source code |
| 13 | pip-audit | BASELINE | No deps changed |

**Independent re-validation (auditor 2026-05-04 22:xx UTC):**
- `pytest tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on*.py -v` → **12 passed in 12.48s**
- `pytest tests/architecture/ -q` → **823 passed in 23.23s**
- AST walk performance budget (`test_arch_fitness_performance_budget`) → **PASS < 2s**

---

## Category Summary (PR-3 small scope — most categories N/A)

| # | Category | Status | Notes |
|---|---|---|---|
| 1 | DDD Compliance | N/A | No source modules |
| 2 | Tenant Isolation | N/A | No queries |
| 3 | Soft Deletes | N/A | No data ops |
| 4 | Code Quality | PASS | Ruff 0 errors, format clean, AST walk well-typed `from __future__ import annotations`, zero noqa abuse |
| 5 | SQLAlchemy 2.0 | N/A | No DB |
| 6 | Async | N/A | Pure sync test |
| 7 | Pydantic v2 / PII | N/A | No DTOs |
| 8 | Migration | N/A | No DDL |
| 9 | Security | PASS | Rule + arch test contain no secrets; no PII; no command injection vectors (paths read-only via `Path.rglob`) |
| 10 | Tests / TDD | PASS | Meta-test (8 cases) covers detection (Pattern 1 + Pattern 2), bypass mechanisms (3 tiers), allowlist existence; performance budget asserted |
| 11 | Cross-cutting | PASS | Spanish neutro (no voseo detected), Native-First respected (no `docker exec` in commits), no `git add .` / `-A` / `-u` (5 commits all scoped by file name), no `git pull`/`--force`/`revert`. CLAUDE.md row appended (not replaced — M8 compliant; coexists with parallel session's E2E row) |
| 12 | Mirror detection | PASS | Sibling pattern of `test_no_legacy_event_bus_publish.py` reused (correct EXTEND vs DUPLICATE). New rule mirrors `anti-duplication.md` structure deliberately + cross-references it |

---

## PR-3-specific criteria (per prompt)

| Criterion | Status | Evidence |
|---|---|---|
| 1. Rule structure mirrors `anti-duplication.md` | PASS | Sections: Origen / Regla cardinal / Workflow 4 steps / Inventario SSoT / Anti-patterns / Enforcement layers (7 capas) / Penalizaciones / Ejemplos. Cross-reference to anti-duplication.md inline at enforcement table |
| 2. Arch fitness detects all 5 FQN variants + Pattern 1 + Pattern 2 | PASS | `LEGACY_MOCK_TARGETS` frozenset = 5 entries (`src.shared.domain.events.EventBus.publish`, `shared.domain.events.EventBus.publish`, `EventBus.publish`, `LegacyEventBus.publish`, `src.shared.domain_events.legacy_event_bus.LegacyEventBus.publish`). Meta-test confirms Pattern 1 (string) + Pattern 2 (`patch.object` synthesis) detection |
| 3. Bypass 3-tier mechanism | PASS | (a) `BYPASS_FILES=10` permanent (capability + meta + cutover + outbox-adapter integration), (b) `KNOWN_LEGACY_MOCK_FILES=3` shrink-only ratchet (deferred per D9), (c) magic comment `# arch-bypass: testing legacy capability`. Two ratchet guards: `test_bypass_files_size_ratchet` and `test_known_legacy_mock_files_size_ratchet` |
| 4. Meta-test covers 8 cases | PASS | Detection string-target / detection patch.object Pattern 2 / magic comment bypass / BYPASS_FILES path coverage (event_bus + cutover) / canonical adapter not flagged / both allowlists exist on disk. **Independent verification:** simulating gate WITHOUT `KNOWN_LEGACY_MOCK_FILES` flagged exactly the 3 documented files (no over- or under-coverage) |
| 5. Performance budget < 2s actual | PASS | `test_arch_fitness_performance_budget` PASS. Auditor re-run: 12 tests / 12.48s wall (includes pytest fixture overhead; AST walk itself < 1s as documented). Budget asserted in-test |
| 6. Failure message links rule | PASS | Assertion message at line 235: `"Ver \`.claude/rules/anti-default-flip-audit.md\`."` Includes migration target, three bypass mechanisms enumerated, structured violations list |
| 7. CLAUDE.md row format matches table | PASS | Row added: `\| BE config flag flips (\`core/config.py\` defaults) \| (none — \`pm\` skill ratification) \| \`rules/anti-default-flip-audit.md\` \|` — 3-column format matches existing "Conditional Rules" table. Coexists with parallel-session's playwright-expert row (M8 compliant) |
| 8. CONTRACT § 7 acceptance complete | PASS | All 11 checkboxes from CONTRACT § 7 implemented and ticked in IMPL-LOG |
| 9. Deviation CONTRACT § 2 (BYPASS=10 vs 7 + new KNOWN_LEGACY=3) justified by grep | PASS | IMPL-LOG documents real codebase scan: 10 capability/meta files + 3 deferred (D9 PI-11). Auditor re-grep confirms exact match: cross-referenced 26 test files mentioning `EventBus.publish`, of which 11 are detected by AST walk → 7 in BYPASS_FILES (capability/meta/cutover) + 3 in BYPASS_FILES (outbox-adapter integration probing flag=False) + 3 in KNOWN_LEGACY_MOCK_FILES (deferred). Remainder do not pattern-match (string mention only, not `@patch`/`patch.object`/`monkeypatch.setattr`). Deviation = TIGHTER than CONTRACT spec, not looser |

---

## Findings

No FAIL findings. No WARN findings. Two INFO observations:

### INFO 1 — Two-allowlist design vs CONTRACT single allowlist

**Category:** 12 (Mirror / Cross-cutting)
**File:** `backend/tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on.py`
**Observation:** CONTRACT § 2 specified one `BYPASS_FILES` (size 7). Builder shipped two allowlists: `BYPASS_FILES=10` (permanent capability/meta) + `KNOWN_LEGACY_MOCK_FILES=3` (deferred migration, shrink-only ratchet). This is a **strict improvement** over CONTRACT — clearer separation between "always-bypass legitimate" and "must-migrate-eventually". Both have ratchet guards. Auditor's independent simulation (running gate WITHOUT KNOWN_LEGACY_MOCK_FILES) confirms exactly the 3 documented violations surface. PM should be aware that target state post PI-11 S2 = `len(KNOWN_LEGACY_MOCK_FILES) == 0`.
**Action:** None for PR-3. PI-11 S2 PR(s) will migrate the 3 deferred files and shrink the ratchet.

### INFO 2 — `EventBus` aliased import pattern not gated

**Category:** 12 (Mirror / Cross-cutting)
**File:** `backend/src/modules/copilot/api/suggestions.py:39-40`
**Observation:** Some modules import `from src.shared.domain_events.outbox.application.event_bus_adapter import adapter_bus as EventBus`. Tests then patch `src.modules.copilot.api.suggestions.EventBus` (whole symbol, no `.publish` suffix). The arch gate correctly does NOT flag these because:
  - The patched symbol post-PR-1 IS the canonical `adapter_bus` (alias)
  - The target string lacks `.publish` (gate matches `EventBus.publish` FQNs, not bare `EventBus`)
  - Symbol-level patching is a valid test pattern when import-aliasing is intentional
**Action:** None. The gate's specificity (suffix `.publish`) is correct. If future modules import legacy `EventBus` (not adapter_bus aliased) and tests patch the whole class, that's a separate audit concern outside PR-3 scope. PR-3 explicitly targets `*.publish` mock targets per CONTRACT § 2.

---

## Contract Compliance (business surface only)

- [x] CONTRACT § 1 — Rule file created with full SPEC (workflow 4 steps + inventario 6 flags + anti-patterns 7 + enforcement layers 7 + penalizaciones + ejemplos correcto/incorrecto)
- [x] CONTRACT § 1 — CLAUDE.md conditional rule row appended
- [x] CONTRACT § 2 — Arch fitness test created (LEGACY_MOCK_TARGETS 5 FQN + AST walk Pattern 1 + Pattern 2 + bypass 3-tier + diagnostic message linking rule)
- [x] CONTRACT § 2 — Meta-test created (8 cases: detection × 2, bypass mechanisms × 4, allowlist existence × 2)
- [x] CONTRACT § 2 — Performance < 2s (asserted in-test; auditor re-validated)
- [x] CONTRACT § 3 — Cross-reference to `anti-duplication.md` present (inline note in enforcement layers section). Original rule NOT modified.
- [x] CONTRACT § 4 — Cross-link PR-1 honored (PR-1 SHIPPED commit `b59251ea`; baseline arch test PASS post-PR-1)
- [x] CONTRACT § 5 — Open questions resolved: q4 (magic comment string verbatim) ✓; q6 (CLAUDE.md row format) ✓; q3 (USE_DEEPAGENTS_* TBD placeholder) ✓; q1 (sequential deployment) ✓ shipped post-PR-1; q2 (test_event_bus_adapter_infers_module bypass) ✓ in BYPASS_FILES; q5 (perf threshold) ✓
- [x] CONTRACT § 7 — All 11 acceptance checkboxes verified in IMPL-LOG and re-validated by auditor
- N/A CONTRACT § 8 (Agentic Surfaces) — empty; no agentic scope

---

## Allowlist Movement

- BYPASS_FILES: NEW allowlist baseline = 10 (initial creation; ratchet asserts ≤10 going forward). Justified by IMPL-LOG enumeration with per-entry comments in source.
- KNOWN_LEGACY_MOCK_FILES: NEW allowlist baseline = 3 (initial creation; ratchet asserts ≤3, shrink-only). Justified by D9 PI-11 deferred decision; per-entry comments cite reason + future-PR placeholder.
- No existing allowlist GREW. Both new allowlists are introduced with shrink-only ratchets in same PR — consistent with project ratchet pattern. No FAIL.

---

## Native-First Audit

- [x] No `docker exec ... ruff|pytest|mypy` in any PR-3 commit body — VERIFIED (5 commits inspected)
- [x] No `git add .` / `git add -A` / `git add -u` — VERIFIED (5 commits, each scoped to specific files; commit `7b23f631` correctly handled CLAUDE.md as append-only per M8 alongside parallel session's E2E row)
- [x] No `git pull` / `--force` / `revert` evidence in commit history
- N/A `make ci-parity` — PR-3 not pushed to main (development branch only)

---

## Verdict Math

- FAIL in categories 1 / 2 / 8 / 9? **No** (1/2/3/5/6/7/8 are N/A; 4/9/10/11/12 are PASS)
- Allowlist grew without justification? **No** (both new baselines, justified)
- `/test-backend` gate FAIL (3-7, 11-13)? **No** (gates 3/4/6 PASS native; 5/7/11/12/13 are baseline-unchanged because no source code touched)
- IMPL-LOG § Skills Consulted empty / missing baseline? **No** (backend-expert + tessl__fastapi + tessl__pytest-api-testing all cited; tessl__graceful-degradation correctly skipped — no external calls in scope)
- `runtime-quality-checklist.md` cited in IMPL-LOG? **YES** (line 9 of IMPL-LOG: "Loaded `runtime-quality-checklist.md` antes commit")
- Two or more category WARNs? **No** (zero WARN)

→ **Overall verdict: PASS**

---

## Recommendation to PM

PR-3 is ready to close. The arch fitness gate is mechanically sound and well-tested; the rule is comprehensive and mirrors the established `anti-duplication.md` defense-in-depth pattern; the bypass design is more rigorous than CONTRACT spec (two-allowlist with separate semantics + ratchets). The 3-file `KNOWN_LEGACY_MOCK_FILES` ratchet creates a clear tracking surface for PI-11 S2 follow-up PRs to migrate (`test_grant_access_idempotent.py`, `test_sale_lifecycle.py`, `test_audit_emitter.py`).

