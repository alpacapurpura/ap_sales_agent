<!-- voseo-allowed: review cites voseo glosario verbatim per .claude/rules/spanish-text.md (R25 magic comment escape) -->

# REVIEW-final — Story B: sales-agent-eval-runner-foundation

**Status:** ALL TICKETS AUDIT-PASSED — Story development scope COMPLETE
**Story:** sales-agent-eval-runner-foundation
**Sprint:** S1-eval-runner / PI-12
**Story owner:** /pm
**Final review by:** /pm orchestrator (Opus 4.7)
**Date:** 2026-05-06

## Story closure verdict: APPROVED

All 6 tickets audit-passed. Story B development scope COMPLETE. Smoke real-LLM scenarios deferred to /pase-produccion brain-UP per fixture B2 contract.

## Tickets summary

| Ticket | Type | State | Commit(s) | Audit verdict | Review |
|---|---|---|---|---|---|
| T-1 | backend (scaffold dirs + README stub) | audit-passed | `9ffae2ce` | APPROVED 10 PASS 3 NA | T-1-review.md |
| T-2 | backend (pytest plumbing + 4 fixtures + 14 meta-tests) | audit-passed | `6abfef7b` | APPROVED_WITH_NOTES (2 minor WARN F632 + voseo) | T-2-review.md |
| T-3 | agentic (TrajectorySpy + artifacts writer) | audit-passed | `555c81c1` | APPROVED 4-layer anti-dup GATE | T-3-review.md |
| T-4 | backend (multi-layer assertion library 5 funcs + LayerAssertionError + Story 7 placeholder) | audit-passed | `674967c4` + `e98a21ea` | APPROVED 1 non-blocking WARN (Cat 11 spec drift forward-fill) | T-4-review.md |
| T-5 | backend (smoke golden + 4 scenarios + regenerate_golden CLI) | audit-passed | `d5b7886a` + `e1b67e74` | APPROVED 1 non-blocking WARN (YAML schema drift forward-fill T-4 precedent) | T-5-review.md |
| T-6 | backend (Makefile target eval-smoke + README operability docs) | audit-passed | `01c078e4` + `d69ddd94` | APPROVED 4 minor R1 ortho self-fixed | T-6-review.md |

## Architectural outcomes

### Achieved

1. **End-to-end eval harness foundation** — `backend/tests/agentic_evals/sales_agent/` complete with directory structure, pytest plumbing (--run-evals flag), 4 fixtures, 5-layer assertion library, TrajectorySpy LangChain callback (composition over subclass), artifacts writer (sanitize_payload reused), smoke golden YAML, 4 scenarios (happy real-LLM + skip-without-flag + degraded-output-monkeypatch + cross-tenant-leak-adversarial), regenerate_golden CLI.

2. **Anti-duplication §0 GATE 4-layer satisfied** — TrajectorySpy extends `langchain_core.callbacks.BaseCallbackHandler` (NOT Nicolify `BaseAgentCallbackHandler`). composition pattern. Lexical grep + AST walk + module-level + tool registry sourcing — all clean.

3. **Langdetect lazy import architecturally enforced** — Top-level `import langdetect` BANNED via AST-walk arch test. Library imported via `importlib.import_module("langdetect")` with try/except graceful degradation.

4. **Tenant isolation in eval harness** — assert_cost_recorded filters BOTH tenant_id AND turn_id. Cross-tenant leak adversarial scenario (Scenario 4) seeds synthetic_tenant alongside Visionarias and verifies DISTINCT tenant_id count = 1 in sales_agent_trace_event post-invoke.

5. **Cost budget enforced** — Smoke real-LLM cost <$0.01/run target. assert_cost_recorded queries sales_agent_llm_call rows post-invoke + sums cost_usd. Alert threshold >$0.05/run signals regression.

6. **Spanish neutro LATAM** — Golden YAML input_message + assertion error messages + README + skip reasons all clean (extended grep 23 voseo terms = 0 matches across all Story B additions).

7. **Operability docs (T-6)** — backend/Makefile NEW (was missing — A1 verifier semantics resolved), 8 README sections covering local run preconditions, golden authoring, fixture catalog, comparison vs `tests/quality/sales_agent_goldens/` (S10 weekly LLM-judge), cleanup, cost budget, future story scope (S2-S9).

### Decisions ratified (binding throughout story)

