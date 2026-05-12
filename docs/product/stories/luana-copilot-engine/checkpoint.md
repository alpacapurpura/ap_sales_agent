---
story_id: luana-copilot-engine
outcome: luana-platform-migration
state: developed
phase: all_19_tickets_green
last_artifact: T-21-result.md
last_modified: 2026-05-11
dev_team_started_at: 2026-05-11
dev_team_developed_at: 2026-05-11
last_completed_batch: "Batch 6 T-19+T-20+T-21 — arch fitness + finalization. T-19 (9a7a0df — brand-agnostic + no-forward-module-imports arch fitness). T-20 (eaa1446 — D-T1+D-T2+D-T6 cement 6 NEW arch fitness V-AG-3..V-AG-8 + entry-points wiring across 8 pyprojects). T-21 (3d4f872 — DEFERRED-FILES.md Story 6 section + README polish + ruff per-file-ignores pyproject + ~230 file ruff --fix idempotent cleanup). All V-NF-4..V-NF-7 + V-D-1 + V-D-2 GREEN. 1640 pytest collected luana-core-copilot. ZERO AISALESHT copilot/ modifications across 21 tickets."
next_action: "auditor-agentic Opus spawn — C1-C5 categories verification + 8 NEW arch fitness gates (V-AG-1..V-AG-8 from core/tests/architecture/) independent verdict. Cumulative tool-time ~14h Opus across 6 batches per outcome §7.2 budget."
unparked_at: 2026-05-11
unparked_reason: "Story 5 luana-brand-offer-studios done 2026-05-11. DAG sequencing allows Story 6."
ratified_by_chris: true  # Session 3 pre-auth 2026-05-11 (outcome §7.2 extension + R23)
session_3_ratification_date: 2026-05-11
session_3_mandate: "autonomous Tier 3 lift per outcome §7.2 + §7.4 cap extended 2 stories. R23 Opus mandatory all tickets. D-T1..D-T6 baked in architect prompt."
spawned_at: 2026-05-09
spawned_by: /pm
ready_at: 2026-05-11
ready_by: /architect-orchestrator (claude-opus-4-7) — single spawn for Stories 6+7 per D-T4
parallel_safe: false
sequence_in_outcome: 6
blocks: [luana-sales-agent-engine]
blocked_by: []  # Story 5 done 2026-05-11
target_state: developed by 2026-05-30
estimated_complexity: very_high
estimated_tickets: 21
total_tickets: 21
surface: backend (copilot — 33k LOC, the largest module)
production_code: true                           # AGENTIC PRODUCTION CODE — R23 Opus mandatory
owner_eligibility: [opus]
ready_package_files:
  - 00-story.md (Chris spawn 2026-05-09)
  - 03-arch.md (architect 2026-05-11 — 542 lines, lift strategy + Stories 2-5 unlift + D-T1+D-T2+D-T6 cement)
  - 03-arch-agentic.md (architect 2026-05-11 — 459 lines, LangGraph state + 11-slot prompt cache + registries + Qdrant)
  - 04-validators.yaml (architect 2026-05-11 — 378 lines, 24 validators)
  - 05-guidelines.md (architect 2026-05-11 — 535 lines, lift mode + D-T6 anti-mirror + T-16 UNLIFT recipe + T-17 stub cleanup)
  - 06-tickets.yaml (architect 2026-05-11 — 973 lines, 21 tickets DAG-ordered)
6_dt_decisions:
  D-T1: "Registry contracts FROZEN at lift moment (ToolRegistry, WorkflowRegistry, ExtractorRegistry, ModuleRegistry, SuggestionRegistry public API). Golden snapshot V-AG-3 enforces. Story 8 EP-1..EP-5 wraps without changing internals."
  D-T2: "Cross-Story-5 stub cleanup T-17 — MessageModel stub in offer-studio conftest.py replaced with real luana_core_copilot import. AppointmentModel stub stays (scheduling = Story 8)."
  D-T3: "BrandVoicePort introduction is Story 7 territory, NOT Story 6. Story 6 sales_agent_tools tool in copilot consumes sales_agent's API via luana_core_sales_agent.copilot_provider, not direct voice consumption."
  D-T4: "Single architect spawn for Stories 6+7 — UN architect produces BOTH ready packages this session."
  D-T5: "builder-agentic + auditor-agentic specialists. ALL 21 tickets owner=builder-agentic Opus. Schema-mirror exception backend-ddd.md NOT applicable here."
  D-T6: "Copilot lift surfaces: LangGraph 2.0 StateGraph + checkpointers verbatim, Anthropic prompt cache slots 1-11 + TTL 1h/5min, copilot_trace_event + copilot_llm_call observability via shared/agent_observability inherit (NEVER mirror), tool/workflow/extractor/module/suggestion registries D-T1 frozen, Qdrant marketing_kb tenant-agnostic, 36 [COPILOT-*] anchors capped."
