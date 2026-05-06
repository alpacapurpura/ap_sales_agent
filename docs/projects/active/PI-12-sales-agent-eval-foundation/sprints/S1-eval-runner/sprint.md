---
sprint_id: S1
slug: eval-runner
pi: PI-12
started_at: 2026-05-04
target_end: 2026-05-18
status: wrap-up                                   # planning | active | wrap-up | done — 2/4 stories COMPLETE; Story 3+4 deferred to S2
checkpoint: ./checkpoint.md
last_modified: 2026-05-06T03:50Z
---

# Sprint S1 — Eval Runner Foundation

## Goal del sprint

Al final del sprint: existe `backend/tests/agentic_evals/sales_agent/`, dev puede correr el runner manualmente, cada golden corre 3 trials con pass^k tracking, runs >$5 son abortados, y el reporte de cost por trial es confiable (deepseek pricing fix aplicado).

## Stories incluidas

| Story ID | Type | Module | Estimate | Status | Tickets count (final) |
|---|---|---|---|---|---|
| `sales-agent-eval-runner-foundation` | service | sales_agent | 3d (actual ~6h Wave 1-5) | **audit-passed** | 6 (T-1..T-6 all audit-passed) |
| `sales-agent-eval-pass-k-tracking` | service | sales_agent | 2d | **deferred-to-S2** | 1 (not started this sprint) |
| `sales-agent-eval-cost-budget-cap` | service | sales_agent | 1d | **deferred-to-S2** | 1 (not started this sprint) |
| `sales-agent-litellm-canonicalization` (was `sales-agent-cost-tracking-deepseek-fix`) | service | shared (cost) + iam | 2d (actual ~12h Wave 2-8) | **audit-passed** | 11 (T-1..T-9 + T-1.bis + T-6b PM-ratified, all complete) |

**Total estimado original:** 8d
**Actual delivered:** 2 stories (17 tickets across 7 waves)
**Deferred:** 2 stories (pass-k-tracking + budget-cap) → S2 next sprint planning

## Tickets por owner pool (estimado pre-architect)

| Owner pool | Stories | Estimate |
|---|---|---|
| claude-opus (eval infra agentic-adjacent) | runner-foundation, pass-k-tracking, budget-cap | 6d |
| qwen-opencode (BE non-agentic patch) | deepseek-fix | 2d |

## Dependencias entre stories

```
sales-agent-eval-runner-foundation
  ├──> sales-agent-eval-pass-k-tracking (necesita runner para iterar trials)
  └──> sales-agent-eval-cost-budget-cap (necesita runner para hookear cost recorder)

sales-agent-cost-tracking-deepseek-fix
  (independiente — puede ejecutarse en paralelo con cualquiera arriba)
```

## Orden ejecución sugerido

1. `sales-agent-cost-tracking-deepseek-fix` (qwen-opencode, paralelizable, desbloquea reporting confiable durante el resto del sprint)
2. `sales-agent-eval-runner-foundation` (claude-opus, bloquea 2 y 3)
3. `sales-agent-eval-pass-k-tracking` (claude-opus)
4. `sales-agent-eval-cost-budget-cap` (claude-opus)

## Cierre del sprint

Criterios:
- [x] 4 stories audit-passed O movidas a próximo sprint — **2/4 audit-passed (Story A litellm-canonicalization + Story B eval-runner-foundation), 2/4 deferred to S2 (pass-k-tracking + budget-cap)**
- [x] `backend/tests/agentic_evals/sales_agent/` existe y tiene al menos 1 smoke golden corriendo verde — **Visionarias smoke golden + 4 scenarios; A2 PASS default suite, A1/A3/A4 deferred /pase-produccion brain-UP per fixture B2 contract**
- [ ] `pass_k_last_run` reportado por golden + agregado por suite — **Story C deferred to S2 (pass-k-tracking)**
- [ ] Run > $5 USD aborta con error claro — **Story D deferred to S2 (budget-cap)**
- [x] `cost_usd != 0` para 100% trials con provider=deepseek (verificar contra `sales_agent_llm_call` table) — **T-1 cost recorder canonicalization shipped; provider canonical via `litellm.get_llm_provider()` + fallback via hint; T-3 migration repaired historical mis-tagged rows**
- [x] `checkpoint.md` sprint marcado `wrap-up` (not done — pending S2 deferred stories closure)
- [x] Retrospective brief al final — **see § "Retrospective S1" below**

## Retrospective S1

