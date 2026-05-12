---
story_id: luana-sales-agent-engine
ticket_id: T-8
owner: builder-agentic (Opus 4.7 — R23)
state: done
last_modified: 2026-05-11
commit_sha: 4129ce9
---

# T-8 — Lift application/orchestrator/ (10 files, LangGraph supervisor + §3 protected smart_debounce + tool_call_dedup)

## Scope

Lift `backend/src/modules/sales_agent/application/orchestrator/` from AISALESHT to `core/luana-core-sales-agent/src/luana_core_sales_agent/application/orchestrator/` (10 files including 2 §3 protected hash-stable files).

## Steps executed

1. `cp -r` orchestrator/ from AISALESHT (10 files).
2. Applied sed pipeline per 05-guidelines.md §1.4 — 22 substitutions total cross-module rewrites.
3. Verified zero top-level `from src.*` leaks via grep.
4. Ran `ruff format` (10 files left unchanged — sed output already canonical isort).
5. Captured §3 sha256 baselines POST-sed POST-ruff for T-18 V-AG-8 cement.
6. Created tests/orchestrator/ + tests/application/orchestrator/ directories + __init__.py.
7. Copied 10 test files (7 from `tests/modules/sales_agent/orchestrator/` + 3 from `tests/modules/sales_agent/application/orchestrator/` + 1 from top-level `test_graph.py`).
8. Applied sed pipeline to test files (both `from src.*` imports AND `"src.*"` monkeypatch string targets).
9. Verified zero `src.*` references in test files.
10. Lifted tests/conftest.py from luana-core-copilot baseline + appended sales_agent specific fixtures (TENANT_B/lead_id/customer_profile_id from AISALESHT conftest).
11. Added `[tool.ruff.lint.per-file-ignores]` to package pyproject.toml (Story 6 T-21 pattern: E402/E501/E741 tolerated in tests).
12. Ruff autofix applied (21/24 errors fixed — pre-existing E501 anchor docstrings exempted via per-file-ignores).
13. Ran isolated tests per ticket step 7 — 31 passed in 137s.

## Sed pipeline applied

22 substitutions per 05-guidelines.md §1.4 (replicated for test files in both unquoted imports AND quoted monkeypatch strings):

```
from src.modules.sales_agent.    → from luana_core_sales_agent.
from src.modules.iam.            → from luana_core_iam.
from src.modules.brand.          → from luana_core_brand_studio.
from src.modules.offer.          → from luana_core_offer_studio.
from src.modules.crm.            → from luana_core_crm.
from src.modules.copilot.        → from luana_core_copilot.
from src.shared.agent_observability.channels.  → from luana_core_channels.
from src.shared.agent_observability.            → from luana_core_observability.
from src.shared.domain_events.   → from luana_core_events.
from src.shared.idempotency.     → from luana_core_idempotency.
from src.shared.billing.         → from luana_core_billing.
from src.shared.compliance.      → from luana_core_compliance.
from src.shared.infrastructure.llm.  → from luana_core_llm.
from src.shared.domain.          → from luana_core_platform.domain.
from src.shared.links.           → from luana_core_platform.links.
from src.shared.infrastructure.  → from luana_core_platform.infrastructure.
from src.shared.application.     → from luana_core_platform.application.
from src.shared.workers.         → from luana_core_platform.workers.
from src.core.                   → from luana_core_platform.core.
```

## §3 hash-stable baselines (CANONICAL for T-18 V-AG-8)

POST-sed POST-ruff format, captured for downstream T-18 architectural fitness test:

```
smart_debounce_runner.py: 7c4201466c9b2d05ff68889015d069ab154657ea731f7220693e67745c190faa
tool_call_dedup.py:        8a9e3895fe8cc863273ab3a92fbf665b7882b3854be57432900a8425db5ab5be
```

## Tests GREEN (per step 7)

```
$ uv run pytest core/luana-core-sales-agent/tests/application/orchestrator/test_state_additive.py \
    core/luana-core-sales-agent/tests/orchestrator/test_tool_call_dedup.py \
    core/luana-core-sales-agent/tests/orchestrator/test_identity_resolver.py -q
...............................                                          [100%]
31 passed in 137.00s
```

