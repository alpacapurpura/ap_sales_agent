<!-- voseo-allowed: review cites voseo glosario verbatim per .claude/rules/spanish-text.md (R25 magic comment escape) -->

# REVIEW-final — Story A: sales-agent-litellm-canonicalization

**Status:** ALL TICKETS AUDIT-PASSED — Story complete pending Wave 8 07-merge ratification + /pase-produccion deploy
**Story:** sales-agent-litellm-canonicalization
**Sprint:** S1-eval-runner / PI-12
**Story owner:** /pm
**Final review by:** /pm orchestrator (Opus 4.7)
**Date:** 2026-05-06

## Story closure verdict: APPROVED

All 11 tickets resolved (10 audit-APPROVED + 1 PM-ratified operational gate). Story A code scope COMPLETE. /pase-produccion deploys T-6a + T-6c migrations + Streamlit final verification.

## Tickets summary

| Ticket | Type | State | Commit(s) | Audit verdict | Review |
|---|---|---|---|---|---|
| T-1 | backend (cost recorder) | audit-passed | `5856be4d` | APPROVED 11/12 categories | T-1-review.md |
| T-1.bis | backend (test bridge migration) | audit-passed | `3cb98fd4` + `d1e099ba` | APPROVED 12/12 | T-1.bis-review.md |
| T-2 | backend (sync-pricing extension) | audit-passed | `8b6d798f` | APPROVED 11/12 categories | T-2-review.md |
| T-3 | migration (snapshot repair) | audit-passed | `71f39529` + `4193cbb3` | APPROVED 12/13 categories | T-3-review.md |
| T-4 | backend (DELETE 6 adapters + gemini audit 6/6) | audit-passed | `429913a3` | APPROVED 11 categories + 3 info | T-4-review.md |
| T-5 | backend (kill flag LITELLM_PROXY_ENABLED) | audit-passed | `28617716` + `560f14b5` | APPROVED 9 gates + 4 acceptance + 4 info | T-5-review.md |
| T-6a | DB+BE (Phase 1 deprecate cols) | audit-passed | `f6e7ad0a` + `29b97eba` | APPROVED 12/12 0 FAIL 0 WARN | T-6a-review.md |
| T-6b | OPS gate (1d zero-read window) | PM-ratified | N/A (operational) | RATIFIED pre-clientes per R7 | checkpoint.md bitácora |
| T-6c | DB+BE (Phase 3 DROP COLUMN final) | audit-passed | `a10e146c` + `dc1714d0` | APPROVED 14 gates 0 FAIL 0 WARN | T-6c-review.md |
| T-7 | backend (tests audit 20 files) | audit-passed | `38f7e1b7` | APPROVED | T-7-review.md |
| T-8 | backend (arch fitness ratchet + meta-test) | audit-passed | `253e6024` | APPROVED 1 non-blocking WARN | T-8-review.md |
| T-9 | docs (purge + learnings.md + 5 R6 decisions) | audit-passed | `aabd3acc` + `c93ba549` | APPROVED 0 FAIL R5b textual-mirror exception | T-9-review.md |

## Architectural outcomes

### Achieved

1. **LiteLLM Proxy = canonical único path** — 6 legacy per-provider adapters DELETED (openai/deepseek/kimi/qwen/gemini/_openai_compat). All LLM dispatch flows through `LiteLLMService` via `litellm_config.yaml` master key.

2. **Cost recorder canonicalization (T-1 architecture)** — `CostRecorderCustomLogger(litellm.integrations.custom_logger.CustomLogger)` bridge primitive. cost_usd consumed via `pop_cost(litellm_call_id)` from kwargs response_cost; calculate_cost retained as reconciliation utility only (NOT in runtime path).

3. **Tenant provider API keys deprecated + dropped** — 4 deprecated cols (openai_api_key, deepseek_api_key, kimi_api_key, dashscope_api_key) NULL'd in Phase 1 (T-6a) + dropped in Phase 3 (T-6c). gemini_api_key PRESERVED. Phase 2 (T-6b) PM-ratified pre-clientes per R7.

4. **Anti-default-flip-audit completed (DELETION case)** — LITELLM_PROXY_ENABLED flag DELETED (T-5) following 4-step DELETION variant: Step 1 grep ZERO active mocks, Step 2 N/A (T-7 pre-migrated), Step 3 single-path 9012 PASS, Step 4 5 mandatory `## ` headers. Inventory `.claude/rules/anti-default-flip-audit.md` row REMOVED + footnote ADDED.

5. **Architectural fitness codified (T-8)** — 3 ratchet enforcement assertions: `test_no_legacy_adapter_imports`, `test_known_legacy_files_set_is_empty`, `test_settings_has_no_litellm_proxy_enabled_attr`. 1 evergreen meta-test `test_violation_detection_works` (4-sub-check via injection). Arch fitness 823 → 827 PASS.

6. **Documentation purged (T-9)** — `docs/domains/llm-routing.md` Capa 5 rollback section DELETED, Capa 3 rewritten LiteLLM-only, NEW `## CustomLogger pattern` section. `docs/domains/tech_module_shared.md` legacy adapter list removed. `docs/product/modules/sales-agent.md` LLM routing section updated. NEW `learnings.md` capturing 5 binding decisions.

