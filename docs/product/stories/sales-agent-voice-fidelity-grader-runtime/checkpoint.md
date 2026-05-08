---
story_id: sales-agent-voice-fidelity-grader-runtime
outcome: pi-12-sales-agent-eval-foundation
state: refining
phase: SPEC_RATIFIED_AWAITING_DESIGN
last_artifact: 01-spec.md  # v2 ratificada Chris 2026-05-08T08:00Z — agentic-story awaits 02-design-agentic.md
last_modified: 2026-05-08T08:00:00Z
next_action: "/ux-agentico lee 01-spec.md → produce 02-design-agentic.md (judge prompt slot architecture + MAJ-EVAL state machine Round 1+Round 2 debate flow + voice constraints + sandbox markers + error recovery + observability) → ratificación Chris → state=refining→refined → /architect"
ratified_by_chris: true
spawned_at: 2026-05-04T20:00:00Z
spawned_by: /pm
parallel_safe: true   # spec ratified; design parallel-safe; build espera Story C+D build done
blocked_reason: null   # A+B done, C+D refined, spec v2 ratified → unblocked para /ux-agentico
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
