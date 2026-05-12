---
story_id: luana-nicolify-migration
outcome: luana-platform-migration
state: refined                                   # 2026-05-12 Session 5 Phase 1 — Chris ratified 01-spec.md + Halt Trigger #11 added to §7.6.2
phase: PHASE_1_SPEC_RATIFIED_PHASE_1B_ARCHITECT
last_artifact: 01-spec.md
last_modified: 2026-05-12
next_action: "architect-orchestrator Opus spawn — emit ready package 5 files (03-arch.md consolidado + 03-arch-be.md + 04-validators.yaml executable + 05-guidelines.md + 06-tickets.yaml sharded per blast-radius)"
ratified_by_chris: true                          # 2026-05-12 — 10 business decisions §7.6 cemented Session 5 Phase 0
spawned_at: 2026-05-09
spawned_by: /pm
ratified_at: 2026-05-12
ratified_by: chris
parallel_safe: false                             # cap ≤2 paralelo Chris explicit framing (NOT 3 — stability priority)
sequence_in_outcome: 10
blocks: [luana-vitalia-bootstrap, luana-comunify-bootstrap, luana-lupulo-bootstrap, luana-brand-voice-elevation]
blocked_by: [luana-v0-1-0-publish]               # done 2026-05-12
target_state: developed by 2026-05-13            # Session 5 target close 6-7h
estimated_complexity: high
estimated_tickets: 12-18                         # revised post-Phase-0 — scope big bang but defer admin+workers Story 10b
surface: full-stack (BE imports rewrite + FE imports rewrite + fresh nicolify DB + AISALESHT archive + /pm SSoT migration)
production_code: false                           # mostly mechanical refactor, NO new business logic — Sonnet eligible for non-agentic, Opus for critical/agentic
owner_eligibility: [sonnet, opus]
session_5_decisions_ratified: §7.6 outcome luana-platform-migration.md
halt_and_ask_triggers: §7.6.2 outcome luana-platform-migration.md
success_criteria: §7.6.3 outcome luana-platform-migration.md
parallelization_cap: 2                           # Chris explicit framing — stability over speed
opus_priority: critical_tickets                  # imports rewrite, schema consolidation, /pm SSoT migration, Vercel reconfig
handoff_prompt_story_10b: required_at_close       # Chris explicit request
---

# Story 10 — Migrate Nicolify to consume Luana Platform

> **Status:** 🔬 refining (Session 5 Phase 0 complete — 10 business decisions ratified)

## Phase 0 closed — 10 decisions ratified 2026-05-12

| # | Decisión | Opción | Detail |
|---|---|---|---|
| 1 | Scope completeness | A — Full big bang | Sub-agent decomposition smart blast radius, cap ≤2 paralelo, Opus crítico |
| 2 | DB migration | B — Fresh nicolify DB + purge + alembic restart | No clientes real, ventana oportunidad clean |
| 3 | AISALESHT lifecycle | A — Archive read-only post-Story-10 | GitHub Settings UI |
| 4 | /pm SSoT location | A — Migrate atómico Fase 4 merge | Muy cuidadoso, snapshot + verify scripts + halt-and-ask |
| 5 | Test parity | B — Match baseline + fix-on-discovery trivial | Delta=0 new failures bloqueante |
| 6 | FE Next.js strategy | B — FE workspace member luana-platform | `pnpm-workspace.yaml` + Vercel reconfig |
| 7 | Streamlit admin | B — Defer Story 10b | Escape hatch architect si trivial |
| 8 | CI parity location | B — luana-platform root cross-brand | Stories 11-13 heredan automático |
| 9 | 40 sales_agent failures | B — Defer Story 14 brand-voice-elevation | DEFERRED-FAILURES-STORY-10.md generated |
| 10 | Pre-auth scope Sesión 5 | A — Story 10 solo | Handoff prompt Story 10b al cierre |

Detail completo: `docs/product/outcomes/luana-platform-migration.md` § 7.6

## Bitácora

- **2026-05-09**: Story spawned by /pm state=parked. blocked_by Story 9 (then in development)
- **2026-05-12**: Story 9 closed DONE. Story 10 unblocked but ratified_by_chris=false
- **2026-05-12 Session 5 Phase 0**: /pm spawned. Chris ratified 10 business decisions §7.6. Transition state=parked → refining. /po next.
- **2026-05-12 Session 5 Phase 1**: /po Opus emitted 01-spec.md (1304 líneas, 9 features × 4 escenarios = 36 Gherkin scenarios). Chris ratified spec + accepted NEW Halt Trigger #11 (test mock missing path). Outcome §7.6.2 updated. Transition state=refining → refined. architect-orchestrator next.
