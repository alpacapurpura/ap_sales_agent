---
story_id: sales-agent-goldens-3-tenants-dataset
outcome: pi-12-sales-agent-eval-foundation
state: ready
phase: ARCHITECT_DELIVERED
last_artifact: 06-tickets.yaml          # ready package complete (03-arch + 04-validators + 05-guidelines + 06-tickets)
last_modified: 2026-05-08T08:00:00Z
next_action: "/dev-team build cuando Story C build done (HARD blocker). Architect phase complete; package autocontenido. T-1 + T-2 paralelos (Story C-independent); T-3 + T-4 agentic_eval validators gated on Story C build done."
ratified_by_chris: true                  # spec v3 ratified 2026-05-08T07Z; ready package follow-on
spawned_at: 2026-05-04T20:00:00Z
spawned_by: /pm
parallel_safe: true                       # architect phase parallel-safe with Story C; build phase HARD blocked by Story C
blocked_reason: null                       # build_blocked_by_external_story handled per-ticket field, not story-level
build_blocked_by_external_story: true
build_blocker:
  story: sales-agent-personas-instrumented-runtime
  blocker_type: hard
  required_state: done
  reason: "Story D T-3 + T-4 require runtime `load_actor_profile_for_tenant` + `get_max_turns_for_persona_kind` from Story C `_internal/personas_loader.py`. T-1 + T-2 are Story C-independent and can build in parallel once Story D state=ready."
audit_iterations: 0
legacy_exempt: true
ready_package:
  03_arch_md: present                     # 03-arch.md (1371 lines)
  04_validators_yaml: present             # 04-validators.yaml (363 lines)
  05_guidelines_md: present               # 05-guidelines.md (298 lines)
  06_tickets_yaml: present                # 06-tickets.yaml (588 lines)
ticket_count: 5
total_estimate_hours: 16
owner_routing:
  T-1_schema: builder-backend-sonnet
  T-2_pii_scanner_hook: builder-backend-sonnet
  T-3_generation_promotion_scripts: builder-backend-sonnet
  T-4_schema_referential_coverage_arch_gates: builder-backend-sonnet
  T-5_docs_reconciliation: pm-post-merge
arch_fitness_gates_added: 5
new_arch_gates:
  - test_goldens_schema_completeness
  - test_goldens_no_mirror_simulator_schema
  - test_pii_patterns_single_source
  - test_goldens_no_committed_pii
  - test_goldens_cost_bucket_invariant   # env-gated EVAL_GOLDENS_COST_BUCKET_VERIFY=1
migrated_from: docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/*/stories/sales-agent-goldens-3-tenants-dataset/
reframe_history:
  - date: 2026-05-06T17:11:00Z
    by: /pm + Chris ratificación
    from: "v1 — extraer 12 goldens de tablas sales_agent_session producción"
    to: "v2 — generar 20-30 goldens desde simulator dual-LLM + curación manual Chris (state-of-the-art mayo 2026)"
    reason: "Sales_agent NO en producción + cero conversaciones reales. Synthetic-first canónico research mayo 2026."
---

## Bitácora

- 2026-05-04 20:00 — `/pm` creó folder + `00-story.md`. Phase=PM_DRAFT, status=pending. Bloqueado hasta S1 + decisión tenants.
- 2026-05-06 — Migrado a paradigma v4: state=refining (legacy_exempt). Pendiente /po para spec ratification.
- 2026-05-06 16:00Z — `/po` redactó `01-spec.md` v1 (extracción de prod), 4 scenarios + 10 open questions. Commit `f7624c9f` push origin/development.
- 2026-05-06 17:11Z — **REFRAME synthetic-first** (Chris ratificó). v1 archivado-en-repo. Story re-rol D en sub-épica `eval-foundation-*`.
- 2026-05-08 06:30Z — `/po` redactó `01-spec.md` v2 synthetic-first reframe. Coverage 5 tenants × 3 kinds × 1-2 winners = 20-30 goldens. 17 decisiones cardinales D1-D17. 8 open questions Q1-Q8.
- 2026-05-08 07:00Z — Chris ratificó Q1-Q8 (todas opción A recomendada, except Q3=B Markdown). `/po` bump v3 inline. `state: refining → refined`. `next_action: /architect orchestrator`.
- 2026-05-08 08:00Z — `/architect` orchestrator (Opus 4.7, SINGLE_SHOT_FULLSTACK BE-only mode per learnings.md 2026-05-08 — sub-architect agent types not registered) entregó **ready package** completo:
  - `03-arch.md` (1371 lines) — schema + tooling + scanner + hook + capability + cross-cutting + 15 D-A-* decisions + state-of-the-art research notes
  - `04-validators.yaml` (363 lines) — 4 categories (non_functional 9 + functional 11 + agentic_eval 3 + scenario_coverage 1 = 24 validators)
  - `05-guidelines.md` (298 lines) — patterns required/forbidden + files in/out scope + reference docs orden estricto + TDD layered + native-first + owner routing
  - `06-tickets.yaml` (588 lines) — 5 tickets atomic DAG (T-1 schema + T-2 PII LIFT/scanner/hook + T-3 generation/promotion scripts + T-4 referential/coverage/README/arch gates + T-5 /pm docs reconciliation)
  - State transition: `refined → ready`. T-1 + T-2 paralelos Story C-independent; T-3 + T-4 agentic_eval validators gated on Story C build done.

## Próximo paso

`/dev-team` autonomous build espera Story C build done (HARD blocker). Mientras Story C state=developing→developed pending, Story D state=ready waiting. Cuando Story C state=done → `/dev-team` toma Story D `06-tickets.yaml`:

1. T-1 + T-2 parallel (Story C-independent)
2. T-3 unit tests (mocked); agentic_eval validators run nightly --run-evals when Story C ready
3. T-4 referential integrity gated on Story C 15 personas YAMLs present
4. T-5 /pm post-merge documentation

Build-time validators GREEN → state=developed → `/auditor` triggered manual by Chris → state=reviewing → APPROVED → state=done → /pm merge → capability promotion + archive `docs/archive/2026/stories/sales-agent-goldens-3-tenants-dataset/`.
