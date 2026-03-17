---
phase: quick
plan: 260317-naa
subsystem: llm, graphs
tags: [langgraph, langchain, langchain-openai, langchain-google-genai, migration]

requires:
  - phase: none
    provides: n/a
provides:
  - "All langgraph graphs use START node pattern (langgraph 1.x API)"
  - "LLM providers use current constructor params (api_key instead of deprecated aliases)"
  - "Backend compatible with langgraph 1.1.2, langchain 1.2.12, langchain-openai 1.1.11, langchain-google-genai 4.2.1"
affects: [sales_agent, copilot, shared]

tech-stack:
  added: []
  patterns: ["langgraph 1.x: add_edge(START, node) replaces set_entry_point(node)"]

key-files:
  created: []
  modified:
    - backend/src/modules/sales_agent/application/agents/sales/graph.py
    - backend/src/modules/sales_agent/application/orchestrator/graph.py
    - backend/src/modules/copilot/application/agents/style_analyzer/graph.py
    - backend/src/modules/copilot/application/agents/web_extractor/graph.py
    - backend/src/modules/copilot/application/orchestrator/graph.py
    - backend/src/shared/infrastructure/llm/providers/gemini.py
    - backend/src/shared/infrastructure/llm/providers/openai.py

key-decisions:
  - "convert_system_message_to_human removed from Gemini (deprecated in langchain-google-genai 2.x+, Gemini handles system messages natively)"
  - "api_key is the canonical constructor param in langchain 1.x (replaces openai_api_key and google_api_key)"
  - "model_name attribute still works in langchain-openai 1.1.11 (no change needed in tracing code)"

patterns-established:
  - "langgraph 1.x graph pattern: import START from langgraph.graph, use add_edge(START, entry_node)"

requirements-completed: []

duration: 4min
completed: 2026-03-17
---

# Quick Task 260317-naa: Fix Breaking Changes from LangChain and LangGraph Migration

**Migrated 5 langgraph graphs to START node pattern and updated 2 LLM providers to use current langchain 1.x constructor params**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-17T21:53:16Z
- **Completed:** 2026-03-17T21:57:00Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments
- All 5 langgraph graph files migrated from deprecated `set_entry_point()` to `add_edge(START, node)` pattern
- Gemini and OpenAI LLM providers updated with current constructor parameter names
- Removed deprecated `convert_system_message_to_human` from Gemini provider
- 278 tests pass, 0 failures, ruff lint clean

## Task Commits

Each task was committed atomically:

1. **Task 1: Migrate langgraph graphs from set_entry_point to START node pattern** - `bbbf109` (fix)
2. **Task 2: Update langchain LLM provider constructor parameters** - `9d811ed` (fix)
3. **Task 3: Verify full backend startup and run existing tests** - verification only, no code changes

## Files Created/Modified
- `backend/src/modules/sales_agent/application/agents/sales/graph.py` - Sales subgraph: START import + add_edge(START, "supervisor")
- `backend/src/modules/sales_agent/application/orchestrator/graph.py` - Main orchestrator: START import + add_edge(START, "supervisor")
- `backend/src/modules/copilot/application/agents/style_analyzer/graph.py` - Onboarding graph: START import + add_edge(START, "janitor")
- `backend/src/modules/copilot/application/agents/web_extractor/graph.py` - Web extractor graph: START import + add_edge(START, "extract")
- `backend/src/modules/copilot/application/orchestrator/graph.py` - Copilot orchestrator: START import + add_edge(START, "router")
- `backend/src/shared/infrastructure/llm/providers/gemini.py` - google_api_key -> api_key, removed convert_system_message_to_human
- `backend/src/shared/infrastructure/llm/providers/openai.py` - openai_api_key -> api_key in ChatOpenAI and OpenAIEmbeddings

## Decisions Made
- `convert_system_message_to_human` removed from Gemini provider (deprecated in langchain-google-genai 2.x+, Gemini models handle system messages natively now)
- `api_key` is the canonical constructor parameter in langchain 1.x (old aliases `openai_api_key` and `google_api_key` are deprecated)
- `model_name` attribute on ChatOpenAI still works in 1.1.11, no change needed for tracing code
- `image_analysis.py` already uses `api_key=` -- no change needed

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Container packages not upgraded to match requirements-runtime.txt**
- **Found during:** Task 1 (langgraph START import failed)
- **Issue:** Container still had langgraph 0.0.24, langchain 0.1.20, starlette 0.36.3 installed despite requirements-runtime.txt specifying newer versions
- **Fix:** Upgraded packages in container: langgraph 1.1.2, langchain 1.2.12, langchain-openai 1.1.11, langchain-google-genai 4.2.1, fastapi 0.135.1 (pulled starlette 0.52.1)
- **Files modified:** None (container runtime only, Dockerfile already has correct requirements)
- **Verification:** All imports succeed, 278 tests pass
- **Committed in:** n/a (runtime package upgrade, not code change)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Container packages needed upgrading before code changes could be verified. No scope creep.

## Issues Encountered
- starlette 0.36.3 + httpx 0.28.x caused TestClient failure (`Client.__init__() got an unexpected keyword argument 'app'`). Resolved by upgrading fastapi to 0.135.1 which pulled starlette 0.52.1.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Backend fully compatible with langgraph 1.1.2, langchain 1.2.12, and all related packages
- All graphs compile and all tests pass

---
*Quick task: 260317-naa*
*Completed: 2026-03-17*
