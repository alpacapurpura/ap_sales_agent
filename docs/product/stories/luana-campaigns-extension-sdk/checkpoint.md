---
story_id: luana-campaigns-extension-sdk
outcome: luana-platform-migration
state: developing
phase: BUILD_BATCH_E
last_artifact: T-13-impl-log.md
last_modified: 2026-05-12
next_action: "Batch D T-9..T-13 DONE (luana-platform commit df722df pushed). T-13 = campaigns api + workers lift (28 files, 446 tests GREEN, zero import leaks). AISALESHT campaigns source V-NF-1 confirmed zero diff. Next = Batch E (T-14..T-18: apps/test-brand smoke pack + final polish)."
ratified_by_chris: true                         # ★ Session 4 ratification 2026-05-12 — Chris delegated `toma tú todas las decisiones` ★
spawned_at: 2026-05-09
spawned_by: /pm
parallel_safe: false
sequence_in_outcome: 8
blocks: [luana-v0-1-0-publish]
blocked_by: []                                  # Story 7 done 2026-05-12 — unblocked
target_state: developed by 2026-05-13           # session 4 autonomous Stories 8+9 secuencial
estimated_complexity: medium-high               # was medium — EP-6..EP-18 signatures-only adds 6-8 tickets per outcome §7.5.2 D1=B
estimated_tickets: 18-22                        # was 10-14 — EP-1..EP-5 critical (10-12) + EP-6..EP-18 signatures (6-8) + stub brand test pack (~3)
surface: backend (campaigns engine lift + extension SDK formalization + apps/test-brand smoke pack)
production_code: false                          # SDK is contract surface + campaigns engine is non-agentic. R23 NOT triggered. Sonnet eligible.
owner_eligibility: [opus, sonnet]
session: 4
session_pre_auth: stories_8_plus_9_sequential_autonomous   # outcome §7.5.2 D7=B (cap §7.4 extended to 3 stories Tier 3)

# ★ Session 4 binding decisions cementadas — architect Story 8 consume §7.5 ★

binding_decisions:
  outcome_section: "§7.5 Session 4 — Story 8 SDK design decisions (ratified 2026-05-12)"

  cross_cutting_policies:                       # outcome §7.5.1
    CC-1: "Signature pattern per-EP natural (data → DataClass, behavior → Callable)"
    CC-2: "Default append + override case-by-case via mode flag"
    CC-3: "Startup-only registration universal"
    CC-4: "Strict raise on duplicate + namespaced obligatorio (brand_slug prefix)"
    CC-5: "Inmutable post-startup (no unregister_*)"

  scope_decisions:                              # outcome §7.5.2
    D1_scope: "Option B — EP-1..EP-5 críticos + EP-6..EP-18 signatures-only"
    D2_discovery: "Option B — Explicit register in FastAPI lifespan"
    D3_brand_context: "Full + extensible frozen dataclass"
    D4_versioning: "Option C — strict alpha minor/patch + flip SemVer Story 9"
    D5_examples: "Option B — Per-vertical concrete examples + vertical-agent-recipe doc"
    D6_stub_brand: "Option A — apps/test-brand/ included Story 8"
    D7_pre_auth_session4: "Option B — Stories 8+9 secuencial autonomous"

  ep_signatures_summary:                        # outcome §7.5.3 — architect Story 8 emits full contracts
    critical_eps: ["EP-1 field_override", "EP-2 offer_preset_pack_register", "EP-3 sales_agent_tool_register", "EP-4 copilot_workflow_register", "EP-5 scheduling_booking_policy_register"]
    backlog_eps: ["EP-6 sidebar_routes_register", "EP-7 extractor_register", "EP-8 channel_adapter_register", "EP-9 metric_register", "EP-10 landing_template_register", "EP-11 campaign_template_register", "EP-12 asset_template_register", "EP-13 sales_agent_guardrail_register", "EP-14 copilot_kb_pack_register", "EP-15 crm_lifecycle_stage_register", "EP-16 iam_signup_handler", "EP-17 tenant_plan_tier_register", "EP-18 onboarding_wizard_steps_register"]

  vertical_agent_recipe:                        # outcome §7.5.4
    decision: "NO EP-19 — pattern doc only"
    doc_deliverable: "docs/extension-points.md section 'Recipe: Build a vertical agent on top of luana-core' (Vitalia treatment-agent as worked example)"

  ep_8_extended_scope:                          # outcome §7.5.3 EP-8 change (was sales_agent only)
    decision: "EP-8 covers sales_agent + copilot + ANY vertical brand agent (treatment_agent, kitchen_agent, etc.)"
    rationale: "Vitalia recipe demands channel adapter usable beyond sales_agent runtime"

  ep_13_extended_scope:                         # outcome §7.5.3 EP-13 change (was pre-send only)
    decision: "EP-13 includes pre-send + pre-receive checks from v0.1.0"
    rationale: "Chris 'pagar precio hoy vs refactor mañana'. Pre-receive useful for PII/off-topic filtering early."

  ep_14_tenant_scope:                           # outcome §7.5.3 EP-14 detail
    decision: "tenant_scope: 'brand' | 'tenant' | 'both'"
    rationale: "Vitalia: brand-scope (medical protocols shared all clínicas) + tenant-scope (clínica internal KB)"

