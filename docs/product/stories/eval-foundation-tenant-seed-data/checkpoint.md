---
story_id: eval-foundation-tenant-seed-data
outcome: pi-12-sales-agent-eval-foundation
state: refined
phase: SPEC_RATIFIED
last_artifact: 01-spec.md
last_modified: 2026-05-06T20:55:00Z
next_action: "/architect orchestrator → produce ready package (03-arch.md + 04-validators.yaml + 05-guidelines.md + 06-tickets.yaml). Service-story BE-only data-seeding (sin FE, sin agentic), 5 tenants × 6 YAMLs + loader + dialect catalog + scanner PII + pre-commit hook Section 7. Estimate 5-7d."
ratified_by_chris: true
spawned_at: 2026-05-06T17:11:00Z
spawned_by: /pm
parallel_safe: false  # blocker absoluto del resto de eval-foundation-*
blocked_reason: null  # spec ratified, ready for architect
audit_iterations: 0
legacy_exempt: true
---

## Bitácora

- 2026-05-06 17:11Z — `/pm` creó folder + checkpoint. Story A (foundation) — pre-requisito absoluto de simulator-homologation, personas-as-simulators, goldens-generated-from-simulation, voice-fidelity-grader, pass-k-tracking, ci-gate, cost-cap, adversarial-suite. Sin 3 tenants seed con data realística completa (brand+offer+personality+pricing+buyer_personas), todo lo posterior es mock que no prueba nada real.
- 2026-05-06 20:30Z — `/po` redactó `01-spec.md` v1 con 4 scenarios + 10 open questions. Awaiting ratificación.
- 2026-05-06 20:50Z — Chris ratificó las 10 preguntas con 4 clarificaciones explicadas (Q4 in-memory vs BD, Q5 PII concept, Q6 edge L0, Q9 URL verification escalable 1000+ tenants). Scope expandido 3→5 tenants (Q1+Q2 split). Q7 disparó creación story nueva placeholder `sales-agent-dialect-configuration` (state=idea) para feature UX tenant config dialecto BCP-47.
- 2026-05-06 20:55Z — `/po` bumpeó a `01-spec.md` v2 con todas decisiones ratificadas: 5 tenants (A1 Coach PEN/es-PE, A2 Medicina estética PEN/es-MX, A3 Clínica dental PEN/es-CO, A4 Growth Marketing video+RRSS PEN/es-AR, A5 Agencia Automatización IA PEN/es-419), dialect catalog BCP-47 ≥13 entradas, scanner PII scope quirúrgico, edge L0 warning+proceed, URL verification solo schema, buyer personas 3 per tenant (2 base + 1 adversarial), estimate 5-7d. **Transition state `refining → refined`** + `ratified_by_chris: true`. Handoff a `/architect`.
