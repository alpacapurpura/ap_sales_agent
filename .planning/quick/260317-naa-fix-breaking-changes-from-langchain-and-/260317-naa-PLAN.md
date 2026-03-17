---
phase: quick
plan: 260317-naa
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/src/modules/sales_agent/application/agents/sales/graph.py
  - backend/src/modules/sales_agent/application/orchestrator/graph.py
  - backend/src/modules/copilot/application/agents/style_analyzer/graph.py
  - backend/src/modules/copilot/application/agents/web_extractor/graph.py
  - backend/src/modules/copilot/application/orchestrator/graph.py
  - backend/src/shared/infrastructure/llm/providers/gemini.py
  - backend/src/shared/infrastructure/files/image_analysis.py
autonomous: true
requirements: []
must_haves:
  truths:
    - "Backend container starts without import errors from langchain/langgraph"
    - "All langgraph graphs compile successfully with new API"
    - "LLM provider services instantiate without deprecation failures"
    - "Existing tests pass after migration"
  artifacts:
    - path: "backend/src/modules/sales_agent/application/agents/sales/graph.py"
      provides: "Sales subgraph using langgraph 1.x API"
      contains: "START"
    - path: "backend/src/modules/sales_agent/application/orchestrator/graph.py"
      provides: "Main orchestrator graph using langgraph 1.x API"
      contains: "START"
    - path: "backend/src/modules/copilot/application/agents/style_analyzer/graph.py"
      provides: "Onboarding graph using langgraph 1.x API"
      contains: "START"
    - path: "backend/src/modules/copilot/application/agents/web_extractor/graph.py"
      provides: "Web extractor graph using langgraph 1.x API"
      contains: "START"
    - path: "backend/src/modules/copilot/application/orchestrator/graph.py"
      provides: "Copilot orchestrator graph using langgraph 1.x API"
      contains: "START"
  key_links:
    - from: "all graph.py files"
      to: "langgraph.graph"
      via: "import START instead of set_entry_point()"
      pattern: "from langgraph\\.graph import.*START"
---

<objective>
Fix breaking changes from LangChain 0.1.x to 1.x and langgraph 0.0.24 to 1.1.2 migration in the backend codebase.

Purpose: The requirements-runtime.txt has already been updated with new package versions. The backend code still uses deprecated/removed APIs that will cause import or runtime errors with the new versions.

Output: All backend Python files updated to use current langgraph 1.x and langchain 1.x APIs.
</objective>

<execution_context>
@/home/chris/AISALESHT/.claude/get-shit-done/workflows/execute-plan.md
@/home/chris/AISALESHT/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@backend/requirements-runtime.txt
@backend/src/modules/sales_agent/application/orchestrator/state.py
@backend/src/shared/infrastructure/llm/providers/openai.py
@backend/src/shared/infrastructure/llm/providers/gemini.py

Key APIs in use:
- `langgraph.graph.StateGraph` + `END` — used in 5 graph files
- `workflow.set_entry_point("node")` — DEPRECATED in langgraph 1.x, must use `add_edge(START, "node")`
- `langchain_core.messages` — HumanMessage, SystemMessage, AIMessage (stable, no changes needed)
- `langchain_openai.ChatOpenAI` — stable API, `openai_api_key` param renamed to `api_key` in recent versions
- `langchain_google_genai.ChatGoogleGenerativeAI` — `google_api_key` may need update, `convert_system_message_to_human` deprecated
- `cryptography.fernet.Fernet` — stable API, no changes needed
- `jwt.decode` with RS256 — stable, no changes needed
- `@app.middleware("http")` — still supported in FastAPI 0.135.1

