---
story_id: luana-copilot-engine
ticket: T-11
status: GREEN
completed_at: 2026-05-11
verdict: done
---

# T-11 result — Lift copilot application/{router, suggestions, workflows, procedures, data_access, extraction, guided, memory, observability}

## Status: GREEN

## Commit
luana-platform main: `3fcd317` (feat(luana-core-copilot): lift application/9-subfolders (T-11))

## Validators satisfied
- V-NF-2 (verbatim lift fidelity — 42 source + 21 root tests + 3 subdir tests)
- V-F-workflows (Workflow + WorkflowNode dataclasses + WorkflowEngine.step + WorkflowRegistry preserved)
- V-F-registry-2 (SuggestionRegistry + WorkflowRegistry + ExtractorRegistry public APIs frozen per D-T1 cardinal)

## Tests run
- 97 PASS isolated
- 23 expected failures all DAG-deferred (T-12 services / T-13 observability / T-15 conftest / T-16 brand_studio unlift)
- NO failures intrinsic to T-11 lift integrity

## Files lifted (~70 total: 42 source + 28 tests/subdirs)
9 application subfolders + 28 tests across root + 3 subdir __init__s

## D-T1 registry compliance
- ToolRegistry (T-10) + WorkflowRegistry + SuggestionRegistry + ExtractorRegistry public APIs preserved verbatim
- Future T-20 will snapshot to `_snapshots/copilot_registry_v1.json` for arch fitness V-AG-3

## Smoke verification (12 modules GREEN)
workflows.registry/engine + suggestions.registry/engine + data_access.conversation + memory.token_counter + guided.state + procedures.base + router.model_router + observability.judge/rag_goldens + extraction.active_job_state.

## Process drifts documented for /pm + auditor (consolidated from Batch 3)
1. **05-guidelines.md §1.3 missing 4 cross-module sed rules** — `social_proof`, `commercial_calendar`, `scheduling`, `sales_agent`. Tools (T-10) + suggestions providers (T-11) reference these. /architect canonical sed should extend before Story 7.
2. **Workflow handler_ref pythonpath drift** — AISALESHT `tests.modules.copilot.*` prefix incompatible with luana-platform per-package `tests/`. Mitigated: pyproject pythonpath extended `[".", "tests"]` + prefix shortened.
3. **05-guidelines.md §1.3 string-literal sed gap reconfirmed (third batch)** — `unittest.mock.patch("dotted.path")` consistently requires manual extension. Pattern now established across T-7/T-8/T-9/T-10/T-11. /architect should canonicalize.

## Batch 3 (T-9 + T-10 + T-11) summary
- T-9 (8602ae0): 18 source + 12 tests — orchestrator LangGraph harness + 11-slot prompt cache composer + 3 subagents. 52 PASS isolated.
- T-10 (c0040be): 42 source + 14 tests — ToolRegistry SSoT + 24 tools + 3 subfolders. 40 PASS isolated.
- T-11 (3fcd317): 42 source + 21 root tests + 6 subdir tests — router + suggestions + workflows + procedures + data_access + extraction + guided + memory + observability. 97 PASS isolated.

Total Batch 3: 102 source .py files + 47 tests, 189 cumulative test PASS isolated.

Total cumulative across batches: ~244 source files + ~78 tests + 300 PASS isolated across 6 tickets (T-3, T-6, T-7, T-8 — Batches 1+2 — and T-9, T-10, T-11 — Batch 3). Plus T-1+T-2 (workspace+skeleton, no test counts).

## Cross-deps deferred per DAG (expected failures clear)
- T-12 lifts `application.services` + `discovery` → unlocks ToolRegistry full smoke + 11 test_offer_suggestion_provider tests
- T-13 lifts `observability` module-level subfolder → unlocks 3 test_suggestion_event_recorded tests
- T-15 lifts conftest.py + remaining tests → unlocks 5 test_workflow_state_persistence tests
- T-16 UNLIFT lifts `brand_studio.copilot_provider` → unlocks 1 test_workflow_registry::TestRealProviderIntegration test

## Next
T-12 — application/services/ (10 files: brand_ai_actions, offer_psychology, mutation_apply, telegram_link, document_processor, contextual_chunker, limits_resolver, event_cleanup, offer_suggestion_reader, handlers/) + application/discovery.py + extraction_card_flow.py