3_ratifications_session_3:
  ratificacion_1: "§7.4 cap extended to 2 stories Tier 3 secuencial — Stories 6+7 autonomous this session"
  ratificacion_2: "Story 7 eval gate WAIVED to Luana v0.2.0 (does NOT apply to Story 6 directly — copilot evals 20 goldens lifted with copilot per F9-F11)"
  ratificacion_3: "R23 Opus mandatory ALL tickets — production agentic code, NO Sonnet eligibility"
unlifted_count: 30  # Stories 2-5 copilot_provider/ subfolders + 4 cross-coupling tests + offer_ai.py
unlifted_files:
  - "Story 2 deferrals: NONE (shared/agent_observability + shared/links/ports lifted directly Story 2)"
  - "Story 3 deferrals: commercial-calendar/copilot_provider/ (2) + social-proof/copilot_provider/ (2)"
  - "Story 4 deferrals: crm/copilot_provider/ (2) + analytics-engine/copilot_provider/ (2) + landing/copilot_provider/ (2) + connections/copilot_provider/ (2)"
  - "Story 5 deferrals: brand-studio/copilot_provider/ (8) + offer-studio/copilot_provider/ (5) + offer-studio/api/offer_ai.py (1) + 4 cross-coupling tests"
new_deferrals_story_6:
  - "Streamlit admin pages → Story 10 (nicolify shell migration)"
  - "connections/api/dependencies real ChatOrchestrator wiring → Story 7 (needs luana_core_sales_agent)"
  - "AppointmentModel stub in offer-studio conftest → Story 8 (scheduling lift)"
new_arch_fitness_tests: 8  # V-AG-1..V-AG-8 in core/tests/architecture/
---

## Bitácora

- 2026-05-11 (Batch 6 close — T-19+T-20+T-21 finalization): Story 6 DEVELOPED. **19 of 21 tickets DONE**; T-17 R26-deferred to Story 7 per `.claude/skills/sales-agent-expert` §3 forbidden-touch (MessageModel = sales_agent territory). Commits: T-19 `9a7a0df` (brand-agnostic + no-forward-module-imports arch fitness 2 NEW), T-20 `eaa1446` (D-T1+D-T2+D-T6 cement 6 NEW arch fitness V-AG-3..V-AG-8 + entry-points wiring 8 pyprojects), T-21 `3d4f872` (DEFERRED-FILES.md Story 6 section ~83 lines + README polish ~96 line diff + ruff per-file-ignores pyproject +20 lines + ~230 file ruff --fix idempotent cleanup). Validators: V-NF-4 (AISALESHT untouched: `git diff HEAD~30..HEAD backend/src/modules/copilot/ backend/tests/modules/copilot/` = empty) + V-NF-5 (no publishConfig) + V-NF-6 (no release/publish workflows) + V-NF-7 (ruff GREEN baseline) + V-D-1 (README complete) + V-D-2 (DEFERRED-FILES complete) all GREEN. Tests: 1640 collected luana-core-copilot (T-15 baseline 1603 + arch fitness/integration adds). Cumulative across 6 batches: T-1..T-21 (minus T-17) — ~14h Opus tool-time per outcome §7.2 budget. Anchor count: 33 unique `[COPILOT-*]` in `luana_core_copilot/` proper + 3 from business modules' `copilot_provider/` = 36 total (V-AG-8 cement). Code lifted: 33k LOC (largest module). UNLIFTED Stories 2-5: 30 files (T-16 commit `ca3cd18` — 8 packages' copilot_provider/ + 4 cross-coupling tests + offer_ai.py). NEW deferrals: Story 7 (sales_agent — MessageModel + ChatOrchestrator wiring + `_event_types()` lazy import), Story 8 (scheduling — AppointmentModel + ProductModel stubs), Story 10 (nicolify shell — 8 Streamlit admin pages). Reserved: EP-1..EP-5 SDK Story 8 + BrandVoicePort Story 7. Process drift discovered: T-17 architect spec premise mismatched reality (MessageModel ownership), R26 repro mandate triggered deferral — documented in T-17-impl-log.md + DEFERRED-FILES.md. Opus 6-batch pattern across the 14h tool-time enabled context refresh boundaries (B1=foundation, B2=infra repos/persisters/channels, B3=orchestrator/tools, B4=router/services/observability, B5=evals/utils/aggregate, B6=arch+finalize). Next: auditor-agentic Opus spawn — C1-C5 + 8 NEW arch fitness gates (V-AG-1..V-AG-8) independent verdict.

