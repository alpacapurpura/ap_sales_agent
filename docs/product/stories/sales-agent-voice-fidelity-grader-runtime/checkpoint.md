---
story_id: sales-agent-voice-fidelity-grader-runtime
outcome: pi-12-sales-agent-eval-foundation
state: refined
phase: SPEC_AND_DESIGN_RATIFIED
last_artifact: 02-design-agentic.md  # v2 ratificada Chris 2026-05-08T09:00Z
last_modified: 2026-05-08T09:00:00Z
next_action: "/architect orchestrator → spawna /architect-be (DDL migrations 2 NEW tables eval_simulator_grade + eval_simulator_grade_cache + Pydantic MajEvalScore + cache impl + qualification-accuracy.md rubric NEW) + /architect-agentic (judge prompt slots 6-slot architecture + MAJ-EVAL state machine Round 1+Round 2 debate flow + sandbox markers + observability writes) → produce ready package (03-arch + 04-validators + 05-guidelines + 06-tickets) → state=refined→ready → /dev-team build (espera Story C+D build done — bloqueador hard)"
ratified_by_chris: true
design_ratified_by_chris: true   # 02-design-agentic.md v2 ratified Chris 2026-05-08T09:00Z
spawned_at: 2026-05-04T20:00:00Z
spawned_by: /pm
parallel_safe: true
blocked_reason: null
artifacts:
  - 00-story.md
  - 01-spec.md            # po_version=2, ratified 2026-05-08T08:00Z
  - 02-design-agentic.md  # ux_version=2, ratified 2026-05-08T09:00Z
audit_iterations: 0
legacy_exempt: true
migrated_from: docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/*/stories/sales-agent-voice-fidelity-grader-runtime/
---

## Bitácora

- 2026-05-04 20:00 — `/pm` creó folder + `00-story.md`. Phase=PM_DRAFT, status=pending. Story de mayor riesgo del PI — calibración manual con Chris.
- 2026-05-06 — Migrado a paradigma v4: state=refining (legacy_exempt). Pendiente /po para spec ratification.
- 2026-05-06 17:11Z — Reframe synthetic-first (outcome `pi-12-sales-agent-eval-foundation.md`). Rol en sub-épica eval-foundation-* = **E — MAJ-EVAL multi-judge debate**. Spec ratification awaits A (tenant-seed) + B (simulator-homologation) refined.
- 2026-05-08 07:30Z — `/po` redactó `01-spec.md` v1 MAJ-EVAL multi-judge debate reframe (Stories A+B done + C+D refined → unblocked). 3 judges heterogéneos (Sonnet=0.4 + GPT-4o=0.4 + Kimi-K2.6=0.2) con weighted aggregation + Round 2 debate trigger on Round 1 variance >0.15. 4 rubrics in scope (voice-fidelity + qualification-accuracy NEW Story E owns + no-overpromise + no-hallucination). Cache `eval_simulator_grade_cache` table NEW con hash invalidation precision (judge weights, rubric version, transcript, voice). Schema `MajEvalScore` v1 cement con SCHEMA_MIGRATIONS forward-compat (Story B H1 reused). Public API surface `simulator/__init__.py` H9 expand 7→8 names (`grade_transcript_maj_eval` NEW). 4 scenarios obligatorios (happy multi-judge / edge debate trigger / cache hit deterministic / adversarial prompt-injection in transcript content). Calibración híbrida (10 Chris turn-labels + auto vs Story D goldens frozen baseline). 20 decisiones cardinales D1-D20. 9 open questions Q1-Q9 awaiting Chris ratificación.
- 2026-05-08 08:00Z — Chris ratificó Q1-Q9 (todas opción A recomendada). `/po` bump `01-spec.md` v2 inline: D2 weights 0.4/0.4/0.2 cement; D5 4 rubrics in scope; D15 GPT-4o pinned `gpt-4o-2024-11-20` (NOT auto-tracking); D3 variance trigger 0.15; D11 calibración 10 turn-labels + auto goldens baseline; D6 Story E owns `qualification-accuracy.md` NEW; D8/D16 cache invalidation automatic via `rubric_version` field; D17 async via `asyncio.create_task`; D13 per-rubric threshold override env vars allowed. `ratified_by_chris: true`. Phase=SPEC_RATIFIED_AWAITING_DESIGN. State permanece `refining` hasta `/ux-agentico` produce `02-design-agentic.md` (judge prompt slot architecture + MAJ-EVAL state machine Round 1+Round 2 + voice constraints + sandbox markers + observability) → ratificación Chris → transition state=refining→refined → `/architect`.
- 2026-05-08 08:30Z — `/ux-agentico` redactó `02-design-agentic.md` v1. State machine MAJ-EVAL Round 1 + variance check + Round 2 + aggregate + persist. 6-slot prompt architecture (3 cacheable TTL=1h + 3 fresh). Sandbox markers `<<TRANSCRIPT_BEGIN>>...<<TRANSCRIPT_END>>` SLOT 5 + system directive SLOT 1 explicit. Judge reasoning English (analytical layer) — transcript subject respects original dialect (es-AR voseo OK if tenant). Error recovery 11 failure modes + graceful degradation (judge timeout/parse-fail/DB unavailable). Cost budget ~$330 cold/run, ~$108 warm cache (≥70% hit target). Observability `eval_simulator_grade` + `eval_simulator_grade_cache` + `eval_simulator_llm_call` (Story B H7 cement). Mockup transcript §11 nurture es-AR voseo Round 1 → variance 0.45 → Round 2 → converged 0.10 → final_score 0.666. 8 design decisiones DQ1-DQ8 awaiting Chris ratificación. Phase=DESIGN_DRAFT_V1_AWAITING_RATIFICATION.
- 2026-05-08 09:00Z — Chris ratificó DQ1-DQ8 (todas opción A recomendada). DQ5 async callback ya cement vía spec Q8/D17. `/ux-agentico` bump v2 inline incorporando ratificaciones. `design_ratified_by_chris: true`. **Transition `state: refining → refined`** (spec v2 + design v2 ambos ratified Chris). Phase=SPEC_AND_DESIGN_RATIFIED. `next_action: /architect orchestrator → ready package`. Story G (CI gate) + I (adversarial) ahora unblocked refinement (depend Story E refined, no longer blocked).
