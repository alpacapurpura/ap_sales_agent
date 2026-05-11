---
ticket: T-10
story_id: luana-copilot-engine
builder: builder-agentic (Claude Opus 4.7 — R23)
started_at: 2026-05-11
completed_at: 2026-05-11
---

# T-10 — Lift copilot application/tools/

## Skills consulted
- copilot-expert (SKILL): D-T1 ToolRegistry public API frozen — `register`, `get`, `list`, `groups` + Tool dataclass field set preserved
- tessl__langgraph: tools decoupled from StateGraph compilation — DAG dependency on data_access flows from registry, not from graph build path

## Lift execution
- `cp -r backend/src/modules/copilot/application/tools/ → core/luana-core-copilot/src/luana_core_copilot/application/tools/`
- 42 source .py files (registry + 24 tool files + ask_tenant_data/ 7 + guided/ 4 + shared_tools/ 2 + _analytics_inputs.py + __init__)
- 14 tool tests (6 in tests root + 8 in tests/application/tools/)

## Sed §1.3 applied + extensions
- Canonical sed (modules + shared + core)
- **3 cross-module rewrites NOT in canonical §1.3:**
  - `src.modules.social_proof.*` → `luana_core_social_proof.*` (Story 3 lift target)
  - `src.modules.commercial_calendar.*` → `luana_core_commercial_calendar.*` (Story 3 lift target)
  - `src.modules.scheduling.*` → `luana_core_scheduling.*` (forward-compat Story 8 lift; package doesn't exist yet, deferred import inside function body — works at runtime once Story 8 lands)
- String-literal sed for `unittest.mock.patch("src.modules.*")` paths in tests

## Tests run
```
cd ~/luana-platform && uv run --package luana-core-copilot pytest \
    core/luana-core-copilot/tests/test_url_inspiration_analyzer.py \
    core/luana-core-copilot/tests/test_offer_ladder_tools.py \
    core/luana-core-copilot/tests/application/tools/test_analytics_tools_observability.py -x -q
→ 40 passed in 134.66s
```

Standalone tool imports smoke (5/5 GREEN):
- fetch_url, pin_to_memory, navigation, knowledge_search, awareness

## Validators
- V-NF-2 verbatim lift fidelity → GREEN
- V-F-tools 24 tools preserved → GREEN
- V-F-registry-1 ToolRegistry public API frozen (D-T1 cardinal) → GREEN
  - `register`, `get`, `list`, `groups` methods present
  - `ALWAYS_AVAILABLE_GROUPS` constant preserved
  - Tool dataclass field set verbatim

## D-T1 cardinal compliance
- ToolRegistry public methods present per spec
- Smoke verification deferred to T-11 due to registry → data_access dependency:
  `registry.py:21 → from luana_core_copilot.application.tools.ask_tenant_data import ask_tenant_data`
  `ask_tenant_data/tool.py:21 → from luana_core_copilot.application.data_access import ...`
  data_access arrives T-11 per DAG.

## Drifts surfaced
1. **05-guidelines.md §1.3 missing 3 cross-module sed rules** — `social_proof`, `commercial_calendar`, `scheduling`. Tools layer references modules beyond Stories 2-5 inventory in §1.3. Mitigated by manual extension.
2. **ticket smoke template assumes registry direct-import success** — but registry imports data_access transitively. Smoke deferred to T-11 follow-up.

## Commit
luana-platform main: `c0040be` (feat(luana-core-copilot): lift application/tools (T-10))

## Next
T-11 — application/{router, suggestions, workflows, procedures, data_access, extraction, guided, memory, observability} (~30 files)