- **B1 (T-3)** — Composition over subclass for TrajectorySpy
- **B2 (T-5)** — Hardcoded offer_id (fail-explicit, no silent shift)
- **B4 (T-3+T-4+T-5)** — required_tools=[], forbidden_tools=13 names from STAGE_TOOL_SCOPE registry (NOT inline hardcode)
- **B5 (T-4)** — Langdetect lazy import via importlib.import_module
- **B6 (T-3+T-4+T-5)** — Cache_hit_rate is Story 7 scope (assert_voice_fidelity placeholder NotImplementedError)
- **B7 (T-5)** — Voice fidelity grader is Story 7 scope (smoke MUST NOT call placeholder)

### Drift documented (non-blocking, forward-compatible)

- **T-4 Cat 11 WARN** — Builder's 4 assertion signatures + LayerAssertionError(Exception) base diverge from `03-arch-be.md` prescriptive code blocks. CONTEXT-BRIEF (validator-approved, faithfulness=clean) was authoritative for builder. Drift is forward-compatible — T-5 composed/wrapped where needed.
- **T-5 Cat 11 WARN** — YAML schema uses flat top-level keys vs arch-be § "Golden YAML schema" prescribed nested structure. Drift ratified upstream by T-4 audit Cat 11 precedent. Forward-compatible.

### Out-of-scope correctly deferred

- **Smoke real-LLM execution (A1/A3/A4 Story B T-5)** — DEFERRED to /pase-produccion brain-UP per fixture B2 contract. Static + compositional verification PASS. visionarias_tenant_session fixture skip-explicit pattern ratified by Story B T-2 audit precedent.
- **A5 regenerate_golden --dry-run** — Brain-DOWN: exits 1 with explicit Spanish stderr; brain-UP: exits 0. Both modes accepted per ticket spec "uses DB connection — SKIP if brain DOWN".
- **Voice fidelity grader (Story 7)** — placeholder NotImplementedError; smoke MUST NOT call.
- **Pass^k aggregation (Story 2)** — out of S1 scope.
- **Multi-tenant goldens (Story 5)** — out of S1 scope (Visionarias smoke single golden).

## Quality metrics

- **Total commits Story B:** 12 (6 feature + 6 docs/SHA-backfill)
- **Test additions:** ~70+ tests across runner + assertions + fixtures + smoke scenarios
- **Coverage 43% threshold:** maintained (eval suite outside coverage source per pyproject)
- **Arch fitness:** 823 baseline → 827 PASS (post Story A T-8 contributions; Story B no arch fitness regressions)
- **Anti-duplication §0:** 0 mirrors introduced (sanitize_payload, BaseAgentCallbackHandler, FXResolver, PricingResolver all REUSED verbatim from canonical paths)
- **Spanish neutro:** Extended grep 23 voseo terms = 0 matches across all Story B additions
- **Native-first:** 100% — zero `docker exec` for lint/tests/typecheck

## Pending /pase-produccion verification

- A1/A3/A4 Story B T-5 smoke real-LLM scenarios (visionarias_tenant_session fixture)
- A5 Story B T-5 regenerate_golden CLI happy path (brain-UP exit 0)
- Cost budget verification post-real-LLM run (<$0.01/run)

## Pipeline harness compliance (R28-R31 enforcement)

- **R28** literal bash output proof: COMPLIED majority iterations
- **R29** gate-runner skeleton-first + cross-ticket archive: manual fallback per R22 throughout
- **R30** builder NO self-audit footer: COMPLIED across all 6 builder spawns
- **R31** auditor auto-prefix R25 magic comment: COMPLIED across all 6 audit reviews
- **R3 downstream regression scope:** N/A throughout Story B (test-only paths, no shared/ touched)
- **R6 decisions honored cite:** present in T-3, T-4, T-5 commit bodies (B1-B7 binding)
- **R12 layer 1 process metrics:** emitted to runs.jsonl for all build + audit phase events

## Cross-scope flags

None. Story B fully contained within `backend/tests/agentic_evals/sales_agent/` + scoped Makefile addition.

## Recommendation: PROCEED to /pm 07-merge.md ratification

Story B development scope COMPLETE. All non-deferred acceptance verifiers PASS. Real-LLM smoke validation will execute at /pase-produccion. Ready for sprint closure.

<!-- @pm: REVIEW-final.md ready (verdict=APPROVED). All 6 tickets audit-passed. Wave 8 next: 07-merge.md ratification + sprint.md done + S1 retrospective. -->