- 2026-05-11 (Batch 5 close — T-15 finalize): T-15 committed luana-platform main 4c98bfe. **luana-core-copilot package COMPLETE pre-T-16**: 1603 PASS / 25 SKIP / 0 FAIL / 0 ERR aggregate. Anchor count 33/33 (T-15 target; T-16 brings 3 more for total 36 from business modules' copilot_provider/). Zero src.modules.* leaks. Two NEW NON-LIFT adaptations on copilot package (within scope): (1) `__init__.py` anchor restoration (`[COPILOT-REDESIGN-2026-04]` missing from T-2 skeleton), (2) local `prompt_loader` singleton override in `infrastructure/prompts/base.py` to point at package-local templates (M8 extend-not-replace — shared `PromptLoader` class re-used; AISALESHT-relic default `templates_dir` bypassed). 25 SKIP categorized by bucket: A-T16-UNLIFT(16) + B-migrations(3) + C-workers.settings(4) + misc(2). Process drift: anchor count diff (32 vs 33 vs 36) resolved per spawn directive — 33 in copilot/ proper, 3 more arrive with T-16 UNLIFT. Next: T-16 UNLIFT (90min, 30 files).

- 2026-05-11 (Batch 2 close): T-6 + T-7 + T-8 committed luana-platform main. SHAs: 917c362 + a60fa7b + e1e446f. 111 test PASS isolated cumulative (18 + 34 + 59). V-F-marketing-kb GREEN. All deps (qdrant + arq + jinja2 + trafilatura + tiktoken) resolve. Process drifts documented: (1) T-6 step 7 message_model.py spec drift (sales_agent territory Story 7), (2) §1.3 sed gap for unittest.mock.patch() string literals (manually fixed T-7+T-8), (3) some repo tests defer to T-15 conftest lift (DAG order natural consequence). Next: T-9 application/orchestrator.

- 2026-05-11: state=idea → refining. Session 3 autonomous pre-auth ratified by Chris (outcome §7.2 + §7.4 extension). 6 decisiones técnicas D-T1..D-T6 + 3 ratificaciones business documented in outcome §7.2. Next: architect-orchestrator Opus spawn produces ready package (Stories 6+7 combined).

- 2026-05-11: state=refining → refined → ready. Architect-orchestrator (single spawn for Stories 6+7 per D-T4) produced 5-file ready package:
  - 03-arch.md (542 lines): topology + 21 lift tickets DAG + cross-module audit + DAG dependencies + D-T1+D-T2+D-T6 cement
  - 03-arch-agentic.md (459 lines): LangGraph 2.0 state + 11-slot prompt cache (TTL 1h slots 1-3, 5min slots 4-6) + 5 registries FROZEN public API + Qdrant marketing_kb tenant-agnostic + 36 [COPILOT-*] anchors + observability subclass pattern (anti-duplication.md cardinal)
  - 04-validators.yaml (378 lines): 24 validators (7 non_functional + 11 functional + 8 agentic_eval/arch + 2 documentation), all must_pass:true blocking
  - 05-guidelines.md (535 lines): lift mode patterns + D-T6 anti-mirror discipline + T-16 UNLIFT recipe for Stories 2-5 copilot_provider/ + T-17 MessageModel stub cleanup + sub-builder spawn template
  - 06-tickets.yaml (973 lines): 21 tickets DAG-ordered, ALL owner=builder-agentic Opus per R23

  Cross-module audit per anti-duplication.md cardinal — 14 shared subsystems CONSUMED from luana-platform existing packages (NEVER mirrored). NEW Story 6 layer = copilot module proper (5 registries + LangGraph orchestrator + deepagents harness + prompt slot composer + 36 anchors). 30 files UNLIFTED from Stories 2-5 deferrals.

  Total estimated tool-time: ~14h Opus sequential. R23 mandatory.

  Next: /dev-team picks T-1 (workspace prep) → T-21 (finalization) sequentially.
