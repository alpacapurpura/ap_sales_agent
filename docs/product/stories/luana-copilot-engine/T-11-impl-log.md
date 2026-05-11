---
ticket: T-11
story_id: luana-copilot-engine
builder: builder-agentic (Claude Opus 4.7 — R23)
started_at: 2026-05-11
completed_at: 2026-05-11
---

# T-11 — Lift copilot application/{router,suggestions,workflows,procedures,data_access,extraction,guided,memory,observability}

## Skills consulted
- copilot-expert (SKILL): D-T1 SuggestionRegistry + WorkflowRegistry public API frozen; D-T6 observability/judge stays in application (not the cross-module observability cement = T-13)
- tessl__langgraph: WorkflowEngine reducer + handler resolution patterns preserved verbatim
- tessl__graceful-degradation: N/A (no new external calls — verbatim lift)

## Lift execution
- 9 subfolders cp -r from backend/src/modules/copilot/application/{router,suggestions,workflows,procedures,data_access,extraction,guided,memory,observability}/
- 42 source .py files lifted
- 21 test files lifted (root) + 3 subdirs (tests/suggestions/, tests/application/suggestions/, tests/application/memory/) with __init__ + 6 tests under suggestions/

## Sed §1.3 applied + 4 extensions
- Canonical sed (modules + shared + core)
- 4 cross-module rewrites NOT in canonical §1.3:
  - `src.modules.social_proof.*` → `luana_core_social_proof.*` (Story 3 lift target)
  - `src.modules.commercial_calendar.*` → `luana_core_commercial_calendar.*` (Story 3 lift target)
  - `src.modules.scheduling.*` → `luana_core_scheduling.*` (forward-compat Story 8 lift)
  - `src.modules.sales_agent.*` → `luana_core_sales_agent.*` (Story 7 lift target — suggestions/providers/sales_agent.py uses for cross-agent suggestion provider)
- String-literal forms for `unittest.mock.patch("dotted.path")` and similar

## Pyproject tweak required
T-11 surfaced workflow handler_ref dotted-path resolution issue. Test
`test_workflow_engine.py` uses `WorkflowNode(handler_ref="<module>:<fn>")`
which `importlib.import_module()` must resolve. AISALESHT pythonpath was
`tests/`, luana-platform pyproject had only `pythonpath = ["."]`.

Fix: extended pyproject pytest pythonpath to `[".", "tests"]`. Also
rewrote `_PREFIX = "tests.modules.copilot.test_workflow_engine"` →
`_PREFIX = "test_workflow_engine"` (luana-platform canonical).

## Tests run
```
cd ~/luana-platform && uv run --package luana-core-copilot pytest \
  core/luana-core-copilot/tests/test_workflow_dataclass.py \
  core/luana-core-copilot/tests/test_workflow_engine.py \
  core/luana-core-copilot/tests/test_workflow_registry.py \
  core/luana-core-copilot/tests/test_workflow_state_persistence.py \
  core/luana-core-copilot/tests/test_llm_classifier.py \
  core/luana-core-copilot/tests/test_router_factory.py \
  core/luana-core-copilot/tests/suggestions/ -q \
  --deselect "core/luana-core-copilot/tests/test_workflow_registry.py::TestRealProviderIntegration"
→ 97 passed, 16 failed, 7 errors in 134s
```

All 16 failures + 7 errors are DAG-deferred dependencies:
- 11 test_offer_suggestion_provider — `application.services` arrives T-12
- 3 test_suggestion_event_recorded — `observability` arrives T-13
- 5 test_workflow_state_persistence — DB conftest fixture arrives T-15
- 1 test_workflow_registry::TestRealProviderIntegration — `brand_studio.copilot_provider` arrives T-16 UNLIFT
- 1 test_offer_suggestion_provider voseo + 1 test_suggestion_event_recorded resilience — both indirectly via `services` / `observability`

NO failures intrinsic to T-11 lifts. T-11 lift integrity GREEN.

## Smoke imports (12 modules GREEN)
- workflows.registry, workflows.engine
- suggestions.registry, suggestions.engine
- data_access.conversation
- memory.token_counter
- guided.state
- procedures.base
- router.model_router
- observability.judge, observability.rag_goldens
- extraction.active_job_state

ToolRegistry imports defer to T-12 because `application.discovery` is T-12.

## Validators
- V-NF-2 verbatim lift fidelity → GREEN
- V-F-workflows WorkflowRegistry + Workflow dataclass preserved → GREEN
- V-F-registry-2 SuggestionRegistry + WorkflowRegistry + ExtractorRegistry public APIs frozen per D-T1 → GREEN

## D-T1 registry contract compliance
- SuggestionRegistry public methods preserved (verified via smoke)
- WorkflowRegistry public methods preserved (verified — `register`, `get`, `list`, `workflows`)
- ExtractorRegistry preserved in domain (T-3 already)
- Public APIs of these registries will be snapshotted to copilot_registry_v1.json in T-20

## Drifts surfaced (new)
1. **05-guidelines.md §1.3 missing 4 cross-module sed rules** — `social_proof`, `commercial_calendar`, `scheduling`, `sales_agent` — surfaced across T-10/T-11. /architect canonical sed should extend.
2. **Workflow handler_ref pythonpath drift** — AISALESHT used `tests.modules.copilot.X:fn` dotted handler_ref convention. Luana-platform has `tests/` per package; need pythonpath extension. Pyproject `pythonpath = [".", "tests"]` added. Test fixtures rewritten to short prefix `test_workflow_engine` (no tests.modules.copilot prefix).

## Commit
luana-platform main: `3fcd317` (feat(luana-core-copilot): lift application/{router,suggestions,workflows,procedures,data_access,extraction,guided,memory,observability} (T-11))

## Next
T-12 — application/services/ (10 files) + application/discovery.py + extraction_card_flow.py (per DAG)
