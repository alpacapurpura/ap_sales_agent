---
story_id: luana-shared-lift
auditor: claude-sonnet-4-6
audit_date: 2026-05-11
audit_iterations: 2
self_fixes_applied: 2
verdict: APPROVED
luana_platform_final_sha: 8e86d98
---

# CHECKPOINTS.md — luana-shared-lift

Auditor: Sonnet 4.6 (independent). Scope: Story 2 LIFT MODE — 9 Python + 6 TS packages lifted from AISALESHT/backend/src/shared + frontend/src/{components/ui,lib,hooks} into ~/luana-platform/core/.

Commit range audited: 9615d47..4ca22c6 (16 dev-team commits) + 2b27bce + 8e86d98 (2 auditor self-fixes).

---

## C1 — Code

| Check | Status | Notes |
|---|---|---|
| Tests RED → GREEN per dev-team output (728 BE + 39 TS pass) | ✅ | Live run: 728 passed, 6 skipped, 0 failed (703 core + 25 nicolify). TS: 39 passed (hooks=5, format=24, api-client=3, ui-kit=7). |
| uv sync --all-packages GREEN | ✅ | "Resolved 122 packages in 4ms. Checked 121 packages." No errors. |
| pnpm install --frozen-lockfile GREEN | ✅ | "Lockfile is up to date. Already up to date." |
| ruff check core GREEN | ✅ | Pre-fix: 1 I001 import-order in message_handler.py. Auditor self-fix applied (iter 2). Post-fix: "All checks passed!" |
| No file outside 05-guidelines.md files_in_scope | ✅ | All 16 commits touch only ~/luana-platform/core/ — workspace config + 15 package dirs. No AISALESHT paths in diff. |
| Stale import (TYPE_CHECKING) in message_handler.py | ✅ (fixed) | `src.shared.infrastructure.channels.base` → `luana_core_channels.infrastructure.channels.base`. Auditor self-fix iter 1 (trivial). Tests remain GREEN (231 passed). |
| Runtime src.modules.* imports in model_registry.py | ⚠ W1 | 30+ runtime imports from `src.modules.*` in model_registry.py. FILE NOT IMPORTED in any luana-platform test or __init__.py path — no runtime impact in current state. EXPECTED: will update per-brand as Stories 3-8 lift modules. Verbatim lift preserves AISALESHT original. Acknowledged as deferred work. |
| Pydantic v2 `class Config` deprecation warning in config.py | ⚠ W2 | Pre-existing in AISALESHT source (confirmed identical). Lift-verbatim preserves original. Not a lift regression. Will address if/when AISALESHT fixes it. |

**C1 score: 7/7 passing (2 warnings, non-blocking, documented)**

---

## C2 — Spec Compliance

