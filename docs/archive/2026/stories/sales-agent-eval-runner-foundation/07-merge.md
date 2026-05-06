# 07-merge — Story B: sales-agent-eval-runner-foundation

**PM ratification:** PROCEED to /pase-produccion
**Story:** sales-agent-eval-runner-foundation
**Sprint:** S1-eval-runner / PI-12
**Ratified by:** /pm orchestrator (Opus 4.7) per Chris pre-authorization
**Date:** 2026-05-06

## Merge approval

All 6 tickets audit-passed. REVIEW-final.md verdict: APPROVED. Story B development scope COMPLETE. Ready for /pase-produccion deploy + brain-UP smoke verification.

## Final commits on `development` (Story B scope)

- `9ffae2ce` feat(pi-12-B-T-1): scaffold dirs + README stub
- `6abfef7b` feat(pi-12-B-T-2): pytest plumbing + 4 fixtures + 14 meta-tests
- `555c81c1` feat(pi-12-B-T-3): TrajectorySpy + artifacts writer
- `674967c4` + `e98a21ea` feat(pi-12-B-T-4): multi-layer assertion library
- `d5b7886a` + `e1b67e74` feat(pi-12-B-T-5): smoke golden + 4 scenarios + regenerate_golden CLI
- `01c078e4` + `d69ddd94` feat(pi-12-B-T-6): Makefile target + README operability docs

Plus closure docs commits (Wave 2/4/5 closures): merged with Story A in shared closure commits.

## Decisions ratified (binding throughout story)

B1 (composition over subclass) + B2 (hardcoded offer_id fail-explicit) + B4 (forbidden_tools from registry) + B5 (langdetect lazy import) + B6 (cache_hit_rate Story 7) + B7 (voice fidelity grader Story 7).

## pm-nico/current-state updates

### `docs/product/modules/sales-agent.md` § Capacidades
**Status:** Will reflect new "Multi-layer eval harness (foundation)" capability.

Add row:
| Capacidad | Estado | Owner |
|---|---|---|
| Multi-layer eval harness foundation | ✅ shipped 2026-05-06 (Story B) | tests/agentic_evals/sales_agent/ |

(Existing capabilities unchanged — eval harness is dev-internal infrastructure, no user-facing change)

### Capability registry
**Status:** No new user-facing capability YAML — eval harness is dev-internal infrastructure per Story B notes.

## /pase-produccion handoff

**Pre-deploy verification:**
- HEAD `development`: latest closure commit (Wave 8 closure pending)
- All 6 audit-passed tickets present
- Default suite passes (40+ eval-marker SKIP per design)
- Arch fitness 827 PASS preserved

**Deploy steps (shared with Story A — single /pase-produccion run):**
1. Merge `development` → `main` (joint with Story A)
2. Run `/test-all` natively
3. `git push origin main` (triggers GitHub Actions auto-deploy)
4. Monitor workflow until deployment completes

**Post-deploy smoke verification (brain-UP — Story B T-5 deferred acceptance):**
1. `make seed-visionarias` (precondition)
2. `make eval-smoke` o `cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/test_eval_runner_smoke.py -v --run-evals`
3. Expected outcomes:
   - **A1 test_smoke_multi_layer**: PASS (5-layer assertions verify trajectory + tool_calls + output + cost + latency)
   - **A3 test_degraded_output_caught**: PASS (monkeypatch forces OutputAssertionError)
   - **A4 test_no_cross_tenant_leak**: PASS (synthetic_tenant fixture seeds T2; agent invoke with Visionarias tenant_id; verifies DISTINCT tenant_id = 1 in sales_agent_trace_event)
   - **A5 regenerate_golden --dry-run**: PASS (exit 0 brain-UP)
4. Artifacts written to `_artifacts/{run_id}/{trace.json,response.txt,assertions.json}` (gitignored)
5. Cost verification: query `SELECT SUM(cost_usd) FROM sales_agent_llm_call WHERE run_id = ?` → < $0.01 per smoke run

**Post-deploy ratification:**
- /pm verifies smoke real-LLM scenarios via /pase-produccion smoke logs
- /pm closes deferred A1/A3/A4/A5 acceptance verifiers in Story B T-5 review
- Sprint.md status → done
- Story B unblocks Story 2 (pass^k aggregation) + Story 5 (multi-tenant goldens) + Story 7 (voice fidelity grader) for next sprint

## Cross-references

- REVIEW-final.md: this story's full audit summary
- 04-tickets.yaml: 6 tickets with all transitions to audit-passed
- checkpoint.md: bitácora chronological closure
- Architect specs: 03-arch-be.md + 03-arch-agentic.md
- Spec: 01-spec.md (Gherkin AI-resistant 4 scenarios)
- Story YAML: docs/product/stories/sales-agent/sales-agent-eval-runner-foundation.yaml
- README operability: backend/tests/agentic_evals/sales_agent/README.md
- Smoke runner: `make eval-smoke` (backend/Makefile)
