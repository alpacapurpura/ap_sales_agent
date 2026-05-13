---
ticket: T-2-bigbang
story: luana-nicolify-migration
date: 2026-05-13
executor: claude-opus-4-7 builder-backend + claude-opus-4-7 /pm orchestrator (verification)
pattern: P1-prepared Phase 3 (atomic big-bang commit)
status: HALT — A1-A5 GREEN, A6 FAIL (+18 NEW failures over R8 cap)
---

# T-2-bigbang Result — Acceptance Grid + Halt Rationale

## Files modified

| Operation | Count |
|---|---|
| Imports rewrite (codemod `--all-modules --apply`) | 1629 modified |
| Class A model deletions (`--delete-aisealsht-models --apply`) | 83 deleted |
| Pre-existing PNG deletions (carried from session start) | 2 deleted |
| **Total tree delta** | **1716 changed** |

Per-module breakdown matches T-2-bigbang-impl-log.md §Step 2 dry-run forecast verbatim.

## Acceptance grid R13 A1-A6

| Predicate | Result | Verdict |
|---|---|---|
| **A1** pytest --collect-only 0 errors | 10183/10195 collected, 0 errors | ✅ GREEN |
| **A2** `grep "from src\."` excluding PRESERVE = 0 | 71 occurrences (all in admin/streamlit + Nicolify-local-not-lifted markers) | ✅ GREEN (per audit §10.3 + Decisión 7 admin defer) |
| **A3** `grep "class X(Base)"` excluding PRESERVE = 0 | 0 | ✅ GREEN |
| **A4** 10 smoke imports luana_core_X | 10/10 OK | ✅ GREEN |
| **A5** Arch fitness 36/36 + ratchet + FieldContract | 1069 passed, 6 skipped (Story 10 placeholders awaiting T-8 FE move) | ✅ GREEN |
| **A6** Full pytest delta ≤ 5 NEW failures in deferred categories | **26 failed (baseline 8, +18 NEW)** — exceeds R8 cap | ❌ FAIL |

**Overall verdict: HALT (R14 H6 triggered — delta > R8 threshold).**

## A6 failure inventory (26 total, 18 NEW vs baseline)

### Eval framework deferred candidates (~7 — could expand Decisión 9)
- `tests/architecture/test_grader_public_api_surface.py::test_no_internal_symbols_leaked_on_grader`
- `tests/scripts/test_promote_golden.py::TestPromoteRefusesCrashedSimulation::test_error_message_mentions_crash_reason`
- `tests/agentic_evals/sales_agent/test_goldens_coverage.py::test_all_cells_covered`
- `tests/agentic_evals/sales_agent/simulator/test_runner_unit.py::test_db_session_propagated_to_agent_bridge_via_contextvar`
- `tests/agentic_evals/sales_agent/grader/test_judge_registry_unit.py::test_litellm_proxy_routing_only`
- `tests/scripts/test_skill_sales_agent_audit.py::test_utility_verdicts_cover_all_skill_sections`
- `tests/scripts/test_skill_sales_agent_audit.py::test_impl_log_has_required_sections`

### Sales_agent chat-flow integration (~5 — Decisión 9 candidates)
- `tests/modules/sales_agent/test_chat_flow_integration.py` (5 tests — test_tool_request_routes_to_tool_executor, test_new_user_routes_to_qualifier, test_state_persists_across_turns, test_qualification_data_extracted, test_buying_signal_increments_score)

### Sales_agent infra (~1)
- `tests/modules/sales_agent/test_output_manager_uses_registry.py::TestOutputManagerArchInvariant::test_imports_get_channel_format`

### NOT eval-deferred — likely codemod test-mocking gaps (~13 — NOT covered by R8 deferred-already-known)
- `tests/modules/copilot/observability/test_atomic_switch.py::TestChatHotPathImportsNewModule::test_imports_observability_context`
- `tests/modules/copilot/api/test_suggestions_endpoint_integration.py::TestSuggestionsIntegration::test_e2e_real_engine_real_offer_provider`
- `tests/modules/copilot/test_route_tool_mapping.py::TestProviderRouteMerging::test_provider_routes_extend_specific_prefix`
- `tests/modules/copilot/test_route_tool_mapping.py::TestProviderRouteMerging::test_provider_routes_extend_wildcard_fallback`
- `tests/modules/analytics/test_campaign_sync_task.py::TestRunCampaignSyncTask::test_credentials_are_flattened_before_pipeline`
- `tests/modules/analytics/test_campaign_sync_task.py::TestRunCampaignSyncTask::test_credentials_include_both_credentials_and_config`
- `tests/modules/analytics/test_seed_metrics.py` (5 tests — staging/official/aggregation/clear/idempotent)
- `tests/modules/offer/test_offer_extraction_service.py::TestOfferExtractionServiceInit::test_imports_webcrawler_from_shared`
- `tests/scripts/test_validate_session_close.py::test_cap_violation_reported_with_count[developed-cap 2]`

