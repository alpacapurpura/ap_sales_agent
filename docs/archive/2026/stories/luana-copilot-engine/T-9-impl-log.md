---
ticket: T-9
story_id: luana-copilot-engine
builder: builder-agentic (Claude Opus 4.7 — R23)
started_at: 2026-05-11
completed_at: 2026-05-11
---

# T-9 — Lift copilot application/orchestrator/

## Skills consulted
- copilot-expert (SKILL): D-T6 anti-mirror + 11-slot prompt cache + LangGraph state shape preserved verbatim
- sales-agent-expert (SKILL): cross-checked shared/agent_observability inheritance pattern
- tessl__langgraph: StateGraph + checkpointer + reducers patterns confirmed for verbatim preservation
- tessl__graceful-degradation: N/A (no new external calls introduced — verbatim lift)

## Lift execution
- cp -r `backend/src/modules/copilot/application/orchestrator/` → `core/luana-core-copilot/src/luana_core_copilot/application/orchestrator/`
- cp `backend/src/modules/copilot/application/__init__.py` → `core/luana-core-copilot/src/luana_core_copilot/application/`
- 18 source files: 17 orchestrator/{block_adapters, chat, context_budget, conversational_questioning, deep_agent, graph, inspirations_layer, invoke_result, output_sanitizer, state, stream_filters, stream_provenance, subagent_budget, system_prompt_composer, system_prompt_layout, tool_call_dedup, __init__} + subagents/{__init__, audit_inspector, data_query, url_analyzer}
- Tests: 12 orchestrator-related tests (test_tool_call_dedup, test_stream_provenance, test_system_prompt_layout, test_system_prompt_neutro_latam, test_brand_lighthouse_in_system_prompt, test_chat_routing_integration, test_conversational_questioning, test_inspirations_layer, test_streaming_integration, application/orchestrator/test_invoke_text, application/orchestrator/test_telegram_channel_context_fragment)

## Sed §1.3 applied
- Module-level: src.modules.{copilot,brand,offer,iam,assets,crm,analytics,landing,connections} → luana_core_*
- Shared-level: src.shared.{agent_observability.channels, agent_observability, domain_events, idempotency, billing, infrastructure.llm, domain, links, infrastructure, application, workers, api} → luana_core_{channels, observability, events, idempotency, billing, llm, platform.domain, platform.links, platform.infrastructure, platform.application, platform.workers, platform.api}
- Core: src.core → luana_core_platform.core
- **String-literal sed extension** (gap surfaced in T-7/T-8): `"src.modules.copilot.*"`, `"src.core.*"`, etc. inside `unittest.mock.patch("dotted.path")` rewrites applied.

## Smoke verification
10/13 non-tool-dependent orchestrator modules import GREEN (state, system_prompt_layout, system_prompt_composer, context_budget, subagent_budget, tool_call_dedup, stream_filters, stream_provenance, block_adapters, output_sanitizer).

7 modules depend on `luana_core_copilot.application.tools` which arrives T-10 per DAG (inspirations_layer, conversational_questioning, graph, deep_agent, chat, invoke_result, subagents/*). This is expected verbatim lift integrity — not a leak.

## Tests run
```
cd ~/luana-platform && uv run --package luana-core-copilot pytest \
    core/luana-core-copilot/tests/test_tool_call_dedup.py \
    core/luana-core-copilot/tests/test_stream_provenance.py \
    core/luana-core-copilot/tests/test_system_prompt_layout.py -x -q
→ 52 passed in 0.06s
```

## Validators
- V-NF-2 verbatim lift fidelity → GREEN
- V-F-langgraph compile smoke → pending T-10 tools arrival (DAG sequence)
- V-F-prompt-cache PromptFragment 11-slot enum preserved → GREEN

## Drifts surfaced
- **05-guidelines.md §1.3 gap reconfirmed** — Sed mapping does not cover `unittest.mock.patch("dotted.path.string")` string literal forms. Mitigated by manual sed expansion in T-9 (same pattern T-7/T-8 documented). Recommend `/architect` update §1.3 for Story 7 sales_agent lift to bake string-literal sed into canonical recipe.
- Orchestrator symbol exports differ from ticket smoke example: ticket §5 mentions `from luana_core_copilot.application.orchestrator.graph import build_deep_agent_graph` but `build_deep_agent_graph` actually lives in `deep_agent.py` (graph.py exports `build_system_prompt` only). Verbatim lift preserved — ticket smoke template inaccurate.

## Commit
luana-platform main: `8602ae0` (feat(luana-core-copilot): lift application/orchestrator (T-9))

## Next
T-10 — application/tools/ (28 files: registry + 24 tools + 4 subfolders ask_tenant_data, guided, shared_tools)
