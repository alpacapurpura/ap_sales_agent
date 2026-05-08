---
story_id: sales-agent-personas-instrumented-runtime
outcome: pi-12-sales-agent-eval-foundation
state: refined
phase: SPEC_AND_DESIGN_RATIFIED
last_artifact: 02-design-agentic.md
last_modified: 2026-05-08T06:00:00Z
next_action: "/architect orchestrator → spawna /architect-be (loader 15 personas + dialect_catalog + Literal v2 6-value) + /architect-agentic (customer prompt v2 sub-slots + max_turns matriz + Scenarios 5+6 graphs) → produce ready package (03-arch + 04-validators + 05-guidelines + 06-tickets) → state=refined→ready"
ratified_by_chris: true
spawned_at: 2026-05-04T20:00:00Z
spawned_by: /pm
parallel_safe: false
blocked_reason: null
audit_iterations: 0
legacy_exempt: true
migrated_from: docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/*/stories/sales-agent-personas-instrumented-runtime/
# voseo-allowed: bitácora cita verbatim Chris autonomy mandate (es-AR voseo) for audit trail integrity
artifacts:
  - 00-story.md
  - 01-spec.md         # po_version=3, ratified 2026-05-08T04:00Z (v2) + 05:00Z (v3 autonomy expansion)
  - 02-design-agentic.md  # ux_version=2, ratified 2026-05-08T05:30Z (autonomy mandate incorporated)
  - delta-spec.md      # delta_version=1, ratified 2026-05-08T05:00Z (Chris autonomy mandate "vos decidís")
---

## Bitácora

- 2026-05-04 20:00 — `/pm` creó folder + `00-story.md`. Phase=PM_DRAFT, status=pending. Bloqueado hasta S1 + Story 5.
- 2026-05-06 — Migrado a paradigma v4: state=refining (legacy_exempt). Pendiente /po para spec ratification.
- 2026-05-06 17:11Z — Reframe synthetic-first (outcome `pi-12-sales-agent-eval-foundation.md`). Rol en sub-épica eval-foundation-* = **C — personas-as-simulators (Strands ActorProfile)**. Spec ratification awaits A (tenant-seed) + B (simulator-homologation) refined.
- 2026-05-08 03:30Z — `/po` redacta `01-spec.md` v1 (4 scenarios obligatorios + 12 decisiones cardinales D1-D12 + 6 open questions).
- 2026-05-08 04:00Z — Chris ratificó Q1-Q6. `/po` bump v2 inline (D2/D4/D6/D8/D9 ajustes + path `archetype-aware/` subdir). `ratified_by_chris: true` (spec).
- 2026-05-08 04:30Z — `/ux-agentico` redacta `02-design-agentic.md` v1 (dual-LLM loop + 5 transcripts archetype-aware + state machine + slot architecture + 4 design open questions DQ1-DQ4).
- 2026-05-08 04:45Z — Chris autonomy mandate: "vos decidís... considerá todos los escenarios posibles + sales agent también califica". Autoriza scope expansion.
- 2026-05-08 05:00Z — `/ux-agentico` redacta `delta-spec.md` v1 (scope 5→15 personas; persona_kind v1 4-val → v2 6-val `+nurture +unqualified`; schema_version 1→2; customer prompt v1→v2 sub-slots; Scenarios 5+6 NEW; max_turns matriz; trial policy heterogeneous; D13-D17 cardinales). `ratified_by_chris: true` (delta).
- 2026-05-08 05:00Z — `/po` bump `01-spec.md` v3 inline incorporando delta (D13-D17 + Scenarios 5+6 + persona_kind 6-val + customer prompt v2). `ratified_by_chris: true` (spec v3).
- 2026-05-08 05:30Z — `/ux-agentico` bump `02-design-agentic.md` v2 incorporando autonomy mandate (max_turns matriz §3 actualizado + cost baseline $0.30→$2.20 §9 + DQ1-DQ4 ratificadas §12 + §13 scope expansion table). `ratified_by_chris: true` (design v2).
- 2026-05-08 06:00Z — `/po` cierra Story C: spec v3 + design v2 + delta v1 todos ratificados Chris. Transition `state: refining → refined`. `next_action: /architect orchestrator` (consume 01-spec.md + 02-design-agentic.md → produce ready package 03-arch + 04-validators + 05-guidelines + 06-tickets → state=refined→ready). Story D (`sales-agent-goldens-3-tenants-dataset`) ahora unblocked para refinement (depends_on A+B+C, todos refined/done).
