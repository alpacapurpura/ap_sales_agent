---
story_id: luana-copilot-engine
ticket: T-9
status: GREEN
completed_at: 2026-05-11
verdict: done
---

# T-9 result — Lift copilot application/orchestrator (LangGraph + deepagents harness + 11-slot prompt cache composer + 3 subagents)

## Status: GREEN

## Commit
luana-platform main: `8602ae0` (feat(luana-core-copilot): lift application/orchestrator (T-9))

## Validators satisfied
- V-NF-2 (verbatim lift fidelity — 18 source + 12 tests)
- V-F-prompt-cache (PromptFragment 11-slot enum preserved in system_prompt_layout.py)

## Validators deferred (DAG sequence)
- V-F-langgraph (compile smoke pending T-10 application/tools arrival)

## Tests run
- 52/52 PASS isolated (test_tool_call_dedup + test_stream_provenance + test_system_prompt_layout)
- 7 tests require application.tools (deferred to T-10 GREEN): test_inspirations_layer, test_conversational_questioning, test_brand_lighthouse_in_system_prompt, test_chat_routing_integration, test_streaming_integration, test_system_prompt_neutro_latam, application/orchestrator/test_invoke_text + test_telegram_channel_context_fragment

## Files lifted (35 total: 18 source + 12 tests + 5 __init__/structure)
- 1 application/__init__.py
- 17 orchestrator/*.py + 1 subagents/__init__.py + 3 subagents/*.py (audit_inspector + data_query + url_analyzer)
- 12 test files (9 in tests root + 3 in tests/application/orchestrator/)

## D-T6 anti-mirror verified
- No shared abstraction redefined in orchestrator (verbatim cp -r — no LLM-rewrite)
- No `class FXResolver | CostCalculator | PricingResolver | BaseObservabilityContext | BaseAgentCallbackHandler` declarations in orchestrator scope (T-13 enforces broader scan)

## D-T1 registry contracts preserved
- 11-slot PromptFragment enum byte-identical post-sed
- CopilotState TypedDict + add_messages reducer preserved verbatim

## Process drifts documented for /pm + auditor
1. **05-guidelines.md §1.3 sed gap reconfirmed** — string-literal patches (`"src.modules.copilot.X"` inside `unittest.mock.patch()`) not covered. Manual extension applied this ticket. /architect should bake into canonical sed recipe before Story 7.
2. **T-9 spec smoke example inaccurate** — ticket cites `from ...graph import build_deep_agent_graph` but build_deep_agent_graph actually exports from `deep_agent.py`. Verbatim lift OK; ticket descriptor inaccurate. No action needed (lift preserved truth).

## Next
T-10 — application/tools/ (28 files: registry + 24 tools + ask_tenant_data/ + guided/ + shared_tools/ subfolders)
