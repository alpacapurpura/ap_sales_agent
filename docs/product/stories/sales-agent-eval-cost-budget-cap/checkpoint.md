---
story_id: sales-agent-eval-cost-budget-cap
outcome: pi-12-sales-agent-eval-foundation
state: ready
phase: READY_PACKAGE_DELIVERED
last_artifact: 06-tickets.yaml  # ready package complete (03-arch + 04-validators + 05-guidelines + 06-tickets)
last_modified: 2026-05-08T12:00:00Z
next_action: "/dev-team build (BLOCKED on Stories B+E build done — hard blocker: Story E `eval_simulator_grade.cost_usd_total` column required for guard SQL sum query; Story B `eval_simulator_llm_call` already done). T-1+T-2+T-5 can build with synthetic fixtures BEFORE Story E build; T-3+T-4+T-6 require Story E build COMPLETE for integration scenarios."
ratified_by_chris: true
spawned_at: 2026-05-04T20:00:00Z
spawned_by: /pm
parallel_safe: true
blocked_reason: null
artifacts:
  - 00-story.md
  - 01-spec.md  # po_version=2, ratified 2026-05-08T11:00Z (Q1-Q6 todas opción A recomendada)
  - 03-arch.md  # /architect orchestrator delivered 2026-05-08T12:00Z (consolidated BE-only)
  - 04-validators.yaml  # 25 validators across 3 categories (non_functional + functional + agentic_eval)
  - 05-guidelines.md  # patterns required + forbidden + files in/out scope
  - 06-tickets.yaml  # 6 tickets atomic DAG dependencies, owner_eligibility=Sonnet OK all tickets
audit_iterations: 0
legacy_exempt: true
migrated_from: docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/*/stories/sales-agent-eval-cost-budget-cap/
---

## Bitácora

- 2026-05-04 20:00 — `/pm` creó folder + `00-story.md`. Phase=PM_DRAFT, status=pending. Bloqueado hasta Story 1 + Story 4.
- 2026-05-06 — Migrado a paradigma v4: state=refining (legacy_exempt). Pendiente /po para spec ratification.
- 2026-05-06 17:11Z — Reframe synthetic-first (outcome `pi-12-sales-agent-eval-foundation.md`). Rol en sub-épica eval-foundation-* = **H — cost-cap**. Spec ratification awaits A (tenant-seed) + B (simulator-homologation) refined.
- 2026-05-08 10:30Z — `/po` redactó `01-spec.md` v1 reframe multi-tier cost-bucket cap. Baseline post Story C+E expansion: ~$115 warm / ~$340 cold (vs original $5/run cap obsoleto). 4 tiers (per_trial=$0.10 / per_grade=$0.20 / per_run=$500 cold $150 warm / per_bucket=$20 generation + $400 cold $130 warm grader). Pre-flight over-estimate strict + periodic sweep 30s post-facto detection. NEW arch fitness `test_eval_llm_calls_use_budget_guard.py` enforce guard wrap. `simulator/__init__.py` H9 expand 8→9 names. Schema `BudgetState` v1 SCHEMA_MIGRATIONS forward-compat. 4 scenarios obligatorios (happy within / edge mid-run abort / edge disable / adversarial bypass). 13 decisiones D1-D13. 6 open questions Q1-Q6.
- 2026-05-08 11:00Z — Chris ratificó Q1-Q6 (todas opción A recomendada). `/po` bump v2 inline. `ratified_by_chris: true`. Service-story → **transition `state: refining → refined`**. Phase=SPEC_RATIFIED. `next_action: /architect`.
- 2026-05-08 12:00Z — `/architect` orchestrator delivered consolidated BE-only ready package:
  - **03-arch.md** (~1150 lines) — §0 Resumen + §1 Surfaces (BE only — AGENTIC/FE N/A) + §2 Existing systems audit (production BudgetGuard shared/billing different paradigm cement; consume Story B + E + shared model_pricing_snapshot read-only) + §3 BE arch (Pydantic schemas + cost_estimator + guard 3 public APIs + sweep periodic asyncio Task + arch fitness gates + H9 expand) + §4 AGENTIC N/A + §5 Cross-cutting + §6 13 decisions D-BE-1..D-BE-13 + §7 Output contract for Stories F/G/I + §8 Open architecture risks + §9 Out of scope + §10 Research notes (asyncio periodic Task + LiteLLM pricing canonical mayo 2026) + §11 Capability YAML + module narrative + downstream regression rule updates required (post-merge by /pm)
  - **04-validators.yaml** (25 validators) — non_functional (10: lint+format+mypy+arch_fitness+coverage+jscpd+legacy_invariants+public_api_h9_9+arch_eval_llm_calls_use_budget_guard+read_only_invariant) + functional (10: 4 scenarios × happy 4 + edge 5 + adversarial 3) + agentic_eval (8: cost_bucket_invariant + pre_flight_over_estimate + periodic_sweep + partial_report + unconverged_cascade + exit_code_2 + idempotent + pii_sanitization) + scenario_coverage matrix 4/4 + hardening_coverage matrix H1/H6/H7/H9 + iteration policy 3 max
  - **05-guidelines.md** — patterns required (Pydantic v2 ConfigDict frozen + structlog + utc_now + Decimal monetary + SQLA 2.0 async + asyncio.create_task) + patterns forbidden (mirror production BudgetGuard / cost_estimator different paradigm cement; no LLM imports; no DDL; no per-tenant scope; no slack/email; no flag flip in core/config.py) + files in scope (8 NEW + 3 EDIT) + files NEVER touched (§3 protected surfaces + Stories B/C/E/F territories) + reference docs + native-first + TDD obligatorio order + decisiones owner routing (Sonnet OK all 6 tickets, escalation paths declared on T-4 sweep + T-5 arch fitness)
  - **06-tickets.yaml** — 6 tickets atomic DAG: T-1 (Pydantic schemas + SCHEMA_MIGRATIONS anchor, 1.5h) → T-2 (cost_estimator over-estimate strict, 1.5h, depends T-1) + T-3 (guard 2 public APIs + env loader, 2.5h, depends T-1+T-2) → T-4 (sweep periodic Task, 2h, depends T-1+T-2+T-3, escalation Opus on lifecycle) + T-5 (arch fitness 2 NEW gates, 1.5h, depends T-1, escalation Opus on AST regex) → T-6 (simulator __init__ H9 expand 8→9 + JSON output + integration + capability YAML + module narrative + downstream regression rule, 2h, depends T-3+T-4+T-5). Total: 11h aggregate sequential, parallelizable T-2+T-3 after T-1; T-5 after T-1.
  - **state transition**: `refining → refined → ready` (skip refined no audit iteration — package autocontenido).
  - **Phase=READY_PACKAGE_DELIVERED**.
  - **next_action**: `/dev-team build` (BLOCKED on Stories B+E build done — hard blocker; Story B already done, Story E refined awaiting build trigger).
  - **Build serialization order**: B(done) → C → D → E → (F+H parallel) → G → I.
