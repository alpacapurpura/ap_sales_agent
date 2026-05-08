---
story_id: sales-agent-eval-cost-budget-cap
outcome: pi-12-sales-agent-eval-foundation
state: refined
phase: SPEC_RATIFIED
last_artifact: 01-spec.md  # v2 ratificada Chris 2026-05-08T11:00Z
last_modified: 2026-05-08T11:00:00Z
next_action: "/architect orchestrator → spawna /architect-be (BudgetState Pydantic + guard impl + cost_estimator + periodic sweep + NEW arch fitness gate test_eval_llm_calls_use_budget_guard.py + capability extension) → produce ready package (03-arch + 04-validators + 05-guidelines + 06-tickets) → state=refined→ready → /dev-team build (espera B+E build done — bloqueador hard)"
ratified_by_chris: true
spawned_at: 2026-05-04T20:00:00Z
spawned_by: /pm
parallel_safe: true
blocked_reason: null
artifacts:
  - 00-story.md
  - 01-spec.md  # po_version=2, ratified 2026-05-08T11:00Z (Q1-Q6 todas opción A recomendada)
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
