---
story_id: luana-nicolify-migration
outcome: luana-platform-migration
state: developing                                 # 2026-05-12 Session 5 Phase 2 paused mid-Wave-1A — T-2 third attempt cut off mid-work
phase: PHASE_2_PAUSED_AWAITING_CHRIS_STRATEGIC_DECISION
last_artifact: SESSION-5-HALT-2026-05-12.md
last_modified: 2026-05-12
next_action: "Chris chooses Session 6 strategy: R1 (proactive lift audit, recommended) | R2 (whack-a-mole continuation) | R3 (accept partial). Detail: SESSION-5-HALT-2026-05-12.md"
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
- **2026-05-12 Session 5 Phase 1B**: architect-orchestrator Opus emitted ready package en 2 spawns (Part 1 = 03-arch + 03-arch-be + 05-guidelines; Part 2 = 04-validators + 06-tickets). Total 5 files: 03-arch.md (639 líneas) + 03-arch-be.md (862 líneas) + 04-validators.yaml (59 validators across 4 cat, 36 scenarios covered) + 05-guidelines.md (535 líneas) + 06-tickets.yaml (14 tickets T-1..T-14 sharded Z1 strategy ≤2 paralelo Wave 1). 10 Opus-mandatory tickets + 4 Sonnet-OK. Transition state=refined → ready. Brief Chris check-in pre-Phase 2 build.
- **2026-05-12 Session 5 Phase 2 (paused mid-Wave-1A)**: T-1 baseline ✓ done (commit `623b4872`). T-1.5 luana-core editable install ✓ done (`039f4f8e`). T-1.6 codemod MAPPING audit fix ✓ done (`340fd350`). T-2 brand+offer rewrite halted 3 times (Trigger #1 mitigated T-1.5, Trigger #11 false positive mitigated T-1.6, third attempt cut off mid-work post-codemod-apply — builder discovered "4 remaining re-exports needed" indicating lift Stories 1-9 incomplete symbol parity). 226 files modified WIP stashed (`stash@{0}: WIP-T-2-third-attempt-cutoff-need-re-exports`). Transition state=ready → developing (Phase 2 active but paused). Cumulative Session 5 cost ~$2100. Halt-and-ask Chris: R1 proactive lift audit (recommended) | R2 whack-a-mole continuation | R3 accept partial. Detail: SESSION-5-HALT-2026-05-12.md.
