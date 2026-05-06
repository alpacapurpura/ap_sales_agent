---
story_id: eval-foundation-simulator-homologation
outcome: pi-12-sales-agent-eval-foundation
state: refining
phase: PM_DRAFT
last_artifact: 00-story.md
last_modified: 2026-05-06T17:11:00Z
next_action: "Esperar `eval-foundation-tenant-seed-data` a refined → luego /po redacta 01-spec.md service-story → ratificación Chris → /architect"
ratified_by_chris: false
spawned_at: 2026-05-06T17:11:00Z
spawned_by: /pm
parallel_safe: false
blocked_reason: "Depende de eval-foundation-tenant-seed-data (state=refining) — el simulator necesita tenants seed para ejecutar"
audit_iterations: 0
legacy_exempt: true
---

## Bitácora

- 2026-05-06 17:11Z — `/pm` creó folder + checkpoint. Story B (foundation) — homologa `client_simulator/` raíz a `backend/tests/agentic_evals/sales_agent/simulator/`. Wirea dual-LLM pattern (1 LLM = user persona, 1 LLM = sales_agent runtime real) usando ActorProfile pattern (AWS Strands Evals). Bloquea personas-as-simulators y goldens-generated-from-simulation.
