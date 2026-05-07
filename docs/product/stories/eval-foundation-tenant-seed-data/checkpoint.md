---
story_id: eval-foundation-tenant-seed-data
outcome: pi-12-sales-agent-eval-foundation
state: developing
phase: BUILD_T2
last_artifact: T-1-result.md
last_modified: 2026-05-06T23:00:00Z
next_action: "/dev-team builder-backend builds T-2: PII scanner (backend/scripts/scan_seed_pii.py) + .eval-whitelist + pre-commit hook Section 7 + test_seed_pii_scanner.py. T-1 closed pushed."
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
- 2026-05-06 22:00Z — `/dev-team` pickup. State `ready → developing` (transition autorizada Chris). Pre-req `maintenance-skill-sales-agent-audit` state=`reviewing` ≥refined ✅. WIP cap developing 0→1/3. Phase=BUILD_T1.
- 2026-05-06 23:00Z — T-1 closed pushed. Builder: claude-sonnet. Deliverables: loader.py + TenantContext + OfferLadderContext + dialect_catalog.yaml (15 entries) + 4 test files baseline. Validators: ruff GREEN, arch fitness 827/827, dialect catalog 4/4 GREEN, loader 1/22 GREEN (RED baseline confirmed). Phase=BUILD_T2.