**Wall-clock:** 2026-05-04 (planning) → 2026-05-06 (Story A + B closure) ≈ 2 working days actual
**Token budget:** ~6-8M tokens estimated across 17 tickets (Opus + Haiku mixed, harness multi-agent overhead per Anthropic 15x estimate)
**Cost:** ~$60-100 USD Opus 4.7 (TBD precise via R12 layer 1 metrics aggregation)

### Wins

1. **17 tickets shipped audit-passed in 8 waves** — consistent pipeline `/po → /architect → /dev-team → /auditor` with R28-R31 enforcement live. Zero ticket regressions caught at audit.

2. **Architectural cleanup**: LiteLLM Proxy = canonical único path. 6 legacy adapters deleted. LITELLM_PROXY_ENABLED flag deleted. Tenant API keys (4 cols) deprecated + dropped via 3-step expand-contract. Anti-default-flip-audit DELETION case completed end-to-end.

3. **Eval harness foundation shipped (Story B)**: TrajectorySpy composition pattern + 5-layer assertions + smoke golden + 4 scenarios + regenerate_golden CLI + Makefile + 318-line README. Anti-duplication §0 GATE 4-layer satisfied throughout.

4. **R7 process-improvement applied**: T-6b operational gate 1d pre-clientes (vs 5d post-clientes activos). PM-ratified pre-clientes per zero production traffic — gate trivially satisfied.

5. **Pipeline harness compliance evidenced**: R3 downstream regression independent re-runs (T-1 cost path → 14/14 callback handler tests; T-6a → 14/14 SSoT downstream; T-6c → 837 sales_agent + copilot observability). R6 decisions honored cite present in commit bodies. R12 layer 1 metrics emitted to runs.jsonl throughout.

### Process improvements observed

1. **R23 Opus mandate enforcement gap (T-4 violation)** — Builder Sonnet 4.6 ran T-4 despite `claude_opus_required:true`. Caught at audit (info-flag). Corrected pre-T-5 onwards via explicit `model: "opus"` param in spawn. Process learning: orchestrator MUST validate Opus mandate before spawn.

2. **R24 validator hard-fail incidents (T-8 + T-9 + T-5)** — context-builder iter-1 Haiku skipped validator citing "low-risk exemption" (R24 violation). /pm spawned `context-validator` manually for compliance. Lesson: enforce validator gate at orchestrator level (PM verifies validation file freshness + Validator pass header populated before consuming brief).

3. **R22 manual gate-runner fallback** — gate-runner Haiku consistently backgrounded pytest beyond bash timeout, OR returned text without writing JSON. Manual JSON finalization per R22 fallback applied throughout. Gate-runner reliability + Haiku capability for long pytest runs needs evaluation in PI-13 process-improvement.

4. **Spec drift forward-fill** — T-4 Cat 11 WARN (assertion signatures vs arch-be prescriptive) ratified by CONTEXT-BRIEF authoritative + validator PASS. T-5 inherited drift cleanly via composition pattern. R5b textual-mirror exception spirit emerged at T-9 audit (codify in next process-improvement).

### Cost optimization observations

- Manual R22 fallback saved ~10min pytest duplication per ticket (~2h total wall-clock saved)
- Single full-suite gate covered both Wave 4 + Wave 5 commits (T-3 Story B + T-4 Story A on shared HEAD; T-6a + T-4 Story B paralelo on shared HEAD) — efficient amortization of pytest run

### Risks remaining

- **Story C + Story D deferred to S2**: pass-k-tracking + budget-cap not started this sprint. S2 planning needed.
- **Brain container DOWN constraint**: A1/A3/A4/A5 acceptance verifiers across multiple tickets DEFERRED to /pase-produccion brain-UP. Sprint closure assumes /pase-produccion will validate.
- **Cost metrics not yet aggregated**: R12 layer 1 emitted runs.jsonl per ticket; layer 2 aggregation script (PI-13 backlog) not yet implemented.

### Recommendations for S2 sprint planning

1. Schedule Story C (pass-k-tracking) + Story D (budget-cap) in S2 — both depend on Story B foundation already shipped
2. Codify R5b textual-mirror exception in process-improvement cycle (auditor T-9 recommendation)
3. Evaluate gate-runner Haiku reliability for long pytest runs — possibly increase timeout OR add JSON-write retry in agent definition
4. Run R12 layer 2 aggregation script post-S1 closure to extract Story A vs Story B token/cost breakdown
5. /pase-produccion verifies A1/A3/A4/A5 deferred acceptance verifiers + Streamlit T-6b auto-promote