frozen_contracts_from_stories_6_7:
  copilot_registries: ["ToolRegistry", "WorkflowRegistry", "ExtractorRegistry", "ModuleRegistry", "SuggestionRegistry"]
  copilot_golden_snapshot: "tests/architecture/test_copilot_registry_contracts_stable.py (V-AG-3 Story 6)"
  sales_agent_registry: ["ToolRegistry"]
  rule: "EP-3/EP-4/EP-5 wrap these registries WITHOUT refactoring. Byte-stable contract."

allowlisted_stubs_for_story_8:                 # Story 7 audit-fix 147c61d carry-over
  - "AppointmentModel stub (scheduling territory)"
  - "ProductModel stub (catalog territory)"
  note: "Story 8 cements removal when scheduling/catalog surfaces lift OR allowlists with explicit reason post-Story-8"

halt_criteria_session_4:
  - "Scope expansion needed beyond lift+SDK (campaigns module refactor needed)"
  - "EP signature decision surfaces durante build NOT covered by outcome §7.5"
  - "Auditor REJECTED + 3 auto-fix Opus iter all fail"
  - "Cumulative session 4 cost crosses $2500 → soft check-in"
  - "Builder cap_reached 10 iter on same ticket"
  - "AISALESHT touched by accident (V-NF-4 invariant violated)"
  - "Stories 6+7 frozen registries breakage detected (EP wrappers no preserve contract byte-stable)"
---

## Bitácora

