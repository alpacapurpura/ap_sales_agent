---
story_id: eval-foundation-tenant-seed-data
outcome: pi-12-sales-agent-eval-foundation
state: ready
phase: READY_PACKAGE_CLOSED
last_artifact: 06-tickets.yaml
last_modified: 2026-05-06T21:35:00Z
next_action: "/dev-team Conv 2 autonomous build → toma T-1 (state ready→developing). 4 tickets en cascada T-1→T-2→T-3→T-4. Total 5-7d. Surfaces BE only, production_code=false los 4. Owner pool [qwen-opencode, claude-sonnet] para T-1+T-2; claude-sonnet preferred para T-3+T-4 (content drafting + Chris assistance)."
ratified_by_chris: true
spawned_at: 2026-05-06T17:11:00Z
spawned_by: /pm
parallel_safe: false  # blocker absoluto del resto de eval-foundation-*
blocked_reason: null
audit_iterations: 0
legacy_exempt: true
---

## Bitácora

- 2026-05-06 17:11Z — `/pm` creó folder + checkpoint. Story A (foundation) — pre-requisito absoluto de simulator-homologation, personas-as-simulators, goldens-generated-from-simulation, voice-fidelity-grader, pass-k-tracking, ci-gate, cost-cap, adversarial-suite.
- 2026-05-06 20:30Z — `/po` redactó `01-spec.md` v1 con 4 scenarios + 10 open questions.
- 2026-05-06 20:50Z — Chris ratificó las 10 preguntas con 4 clarificaciones explicadas (Q4 in-memory vs BD, Q5 PII concept, Q6 edge L0, Q9 URL verification escalable 1000+ tenants). Scope expandido 3→5 tenants (Q1+Q2 split). Q7 disparó creación story nueva placeholder `sales-agent-dialect-configuration` (state=idea) para feature UX tenant config dialecto BCP-47.
- 2026-05-06 20:55Z — `/po` bumpeó a `01-spec.md` v2 con todas decisiones ratificadas. Transition state `refining → refined` + `ratified_by_chris: true`.
- 2026-05-06 21:35Z — `/architect` cerró ready package. Single sub-architect inline (BE only, surface data-fixtures pure sin DDD/services/migrations, sin spawn de /architect-be subagent). Artifacts: `03-arch.md` consolidado (AD1-AD10 decisiones cardinales) + `04-validators.yaml` (10 validators, 4/4 scenarios cubiertos) + `05-guidelines.md` (workflow 4 tickets + patterns required/forbidden + files in scope + catálogo BCP-47 inicial + .eval-whitelist inicial + scanner regex set) + `06-tickets.yaml` (4 tickets cascada T-1 infra → T-2 scanner+hook → T-3 drafts content → T-4 curación, total 5-7d, production_code=false los 4, owner pool sonnet/qwen). **Transition state `refined → ready`.** Conv 2 autonomous build puede arrancar.
- 2026-05-06 21:35Z — Resume post computer crash: 03-arch.md + 04-validators.yaml ya escritos pre-crash (verificados íntegros), 05-guidelines.md + 06-tickets.yaml + checkpoint update completados post-resume.
