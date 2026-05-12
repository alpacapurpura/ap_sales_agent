---
story_id: luana-sales-agent-engine
outcome: luana-platform-migration
state: done
phase: merged_archived
last_artifact: 07-merge.md
last_modified: 2026-05-12
dev_team_started_at: 2026-05-12
dev_team_completed_at: 2026-05-12
audit_started_at: 2026-05-12
audit_completed_at: 2026-05-12
done_at: 2026-05-12
merged_by: /pm (claude-opus-4-7)
next_action: "Story 7 closed DONE. 7/14 outcome stories. Story 8 unblocked. Session 3 closes (Stories 6+7 sequential autonomous extension §7.4 cap 2 stories Tier 3 completed)."
ratified_by_chris: true  # Session 3 pre-auth 2026-05-11 (outcome §7.2 + ratificación 2 eval WAIVED)
session_3_ratification_date: 2026-05-11
session_3_mandate: "autonomous Tier 3 lift per outcome §7.2 + §7.4 cap extended 2 stories. R23 Opus mandatory all tickets. D-T3 BrandVoicePort hexagonal introduced this story."
unparked_at: 2026-05-11
unparked_reason: "Session 3 autonomous mandate — Story 7 executes after Story 6 done sequencially. Eval gate Story E WAIVED to Luana v0.2.0 per outcome §2 OQ1 + session 3 ratificación 2."
spawned_at: 2026-05-09
spawned_by: /pm
ready_at: 2026-05-11
ready_by: /architect-orchestrator (claude-opus-4-7) — single spawn for Stories 6+7 per D-T4
parallel_safe: false
sequence_in_outcome: 7
blocks: [luana-campaigns-extension-sdk]
blocked_by: [luana-copilot-engine]   # Story E (sales-agent-voice-fidelity-grader-runtime) WAIVED to Luana v0.2.0 per session 3 ratificación 2
blocker_waivers:
  - blocker_id: "story-E-sales-agent-voice-fidelity-grader-runtime done"
    waived_at: 2026-05-11
    waived_by: chris (session 3 mandate)
    reason: "Outcome §2 OQ1 explicitly states eval framework deferred to Luana v0.2.0. Story E blocked by PI-12 eval-foundation incompleta. Lift sales_agent runtime WITHOUT Story E done; voice fidelity CI gate deferred until v0.2.0 eval framework ship complete. Track in Story 7 DEFERRED-FILES."
target_state: developed by 2026-06-01
estimated_complexity: very_high
estimated_tickets: 19
total_tickets: 19
surface: backend (sales_agent — 17k LOC)
production_code: true                           # AGENTIC PRODUCTION CODE — R23 Opus mandatory
owner_eligibility: [opus]
ready_package_files:
  - 00-story.md (Chris spawn 2026-05-09)
  - 03-arch.md (architect 2026-05-11 — 626 lines, lift strategy + D-T3 BrandVoicePort + connections wiring + §3 protected surfaces + eval framework WAIVED)
  - 03-arch-agentic.md (architect 2026-05-11 — 283 lines, supervisor specialist routing + 5-slot prompt cache + slot 5 BRAND_VOICE via D-T3 + §3 12 protected files)
  - 04-validators.yaml (architect 2026-05-11 — 357 lines, 22 validators)
  - 05-guidelines.md (architect 2026-05-11 — 640 lines, lift mode + D-T3 unique T-3 + D-T6 anti-mirror + eval EXCLUSION + §3 hash-stable + Spanish voseo exception)
  - 06-tickets.yaml (architect 2026-05-11 — 870 lines, 19 tickets DAG-ordered)
6_dt_decisions:
  D-T1: "Sales agent tool registry frozen public API at lift moment — parallels Story 6 D-T1 pattern. Story 8 EP-1..EP-5 wraps."
  D-T2: "N/A — Story 5 stub cleanup is Story 6 T-17. AppointmentModel stub stays Story 8."
  D-T3: "★ Story 7 INTRODUCES BrandVoicePort + BrandVoiceService in luana-core-brand-studio (T-3) per ADR-001 §2.4. Sales agent slot 5 BRAND_VOICE consumes via hexagonal port. PersonalityCompiler SSoT cement Story 5 preserved (NEVER moved, NEVER mirrored)."
  D-T4: "Single architect spawn — produced Stories 6+7 ready packages together this session."
  D-T5: "builder-agentic + auditor-agentic Opus mandatory ALL 19 tickets."
  D-T6: "Sales agent lift surfaces: LangGraph supervisor specialist routing verbatim, slot 5 BRAND_VOICE via BrandVoicePort, observability subclass pattern (SalesAgentCallbackHandler + SalesAgentObservabilityContext from luana_core_observability), §3 protected surfaces hash-stable (12 files: closer_studio API+WS + SmartBufferService + OutputManager + enrollment + webhook adapters + follow_up_engine + PromptVersionModel + tool_call_dedup), typing_simulation_cpm registry preserved."