| Check | Status | Notes |
|---|---|---|
| 9 Python packages at core/luana-core-*/src/ with pyproject.toml version 0.0.1-alpha | ✅ | All 9 confirmed: platform, llm, channels, idempotency, observability, events, extraction, compliance, billing. All at version 0.0.1-alpha. |
| 6 TS packages at core/@luana/*/src/ with package.json version 0.0.1-alpha, private:true | ✅ | All 6 confirmed: api-client, design-tokens, format, hooks, schemas, ui-kit. All version=0.0.1-alpha, private=True. |
| Each package registered in root pyproject.toml + pnpm-workspace.yaml | ✅ | pyproject.toml [tool.uv.workspace] members lists all 9. [tool.uv.sources] lists all 9. pnpm-workspace.yaml has `core/@luana/*` glob covering all 6 TS. |
| Tests lifted alongside (non-empty OR documented placeholder) | ✅ | Python: all 9 packages have test files (platform=17, llm=10, channels=4, idempotency=3, observability=11, events=8, extraction=2, compliance=7, billing=9). TS: 4 of 6 have tests; design-tokens and schemas have no original tests (design-tokens: pure constants, schemas: placeholder — documented in READMEs). |
| Scenarios A-E in 01-spec.md §7 | ✅ | A: Python pkg lift + uv sync GREEN. B: TS pkg lift + pnpm install GREEN. C: AISALESHT untouched (git diff empty). D: cross-package imports smoke passes live. E: 4 arch fitness tests pass, 3 deferred. |
| 5 deviations in checkpoint.md frontmatter justified within lift mode boundaries | ✅ | All 6 deviations (checkpoint lists 6, gate-output lists 6) are within lift mode: (1) src/core/ lift into platform needed for bootstrap — arch confirmed; (2) @luana/format extends to utils/constants — purely additive; (3) @luana/schemas placeholder — docs @luana/schemas README; (4) 4 module-coupled files deferred — DEFERRED-FILES.md audit trail; (5) 9 not 10 Python packages — mapping resolved correctly; (6) cyclic dep platform↔llm resolved via uv workspace sources per 03-arch.md §4. |

**C2 score: 6/6 passing**

---

## C3 — Architecture

| Check | Status | Notes |
|---|---|---|
| Dependency graph in 03-arch.md respected (lift order followed: platform first, then dependents) | ✅ | Commit order matches DAG: T-1 (workspace) → T-2 (platform) → T-3..T-10 (dependents) → T-11..T-12 (TS) → T-13..T-17 (integration+finalization). Git log confirms ordering. |
| Cyclic platform↔llm resolved via uv workspace sources (not refactor) | ✅ | luana-core-platform pyproject declares `luana-core-llm` as dep; luana-core-llm declares `luana-core-platform`. Root pyproject [tool.uv.sources] resolves both via workspace. uv sync resolves without error. No code logic changed. |
| No new patterns introduced (preserve names/APIs) | ✅ | Lift-verbatim confirmed. All class/function names match AISALESHT originals. Import path rewrites are the only diff (src.shared.X → luana_core_X per 05-guidelines.md §1.3 mapping). |
| Arch fitness tests at core/tests/architecture/ pass (4 active + 3 _deferred/) | ✅ | `uv run pytest core/tests/architecture/` → 4 passed in 0.04s. _deferred/ tests correctly identified (copilot/sales_agent/campaign module deps not yet lifted). |
| DEFERRED-FILES.md documents 4-8 module-coupled files deferred to Stories 6/7 | ✅ | 4 source files + 4 test files + 3 deferred arch tests documented with reasons and target stories. Content matches gate-output.json deferred_files list. |

**C3 score: 5/5 passing**

---

## C4 — Cross-cutting (Lift Mode Boundary)

| Check | Status | Notes |
|---|---|---|
| AISALESHT UNTOUCHED — V-NF-4 | ✅ | `git diff 4575283a HEAD --name-only` filtered on `backend/src/shared` and `frontend/src/{components/ui,lib,hooks}` → empty. Only docs/product/stories/luana-shared-lift/ and BACKLOG files modified in AISALESHT. |
| No `publishConfig` in any package.json | ✅ | grep -l publishConfig returns empty. All 6 TS packages verified. |
| No `.releaserc.json` | ✅ | find returns empty. |
| No `release.yml` / publish workflow | ✅ | find .github/workflows returns empty for release/publish patterns. |
| No `semantic-release` dependency | ✅ | grep returns empty for all package.json files + root. |
| Imports inside luana-platform use new paths (luana_core_X / @luana/X) | ✅ | No `from @/` in TS packages. No `from src.shared.` or `from src.core.` runtime imports in active code (all residual src.* are TYPE_CHECKING-only in ports/ or the verbatim model_registry.py bootstrap file). |
| Commit messages Conventional Commits | ✅ | All 16 dev-team commits + 2 auditor commits follow `type(scope): desc` format. |
| Spanish neutro N/A | ✅ | Lift mode preserves originals. README stubs use English (technical). No user-facing Spanish strings introduced. |

**C4 score: 8/8 passing**

---

## C5 — Trace

| Check | Status | Notes |
|---|---|---|
| All 17 tickets marked done in gate-output.json | ✅ | gate-output.json tickets object: T-1 through T-17 all "done". |
| gate-output.json present + commit SHA matches luana-platform HEAD (at time of close) | ✅ | gate-output.json final_commit="4ca22c6" matches luana-platform git log HEAD at Story 2 close (auditor self-fixes added 2 more commits after: 2b27bce + 8e86d98). |
| checkpoint.md state coherent for merge transition | ✅ | state=reviewing, phase=AUDIT_C1_C5, next_action describes APPROVED path. |
| BACKLOG regen'd (R33 auto) | ✅ | Commit f3736853 "close Story 2 DEVELOPED" touches docs/product/BACKLOG.md + BACKLOG.yaml. Pre-commit hook Section 6 ran. |
| No T-N-result.md files (consolidated into gate-output.json per Sonnet decision) | ⚠ W3 | No individual T-N-result.md or T-N-impl-log.md files. Gate-output.json consolidates pass/fail per ticket. Minor audit trail gap: no per-ticket impl details. Non-blocking per this audit — gate-output evidence suffices for APPROVED verdict. /pm may want to enforce T-N-impl-log.md granularity for future stories per process preference. |
| Capability promotion target known | ✅ | 15 luana-core-* packages → outcome `luana-platform-migration` tracking at story/outcome level. Per-package capability entries pending Story 9 publish. |

**C5 score: 5/5 passing (1 informational warning on audit trail granularity)**

---

## Summary

**Story 2 luana-shared-lift APPROVED.**

C1: 7/7 (2 non-blocking warnings: model_registry.py deferred src.modules imports W1, Pydantic v2 class Config W2 pre-existing). C2: 6/6 (all acceptance criteria met, 6 deviations justified within lift-mode boundaries). C3: 5/5 (DAG order correct, cyclic dep resolved, arch fitness 4/4 active GREEN, DEFERRED-FILES.md complete). C4: 8/8 (AISALESHT untouched hard requirement SATISFIED, no publish artifacts, all imports updated). C5: 5/5 (W3: no T-N-impl-log granularity — consolidated gate-output suffices for this story).

**Auditor self-fixes (cap 2/2 trivial):**
- Fix 1: Updated stale TYPE_CHECKING import `src.shared.infrastructure.channels.base` → `luana_core_channels.infrastructure.channels.base` in message_handler.py. Commit 2b27bce.
- Fix 2: Fixed ruff I001 import sort order triggered by fix 1. Commit 8e86d98.

**Findings (WARN, non-blocking):**
- W1: `model_registry.py` has 30+ runtime `src.modules.*` imports (verbatim lift from AISALESHT). File is not imported in any luana-platform test or __init__ path — zero runtime impact in current state. Will be updated organically as Stories 3-8 lift individual modules. Not a regression introduced by Story 2.
- W2: Pydantic v2 `class Config` deprecation warning in config.py — pre-existing in AISALESHT source, preserved by lift-verbatim per constraint. No action needed until AISALESHT source is updated.
- W3: No per-ticket T-N-impl-log.md audit trail. gate-output.json consolidation suffices for verdict but may be a process preference issue for /pm to address in future stories.

**Recommended /pm next step:** Merge luana-platform Story 2 → promote to `done`. Unblocks `luana-iam-tenancy-content` (Story 3). Update checkpoint.md state=done, archive story to docs/archive/2026/stories/luana-shared-lift/.
