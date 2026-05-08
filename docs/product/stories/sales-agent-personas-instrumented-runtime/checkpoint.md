---
story_id: sales-agent-personas-instrumented-runtime
outcome: pi-12-sales-agent-eval-foundation
state: ready
phase: ARCH_PACKAGE_DELIVERED
last_artifact: 06-tickets.yaml
last_modified: 2026-05-08T07:30:00Z
next_action: "/dev-team picks 06-tickets.yaml T-1 (or T-2 in parallel) → autonomous build vs validators → on GREEN state=developing→developed → manual /auditor trigger Conv 3 by Chris"
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
  - 01-spec.md             # po_version=3, ratified 2026-05-08T05:00Z
  - 02-design-agentic.md   # ux_version=2, ratified 2026-05-08T05:30Z
  - delta-spec.md          # delta_version=1, ratified 2026-05-08T05:00Z
  - 03-arch.md             # arch_version=1, /architect 2026-05-08T07:00Z (single-shot full-stack mode)
  - 04-validators.yaml     # schema v4, /architect 2026-05-08T07:00Z
  - 05-guidelines.md       # /architect 2026-05-08T07:00Z
  - 06-tickets.yaml        # 9 tickets DAG, /architect 2026-05-08T07:00Z
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
- 2026-05-08 05:30Z — `/ux-agentico` bump `02-design-agentic.md` v2 incorporando autonomy mandate. `ratified_by_chris: true` (design v2).
- 2026-05-08 06:00Z — `/po` cierra Story C: spec v3 + design v2 + delta v1 todos ratificados. Transition `state: refining → refined`. `next_action: /architect orchestrator`.
- 2026-05-08 07:00Z — `/architect` (Opus 4.7, single-shot full-stack mode per learnings.md 2026-05-08 — sub-architect-be + sub-architect-agentic types not registered) entrega ready package:
    - `03-arch.md` (consolidated full-stack arch — BE test-infra YAMLs + AGENTIC test-infra loader/prompt v2/scenarios)
    - `04-validators.yaml` (schema v4 — 4 categories, 21 validators, scenario_coverage 6/6)
    - `05-guidelines.md` (patterns required + forbidden + 27 files in scope + 22 files NEVER touched + skills/rules to load)
    - `06-tickets.yaml` (9 tickets DAG, 22h estimate, 7 AGENTIC Opus + 1 BE Sonnet + 1 DOCS /pm)
  Cross-module audit ejecutado (NO NEW LAYER rule): personas_loader genuinamente NEW, ActorProfile EXTEND, SCHEMA_MIGRATIONS EXTEND, CUSTOMER_PERSONA_PROMPT V2 ADDITIVE. Story B 7-name __init__ surface frozen. R23 mandatory Opus 4.7 para 7 agentic tickets per Chris autonomy mandate cero deuda. Transition `state: refined → ready`. `next_action: /dev-team` Conv 2 autonomous build.

## Próximo paso

`/dev-team` Conv 2 starts:
1. Reads `06-tickets.yaml` — picks T-1 (ActorProfile schema bump + migrators) and T-2 (20 YAML + arch fitness) **in parallel** (independent DAG roots).
2. Spawns `builder-agentic` Opus 4.7 for T-1, T-3, T-4, T-5, T-6, T-7, T-8 (7 tickets — production-critical agentic).
3. Spawns `builder-backend` Sonnet for T-2 (declarative YAML + arch fitness gate).
4. Iterates each ticket vs `04-validators.yaml` until GREEN or cap_reached (3 iterations max).
5. On GREEN: state=developing→developed, append iteration_log to T-{n}-impl-log.md, commit + push (parallel-safety stage by name).
6. T-9 (docs reconciliation) deferred to /pm post-merge — only after T-6/T-7/T-8 done.
7. Awaiting Chris manual `/auditor` trigger (Conv 3) once all tickets developed — auditor scope: C1-C3 Opus + tests/lint/format Sonnet + downstream regression scope per `.claude/rules/auditor-downstream-regression.md`.
