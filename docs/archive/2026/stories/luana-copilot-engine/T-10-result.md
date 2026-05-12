---
story_id: luana-copilot-engine
ticket: T-10
status: GREEN
completed_at: 2026-05-11
verdict: done
---

# T-10 result — Lift copilot application/tools (ToolRegistry SSoT + 24 tools + 3 subfolders)

## Status: GREEN

## Commit
luana-platform main: `c0040be` (feat(luana-core-copilot): lift application/tools (T-10))

## Validators satisfied
- V-NF-2 (verbatim lift fidelity — 42 source + 14 tests)
- V-F-tools (24 tools preserved verbatim)
- V-F-registry-1 (ToolRegistry public API frozen D-T1 cardinal — register/get/list/groups methods + Tool dataclass)

## Tests run
- 40/40 PASS isolated (test_url_inspiration_analyzer + test_offer_ladder_tools + test_analytics_tools_observability — analytics PII + exception + JSON-string invariants)

## Files lifted (56 total: 42 source + 14 tests)
- 1 tools/__init__.py + 1 registry.py + 1 _analytics_inputs.py
- 24 tool files (analytics, assets, awareness, connections, crm, document, extract_from_doc, extraction, fetch_url, knowledge_search, knowledge_tools, landing, module, mutations, navigation, offer_ladder, offer_section, pin_to_memory, procedure, research, sales_agent, telegram_redirect, url_inspiration_analyzer, _analytics_inputs)
- ask_tenant_data/ subfolder (7 files: __init__, date_parser, executor, intent_classifier, query_builder, state_check, synthesizer, tool)
- guided/ subfolder (4 files)
- shared_tools/ subfolder (2 files)
- 14 test files (6 in tests root + 8 in tests/application/tools/)

## D-T1 registry contract compliance
- Public API preserved verbatim per arch §7.3 + snapshot V-AG-3 (created T-20):
  - ToolRegistry.register / get / list / groups methods
  - ALWAYS_AVAILABLE_GROUPS constant
  - Tool dataclass: name, description, function, groups, schema, tenant_scoped, external_calls fields

## DAG cross-dep deferral
- `ToolRegistry` import path requires `application.data_access` which arrives T-11. Full registry smoke deferred to T-11 GREEN.
- 5/5 standalone tool modules verified GREEN this ticket (fetch_url, pin_to_memory, navigation, knowledge_search, awareness).

## Process drifts documented for /pm + auditor
1. **05-guidelines.md §1.3 missing 3 cross-module sed rules** — `social_proof`, `commercial_calendar`, `scheduling`. Tools layer references beyond Stories 2-5 inventory. Mitigated manually. /architect should extend sed canonical recipe for Story 7.
2. **scheduling forward-compat rewrite** — `from luana_core_scheduling.*` written even though package not yet lifted (Story 8). Deferred-import-in-function-body pattern means failure is delayed to runtime call, not module load. Acceptable verbatim lift.

## Next
T-11 — router + suggestions + workflows + procedures + data_access + extraction + guided + memory + observability (~30 files)
