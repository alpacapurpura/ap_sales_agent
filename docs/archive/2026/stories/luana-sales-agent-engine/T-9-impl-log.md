---
story_id: luana-sales-agent-engine
ticket_id: T-9
owner: builder-agentic (Opus 4.7 — R23)
state: done
last_modified: 2026-05-11
commit_sha: c57aa3d
---

# T-9 — Lift application/agents/sales/ (4 files specialist sub-agents subgraph)

## Scope

Lift `backend/src/modules/sales_agent/application/agents/sales/` from AISALESHT to luana-core-sales-agent. 4 source files + 2 test files.

## Steps executed

1. `cp -r` agents/ from AISALESHT.
2. Cleared __pycache__.
3. Applied sed pipeline per 05-guidelines.md §1.4 (22 substitutions).
4. Verified zero `from src.*` leaks via grep.
5. Copied 2 test files (test_nodes from top-level + test_supervisor_outbound_skip from application/agents/sales/).
6. Applied sed pipeline to tests (imports + monkeypatch string targets).
7. Ran `ruff format` (4 files reformatted — isort-only sort of imports).
8. Ran `ruff check --fix` (some imports cleaned by autofix).
9. Detected E402 in `tools.py` (deliberate forward-reference imports below function defs to break circular deps tools↔agents). Added per-file-ignores per 05-guidelines.md §1.7 §3 verbatim-lift principle.
10. Final ruff check: All checks passed!
11. AST parse OK all 6 files.

## Tests deferred

T-9 isolated tests fail with `ModuleNotFoundError: No module named 'luana_core_sales_agent.application.prompts'` because nodes.py imports application.prompts.compose (T-11) and tools.py imports application.tools.payment + .scheduling (T-10). Expected per DAG.

Tests sed-applied + copied — will run GREEN post T-10+T-11:
- tests/application/agents/sales/test_nodes.py
- tests/application/agents/sales/test_supervisor_outbound_skip.py

## Invariants verified

| Invariant | Status | Evidence |
|---|---|---|
| AISALESHT UNTOUCHED (V-NF-4) | ✅ | git status of AISALESHT clean |
| Zero `from src.*` leaks (V-AG-1) | ✅ | grep returns empty |
| AST parse OK | ✅ | python ast.parse() success on 6 files |
| ruff check + format clean | ✅ | "All checks passed!" |
| Forward-ref imports preserved | ✅ | per-file-ignores for tools.py |
| Supervisor specialist node fns preserved | ✅ | nodes.py copied verbatim |

## Files created (luana-platform)

### src — 6 files (incl 2 __init__.py)
- core/luana-core-sales-agent/src/luana_core_sales_agent/application/agents/__init__.py
- core/luana-core-sales-agent/src/luana_core_sales_agent/application/agents/sales/__init__.py
- core/luana-core-sales-agent/src/luana_core_sales_agent/application/agents/sales/graph.py
- core/luana-core-sales-agent/src/luana_core_sales_agent/application/agents/sales/nodes.py
- core/luana-core-sales-agent/src/luana_core_sales_agent/application/agents/sales/tools.py
- core/luana-core-sales-agent/src/luana_core_sales_agent/application/agents/sales/enrollment_tools.py

### tests — 4 files (incl 2 __init__.py)
- core/luana-core-sales-agent/tests/application/agents/__init__.py
- core/luana-core-sales-agent/tests/application/agents/sales/__init__.py
- core/luana-core-sales-agent/tests/application/agents/sales/test_nodes.py
- core/luana-core-sales-agent/tests/application/agents/sales/test_supervisor_outbound_skip.py

### Modified
- core/luana-core-sales-agent/pyproject.toml (added per-file-ignores for tools.py forward-refs)

## Validators addressed

- V-NF-2: zero `from src.*` cross-module leaks ✅

## Commit

```
c57aa3d feat(luana-core-sales-agent): lift application agents/sales subgraph (4 files)
```
