---
story_id: sales-agent-adversarial-jailbreak-suite
outcome: pi-12-sales-agent-eval-foundation
state: refined
phase: SPEC_AND_DESIGN_RATIFIED
last_artifact: 02-design-agentic.md  # v2 ratificada Chris 2026-05-08T14:00Z
last_modified: 2026-05-08T14:00:00Z
next_action: "/architect orchestrator → spawna /architect-orchestrator full-stack (NEW rubric toxicity-control.md v1 + 5 adversarial personas YAML + 5-10 goldens curation pipeline reused Story D + Story E grader rubric Literal extension + Story F EvalPassKSummary persona_kind extension + arch fitness gate test_adversarial_persona_metadata_axis.py + capability extension) → produce ready package (03-arch + 04-validators + 05-guidelines + 06-tickets) → state=refined→ready → /dev-team build LAST en sub-épica eval-foundation (espera ALL prior stories build done — bloqueador hard)"
ratified_by_chris: true
design_ratified_by_chris: true
spawned_at: 2026-05-04T20:00:00Z
spawned_by: /pm
parallel_safe: true
blocked_reason: null
artifacts:
  - 00-story.md
  - 01-spec.md             # po_version=2, ratified 2026-05-08T13:00Z
  - 02-design-agentic.md   # ux_version=2, ratified 2026-05-08T14:00Z
audit_iterations: 0
legacy_exempt: true
migrated_from: docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/*/stories/sales-agent-adversarial-jailbreak-suite/
---

## Bitácora

- 2026-05-04 20:00 — `/pm` creó folder + `00-story.md`. Phase=PM_DRAFT, status=pending. Última story del PI — al cerrar marca cierre PI-12.
- 2026-05-06 — Migrado a paradigma v4: state=refining (legacy_exempt). Pendiente /po para spec ratification.
- 2026-05-06 17:11Z — Reframe synthetic-first (outcome `pi-12-sales-agent-eval-foundation.md`). Rol en sub-épica eval-foundation-* = **I — PersonaGym Toxicity Control axis**. Spec ratification awaits A (tenant-seed) + B (simulator-homologation) refined.
- 2026-05-08 12:30Z — `/po` redactó `01-spec.md` v1 reframe PersonaGym Toxicity Control axis + extension pattern. Story I OWNS NEW rubric `toxicity-control.md` v1 (5th PersonaGym axis). 5 attack categories (jailbreak/injection/hostile/coercion/compliance probes NEW). 5 NEW archetype-aware adversarial personas (1 per tenant, multi-vector 2-3 categories cada). 5-10 adversarial goldens via Story B+E pipeline + Chris curation. pass_k=1.0 cero tolerance. Stricter thresholds (toxicity-control=0.85, voice-fidelity=0.80, no-hallucination=0.85). Story G monthly cadence ONLY. 4 scenarios obligatorios. 15 D-decisions. 8 open questions Q1-Q8.
- 2026-05-08 13:00Z — Chris ratificó Q1-Q8 (todas opción A recomendada). `/po` bump v2 inline. `ratified_by_chris: true` (spec).
- 2026-05-08 13:30Z — `/ux-agentico` redactó `02-design-agentic.md` v1. REUSE Story B+C+E infra (no new state machine). 5 transcripts mockup §2 illustrative (jailbreak/injection/hostile/coercion/compliance). Tools sequence reuses existing infra. Voice cement compiler v2 NEVER touched (sales-agent-expert §3 protected). Error recovery 8 failure modes adversarial-specific. Cost ~$3-6 cold added to Story G monthly run. Observability extends Story E con `attack_category` + `system_leak_detected` + `compliance_violation`. 7 design decisiones DQ1-DQ7.
- 2026-05-08 14:00Z — Chris ratificó DQ1-DQ7 (todas opción A recomendada). `/ux-agentico` bump v2 inline. `design_ratified_by_chris: true`. **Transition `state: refining → refined`** (spec v2 + design v2 ambos ratified Chris). Phase=SPEC_AND_DESIGN_RATIFIED. `next_action: /architect orchestrator → ready package`. Story I es LAST story PI-12 sub-épica eval-foundation.