## Sample root-cause investigation (1 failure inspected)

`test_route_tool_mapping.py::test_provider_routes_extend_wildcard_fallback`:

```
AssertionError: tool_groups merge already worked pre-fix
assert '_tp10_synth_group' in {'analytics': [...], 'brand': [...], ...}
where {'analytics': ..., 'brand': ...} = <module 'src.modules.copilot.application.tools.registry'>.TOOL_GROUPS
```

Test injects mock provider via legacy `src.modules.X` namespace. Provider discovery
post-codemod operates on `luana_core_X` namespace. Mock no longer discoverable → expected
`_tp10_synth_group` never added → assertion fails.

**Pattern hypothesis (preliminary, needs full categorization):**
- Codemod's `MockPatchStringRewriter` handles `mock.patch("src.X.Y")` string literals
- BUT does NOT handle:
  - Test-side dynamic provider registration referencing `src.modules.X` import path
  - `assert "src.X" in source` style import-path-assertion tests
  - `monkeypatch.setattr` on full module objects loaded via `src.modules.X`
  - `importlib.import_module("src.modules.X")` calls in test setup

This is a **codemod augmentation gap**, not 18 individual trivial fixes.

## Cost Session 7 (estimate)

| Phase | Cost estimate |
|---|---|
| Fase 0 bootstrap | $10 |
| Fase 1 T-1.10 runtime audit (Opus, ~272k tokens, 50 tool uses) | ~$500 |
| Fase 2 codemod augmentation (Sonnet, ~134k tokens, 12 tool uses) | ~$150 |
| Fase 3 big-bang Opus (~104k tokens, 132 tool uses heavy) | ~$2000-2500 |
| Verification by /pm orchestrator (pytest runs + grep) | ~$100 |
| **Total Session 7 (estimate)** | **~$2750-3250** |
| **Cumulative S5+S6+S7** | **~$6100-6600** |

Over $5000 soft cap (R2 — continue + report, not halt). Under $10000 hard cap (R3).

Per R12: T-8/T-10 wave 3+ continuation requires cumulative < $5000. **Skipped.** Story 10
BE migration core work pauses at T-2-bigbang halt awaiting Chris review.

## R13 / R14 audit trail

- R13 predicates: A1-A5 GREEN (5/6) confirms core P1-prepared mechanic worked (Base unified
  + 83 deletes resolved Class A + imports rewritten + arch fitness intact).
- R14 H6 trigger: A6 delta +18 NEW failures > R8 cap of 5 → HALT.
- R9 fix-on-discovery cap (3 trivial fixes): unused — failures not individually trivial.
- R11: T-2-prep Pattern P6 stub remains in place (excluded from codemod).

## Recommended next-session action (Chris ratifies)

### Option A — Codemod augmentation cycle (Sonnet, ~$200-400)

Categorize 18 NEW failures by mechanism:
1. Tests with import-path assertions (`assert "src.modules.X" in ...`) — extend codemod with string-literal rewriter
2. Tests with dynamic mock provider injection — rewrite test setup to use `luana_core_X` paths
3. Tests with monkeypatch on imported modules — rewrite test setup

Re-run codemod, re-run pytest, re-verify A6.

Estimated cost: ~$300-500 (Sonnet codemod + Opus verify pass). Risk: residual ~5-10% chance another category surfaces.

### Option B — Expand Decisión 9 (defer all 18 to Story 14)

Outcome §7.6 Decisión 9 already defers 40 sales_agent failures to Story 14 brand-voice-elevation.
Expand scope to include 18 NEW = 58 total deferred. Document in DEFERRED-FAILURES-STORY-10.md.

Atomic commit accepted as-is. T-8/T-10 proceed in next session with fresh budget.

Estimated cost: ~$50 (Haiku doc update + commit).

### Option C — Hybrid (recommended)

- 7 eval-framework failures + 5 chat_flow + 1 output_manager = 13 → Option B (Story 14 deferred)
- 13 NOT-deferred failures (copilot/analytics/offer/scripts) → Option A targeted codemod augmentation

Estimated cost: ~$200-400 hybrid.

### Option D — Rollback Phase 3 commit

Single `git revert <halt-commit-sha>`. Re-plan Pattern P1-prepared with augmented codemod that anticipates test-side mock infrastructure. ~$50 rollback + re-spawn next session.

## Chris ratification needed

Halt awaiting Chris ratification on Options A/B/C/D before any further work on Story 10.
Recommendation: Option C hybrid balances cost (~$300) with sound coverage.
