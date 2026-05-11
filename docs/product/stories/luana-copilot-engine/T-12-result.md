---
story_id: luana-copilot-engine
ticket: T-12
status: GREEN
completed_at: 2026-05-11
verdict: done
---

# T-12 result — Lift copilot application/services + discovery + extraction_card_flow

## Status: GREEN (lift integrity preserved — 25/27 tests PASS isolated, 2 DAG-deferred)

## Commit
luana-platform main: (pending push)

## Validators satisfied
- V-NF-2 (verbatim lift fidelity — 14 source + 5 tests + conftest minimal)

## Tests run
- 25 PASS isolated
- 2 deferred to downstream (NOT lift integrity failures — process drifts upstream)

## Files lifted (15: 14 source + 5 tests + 1 conftest)
- services/__init__ + 10 service files + handlers/__init__ + handlers/brand_apply_handler
- application/discovery.py
- application/extraction_card_flow.py
- Tests: test_contextual_chunker, test_discovery, test_document_processor, test_limits_resolver, test_offer_psychology_service
- Tests/conftest.py minimal (env-var setup — overwritten T-15)

## Cross-deps deferred per DAG (expected — clear)
- T-13 lifts observability subfolder → unlocks any test that checks llm_call recording
- T-15 lifts full conftest.py → may replace minimal version + add fixtures
- T-16 UNLIFT copilot_provider/ → unlocks `test_discovery::test_picks_up_in_repo_providers` (or discovery refactor for luana-platform paradigm — flagged)

## Drifts flagged for /pm + /architect
1. §1.3 sed missing `patch("src.modules...")` string-literal rule (4th batch — canonicalize urgently)
2. T-15 conftest DAG-defer needs earlier env-var subset (mitigated this batch)
3. `_CONVENTION_PACKAGE = "src.modules"` discovery hardcode — refactor for luana-platform paradigm needed (T-16 or new ticket)
4. `luana_core_platform.PromptLoader` default templates_dir wrong post-Story-2-lift (test_offer_psychology_prompt_resolves_from_copilot_templates depends on it)

## Next
T-13 — observability subfolder D-T6 subclass invariants.
