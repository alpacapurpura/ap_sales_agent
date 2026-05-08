---
story_id: sales-agent-voice-fidelity-ci-gate
outcome: pi-12-sales-agent-eval-foundation
state: refined
phase: SPEC_RATIFIED
last_artifact: 01-spec.md  # v2 ratificada Chris 2026-05-08T12:00Z
last_modified: 2026-05-08T12:00:00Z
next_action: "/architect orchestrator → spawna /architect-be (orchestrator + comment generator + cadence config + workflow YAML voice-fidelity-gate.yml + arch fitness gate + DDL migration eval_gate_verdict + capability extension) → produce ready package (03-arch + 04-validators + 05-guidelines + 06-tickets) → state=refined→ready → /dev-team build (espera B+C+D+E+F+H build done — last en sub-épica)"
ratified_by_chris: true
spawned_at: 2026-05-04T20:00:00Z
spawned_by: /pm
parallel_safe: true
blocked_reason: null
artifacts:
  - 00-story.md
  - 01-spec.md  # po_version=2, ratified 2026-05-08T12:00Z (Q1-Q7 todas opción A recomendada)
audit_iterations: 0
legacy_exempt: true
migrated_from: docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/*/stories/sales-agent-voice-fidelity-ci-gate/
---

## Bitácora

- 2026-05-04 20:00 — `/pm` creó folder + `00-story.md`. Phase=PM_DRAFT, status=pending. Última story del Sprint 3 — cierra el loop del Objetivo 2 del PI.
- 2026-05-06 — Migrado a paradigma v4: state=refining (legacy_exempt). Pendiente /po para spec ratification.
- 2026-05-06 17:11Z — Reframe synthetic-first (outcome `pi-12-sales-agent-eval-foundation.md`). Rol en sub-épica eval-foundation-* = **G — CI gate dynamic threshold (daily→weekly→monthly)**. Spec ratification awaits A (tenant-seed) + B (simulator-homologation) refined.
- 2026-05-08 11:30Z — `/po` redactó `01-spec.md` v1 reframe dynamic threshold per cadence (outcome v2 mandate). 3 cadences: PR (5 smoke goldens × K=1 × 0.65 × $30/$80 × block × <5min) / nightly (full × heterogeneous K × 0.70 × $150/$500 × block × <30min) / monthly (full + adversarial Story I × 0.75 × $200/$700 × warning + Chris semestral × <60min). Consume Story F `pass_k_report.json` + Story H `budget_summary.json` cascade. GitHub Actions workflow `voice-fidelity-gate.yml` + path filters + cron + required check branch protection. PR comment rich attribution con root cause Bloom stage + reproduce cmd + calibration ref. 5-layer bypass defense (skip ci → required check + workflow file changes review + goldens hash + threshold defaults arch fitness + audit trail). Schema `GateVerdict` v1 SCHEMA_MIGRATIONS forward-compat. DDL idempotent `eval_gate_verdict` table NEW. 4 scenarios obligatorios. 15 decisiones D1-D15. 7 open questions Q1-Q7.
- 2026-05-08 12:00Z — Chris ratificó Q1-Q7 (todas opción A recomendada). `/po` bump v2 inline. `ratified_by_chris: true`. Service-story → **transition `state: refining → refined`**. Phase=SPEC_RATIFIED. `next_action: /architect`.
