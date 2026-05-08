---
story_id: sales-agent-eval-pass-k-tracking
outcome: pi-12-sales-agent-eval-foundation
state: refined
phase: SPEC_RATIFIED
last_artifact: 01-spec.md  # v2 ratificada Chris 2026-05-08T10:00Z
last_modified: 2026-05-08T10:00:00Z
next_action: "/architect orchestrator → spawna /architect-be (DDL migration eval_pass_k_summary + Pydantic EvalPassKSummary/BloomStageResult/TrialResult/PassKAggregateReport + aggregator + bloom_scorer + inputs_hasher + script + pre-commit hook Section 9 + capability extension) → produce ready package (03-arch + 04-validators + 05-guidelines + 06-tickets) → state=refined→ready → /dev-team build (espera Stories C+D+E build done — bloqueador hard)"
ratified_by_chris: true
spawned_at: 2026-05-04T20:00:00Z
spawned_by: /pm
parallel_safe: true
blocked_reason: null
artifacts:
  - 00-story.md
  - 01-spec.md  # po_version=2, ratified 2026-05-08T10:00Z (Q1-Q7 todas opción A recomendada)
audit_iterations: 0
legacy_exempt: true
migrated_from: docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/*/stories/sales-agent-eval-pass-k-tracking/
---

## Bitácora

- 2026-05-04 20:00 — `/pm` creó folder + `00-story.md`. Phase=PM_DRAFT, status=pending. Bloqueado hasta Story 1.
- 2026-05-06 — Migrado a paradigma v4: state=refining (legacy_exempt). Pendiente /po para spec ratification.
- 2026-05-06 17:11Z — Reframe synthetic-first (outcome `pi-12-sales-agent-eval-foundation.md`). Rol en sub-épica eval-foundation-* = **F — Bloom-style pass^k**. Spec ratification awaits A (tenant-seed) + B (simulator-homologation) refined.
- 2026-05-08 09:30Z — `/po` redactó `01-spec.md` v1 reframe Bloom 4-stage strict all-of-K (Anthropic Bloom paper mayo 2026). Stages: Understanding/Ideation/Rollout/Judgment per trial. Heterogeneous K per persona_kind (Story C cement: happy=3, nurture=1, unqualified=3, adversarial=3). Aggregator read-only consume Story B (sim trace events) + Story C (trial policy) + Story D (goldens YAML ground truth) + Story E (MajEvalScore.final_score). Schema `EvalPassKSummary` v1 con `inputs_hash` tamper detection + `golden_yaml_hash` mutation snapshot. Per-stage threshold env vars (4 × `SALES_AGENT_BLOOM_<stage>_THRESHOLD=0.7`). DDL idempotent migration `eval_pass_k_summary` table NEW. JSON report `_artifacts/eval_runs/{run_id}/pass_k_report.json` versioned. 4 scenarios obligatorios (happy/edge stage attribution/edge heterogeneous K/adversarial tamper detection). 16 decisiones cardinales D1-D16. 7 open questions Q1-Q7.
- 2026-05-08 10:00Z — Chris ratificó Q1-Q7 (todas opción A recomendada). `/po` bump v2 inline. `ratified_by_chris: true`. Service-story → **transition `state: refining → refined`**. Phase=SPEC_RATIFIED. `next_action: /architect`.
