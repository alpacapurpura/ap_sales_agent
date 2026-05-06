<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# Backend Code Review: T-9 Documentation purge (LiteLLM canonicalization)

**Date:** 2026-05-05
**PR / CONTRACT:** PI-12 S1 sales-agent-litellm-canonicalization · ticket T-9 · 04-tickets.yaml § T9
**Files Reviewed:** 7 (5 docs + 2 sales_agent docstrings)
**Domains touched:** docs (llm-routing, tech_module_shared, sales-agent product), sales_agent (docstring textual touch)
**Skills consulted:** backend-expert (runtime-quality-checklist), tessl__fastapi (N/A — no router surface), tessl__pytest-api-testing (N/A — no tests added), tessl__graceful-degradation (N/A — zero external calls), spanish-text rule (R2 voseo glosario)
**Commits:** `aabd3acc` (main 7 files) + `c93ba549` (SHA backfill in impl-log)
**Verdict:** **PASS**

## /test-backend Gate Status

Source: `gate-output.json` (gate-runner Haiku ran scoped subset per docs ticket; pragmatic R22 fallback documented).
Note: gate-runner ran scoped command (lint+format+pytest scoped to sales_agent + arch_hardcoded_models + 4 acceptance verifiers), not full `/test-backend` 13-gate suite, because T-9 surface is 99% docs and Python touches are 2 docstring lines with zero AST semantic change.