- 2026-05-09: spawned by /pm, state=parked (blocked_by Story 7)
- 2026-05-12: Story 7 done — Story 8 unblocked
- 2026-05-12: Session 4 Phase 0 — Chris ratified scope=B (EP-1..5 + EP-6..18 signatures-only). Chris delegated remaining 6 decisions + 13 backlog EP signatures + 5 CC policies to /pm. Decisions cementadas en outcome §7.5. State parked → refining. Next: spawn /po Opus for 01-spec.md draft.
- 2026-05-12: /po Opus drafted 01-spec.md (1047 lines, 22 Gherkin scenarios, 14 explicit out-of-scope, 5 open Qs for architect, 3 exception types, BrandContext frozen 9-field per §7.5.2 D3). Per §7.5.2 D7=B Chris pre-auth secuencial autonomous, state refining → refined. Next: spawn architect-orchestrator Opus for ready package.
- 2026-05-12: architect-orchestrator Opus emitted ready package — 03-arch.md (325 lines) + 03-arch-be.md (1387 lines) + 04-validators.yaml (26 validators: 5 V-NF + 12 V-F + 6 V-AG + 3 V-D) + 05-guidelines.md (858 lines) + 06-tickets.yaml (18 tickets DAG-ordered, T-5+T-6 Opus required for Stories 6+7 frozen registries wrappers, T-1..T-4 + T-7..T-18 Sonnet eligible). 5 open Qs resolved architect-bounded (26 Python + 7 TS workspace members post-Story-8, scheduling NOT lifted Story 8, EP-3/EP-4 read-only adapter graceful NotImplementedError, BrandContext.feature_flags opaque dict, TS hand-maintained alpha). State refined → ready. Next: /dev-team autonomous build.
- 2026-05-12: builder-backend Sonnet Batch A T-1..T-4 DONE. luana-platform commits ae8cb96..ee0b15a pushed. Files: workspace pyproject.toml (T-1) + SDK skeleton (T-2) + BrandContext 9-field frozen (T-3 TDD 4 tests GREEN) + exceptions+18models+protocols (T-4 TDD 14 tests GREEN). All uv run pytest tests/unit/ PASS. Ruff lint 0 errors. AISALESHT impl-logs T-1..T-4 written. State developing, phase BUILD_BATCH_A → BUILD_BATCH_B.
- 2026-05-12: builder-agentic Opus Batch B T-5+T-6 DONE. luana-platform commits 5ece4cf + 2e20def pushed. T-5 = ExtensionPointRegistry executable EP-1..EP-5 + CC-1..CC-5 runtime enforcement (TDD 33 tests, 31/33 GREEN — 2 adapter graceful tests RED awaiting T-6). T-6 = `_adapters.py` read-only Stories 6+7 frozen registry wrappers (TDD 9 tests GREEN; AST parse no private surface; NotImplementedError graceful when public method absent — current Story 6+7 state). Full SDK test suite: 60/60 PASS post Batch B. Stories 6+7 V-AG-3 byte-stable golden snapshots: 15/15 PASS (test_copilot_registry_contracts_stable + test_story{6,7}_brand_agnostic_engine + test_story{6,7}_no_forward_module_imports). Ruff check + format clean. AISALESHT impl-logs T-5+T-6 written. State developing, phase BUILD_BATCH_B → BUILD_BATCH_C.
- 2026-05-12: builder-backend Sonnet Batch C T-7+T-8 DONE. luana-platform commits 665331a + fbdc39c pushed. T-7 = 32 unit tests EP-6..EP-18 (test_ep6_through_ep18_signature_only.py) — 13 register_succeeds + 13 dispatch_raises_not_implemented + 6 CC cross-cutting; full suite 92/92 PASS. Key: all EP-6..EP-18 methods already present from T-5 Opus — T-7 test-file only. T-8 = core/@luana/extension-sdk TS type mirror (package.json v0.0.8-alpha + tsconfig.json + README + src/brand-context.ts + src/models.ts + src/index.ts); pnpm workspace registered; tsc --noEmit 0 errors. Validators addressed: V-NF-2, V-NF-5, V-F-ts-1, V-F-sdk-1, V-F-sdk-3, V-F-sdk-4 (CC-2/CC-3/CC-4), V-D-1. AISALESHT impl-logs T-7+T-8 written. State developing, phase BUILD_BATCH_C → BUILD_BATCH_D.
- 2026-05-12: builder-backend Sonnet Batch D T-9..T-13 DONE. luana-platform commits ea48804+8a422fd+1427017+9e3da61 (T-9..T-12 prev spawn) + df722df (T-13 this spawn) pushed. T-13 = campaigns api+workers layer lift — 8 src files (api/: __init__ + _async_session + _dependencies + _service_factories + routers×3 + workers/: __init__ + execution_task + scheduler_tick + segment_refresh_tick + audit_retention_task) + 28 total committed files (integration+workers+api tests). Full suite: 446 passed / 0 failed (33 test files). Key fixes: (1) `from src.main import app` → _make_campaigns_test_app() singleton factory (tests/api/_test_helpers.py); (2) test_campaigns_stats_endpoint.py router path updated parents[4]→parents[2] for luana-platform layout. V-NF-1: AISALESHT campaigns zero diff confirmed. Downstream sanity: luana-core-platform + luana-core-events GREEN. AISALESHT impl-log T-13 written. State developing, phase BUILD_BATCH_D → BUILD_BATCH_E.