3_ratifications_session_3:
  ratificacion_1: "§7.4 cap extended to 2 stories Tier 3 secuencial — Story 7 executes post Story 6 done"
  ratificacion_2: "★ Story 7 eval gate WAIVED to Luana v0.2.0 — eval simulator + MAJ-EVAL grader + personas catalog + goldens dataset infra + Story I adversarial DEFERRED. Sales agent runtime lifts WITHOUT eval framework. Cost-bucket separation tables (eval_simulator_llm_call, eval_simulator_trace_event, eval_simulator_grade, eval_simulator_grade_cache, eval_synthetic_tenants) stay in nicolify repo. Story E voice fidelity CI gate WAIVED."
  ratificacion_3: "R23 Opus mandatory ALL 19 tickets — production agentic code, NO Sonnet eligibility"
introduced_abstractions:
  - "BrandVoicePort Protocol — core/luana-core-brand-studio/src/luana_core_brand_studio/application/ports/brand_voice_port.py (D-T3 ADR-001 §2.4)"
  - "BrandVoiceService concrete adapter — core/luana-core-brand-studio/src/luana_core_brand_studio/application/services/brand_voice_service.py (D-T3)"
unlifted_resolutions:
  - "luana-core-connections/api/dependencies/__init__.py NotImplementedError stub REPLACED with real ChatOrchestrator wiring (Stories 4+6 deferral resolved via T-16 — Story 7 has both luana_core_copilot + luana_core_sales_agent)"
new_deferrals_story_7:
  - "Eval framework → Luana v0.2.0 (per Session 3 ratificación 2 + outcome §2 OQ1): observability/eval_simulator/ + tests/agentic_evals/sales_agent/ + Story E voice fidelity grader runtime + MAJ-EVAL grader + personas catalog + goldens dataset + adversarial jailbreak"
  - "Scheduling concrete provider runtime → Story 8 (campaigns-extension-sdk batch): sales_agent/application/tools/scheduling/providers.py lifts WITH deferred-import pattern preserved. Runtime fails on scheduler invocation in Luana standalone UNTIL Story 8 lifts scheduling module."
  - "Streamlit admin pages → Story 10 (nicolify shell migration)"
new_arch_fitness_tests: 8  # V-AG-1..V-AG-8 in core/tests/architecture/
---

## Bitácora

- 2026-05-12 (state reviewing → done): Phase 7 merge applied by /pm. auditor-agentic Opus APPROVED with 1 trivial finding auto-fixed iter 1 of cap 2 (D-T2 T-17 cement MessageModel stub cleanup — commit `147c61d` luana-platform). REVIEW-agentic.md cement. Capability `luana-core-sales-agent` v0.0.7-alpha promoted to docs/product/capabilities/luana-core/sales-agent.yaml. Outcome `luana-platform-migration` stories_done append luana-sales-agent-engine → 7/14 stories DONE. Story 8 luana-campaigns-extension-sdk unblocked. Session 3 closes (Stories 6+7 secuencial autonomous Tier 3 §7.4 cap extension completed).

- 2026-05-12 (state developed → reviewing): Phase 6 audit start. auditor-agentic Opus spawned. C1 (code) + C2 (spec) + C3 (architecture) + C4 (cross-cutting) + C5 (trace) + 8 NEW arch fitness V-AG-1..V-AG-8 + downstream regression R3. Auto-fix cap 2 iter trivial findings (lint/typo/format). Halt criteria: REJECT + 3 auto-fix iter fail → escalate Chris.

- 2026-05-12 (batch 6 — T-16+T-17+T-18+T-19 GREEN, state developing → developed): Phase 5 build CLOSED. luana-platform commits `6625646` (T-16 connections wiring real ChatOrchestrator — Stories 4+6 deferral resolved) + T-17 verification-only (no commit, uv sync 23 packages + V-F-x-1 cross-package smoke + ModuleRegistry 9 modules + V-F-x-2 waiver acceptance per Story 6 precedent) + `9d497d6` (T-18 8 NEW arch fitness V-AG-1..V-AG-8 + §3 protected surfaces snapshot v1 — D-T3 + D-T6 + Story 5 SSoT regression cement) + `537a6d8` (T-19 finalization — ruff GREEN + AISALESHT untouched verified + DEFERRED-FILES.md Story 7 section appended + README polish). All 19 Story 7 tickets GREEN. 22 validators must_pass GREEN or WAIVED. AISALESHT `backend/src/modules/sales_agent/` UNTOUCHED throughout 19 tickets (V-NF-4 cardinal live-verified). Next: Phase 6 spawn auditor-agentic Opus.