Tests deferred to subsequent tickets (require T-9 application/agents/sales):
- test_audit_emitter.py (depends on chat module → conversation_pipeline → graph → agents.sales.graph)
- test_chat_orchestrator_snapshot.py
- test_conversation_pipeline.py
- test_node_tool_executor_dedup.py
- test_outbound_orchestrator.py
- test_inbound_campaign_recognition.py
- test_graph.py

These will be GREEN post T-9 (sales subgraph lift) and possibly T-10/T-11 (tools/prompts).

## Invariants verified

| Invariant | Status | Evidence |
|---|---|---|
| AISALESHT UNTOUCHED (V-NF-4) | ✅ | `git status` of AISALESHT shows no sales_agent/ modifications |
| Zero `from src.*` leaks (V-AG-1) | ✅ | grep returns empty |
| Zero `"src.*"` quoted leaks in tests | ✅ | grep returns empty |
| §3 sha256 captured for T-18 | ✅ | smart_debounce_runner.py + tool_call_dedup.py hashes documented |
| LangGraph SalesAgentState TypedDict preserved | ✅ | state.py copied verbatim — only sed rewrites |
| Supervisor specialist routing preserved | ✅ | graph.py copied verbatim |
| ruff check + format clean | ✅ | "All checks passed!" + 0 files reformatted (post-autofix) |

## Files modified/created (luana-platform)

### Created (src — 10 files)
- core/luana-core-sales-agent/src/luana_core_sales_agent/application/__init__.py
- core/luana-core-sales-agent/src/luana_core_sales_agent/application/orchestrator/__init__.py
- core/luana-core-sales-agent/src/luana_core_sales_agent/application/orchestrator/audit_emitter.py
- core/luana-core-sales-agent/src/luana_core_sales_agent/application/orchestrator/chat.py
- core/luana-core-sales-agent/src/luana_core_sales_agent/application/orchestrator/conversation_pipeline.py
- core/luana-core-sales-agent/src/luana_core_sales_agent/application/orchestrator/graph.py
- core/luana-core-sales-agent/src/luana_core_sales_agent/application/orchestrator/identity_resolver.py
- core/luana-core-sales-agent/src/luana_core_sales_agent/application/orchestrator/outbound_orchestrator.py
- core/luana-core-sales-agent/src/luana_core_sales_agent/application/orchestrator/smart_debounce_runner.py (§3)
- core/luana-core-sales-agent/src/luana_core_sales_agent/application/orchestrator/state.py
- core/luana-core-sales-agent/src/luana_core_sales_agent/application/orchestrator/tool_call_dedup.py (§3)

### Created (tests — 14 files)
- core/luana-core-sales-agent/tests/conftest.py
- core/luana-core-sales-agent/tests/application/__init__.py
- core/luana-core-sales-agent/tests/application/orchestrator/__init__.py
- core/luana-core-sales-agent/tests/application/orchestrator/test_inbound_campaign_recognition.py
- core/luana-core-sales-agent/tests/application/orchestrator/test_outbound_orchestrator.py
- core/luana-core-sales-agent/tests/application/orchestrator/test_state_additive.py
- core/luana-core-sales-agent/tests/orchestrator/__init__.py
- core/luana-core-sales-agent/tests/orchestrator/_chat_flow_snapshot_helpers.py
- core/luana-core-sales-agent/tests/orchestrator/test_audit_emitter.py
- core/luana-core-sales-agent/tests/orchestrator/test_chat_orchestrator_snapshot.py
- core/luana-core-sales-agent/tests/orchestrator/test_conversation_pipeline.py
- core/luana-core-sales-agent/tests/orchestrator/test_graph.py
- core/luana-core-sales-agent/tests/orchestrator/test_identity_resolver.py
- core/luana-core-sales-agent/tests/orchestrator/test_node_tool_executor_dedup.py
- core/luana-core-sales-agent/tests/orchestrator/test_tool_call_dedup.py

### Modified
- core/luana-core-sales-agent/pyproject.toml (added per-file-ignores for tests/)

## Validators addressed

- V-NF-2: zero `from src.*` cross-module leaks ✅
- V-F-langgraph: SalesAgentState TypedDict + supervisor specialist routing preserved verbatim ✅
- V-F-buffer-output: §3 smart_debounce_runner sha256 captured for T-18 cement ✅

## Commit

```
4129ce9 feat(luana-core-sales-agent): lift application orchestrator (10 files — LangGraph supervisor + §3 smart_debounce_runner + tool_call_dedup hash-stable)
```