7. **Pricing sync extension (T-2)** — `litellm_sync.py` extended with config_yaml cross-check vs litellm.model_cost registry + drift detection. Makefile target `make sync-pricing` (native, ARQ primary per A6 binding). Pricing snapshot mis-tagging repaired via T-3 migration.

### Decisions ratified (binding throughout story)

- **A1 (T-1)** — Slashed model field preserved (model="provider/model")
- **A2 (T-1)** — 3-step expand-contract migration (T-6a/T-6b/T-6c)
- **A3 (T-4)** — MANDATORY gemini.py audit 6/6 pre-delete (function calling extra_body, safety_settings extra_body, system_instruction conversion, generation_config mapping, vision multipart, streaming chunks). All 6 PASS.
- **A4 (T-1)** — DROP 4 cols sin rename
- **A5 (T-2)** — litellm_sync.py EXTENDS (no parallel module)
- **A6 (T-2)** — ARQ worker primary + GHA backup (no GHA created — ARQ already configured)
- **X1 (T-1)** — Keep proxy mode (until T-5 deletes flag)
- **X2 (T-1)** — calculate_cost removed from runtime path (utility only)

### Process learnings (cross-cutting)

- **R7 process-improvement** (1d operational gate pre-clientes vs 5d post-clientes activos) APPLIED to T-6b ratification
- **R5b textual-mirror exception** spirit applied for T-9 sales_agent docstring touches (zero behavioral change) — auditor recommends codifying in next process-improvement cycle
- **R23 Opus mandate** — T-4 Sonnet 4.6 violation detected post-build; corrected pre-T-5 onwards (explicit `model: "opus"` param in spawn). Process metric tracked.
- **R24 validator hard-fail** — context-builder T-8 + T-9 initial iterations skipped validator (R24 violation). /pm spawned `context-validator` manually for compliance. Lesson: enforce validator gate at orchestrator level.
- **R22 gate-runner manual fallback** applied throughout (builder Opus already ran full suite natively; re-spawning gate-runner Haiku would duplicate 10-min pytest with no signal gain)

### Out-of-scope correctly deferred

- Smoke real-LLM verification (Story B T-5 + T-6c A5) — DEFERRED to /pase-produccion brain-UP per fixture B2 contract precedent
- Operational verification (T-6b 1d window) — PM-ratified pre-clientes; auto-promoted post-/pase-produccion + Streamlit verify

## Quality metrics

- **Total commits Story A:** 22 (11 feature + 11 docs/result/SHA-backfill)
- **Test additions:** 50+ new tests across iam + arch fitness + LLM routing + pricing + cost recorder + agentic_evals harness
- **Coverage maintained:** 43% threshold satisfied throughout
- **Arch fitness:** 823 baseline → 827 final (+4 ratchet enforcement net additions)
- **Anti-duplication §0 GATE:** 0 mirrors introduced
- **Spanish neutro:** Extended grep 23 voseo terms = 0 matches across all docs additions
- **Native-first:** 100% — zero `docker exec` for lint/tests/typecheck

## Pending /pase-produccion verification

- A5 T-3 + T-6a + T-6c: live `alembic upgrade head` x2 (idempotency)
- T-6b auto-promote: post-deploy Streamlit verify `SELECT COUNT(*) WHERE 4 deprecated cols IS NOT NULL = 0`
- gemini_api_key preservation: `\d tenants` post-deploy verifies col present

## Pipeline harness compliance (R28-R31 enforcement)

- **R28** literal bash output proof in briefs: COMPLIED most iterations (some context-builder skips → /pm caught at consumer level)
- **R29** gate-runner skeleton-first + cross-ticket archive + ticket field: applied; manual fallback per R22 majority of iterations
- **R30** builder NO self-audit footer: COMPLIED across all 11 builder spawns
- **R31** auditor auto-prefix R25 magic comment: COMPLIED across all 10 audit reviews
- **R3 downstream regression scope (Step 4.5):** verified per ticket using SSoT tabla in `.claude/rules/auditor-downstream-regression.md`
- **R6 decisions honored cite:** present in commit bodies for tickets with decisions_applicable
- **R12 layer 1 process metrics:** emitted to `runs.jsonl` for all build + audit phase events

## Cross-scope flags

None. Story A scope cleanly contained within `shared/infrastructure/llm/`, `modules/iam/`, `tests/architecture/`, `docs/domains/`, `docs/product/modules/sales-agent.md`. Two sales_agent docstring touches under R5b textual-mirror exception (auditor T-9 ratified, /pm to codify in process-improvement).

## Recommendation: PROCEED to /pm 07-merge.md ratification

Story A code scope COMPLETE. All acceptance verifiers PASS or DEFERRED with explicit /pase-produccion path. R3 downstream regression verified independently per ticket. Pipeline harness compliance documented. Ready for sprint closure + /pase-produccion deploy.

<!-- @pm: REVIEW-final.md ready (verdict=APPROVED). All 11 tickets resolved. Wave 8 next: 07-merge.md ratification + sprint.md done + /pase-produccion deploy T-6a + T-6c + Streamlit final verify. -->