| # | Gate | Result | Detail |
|---|---|---|---|
| 1 | Tools | PASS | ruff + pytest in venv 3.12 |
| 2 | Postgres pre-flight | N/A | docs ticket — no migration |
| 3 | Lint (ruff check) | PASS | scoped to 2 sales_agent files; 0 errors |
| 4 | Format (ruff format --check) | PASS | 2 files already formatted |
| 5 | Type check (mypy) | N/A scoped | docstring textual change — no annotation surface |
| 6 | Arch fitness | PASS (subset) | `test_no_hardcoded_models_sales_agent.py` PASS |
| 7 | Tests + coverage | PASS | 680/680 sales_agent module tests PASS, zero regression |
| 8 | Verify marker | N/A | docs ticket |
| 9 | Integration | N/A | docs ticket |
| 10 | Migration idempotency | N/A | no migration |
| 11 | jscpd | N/A scoped | docs only |
| 12 | interrogate | N/A scoped | 2 Python files modified retain prior docstrings |
| 13 | pip-audit | N/A | no deps change |
| Acc1 | A1 verifier (`! grep LITELLM_PROXY_ENABLED|rollback`) | PASS | re-verified by auditor independently |
| Acc2 | A2 verifier (`! grep KimiService\|...` in 2 files) | PASS | re-verified by auditor |
| Acc3 | A3 verifier (`grep '## CustomLogger pattern'`) | PASS | re-verified by auditor |
| Acc4 | A4 verifier (Spanish neutro 8-term grep) | PASS | re-verified by auditor + extended 23-term grep across all 4 user-facing docs also clean |

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | DDD Compliance | PASS | 0 |
| 2 | Tenant Isolation | N/A | 0 (no DB queries touched) |
| 3 | Soft Deletes | N/A | 0 |
| 4 | Code Quality | PASS | 0 |
| 5 | SQLAlchemy 2.0 | N/A | 0 (no DB code) |
| 6 | Async Consistency | N/A | 0 |
| 7 | Pydantic v2 / PII | N/A | 0 (no DTOs/responses) |
| 8 | Migration Quality | N/A | 0 |
| 9 | Security | N/A | 0 |
| 10 | Tests / TDD | PASS | 0 (docs ticket, no tests required; no regression in 680 tests) |
| 11 | Cross-cutting | PASS | 0 (Spanish neutro CRITICAL — clean; R6 decisions cited; native-first; parallel-safety scoped commits) |
| 12 | Anti-duplication / Mirror | PASS | 0 (no new files; learnings.md is documentation, not pattern mirror) |
| 14 | Default flip side-effect | N/A | 0 (T-9 doesn't touch core/config.py) |

## Cross-scope flags

| File | Module | Auditor judgment |
|---|---|---|
| `backend/src/modules/sales_agent/domain/model_tier.py` (3-line docstring touch) | sales_agent | **Accepted under pragmatic interpretation** (info-level flag below) |
| `backend/src/modules/sales_agent/application/agents/sales/nodes.py` (5-line docstring touch) | sales_agent | **Accepted under pragmatic interpretation** (info-level flag below) |

### info: Sales_agent docstring touches — pragmatic R5 spirit application

**Category:** 1 (DDD scope — agentic boundary)
**Files:** `backend/src/modules/sales_agent/domain/model_tier.py:30`, `backend/src/modules/sales_agent/application/agents/sales/nodes.py:192`
**Issue:** CLAUDE.md hard rule states "AGENTIC tickets (modules/copilot, modules/sales_agent) → Opus 4.7 SIEMPRE", typically routed through `builder-agentic`. T-9 is owned by `builder-backend` per architect (4o-tickets.yaml § T9 owner_eligibility = `claude_opus_required: true` but type=`docs`). Both docstring edits live inside `modules/sales_agent/{domain,application}/`, which is agentic-territory by default.
**Auditor judgment:** ACCEPTED under R5 schema-mirror exception **spirit** (textual-only changes, zero behavioral diff). Justification:

1. **Only diff:** docstring text replacement of `KimiService._get_chat_model` → `LiteLLMService (vía litellm_config.yaml model entry)`. Zero AST semantic change (docstrings don't run).
2. **Zero behavioral risk:** 680/680 sales_agent module tests + arch_hardcoded_models PASS. Module imports verified intact (`LLM_ROLE_BY_SITE`, `SPECIALIST_TO_ROLE`, `node_closer`, `node_product_expert`).
3. **Architect explicit allowance:** ticket spec § "NOTE on sales_agent module ownership" instructs builder-backend to handle pragmatically with /pm fallback if auditor flags.
4. **Builder transparency:** commit body § "Sales_agent module ownership note" + impl-log § "Cross-module reads" both document the decision and request auditor scrutiny.
5. **Owner verified Opus 4.7:** Co-Authored-By header on commit `aabd3acc` reads `Claude Opus 4.7 (1M context)` — agentic-grade reasoning was applied even though spawn was builder-backend.
6. **R5 schema-mirror precedent:** R5 already established that builder-backend may touch `modules/{copilot,sales_agent}/persistence/models/` for schema ripple from shared/ migration — without case-by-case auditor judgment. T-9 is the spiritual analog: textual ripple from T-4 deletion (KimiService class no longer exists). Re-spawning builder-agentic for 2 docstring text-replacement lines is process overhead disproportionate to risk.

**Recommendation:** /pm document this as a precedent extension of R5 (or creation of R5b "textual-mirror exception") in next process-improvement cycle, so the pattern is codified and future docstring-touch tickets don't require auditor judgment. No action required for T-9 closure.

**Skill ref:** `.claude/rules/backend-ddd.md` § "Schema-mirror exception" (R5); CLAUDE.md "Hard rule" agentic routing.

## Findings

### PASS items (no findings, summary only)

**Cat 1 (DDD):** No business logic in api/, no DB queries in services, domain pure. T-9 touches no layered code beyond docstrings.

**Cat 4 (Code Quality):** Ruff check + ruff format clean on 2 modified Python files. No `# noqa`, no `# type: ignore` introduced. Docstrings remain Google-style.

**Cat 10 (Tests / TDD):** Per `.claude/rules/tdd-mandatory.md` § "No aplica: config pura, docs, styling sin lógica" — TDD doesn't apply to docstring textual changes. No test regression: 680/680 sales_agent + arch_hardcoded_models PASS. Spec did not require new tests; A1-A4 are bash grep verifiers, all PASS.

**Cat 11 (Cross-cutting):**
- ✅ **Spanish neutro LATAM CRITICAL (A4):** Auditor independently grep'd 23 voseo terms across all 5 modified docs. ZERO matches in user-facing docs (llm-routing, tech_module_shared, sales-agent, learnings). The 3 occurrences in `T-9-impl-log.md` are inside the audit trail table and are correctly escaped via R25 magic comment `<!-- voseo-allowed: technical reference citing the voseo→neutro glosario verbatim... -->` on line 3 (per `.claude/rules/spanish-text.md` § "Magic comment escape").
- ✅ **R6 Decisions honored cite:** Commit body § "Decisions honored (R6)" cites all 5 binding decisions verbatim with locations:
  - A1 BINDING T-1 (slashed model field) → `llm-routing.md` Recorder row
  - X2 BINDING T-1 (calculator.py reconciliation-only) → `llm-routing.md` CustomLogger section + `learnings.md` §1
  - A2 BINDING T-6a (expand-contract Phase 1) → `llm-routing.md` Capa 5 + `sales-agent.md` LLM routing
  - A3 BINDING T-4 (gemini audit checklist 6/6) → `learnings.md` §3
  - R7 process-improvement (T-6b 1d wall-clock pre-clientes) → `learnings.md` §2
- ✅ **Native-first:** No `docker exec ... ruff|pytest` in commits. Builder ran native venv per impl-log § "Acceptance + quality gates".
- ✅ **Parallel-safety:** `git add` by exact file name (7 files). No `git add .|-A|-u`. Ajenos files (T-8 session leftover + CONTEXT-BRIEF-validation auto-modified during T-9 brief gen) preserved untouched per M1/M8 (impl-log § "State at handoff").
- ✅ **Master data / currency:** N/A (docs ticket, no DTOs / monetary fields touched).
- ✅ **Native-first push:** Push to `development` (commit hash `aabd3acc..253e6024 → aabd3acc`), not `main`. `make ci-parity` not required for `development` push.

**Cat 12 (Mirror detection):** No new code files. The 2 NEW docs files (`learnings.md`, `T-9-impl-log.md`) are story-scoped artifacts following established `docs/projects/active/PI-N/.../05-impl/` and `06-audit/` patterns. No cross-module mirror risk.

## Contract Compliance (business surface only)

T-9 is a docs ticket — no Pydantic entities, no DTOs, no FastAPI routes, no repositories, no migrations, no domain events. Architect deliverables verified:

- [x] llm-routing.md DELETE old "Capa 5 — LiteLLM Proxy (rollback)" → done (line 21 now reads "Capa 5 — LiteLLM Proxy = canonical único"; toggle row removed from table)
- [x] llm-routing.md REWRITE "Capa 5" → done with shipped 2026-05-06 marker, single-path language, no fallback/toggle/reversal verbiage
- [x] llm-routing.md ADD "## CustomLogger pattern (cost recorder)" → done (lines 49-90, comprehensive: components, NEW class justification, TTL invariants, cost runtime vs reconciliation, references to T-1 commit)
- [x] tech_module_shared.md REMOVE legacy adapter list → done (lines 18-24 rewritten to LiteLLM-only with cost_recorder reference)
- [x] model_tier.py:30 KimiService → LiteLLMService (vía litellm_config.yaml) → done
- [x] nodes.py:192 KimiService._get_chat_model → LiteLLMService → done
- [x] learnings.md NEW with 3 sections → done (CostRecorderCustomLogger NEW class justification §1, T-6b operational gate rationale §2, gemini audit 6/6 PASS §3)
- [x] sales-agent.md UPDATE § "LLM routing" → done (model name refresh K2.5→K2.6, V3→DeepSeek-Reasoner; new ## LLM routing section with deprecation status)

**Architect § 8 Agentic Surfaces flag:** N/A — T-9 has no agentic logic. The 2 docstring touches in sales_agent are flagged in cross-scope table above with auditor judgment.

## Allowlist Movement

- No allowlist files modified in T-9. `KNOWN_LEGACY_LLM_FILES` set stayed empty post-T-8 (separate ticket already merged at commit `253e6024`). T-9 doesn't introduce new violations or move ratchets.

## Native-First Audit

- ✅ No `docker exec ... ruff|pytest|tsc|vitest|mypy|eslint` in commit `aabd3acc` or `c93ba549`.
- ✅ No `git add .` / `git add -A` / `git add -u` (impl-log § "Commit + push" + parallel-safety enforcement).
- ✅ Pushed to `development` (not main) — `make ci-parity` not required.

## Downstream regression scope (per `.claude/rules/auditor-downstream-regression.md`)

| Surface modified | Tabla SSoT match? | Downstream test targets |
|---|---|---|
| `docs/domains/llm-routing.md` | NO (docs SSoT, not code surface) | N/A |
| `docs/domains/tech_module_shared.md` | NO | N/A |
| `docs/product/modules/sales-agent.md` | NO | N/A |
| `backend/src/modules/sales_agent/domain/model_tier.py` (docstring) | NO (sales_agent module path not in SSoT table — module-level entries are for `shared/agent_observability/`, `shared/infrastructure/llm/`, `core/config.py`) | gate-runner already ran sales_agent suite (680/680 PASS) |
| `backend/src/modules/sales_agent/application/agents/sales/nodes.py` (docstring) | NO (same reason) | gate-runner already ran sales_agent suite (680/680 PASS) |
| `docs/projects/.../learnings.md` (NEW) | NO | N/A |
| `docs/projects/.../05-impl/T-9-impl-log.md` (NEW) | NO | N/A |

**No additional downstream gate-runner spawn required.** Surfaces modified do not trigger SSoT tabla entries:
- T-9 does NOT touch any path in `shared/agent_observability/`, `shared/infrastructure/llm/`, `shared/domain_events/outbox/`, `shared/idempotency/`, `shared/billing/`, `shared/compliance/`, `shared/events/`, `shared/links/ports/`, `shared/domain/locale.py`, `core/config.py`, `core/enums/`, `modules/copilot/observability/recording/`, `modules/sales_agent/observability/recording/` (covered by R3+R5), or any FE shared paths.
- The 2 sales_agent docstring touches are textual-only (zero AST semantic change). Original gate-runner subset (680/680 sales_agent + arch_hardcoded_models PASS) covers consumers of `LLM_ROLE_BY_SITE`, `SPECIALIST_TO_ROLE`, `node_closer`, `node_product_expert`.

## R31 / R23 / R26 / R5 / R7 enforcement checks

| Rule | Check | Result |
|---|---|---|
| R31 (auto-prefix voseo-allowed magic comment in audit review) | This file's first line is the magic comment | ✅ PASS |
| R23 (owner verification) | Co-Authored-By in `aabd3acc` reads `Claude Opus 4.7 (1M context)`; impl-log front-matter `assigned_to: claude-opus-4-7` | ✅ PASS |
| R24 (CONTEXT-BRIEF validation gate) | `Validator pass: CLEAN`, `Faithfulness flag: provisional clean` (validator confirmed CLEAN); not blocking | ✅ PASS |
| R25 (voseo magic comment escape) | T-9-impl-log.md line 3 has correct `<!-- voseo-allowed: technical reference... -->` for legitimate audit-trail glosario citation | ✅ PASS |
| R26 (hot-fix repro mandatory) | T-9 is NOT a hot-fix ticket (state=`draft` from architect inception, not `bis`/`fix forward`/`incident`/`regression`). N/A. | N/A |
| R6 (decisions honored cite) | Commit body explicitly cites 5 binding decisions with locations | ✅ PASS |

## Verdict Math

- ❌ Downstream regression FAIL → **NO** (no shared/ paths touched; 680/680 sales_agent tests PASS)
- ❌ Cat 1/2/8/9/12 FAIL → **NO** (Cat 1 has info-level scope flag accepted under R5 spirit, not FAIL)
- ❌ Allowlist grew without justification → **NO** (no allowlist movement)
- ❌ Any /test-backend gate FAIL → **NO** (all relevant gates PASS, scoped subset documented)
- ❌ IMPL-LOG § Skills Consulted empty/missing → **NO** (full table present with 8 skills evaluated, decisions captured)
- ❌ runtime-quality-checklist.md not cited → **NO** (impl-log Skills row 1 cites "`references/runtime-quality-checklist.md` re-read pre-commit")
- ❌ Two or more category WARNs → **NO** (zero category WARNs; one info-level cross-scope flag handled per architect spec)

→ **PASS**

The build is shippable. T-9 closes Story A code-side cleanly. Wave 8 PM closure (07-merge.md) can proceed, gating on T-6b operational verification per architect spec.

## Recommendation to /pm

1. **Promote T-9 to `audit-passed`** in `04-tickets.yaml`. Update `transitions:` with timestamp + this review path.
2. **Update `checkpoint.md`** Wave 7 (tail) closure entry — Story A code-side complete; Wave 8 (PM merge.md) unblocked.
3. **R5 spirit codification (optional, deferrable):** Consider extending `.claude/rules/backend-ddd.md` § "Schema-mirror exception" to cover textual-only docstring touches in copilot/sales_agent (R5b proposal — auditor accepted T-9 case under spirit interpretation; codifying avoids re-litigation in future tickets that touch agentic docstrings without behavioral change). Origen: T-9 PI-12 S1 sales-agent-litellm-canonicalization.
4. **No re-spawn required.** `builder-agentic` does not need to be invoked retroactively for the 2 docstring lines.

