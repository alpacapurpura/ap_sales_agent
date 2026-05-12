<!-- voseo-allowed: guidelines cite rules + glossary verbatim for traceability per R25 -->
---
story_id: luana-nicolify-migration
guidelines_version: 1
architect_owner: claude-opus-4-7
ratified_by_chris: false
last_modified: 2026-05-12
parent_docs:
  - 01-spec.md
  - 03-arch.md
  - 03-arch-be.md
purpose: |
  Patterns required/forbidden for sub-agent builders + auditors during Story 10 build phase.
  Files in scope per ticket. Skills/rules to load per sub-agent type. Single-source process discipline.
---

# 05-guidelines — Story 10 sub-agent guidelines

> **Read first:** 01-spec.md §5 (Gherkin scenarios are BINDING — sub-agents implement to pass) + 03-arch.md §3 (Wave sequence + ticket overview) + 03-arch-be.md §2 (codemod mapping) + this doc (process discipline).
>
> **Audience:** `builder-backend` + `builder-frontend` sub-agents during T-1..T-14 build phase. Auditors `auditor-backend` + `auditor-frontend` consume this doc to verify compliance.

## 0. Cap paralelización + Opus priority (binding Chris framing)

**HARD CONSTRAINT:** ≤2 sub-agents simultaneous (NOT 3 — Chris stability over speed). `/dev-team` orchestrator enforces via `parallelization_cap: 2` in checkpoint frontmatter.

