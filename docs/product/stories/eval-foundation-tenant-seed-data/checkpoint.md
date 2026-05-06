---
story_id: eval-foundation-tenant-seed-data
outcome: pi-12-sales-agent-eval-foundation
state: refining
phase: PM_DRAFT
last_artifact: 00-story.md
last_modified: 2026-05-06T17:11:00Z
next_action: "Esperar `maintenance-skill-sales-agent-audit` a refined → luego /po-ux (UI std data seeding flow) o /po (service) redacta 01-spec.md → ratificación Chris → /architect"
ratified_by_chris: false
spawned_at: 2026-05-06T17:11:00Z
spawned_by: /pm
parallel_safe: false  # blocker absoluto del resto de eval-foundation-*
blocked_reason: "Depende de maintenance-skill-sales-agent-audit (state=refining) — no procede hasta que skill audit esté refined"
audit_iterations: 0
legacy_exempt: true
---

## Bitácora

- 2026-05-06 17:11Z — `/pm` creó folder + checkpoint. Story A (foundation) — pre-requisito absoluto de simulator-homologation, personas-as-simulators, goldens-generated-from-simulation, voice-fidelity-grader, pass-k-tracking, ci-gate, cost-cap, adversarial-suite. Sin 3 tenants seed con data realística completa (brand+offer+personality+pricing+buyer_personas), todo lo posterior es mock que no prueba nada real.