Non-breaking (no code changes needed):
- `langchain_core.messages` imports are stable
- `cryptography.fernet.Fernet` API unchanged
- PyJWT RS256 usage is fine (ECDSA curve changes don't apply)
- FastAPI middleware pattern still works
- SQLAlchemy 2.0 already in use
</context>

<tasks>

<task type="auto">
  <name>Task 1: Migrate langgraph graphs from deprecated set_entry_point to START node pattern</name>
  <files>
    backend/src/modules/sales_agent/application/agents/sales/graph.py
    backend/src/modules/sales_agent/application/orchestrator/graph.py
    backend/src/modules/copilot/application/agents/style_analyzer/graph.py
    backend/src/modules/copilot/application/agents/web_extractor/graph.py
    backend/src/modules/copilot/application/orchestrator/graph.py
  </files>
  <action>
In all 5 graph files, apply the langgraph 1.x migration:

1. Change import from `from langgraph.graph import StateGraph, END` to `from langgraph.graph import StateGraph, START, END`

2. Replace all `workflow.set_entry_point("node_name")` calls with `workflow.add_edge(START, "node_name")`

This is the primary breaking change in langgraph 1.x — `set_entry_point()` was deprecated in 0.2.x and removed in 1.x. The `START` sentinel replaces it.

Files and their entry points:
- `sales/graph.py`: `set_entry_point("supervisor")` -> `add_edge(START, "supervisor")`
- `orchestrator/graph.py` (sales): `set_entry_point("supervisor")` -> `add_edge(START, "supervisor")`
- `style_analyzer/graph.py`: `set_entry_point("janitor")` -> `add_edge(START, "janitor")`
- `web_extractor/graph.py`: `set_entry_point("extract")` -> `add_edge(START, "extract")`
- `copilot/orchestrator/graph.py`: `set_entry_point("router")` -> `add_edge(START, "router")`

Do NOT change any graph logic, node definitions, conditional edges, or state definitions. Only the entry point pattern changes.
  </action>
  <verify>
    <automated>docker exec -t visionarias_brain_dev python -c "
from src.modules.sales_agent.application.agents.sales.graph import sales_app;
from src.modules.sales_agent.application.orchestrator.graph import agent_app;
from src.modules.copilot.application.agents.style_analyzer.graph import onboarding_app;
from src.modules.copilot.application.agents.web_extractor.graph import web_extractor_graph;
from src.modules.copilot.application.orchestrator.graph import copilot_app;
print('All graphs imported and compiled successfully')
"</automated>
  </verify>
  <done>All 5 langgraph graph files use START node pattern instead of deprecated set_entry_point(), and all graphs compile without errors.</done>
</task>

<task type="auto">
  <name>Task 2: Update langchain LLM provider constructor parameters for 1.x compatibility</name>
  <files>
    backend/src/shared/infrastructure/llm/providers/gemini.py
    backend/src/shared/infrastructure/llm/providers/openai.py
    backend/src/shared/infrastructure/files/image_analysis.py
  </files>
  <action>
Update LLM provider files for langchain 1.x / langchain-google-genai 4.x compatibility:

**gemini.py:**
1. Remove `convert_system_message_to_human=True` parameter from `ChatGoogleGenerativeAI()` constructor — this parameter was deprecated and removed in langchain-google-genai 2.x+. Gemini models now handle system messages natively.
2. Change `google_api_key=` to `api_key=` if the old parameter name causes deprecation warnings (check: `google_api_key` may still work as alias but `api_key` is the canonical name in langchain-google-genai 4.x).
3. For `GoogleGenerativeAIEmbeddings`, apply same `google_api_key` -> `api_key` rename if needed.

**openai.py:**
1. Change `openai_api_key=` to `api_key=` in both `ChatOpenAI()` constructors (lines 28-30, 34-37) and the `OpenAIEmbeddings()` constructor (line 41-43). The `openai_api_key` parameter is deprecated in langchain-openai 1.x in favor of the standard `api_key`.

**image_analysis.py:**
1. Change `api_key=` parameter name — verify it's already using the correct parameter name for `ChatOpenAI` in langchain-openai 1.x (it uses `api_key=` which is correct, no change needed here).

Do NOT change any business logic, message construction, response parsing, or tracing code. Only constructor parameter names change.
  </action>
  <verify>
    <automated>docker exec -t visionarias_brain_dev python -c "
import os; os.environ.setdefault('OPENAI_API_KEY', 'sk-test');
from src.shared.infrastructure.llm.providers.openai import OpenAIService;
from src.shared.infrastructure.files.image_analysis import ImageAnalysisService;
print('OpenAI and ImageAnalysis providers import successfully');
" 2>&1 | head -20</automated>
  </verify>
  <done>LLM provider constructors use current parameter names (api_key instead of deprecated openai_api_key/google_api_key), and convert_system_message_to_human removed from Gemini provider. All providers instantiate without deprecation errors.</done>
</task>

<task type="auto">
  <name>Task 3: Verify full backend startup and run existing tests</name>
  <files></files>
  <action>
Run the full backend test suite and verify no import errors or runtime failures from the dependency upgrades.

1. Run `docker exec -t visionarias_brain_dev python -c "from src.main import app; print('FastAPI app created successfully')"` to verify the app starts without import errors.

2. Run `docker exec -t visionarias_brain_dev pytest tests/ -x --tb=short -q` to verify all existing tests pass.

3. Run `docker exec -t visionarias_brain_dev ruff check src --fix` to ensure no lint issues were introduced.

If any tests fail due to the upgrades, fix the specific issues:
- If `model_name` attribute access fails on ChatOpenAI, it may have been renamed to `model` in langchain-openai 1.x — update the reference in openai.py line 140.
- If any other import paths changed, update them.

This is a verification task — only make fixes if test failures are directly caused by the dependency migration.
  </action>
  <verify>
    <automated>docker exec -t visionarias_brain_dev pytest tests/ -x --tb=short -q 2>&1 | tail -20</automated>
  </verify>
  <done>Backend starts cleanly, all existing tests pass, ruff lint clean. No import errors or runtime failures from the langchain/langgraph/FastAPI dependency upgrades.</done>
</task>

</tasks>

<verification>
- All 5 langgraph graph files use `START` node pattern
- LLM providers use current constructor parameter names
- Backend container starts without import errors
- All existing tests pass
- No ruff lint violations introduced
</verification>

<success_criteria>
- `docker exec -t visionarias_brain_dev python -c "from src.main import app"` succeeds
- All langgraph graphs compile (import without error)
- `pytest tests/` passes with same pass count as before migration
- Zero new ruff violations
</success_criteria>

<output>
After completion, create `.planning/quick/260317-naa-fix-breaking-changes-from-langchain-and-/260317-naa-SUMMARY.md`
</output>