**Opus 4.7 mandatory tickets:**
- T-5 (copilot imports rewrite — agentic R23)
- T-6 (sales_agent imports rewrite — agentic R23)
- T-7 (shared/* cross-cutting — high cross-coupling risk, anti-duplication enforcement)
- T-2 (brand + offer — cross-cuts shared/agent_observability via PersonalityProfile dependency)
- T-8 (FE git mv + workspace registration + Vercel reconfig criticality)
- T-9 (Vercel reconfig + CF tunnel verify — Halt Triggers #3 + #4)
- T-10 (Alembic snapshot consolidation — Halt Trigger #5 schema drift)
- T-13 (/pm SSoT atomic git mv — Halt Decisión 4A hardcoded paths)

**Sonnet OK:**
- T-1 (baseline capture + arch fitness tests + scripts — mechanical TDD)
- T-3 + T-4 (BE business modules non-agentic sharded — mechanical)
- T-11 (Playwright smoke E2E — follows playwright-expert skill template)
- T-12 (Make ci-parity migration — mechanical)
- T-14 (AISALESHT archive + DB drop + Story 10 archive — mechanical closure)

**Sub-agent prompt header for Opus tickets** MUST contain:
```
PRODUCTION CODE: true (R23 — agentic production code mandates Opus 4.7)
PARALLELIZATION CAP: 2 concurrent agents max (Decisión 1A)
HALT TRIGGERS: per §7.6.2 (11 triggers) — escalate Chris, no silent proceed
```

## 1. Required patterns (sub-agent MUST honor)

### 1.1 Imports rewrite

**REQUIRED:**

- **Use `libcst` AST-based codemod** (BE) or `jscodeshift` AST-based codemod (FE). NEVER sed regex on production code paths — sed misses (a) `as` aliases, (b) multi-line imports, (c) string-literal type annotations, (d) `getattr(module, "X")` dynamic refs, (e) `__import__()`.
- **Rewrite test mocks in same commit as production rewrite.** If T-2 rewrites `src/modules/brand/` production imports, T-2 ALSO rewrites `tests/modules/brand/` mock paths in same commit. Auditor C5 verifies via `grep -r 'patch.*src\.' tests/`.
- **Preserve git history via `git mv` semantics.** Use `rsync -a` if cross-repo (per architect Phase 0 Q7 resolution — `git mv` doesn't span repos; commit narrative documents move).
- **One Wave subsystem at a time** (T-7 sub-shards per subsystem, ≤2 paralelo). NEVER mass-rewrite all shared/* in one commit — blast radius unbounded.
- **Verify `from src\.` count = 0 post each ticket** via `grep -rln "from src\.\|^import src\." {scope}/ | wc -l` (scope = files in ticket).
- **Verify test mock `patch("src.X.Y")` count = 0 post each ticket** via `grep -rln 'patch.*[\"\\\']src\\.' tests/{scope}/ | wc -l`.
- **Run arch fitness tests AFTER each rewrite ticket:**
  ```bash
  cd /home/chris/AISALESHT/backend  # or luana-platform/nicolify/backend post Wave 3
  .venv/bin/pytest tests/architecture/ -v --tb=short
  ```
- **Auditor reads `gate-output.json`** after each ticket — confirms `test_no_legacy_src_paths.py` + `test_no_legacy_src_mock_paths.py` GREEN.

**Baseline FIRST (T-1) — MANDATORY before any rewrite:**
- T-1 captures `baseline-be-tests.json` + `baseline-fe-tests.json` BEFORE any production code change
- T-1 produces `scripts/test_delta_check.py` + 4 new arch fitness tests
- T-1 commits all baseline artifacts as audit trail
- Subsequent tickets (T-2+) FAIL spawn if T-1 not closed `done`

### 1.2 Codemod scope discipline

**REQUIRED per ticket:**

- **Single Wave subsystem per ticket.** T-2 = brand + offer (Wave 1 BE business). T-5 = copilot only (Wave 2 agentic). T-7 = one shared subsystem at a time.
- **Reject scope creep.** If sub-agent during T-2 encounters `from src.shared.X` import that's not in T-2 scope → DO NOT rewrite. Document in `T-2-impl-log.md ## Out-of-scope discovered` + defer to T-7 Wave 2.
- **Idempotent codemod.** Re-running codemod on already-rewritten files MUST be no-op (architect Phase 0 sanity check).
- **Per-package verification commit** — one git commit per ticket. NEVER squash multi-ticket into one commit.

### 1.3 Test parity baseline + delta=0

**REQUIRED:**

- **T-1 captures baseline before any change** (BE + FE). Files committed: `baseline-be-tests.json` + `baseline-fe-tests.json` in story dir.
- **T-N final delta check** must pass `scripts/test_delta_check.py --max-new-failures=0` (BE + FE).
- **40 pre-existing sales_agent failures are baseline (Decisión 9B)** — they are in `M failed` of baseline, MUST remain in `M' failed` of final. NOT regressed. NOT fixed.
- **Fix-on-discovery 5min cap (Decisión 5B):** if rewrite encounters test failure with trivial fix (mock path stale, import alias), apply inline. Document in `T-N-impl-log.md ## Fix-on-discovery`. If >5min OR scope expansion → defer + DEFERRED-FAILURES doc entry.

### 1.4 Halt triggers honored (§7.6.2 — 11 triggers)

**REQUIRED:**

If sub-agent encounters ANY of these → STOP, document in `T-N-impl-log.md ## Halt Trigger #X raised`, escalate `/dev-team` orchestrator → Chris. NO silent proceed.

| # | Trigger | Sub-agent action |
|---|---|---|
| 1 | Coupling oculto cross-module no documentado outcome §2 | Halt + report missing symbol path + propose 3 mitigations |
| 2 | Builder rewrite cross-module dep to module in DIFFERENT Wave group | Halt + report Wave violation + propose re-shard |
| 3 | Vercel reconfig surface unexpected issue | Halt + document Vercel error verbatim + escalate Chris |
| 4 | CF tunnel `dev-app.nicolify.com` mapping rompe post-FE-move | Halt + document tunnel error + escalate Chris |
| 5 | Alembic snapshot surface schema inconsistency (models ≠ DB) | Halt + report drift table + propose 3 mitigations per Scenario 3.2 |
| 6 | Tests pass local but ci-parity root fails (env divergence) | Halt + document env diff + propose fix |
| 7 | Pipeline release-please primer execution falla | N/A Story 10 (orthogonal — Story 9 already merged Stories 1-9 release infra). Halt + escalate if encountered. |
| 8 | luana-platform monorepo state inesperado (uncommitted, branch mismatch) | Halt + `git status --short` capture + escalate Chris |
| 9 | Cumulative cost sesión > $5000 (soft check-in) | Report Chris cost @ $4000/$4500/$5000 markers. Continue execution. |
| 10 | Auditor + 2 auto-fix iter all fail | Halt + escalate. NO 3rd iter sin Chris ratify. |
| 11 | **Test mock `patch("src.shared.X.Y")` Y has NO equivalent in luana_core_X** | Halt + Trigger #11 workflow (03-arch-be.md §6) — Chris ratifies between (A) inline mock, (B) Story 14 lift defer, (C) magic comment skip |

### 1.5 Sub-agent skills loading per ticket

**REQUIRED skill loading (via Skill tool or context — sub-agent reads at task start):**

| Ticket | Skills MUST load |
|---|---|
| T-1 (baseline + scripts + arch tests) | `backend-expert` |
| T-2 (brand + offer) | `backend-expert` + `brand-expert` + `offer-expert` + `anti-duplication` (rule file) |
| T-3 (landing + assets + connections + scheduling + iam + crm + commercial_calendar) | `backend-expert` |
| T-4 (analytics + campaigns + social_proof + tenant_profile + tenant_domains + advertising + social_media) | `backend-expert` + `metrics-expert` (for analytics ETL contract surface) |
| T-5 (copilot — agentic R23 Opus) | `copilot-expert` + `tessl__langgraph` + `tessl__fastapi` + `backend-expert` |
| T-6 (sales_agent — agentic R23 Opus) | `sales-agent-expert` + `tessl__langgraph` + `tessl__graceful-degradation` + `backend-expert` |
| T-7 (shared/* cross-cutting) | `backend-expert` + `copilot-expert` (anti-duplication shared inventory) + `sales-agent-expert` (anti-duplication §0) |
| T-8 (FE git mv + imports rewrite) | `frontend-expert` |
| T-9 (Vercel reconfig + CF tunnel) | `frontend-expert` + `chrome-devtools-verify` (post-reconfig live verify) |
| T-10 (Alembic snapshot consolidation) | `backend-expert` (backend-migrations.md) |
| T-11 (Playwright smoke E2E) | `playwright-expert` (SSoT — replaces e2e-testing.md stub) |
| T-12 (Make ci-parity migration) | `backend-expert` |
| T-13 (/pm SSoT atomic git mv) | `backend-expert` + `pm` skill (capability + BACKLOG regen post-move) |
| T-14 (AISALESHT archive + DB drop + Story 10 archive) | `git-manager` + `pm` skill |

**ALL tickets** load these baseline rules:
- `.claude/rules/git-safety.md` (no `git pull`, no `--force`, no `--no-verify`)
- `.claude/rules/parallel-safety.md` (cap ≤2 paralelo Decisión 1A, no `git add .`)
- `.claude/rules/tdd-mandatory.md` (RED tests before GREEN — even for codemod scripts)
- `.claude/rules/anti-duplication.md` (shared abstractions inventory — NEVER mirror)
- `.claude/rules/anti-default-flip-audit.md` (NO flag flips Story 10 — pure migration)
- `.claude/rules/auditor-downstream-regression.md` (R3 scope cumulative for shared/* changes — auditor verifies downstream package consumers preserved post rewrite)
- `.claude/rules/spanish-text.md` (UI strings preserved — sales_agent voice exception)

## 2. Forbidden patterns (sub-agent MUST NOT do)

### 2.1 Scope expansion (HARD STOP)

**FORBIDDEN:**

- ❌ Refactor business logic during migration. Story 10 = mechanical imports rewrite ONLY. Zero new endpoints, zero new DTOs, zero new domain methods, zero boundary refactors.
- ❌ Touch `backend/src/admin/` Streamlit panel. **DEFERRED Story 10b** (Decisión 7B). Escape hatch via architect proposal — sub-agent does NOT decide.
- ❌ Touch `backend/src/workers/` + per-module `workers/` subdirs. **DEFERRED Story 10b/14** (Decisión 1A clarification). Halt if encountered.
- ❌ Fix the 40 sales_agent pre-existing failures. **DEFERRED Story 14** (Decisión 9B). Story 14 brand-voice-elevation natural home. T-N final generates `DEFERRED-FAILURES-STORY-10.md` with 40 paths.
- ❌ Touch Vitalia/Comunify/Lupulo brand dirs (`luana-platform/vitalia/`, `luana-platform/comunify/`, `luana-platform/lupulo/`). **DEFERRED Stories 11-13**.
- ❌ Add new feature flags or flip existing flag defaults. Story 10 is pure migration — `.claude/rules/anti-default-flip-audit.md` § "Tests audit" not invoked.
- ❌ Bump `_CATALOG_VERSION` in offer presets (no preset changes Story 10).
- ❌ Update baseline tests (`test_brand_editable_fields_baseline.py`, `test_buyer_persona_editable_fields_baseline.py`, etc.) — no description changes Story 10.

### 2.2 Anti-patterns by surface

**FORBIDDEN (BE imports rewrite — T-2..T-7):**

- ❌ sed regex on production code (use libcst AST). Acceptable: sed on test mock string literals if libcst doesn't capture.
- ❌ Skip test mock rewrite in same commit as production rewrite. Auditor C5 will catch + REVERT.
- ❌ Mass-rewrite all shared/* in one commit. T-7 sub-shards by subsystem, ≤2 paralelo. Blast radius unbounded otherwise.
- ❌ Touch `[COPILOT-*]` anchors (cap 36/36 frozen — T-5 preserves byte-stable).
- ❌ Touch 22 frozen `copilot → módulo` import ratchet (T-5 preserves — rewrites path strings but NOT import structure).
- ❌ Touch §3 NO TOUCH surfaces in sales_agent (`Closer Studio API + WS` · `SmartBufferService` · `OutputManager.process_response chunking` · `enrollment_*` · `agent_state_checkpoints schema` · webhook adapters · `follow_up_engine cadence math` · `PromptVersionModel` · `model_pricing_snapshot schema` · `tool_call_dedup.py`). T-6 rewrites imports inside these files but does NOT change their public surface.
- ❌ Mirror `shared/agent_observability` patterns in `modules/{copilot,sales_agent}/observability/recording/` (anti-duplication.md cardinal §0). Both modules consume shared via subclass.
- ❌ Create new test files. Migration is mechanical — existing tests cover the rewrite paths via existing module test suites.

**FORBIDDEN (FE imports rewrite — T-8):**

- ❌ sed regex on TS imports (use jscodeshift AST). String literals with `"@/..."` paths in dynamic imports must be tracked separately.
- ❌ Rewrite `from "@/app/..."` (Next.js routes — Nicolify-local).
- ❌ Rewrite `from "@/features/..."` (Nicolify business features — Nicolify-local).
- ❌ Rewrite `from "@/stores/..."` (Nicolify-local Zustand).
- ❌ Rewrite `from "@/components/shared/..."` (Nicolify layouts — stay local).
- ❌ Default exports for new files (Next.js pages exempted).
- ❌ Break FSD-Lite boundary plugin via cross-feature imports.
- ❌ `any` types introduced during rewrite (use `unknown` + type guards).

**FORBIDDEN (Alembic consolidation — T-10):**

- ❌ `op.create_table()` / `op.add_column()` / `op.create_index()` (NOT idempotent — `.claude/rules/backend-migrations.md`). Use raw SQL `IF NOT EXISTS`.
- ❌ `sa.Enum(..., create_type=True)` (broken SA 2.0.27 — use raw SQL `CREATE TYPE ... IF NOT EXISTS` via `DO $$ ... EXCEPTION WHEN duplicate_object` block).
- ❌ Skip Phase 0 spike (autogenerate + pg_dump diff). Halt Trigger #5 mandatory if drift > minimal cosmetic.
- ❌ Replay 131 historical migrations (Decisión 2B explicit — consolidate into `001_initial_snapshot.py`).
- ❌ Drop `visionarias_logs` DB before 24h soak post-smoke (Scenario 3.4 adversarial — sub-agent verifies preconditions).

**FORBIDDEN (/pm SSoT atomic — T-13):**

- ❌ `git pull` to "sync" branches (per parallel-safety.md cardinal). Push fails non-fast-forward → STOP + escalate.
- ❌ `git mv` without snapshot tarball audit trail (`/tmp/pre-move-snapshot.tar.gz` mandatory).
- ❌ Run scripts post-move without verify → if `python scripts/generate_backlog.py --check` fails post-move → Halt + rollback per Scenario 7.3.
- ❌ Commit hardcoded `/home/chris/AISALESHT/docs/product/...` paths in luana-platform scripts/rules (Halt Decisión 4A — replace with relative or `pathlib.Path(__file__).parents[N]`).
- ❌ Leak `docs/product/` content to public repos. luana-platform is PRIVATE (verified via `gh repo view alpacapurpura/luana-platform --json visibility --jq .visibility`).

**FORBIDDEN (AISALESHT archive — T-14):**

- ❌ Archive AISALESHT with uncommitted changes (Scenario 8.3 — Halt Trigger #8).
- ❌ Drop `visionarias_logs` DB before 24h soak elapsed (Scenario 3.4).
- ❌ Use `git revert` to roll back commits without Chris ratification (per git-safety.md).
- ❌ Force-push to AISALESHT main pre-archive (per git-safety.md).

### 2.3 Git workflow (cumulative — git-safety.md + parallel-safety.md)

**FORBIDDEN:**

- ❌ `git pull` (any form, any reason) — PROHIBITED sin excepción
- ❌ `git fetch && merge`
- ❌ `git push --force` / `--force-with-lease`
- ❌ `git revert` without Chris ratification
- ❌ `git reset --hard` without Chris ratification
- ❌ `git commit --no-verify` (pre-commit hook mandatory)
- ❌ `git add .` / `-A` / `-u` (parallel sessions have WIP)
- ❌ Feature branches / worktrees / release / hotfix branches (single branch `development` AISALESHT + `main` luana-platform)
- ❌ Push to `main` luana-platform without Chris approval (`main` = prod deploy auto)
- ❌ Tree sucio archivos AJENOS tocados — proceed NO TOUCH, report list

**REQUIRED:**

- Stage by exact filename: `git add path/file`
- Conventional Commits format: `feat(scope): summary`
- `git status --short` antes stage para categorizar MINE vs OTHERS
- Pre-commit hook runs natively (Sections 4-9 per architect Phase 0 Q7 path updates)
- Multi-file commit → delegate to Haiku worker via Agent tool per git-haiku-delegation.md (orchestrator decision, sub-agents commit single-file inline OK)

## 3. Files in scope (paths exact)

> **Critical:** sub-agent reads this list to know exactly what to touch + what NOT to touch.

### 3.1 MODIFIED (rewrite imports — main work)

**BE business modules (T-2..T-4):**
```
/home/chris/AISALESHT/backend/src/modules/brand/**/*.py
/home/chris/AISALESHT/backend/src/modules/offer/**/*.py
/home/chris/AISALESHT/backend/src/modules/landing/**/*.py
/home/chris/AISALESHT/backend/src/modules/assets/**/*.py
/home/chris/AISALESHT/backend/src/modules/connections/**/*.py
/home/chris/AISALESHT/backend/src/modules/scheduling/**/*.py   # Nicolify-local rewrite
/home/chris/AISALESHT/backend/src/modules/iam/**/*.py
/home/chris/AISALESHT/backend/src/modules/crm/**/*.py
/home/chris/AISALESHT/backend/src/modules/commercial_calendar/**/*.py
/home/chris/AISALESHT/backend/src/modules/analytics/**/*.py
/home/chris/AISALESHT/backend/src/modules/campaigns/**/*.py
/home/chris/AISALESHT/backend/src/modules/social_proof/**/*.py
/home/chris/AISALESHT/backend/src/modules/tenant_profile/**/*.py
/home/chris/AISALESHT/backend/src/modules/tenant_domains/**/*.py
/home/chris/AISALESHT/backend/src/modules/advertising/**/*.py    # Nicolify-local rewrite
/home/chris/AISALESHT/backend/src/modules/social_media/**/*.py   # Nicolify-local rewrite (empty scaffold)
```

**BE agentic modules (T-5, T-6 — Opus 4.7 mandatory):**
```
/home/chris/AISALESHT/backend/src/modules/copilot/**/*.py        # 150 files
/home/chris/AISALESHT/backend/src/modules/sales_agent/**/*.py    # 104 files
```

**BE shared subsystems (T-7 — sharded by subsystem, ≤2 paralelo):**
```
/home/chris/AISALESHT/backend/src/shared/agent_observability/**/*.py
/home/chris/AISALESHT/backend/src/shared/events/**/*.py
/home/chris/AISALESHT/backend/src/shared/domain_events/**/*.py
/home/chris/AISALESHT/backend/src/shared/billing/**/*.py
/home/chris/AISALESHT/backend/src/shared/compliance/**/*.py
/home/chris/AISALESHT/backend/src/shared/idempotency/**/*.py
/home/chris/AISALESHT/backend/src/shared/infrastructure/**/*.py
/home/chris/AISALESHT/backend/src/shared/application/**/*.py
/home/chris/AISALESHT/backend/src/shared/api/**/*.py
/home/chris/AISALESHT/backend/src/shared/domain/**/*.py
/home/chris/AISALESHT/backend/src/shared/links/**/*.py
```

**BE tests (parallel rewrite per ticket — same commit as production rewrite):**
```
/home/chris/AISALESHT/backend/tests/modules/**/*.py             # rewrite mock paths
/home/chris/AISALESHT/backend/tests/shared/**/*.py              # rewrite mock paths
/home/chris/AISALESHT/backend/tests/admin/**/*.py               # DEFERRED — Story 10b
/home/chris/AISALESHT/backend/tests/quality/**/*.py             # rewrite mock paths
/home/chris/AISALESHT/backend/tests/agentic_evals/**/*.py       # rewrite mock paths (Stories C/D/E/F simulator + grader)
```

**FE (T-8):**
```
/home/chris/AISALESHT/frontend/                                  # entire dir → git mv to luana-platform/nicolify/frontend/
/home/chris/AISALESHT/frontend/src/**/*.{ts,tsx}                 # rewrite @/components/ui → @luana/ui-kit etc.
/home/chris/AISALESHT/frontend/package.json                      # workspace deps + name
/home/chris/AISALESHT/frontend/playwright.config.ts              # path updates if needed
/home/chris/AISALESHT/frontend/e2e/                              # auth fixture path
```

**Alembic (T-10):**
```
/home/chris/AISALESHT/backend/alembic/versions/                  # 131 migrations → consolidate into 001_initial_snapshot.py at luana-platform location
/home/chris/luana-platform/nicolify/backend/alembic/versions/001_initial_snapshot.py  # NEW
```

**ci-parity (T-12):**
```
/home/chris/AISALESHT/Makefile                                   # ci-parity target migrates
/home/chris/AISALESHT/scripts/ci-parity.sh                       # moves to luana-platform/scripts/ + --brand= flag
/home/chris/AISALESHT/scripts/git-hooks/pre-push                 # path update
/home/chris/luana-platform/Makefile                              # add ci-parity-{brand} pattern + BRANDS var
/home/chris/luana-platform/scripts/ci-parity.sh                  # NEW (migrated)
/home/chris/luana-platform/.husky/pre-push                       # path update
```

**/pm SSoT (T-13 — atomic Phase 4):**
```
/home/chris/AISALESHT/docs/product/                              # moves to /home/chris/luana-platform/docs/product/
/home/chris/AISALESHT/scripts/generate_backlog.py                # moves
/home/chris/AISALESHT/scripts/reconcile_capabilities.py          # moves
/home/chris/AISALESHT/scripts/emit_process_metric.py             # moves
/home/chris/AISALESHT/scripts/_pii_patterns.py                   # moves (or lift to luana-core if cross-vertical — Phase 0 verify)
/home/chris/AISALESHT/scripts/git-hooks/pre-commit               # paths updated + moves
/home/chris/AISALESHT/backend/tests/scripts/                     # moves (R12 + freshness gate tests)
```

**AISALESHT archive (T-14):**
```
GitHub Settings → AISALESHT → Danger Zone → Archive (Chris manual OR gh api PATCH)
psql DROP DATABASE visionarias_logs;                             # post 24h soak + Chris ratify
docker compose -f /home/chris/AISALESHT/docker-compose.dev.yml down
/home/chris/AISALESHT/README.md                                  # final state per Phase 0 Q6 — skeleton pointing to luana-platform
```

### 3.2 NEW (architect emits via T-1)

```
/home/chris/AISALESHT/scripts/codemod_be_imports.py              # libcst AST codemod
/home/chris/AISALESHT/scripts/codemod_fe_imports.ts              # jscodeshift codemod
/home/chris/AISALESHT/scripts/test_delta_check.py                # baseline vs final delta calculator
/home/chris/AISALESHT/backend/tests/architecture/test_no_legacy_src_paths.py             # NEW arch fitness
/home/chris/AISALESHT/backend/tests/architecture/test_no_legacy_src_mock_paths.py        # NEW arch fitness
/home/chris/AISALESHT/backend/tests/architecture/test_consolidated_migration_idempotent.py  # NEW arch fitness
/home/chris/AISALESHT/backend/tests/architecture/test_delta_zero_enforcement.py          # NEW arch fitness
/home/chris/AISALESHT/docs/product/stories/luana-nicolify-migration/baseline-be-tests.json   # T-1 baseline audit trail
/home/chris/AISALESHT/docs/product/stories/luana-nicolify-migration/baseline-fe-tests.json   # T-1 baseline audit trail
```

### 3.3 NEW (architect emits via T-11)

```
/home/chris/luana-platform/nicolify/frontend/e2e/specs/smoke/chris-journey-e2e.spec.ts   # smoke E2E
```

### 3.4 NEW (architect emits via T-14)

```
/home/chris/luana-platform/docs/product/stories/luana-nicolify-migration/DEFERRED-FAILURES-STORY-10.md   # 40 sales_agent paths + Trigger #11 lifts
/home/chris/luana-platform/docs/product/stories/luana-nicolify-migration/HANDOFF-STORY-10B.md            # Chris next session handoff
```

### 3.5 OUT OF SCOPE (NEVER touch Story 10)

```
/home/chris/AISALESHT/backend/src/admin/                         # DEFERRED Story 10b
/home/chris/AISALESHT/backend/src/workers/                       # DEFERRED Story 10b/14
/home/chris/AISALESHT/backend/src/modules/sales_agent/           # touch ONLY for imports rewrite in T-6
                                                                  # but NEVER fix 40 pre-existing failures
/home/chris/luana-platform/vitalia/                              # Story 11
/home/chris/luana-platform/comunify/                             # Story 12
/home/chris/luana-platform/lupulo/                               # Story 13
/home/chris/luana-platform/core/luana-core-*/                    # Stories 1-9 published — NEVER touch luana-core packages source
                                                                  # (consumer migration consumes them — does not modify)
```

### 3.6 §3 NO TOUCH within sales_agent (T-6 preserves byte-stable)

Per `sales-agent-expert` skill §3:
```
/home/chris/AISALESHT/backend/src/modules/sales_agent/api/closer_studio.py                 # API + WS
/home/chris/AISALESHT/backend/src/modules/sales_agent/infrastructure/external/smart_debounce_runner.py  # SmartBufferService
/home/chris/AISALESHT/backend/src/modules/sales_agent/infrastructure/external/output_manager.py        # process_response chunking
/home/chris/AISALESHT/backend/src/modules/sales_agent/application/services/enrollment_*.py             # end-to-end enrollment
/home/chris/AISALESHT/backend/src/modules/sales_agent/infrastructure/persistence/models/agent_state_checkpoints.py  # schema
/home/chris/AISALESHT/backend/src/modules/sales_agent/api/webhooks/                                    # Telegram/WhatsApp/IG adapters
/home/chris/AISALESHT/backend/src/modules/sales_agent/application/services/follow_up_engine.py        # cadence math
/home/chris/AISALESHT/backend/src/modules/sales_agent/infrastructure/persistence/models/prompt_version.py  # PromptVersionModel
/home/chris/AISALESHT/backend/src/modules/sales_agent/application/orchestrator/tool_call_dedup.py     # anti-loop guard
```

**T-6 ALLOWED on these files:** ONLY import statement rewrites (`from src.X` → `from luana_core_X`). NO changes to method bodies, NO changes to public surface, NO new methods, NO refactor.

## 4. Auditor checklist (Story 10 specific)

Auditor `auditor-{backend,frontend}` post each ticket runs gate-runner + downstream regression + C1-C5 checks per `.claude/skills/auditor/SKILL.md`. Story 10 specific additions:

### C1 — Spec compliance (cite Gherkin scenarios)

- [ ] Each scenario §5 has corresponding implementation in commit
- [ ] Graders pass (shell commands + pytest assertions cited verbatim in scenario)
- [ ] Halt triggers honored — if invoked, audit trail records Chris ratify timestamp

### C2 — Architecture compliance

- [ ] `from src\.` count = 0 in scope-of-ticket post rewrite
- [ ] `patch.*"src\.` count = 0 in scope-of-ticket post rewrite
- [ ] No business logic changes (mechanical rewrite ONLY)
- [ ] §3 NO TOUCH preserved for sales_agent (T-6) — byte-equal except import statements
- [ ] Anchors `[COPILOT-*]` cap 36/36 preserved (T-5)
- [ ] 22 frozen `copilot → módulo` ratchet preserved (T-5)
- [ ] Anti-duplication §0: no mirror created in `modules/X/observability/recording/` etc. (T-5, T-6, T-7)

### C3 — Cross-cutting (tenant isolation, currency, locale, PII, Spanish, native-first)

- [ ] Smoke Scenario 5.4 GREEN (tenant cross-leak blocked post FE rewrite)
- [ ] Smoke Scenario 5.3 GREEN (cost_usd > 0 — no NULL regression per Story PI-12 S1 T-1.bis lesson)
- [ ] Currency `currency: str | None` DTOs preserved (no hardcoded USD introduced)
- [ ] Master data UTC + `useTenantLocale()` FE preserved
- [ ] PII `response_model=` allowlist preserved (every route)
- [ ] Spanish neutro preserved (`spanish-text.md` rule — UI strings; sales_agent voice exception)
- [ ] Native WSL execution (no `docker exec ruff/pytest/tsc/vitest`)

### C4 — Downstream regression (R3 scope cumulative)

When ticket modifies shared/ subsystem (T-7 sub-shards), auditor MUST run downstream regression per `.claude/rules/auditor-downstream-regression.md`. Tabla SSoT:

- `shared/agent_observability/` modified → run `tests/modules/copilot/observability/` + `tests/modules/sales_agent/observability/`
- `shared/infrastructure/llm/` modified → run consumer tests (todos modules llaman LLM)
- `shared/events/` + `domain_events/outbox/` modified → run all module application/ tests
- `shared/billing/` modified → run sales_agent + campaigns + copilot
- `shared/compliance/` modified → run campaigns + sales_agent
- `shared/application/extraction/` modified → run brand + offer + landing + buyer_persona

### C5 — Test mock path audit + Trigger #11 instances

- [ ] `grep -rn 'patch.*[\"\\\']src\\.' tests/` returns 0 cumulative
- [ ] Each Trigger #11 invocation documented in `DEFERRED-FAILURES-STORY-10.md` with Chris ratify timestamp + strategy chosen (A/B/C)
- [ ] Story 14 ticket queue captures lifts deferred (B path)
- [ ] Magic comments `# luana-migration-defer` linked to Story 14 ticket Q-XX (C path)

### C6 (Story 10 NEW) — Delta=0 enforcement

- [ ] `scripts/test_delta_check.py --max-new-failures=0` GREEN (BE)
- [ ] Same for FE
- [ ] 40 pre-existing sales_agent failures unchanged (in baseline, in final)
- [ ] Fix-on-discovery instances documented in `T-N-impl-log.md ## Fix-on-discovery` (≤5min cap each)

## 5. Audit trail discipline

Every ticket emits 3 files in `docs/product/stories/luana-nicolify-migration/`:

| File | Content |
|---|---|
| `T-N-impl-log.md` | Step-by-step implementation log + commands run + outputs + halts encountered |
| `T-N-result.md` | Summary: what was done + tests run + commit SHA + grader assertions GREEN |
| `T-N-review.md` | (Auditor emits) C1-C6 check results + verdict APPROVED/CHANGES_REQUESTED |

**Halt trigger documentation pattern:**
```markdown
## Halt Trigger #X raised at YYYY-MM-DDTHH:MM:SSZ

**Context:** {what sub-agent was doing}

**Trigger evidence:**
{verbatim error or command output that triggered halt}

**3 mitigation options:**
- (A) {option}
- (B) {option}
- (C) {option}

**Chris ratify:** YYYY-MM-DDTHH:MM:SSZ — {strategy chosen} — rationale: {Chris's note}

**Resume action:** {what sub-agent did post-ratify}
```

## 6. Process metrics (R12 layer 1 emission)

Each ticket emits a process metric line via `scripts/emit_process_metric.py`:

```bash
python scripts/emit_process_metric.py \
    --story=luana-nicolify-migration \
    --ticket=T-{n} \
    --owner=builder-{backend,frontend} \
    --duration_minutes={N} \
    --cost_usd={N} \
    --halt_triggers_invoked={comma-separated #s} \
    --files_modified={N} \
    --tests_added={N} \
    --tests_modified={N}
```

T-N final ticket aggregates cumulative metrics + cost summary. Reports vs $5000 cap soft check-ins.

## 7. Skill helpers and slash commands available

| Tool | When to invoke |
|---|---|
| `/commit-push` slash command | Multi-file commit + push (delegates to Haiku worker per git-haiku-delegation.md) |
| `/test-backend` slash command | Spawn gate-runner BE post each BE rewrite ticket |
| `/test-frontend` slash command | Spawn gate-runner FE post each FE rewrite ticket |
| `/test-all` slash command | Final delta check pre Story 10 review (T-N) |
| `chrome-devtools-verify` skill | Live verify Vercel deployment post T-9 (FE workspace move) |
| `playwright-expert` skill | T-11 smoke E2E construction (SSoT — Clerk auth, POMs, fixtures, native execution) |
| `git-manager` skill | T-14 archive + closure (gh api archive, branch cleanup) |
| `pm` skill | T-13 + T-14 — capability promotion, BACKLOG regen, archive at luana-platform location |

## 8. Final checklist (Auditor T-N before APPROVED verdict)

- [ ] All 14 tickets `done` per checkpoint
- [ ] `grep -rn "from src\." luana-platform/nicolify/backend/src/` returns 0 (assertion via arch fitness `test_no_legacy_src_paths.py`)
- [ ] `grep -rn 'patch.*[\"\\\']src\\.' luana-platform/nicolify/backend/tests/` returns 0 (assertion via arch fitness `test_no_legacy_src_mock_paths.py`)
- [ ] `grep -rn 'from "@/' luana-platform/nicolify/frontend/src/` returns 0 (manual verify if no arch fitness equivalent FE-side — architect Phase 0 Q open)
- [ ] `scripts/test_delta_check.py --max-new-failures=0` GREEN (BE + FE)
- [ ] `make ci-parity` from luana-platform GREEN
- [ ] Smoke E2E Chris journey GREEN (T-11 spec)
- [ ] AISALESHT `git status --short` clean (pre-archive)
- [ ] `gh api repos/alpacapurpura/AISALESHT --jq .archived` returns `true` (post Chris archive)
- [ ] `psql -lqt | grep -qw visionarias_logs` exit 1 (post 24h soak + Chris ratify drop)
- [ ] `psql -lqt | grep -qw nicolify_dev` exit 0 (new DB exists)
- [ ] luana-platform/docs/product/ scripts GREEN (`generate_backlog.py --check` + `reconcile_capabilities.py --check`)
- [ ] luana-platform/docs/archive/2026/stories/luana-nicolify-migration/checkpoint.md state=`done`
- [ ] DEFERRED-FAILURES-STORY-10.md exists with 40 sales_agent paths + Trigger #11 lifts
- [ ] HANDOFF-STORY-10B.md exists with scope + inherited decisions + open re-ratify per session
- [ ] outcome §1 stories_done = 10/14 (BACKLOG regen reflects)
- [ ] All Halt Triggers (if invoked) have Chris ratify timestamp in audit trail
- [ ] R12 process metrics aggregated cumulative (cost cap $5000 honored)
- [ ] /pm capability promoted `luana-core/brand-consumer-migration.yaml` status=done
- [ ] R3 downstream regression cumulative GREEN (Stories 1-9 luana-core consumers preserved)

## 9. References

- `01-spec.md` — BINDING Gherkin scenarios (sub-agent implements to pass)
- `03-arch.md` — consolidated overview (Wave sequence, surface→builder mapping, risks)
- `03-arch-be.md` — BE deep dive (codemod mapping, alembic, Trigger #11 workflow)
- `docs/product/outcomes/luana-platform-migration.md` §7.6 (binding decisions) + §7.6.1 (cross-story inheritance) + §7.6.2 (11 halt triggers) + §7.6.3 (success criteria)
- `/home/chris/luana-platform/docs/migration-from-nicolify.md` §3 (canonical import mapping SSoT)
- Skills: `backend-expert`, `frontend-expert`, `copilot-expert`, `sales-agent-expert`, `brand-expert`, `offer-expert`, `offer-type-preset-expert`, `metrics-expert`, `playwright-expert`, `pm`, `git-manager`, `chrome-devtools-verify`, `tessl__langgraph`, `tessl__fastapi`, `tessl__graceful-degradation`
- Rules: `.claude/rules/{git-safety,parallel-safety,tdd-mandatory,anti-duplication,anti-default-flip-audit,auditor-downstream-regression,backend-ddd,backend-migrations,tenant-isolation,spanish-text,e2e-testing}.md`
- Story 9 precedent: `docs/archive/2026/stories/luana-v0-1-0-publish/{03-arch.md,03-arch-be.md,07-merge.md}`