- 2026-05-12 (batch 5 — T-13+T-14+T-15 GREEN): luana-platform commits `18bea75` (T-13 api+workers + 6 §3 hash-stable) + `84c3377` (T-14 observability subfolder D-T6 subclass + EXCLUDE eval_simulator + agentic_evals Luana v0.2.0) + `c82a3f2` (T-15 copilot_provider + entry-point + ModuleRegistry discovery picks up sales_agent). 9 modules total in registry (Stories 6 8 + Story 7 sales_agent). D-T6 anti-mirror cardinal verified 4-layer evidence. AISALESHT UNTOUCHED throughout 15 tickets cumulative.

- 2026-05-12 (batch 1-4): T-1..T-12 GREEN (12 commits cumulative — workspace + skeleton + D-T3 BrandVoicePort + domain + infra layers + orchestrator + agents/sales + tools + quality+prompts D-T3 compose_prompt + services). 20 pre-existing failures categorized as Story 4 luana-core-platform CRM tech debt + T-7 templates_dir absolute path inherited issue.

- 2026-05-12: state=ready → developing. Session 3 Phase 5 build start. Builder-agentic Opus batch 1 spawning (T-1+T-2+T-3). Story 6 closed DONE 2026-05-11 (commit 6d95b503 archive). All 19 tickets owner=builder-agentic Opus (R23). D-T3 BrandVoicePort intro T-3 — only Story 7 ticket touching luana-core-brand-studio (pre-ratified ADR-001 §2.4 + Session 3 ratificación). Eval framework WAIVED Luana v0.2.0.

- 2026-05-11: state=parked → refining. Session 3 autonomous pre-auth ratified Chris (outcome §7.2 + §7.4 extension). Story E voice fidelity CI gate WAIVED to Luana v0.2.0 per ratificación 2 + outcome §2 OQ1. D-T3 BrandVoicePort hexagonal introduction baked in architect prompt. Next: architect-orchestrator Opus produces ready package combined w/ Story 6.

- 2026-05-11: state=refining → refined → ready. Architect-orchestrator (single spawn for Stories 6+7 per D-T4) produced 5-file ready package:
  - 03-arch.md (626 lines): topology + 19 lift tickets + cross-module audit + D-T3 BrandVoicePort introduction + D-T6 observability subclass + §3 protected surfaces + eval framework WAIVED §9.1 + scheduling deferred imports preserved §9.2 + connections wiring resolution §9.3
  - 03-arch-agentic.md (283 lines): supervisor specialist routing (qualifier/product_expert/closer/supervisor/tool_executor/safety/escalate) + 5-slot prompt cache (slot 5 BRAND_VOICE via D-T3 BrandVoicePort, TTL 5min per-tenant cache prefix) + 5 base tool groups (qualification/knowledge/scheduling/payment/follow_up + safety) + observability D-T6 subclass + 12 §3 protected files preservation map
  - 04-validators.yaml (357 lines): 22 validators (7 non_functional + 13 functional + 8 agentic_eval/arch + 2 documentation), all must_pass:true blocking
  - 05-guidelines.md (640 lines): lift mode + T-3 D-T3 port intro UNIQUE recipe + sed mapping + D-T6 anti-mirror discipline + eval framework EXCLUSION (§1.6) + §3 protected surfaces hash-stable (§1.7) + Spanish voseo exception sales_agent output + sub-builder spawn template + halt criteria
  - 06-tickets.yaml (870 lines): 19 tickets DAG-ordered, ALL owner=builder-agentic Opus per R23

  Cross-module audit per anti-duplication.md cardinal — 14 shared subsystems CONSUMED from luana-platform existing packages (NEVER mirrored). NEW Story 7 layer = sales_agent module proper + D-T3 BrandVoicePort + BrandVoiceService NEW abstractions in luana-core-brand-studio (only Story 7 modification to brand-studio package, pre-ratified ADR-001 §2.4). T-16 RESOLVES Stories 4+6 connections wiring deferral.

  Total estimated tool-time: ~13h Opus sequential. Combined Stories 6+7 ~27h. R23 mandatory. Budget per outcome §7.2 NO HARD CAP, soft check-ins $500/$1000/$1500/$2500 cumulative.

  Next: /dev-team picks T-1 → T-19 sequentially AFTER Story 6 done (blocked_by Story 6).
