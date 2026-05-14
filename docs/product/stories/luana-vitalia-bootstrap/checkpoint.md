---
story_id: luana-vitalia-bootstrap
outcome: luana-platform-migration
state: ready
phase: READY_PACKAGE_DONE
last_artifact: 06-tickets.yaml
last_modified: 2026-05-13
next_action: "Sesion 3: /dev-team picks 06-tickets.yaml ticket-by-ticket autonomous build. Working dir /home/chris/luana-platform/vitalia/. 38 atomic tickets (15 AGENTIC opus-mandatory R23 + 23 BE/FE/config Sonnet-OK). Validators 70 (4 categories) executable must_pass:true c/u. State ready → developing."
ratified_by_chris: true
phase0_ratified_by_chris: true
design_agentic_drafted: true                    # Sesion 2 Phase 1 (2026-05-13)
architecture_drafted: true                      # Sesion 2 Phase 2 (2026-05-13) — 03-arch.md + 03-arch-{be,fe,agentic}.md
validators_drafted: true                        # 04-validators.yaml 70 validators 4 cats
guidelines_drafted: true                        # 05-guidelines.md
tickets_drafted: true                           # 06-tickets.yaml 38 atomic tickets
spec_ratified_at: 2026-05-13
spawned_at: 2026-05-09
spawned_by: /pm
unblocked_at: 2026-05-16                        # Story 10 done APPROVED 27/27 CHECKPOINTS (cc508afb)
refining_started_at: 2026-05-13                 # Sesion 1 Phase 0 ratification
refined_at: 2026-05-13                          # Sesion 1 spec ratified
ready_at: 2026-05-13                            # Sesion 2 ready package completed
parallel_safe: true                             # parallel with 12, 13, 14
sequence_in_outcome: 11
blocks: []
blocked_by: []                                  # Story 10 done 2026-05-16
target_state: developed by 2026-07-04
estimated_complexity: very_high
estimated_tickets: 25-30                        # narrowed post-Q17 ratification (deferred multi_site UI + insurance + Stripe HC flag + wellness deep)
actual_tickets: 38                              # Sesion 2 /architect decomposed atomic ≤4h c/u — slightly above target, justified vertical-medical big-bang
total_validators: 70                            # 13 non_functional + 15 functional + 20 visual + 22 agentic_eval
estimated_total_hours: 130-150
surface: full-stack new brand app (vertical-medical extensions)
production_code: true                           # vertical-medical agentic tools
owner_eligibility: [opus]                       # AGENTIC vertical for medical (mixed BE/FE Sonnet OK; 15 AGENTIC tickets Opus exclusive R23)
sesion_1_scope_completed: phase_0_ratification + po-ux_01-spec_authoring + chris_ratification → state refined
sesion_2_scope_completed: ux-agentico_02-design-agentic + architect_03-arch_consolidated + 03-arch_be_fe_agentic + 04-validators_70 + 05-guidelines + 06-tickets_38 → state ready
phase_0_decisions:                              # ratified 2026-05-13 Sesion 1 Fase A
  Q1_scope: A_full_big_bang                     # 25-30 tickets full skeleton+config+agentic+payment
  Q2_agentic: A_full_per_spec                   # 4 tools + 2 extractors + 1 workflow + 3 KB packs
  Q3_deploy: B_subdir_luana_platform            # vitalia/ subdir + extraction Story 11.bis
  Q4_setup_ownership: B_chris_ui_manual         # Clerk app #2 + K8s + DNS + payment keys = Chris UI gate
  Q5_piloto: research_driven_fixtures           # 3 LatAm clinic fixtures (Aurora dental AR + Mindful CL + Sanaré LATAM MX)
  Q6_halts: A_h1_h13_verbatim                   # Story 10 H1-H13 adapted brand bootstrap context
  Q7_sesion_1: A_spec_only                      # 01-spec.md + ratify → refined → close Sesion 1
spec_q17_decisions:                             # ratified 2026-05-13 Sesion 1 Fase B
  Q1_voseo_chrome_ui: B_spanish_neutro_pure
  Q2_multi_site_ui: B_defer_story_11_bis
  Q3_insurance_latam: B_defer_story_11_bis
  Q4_doctor_calendar: A_reuse_luana_core_plus_extensions
  Q5_booking_widget: B_both_iframe_and_canonical
  Q6_payment_gateway: B_mercadopago_primary_stripe_connect_fallback_no_hc_flag
  Q7_wellness_scope: B_ui_enabled_deep_coverage_defer_story_11_bis
---
