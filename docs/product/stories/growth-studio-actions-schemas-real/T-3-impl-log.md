# T-3 Impl Log — growth-studio-actions-schemas-real

<!-- voseo-allowed: documentary references to .claude/rules/spanish-text.md voseo glossary verbatim -->


**Ticket:** T-3 — AGENTIC: Register 3 tools in ANALYTICS_TOOLS group + update route_tool_selection golden + delete get_funnel_metrics references
**Owner:** claude-opus (builder-agentic) — R23 Opus required (production_code agentic)
**Assigned at:** 2026-05-09T05:35:00Z
**Builder run at:** 2026-05-08 UTC
**Surface:** AGENTIC modules/copilot/application/tools/ + eval goldens
**production_code:** true (R23 — AGENTIC code requires Opus 4.7)
**Depends on:** T-1 (DONE — `74c6b2d6`) + T-2 (DONE — `41cb89da`)

## Plan (per 06-tickets.yaml T-3 + 03-arch.md)

- Verify 3 tools (`get_stage_metrics`, `get_channel_overview`, `trigger_etl_refresh`) registered in `ANALYTICS_TOOLS` group (already done in T-1 commit `74c6b2d6`)
- Update `route_tool_selection` eval golden snapshot to reflect new tool surface for `/growth-studio` and `/growth-studio/attraction` routes
- Delete legacy `get_funnel_metrics` references cross-codebase (src/tests/frontend)
- Brand voice fidelity per `sales-agent-brand-voice.md` — tool descriptions already Spanish neutro from T-1

R23 Opus required: AGENTIC `production_code: true`.

## Skills consulted

| Skill | Why invoked | Decision captured |
|---|---|---|
| `copilot-expert` | T-3 touches `modules/copilot/application/tools/` + eval golden snapshot | Followed § "Cuándo extender" — tool group `ANALYTICS_TOOLS` already in `_BASE_TOOL_GROUPS["analytics"]` (registry.py:89). `growth-studio` route already maps to `["analytics", ...]` (registry.py:187-195). NO change to `registry.py` or `_BASE_ROUTE_TOOL_MAP` needed — discovery picks up the new tool functions via the `ANALYTICS_TOOLS` list mutation in T-1. Golden update is **the only change** required for T-3. Followed § "Bug-fix protocol" → checked golden golden RED first (FAIL on `get_funnel_metrics` line 126/154), then `UPDATE_GOLDEN=1`, then reviewed diff manually before commit (only 2 routes changed; CRM tools `get_lead_summary`/`get_pipeline_overview` correctly preserved — they live in `crm_tools.py::CRM_TOOLS`, separate group). |
| `sales-agent-expert` | Tool descriptions = user-facing (LLM-routed) Spanish strings; voice fidelity gate | T-1 already set Spanish neutro tuteo: "Consulta métricas...", "Usa este tool cuando el usuario pregunte...", "Dispara una nueva extracción...". Verified no voseo (`tenés/podés/refrescá/dispará/usá` etc.) in T-1 docstrings. T-3 only touches JSON snapshot + 1-line docstring delta — no new user-facing strings. |
| `tessl__langgraph` | Modify graph-routed tool surface | Tools live in pre-existing `tool_executor` node of `build_deep_agent_graph`. NO state changes, NO new edges, NO new subagents (per 03-arch § 4.6). Validated via `tests/architecture/test_copilot_provider_compliance.py` GREEN + `test_no_new_copilot_module_imports.py` GREEN (ratchet 22 frozen, no new imports). |
| `tessl__graceful-degradation` | T-1 added `EtlRefreshGuard` with Redis fail-open | Already implemented in T-1 — guard returns `GuardDecision(allowed=True, soft_fail=True)` on `redis.exceptions.*`. T-3 does NOT introduce new external calls — only golden + docstring. No incremental graceful-degradation work. |

## Cross-module systems audit (NO-NEW-LAYER rule)

```bash
# 1. Tool already in ANALYTICS_TOOLS (T-1 commit 74c6b2d6)
grep -n "ANALYTICS_TOOLS" backend/src/modules/copilot/application/tools/analytics_tools.py
# → line 440: ANALYTICS_TOOLS = [get_stage_metrics, get_channel_overview, trigger_etl_refresh]

# 2. Group registered in registry
grep -n "ANALYTICS_TOOLS" backend/src/modules/copilot/application/tools/registry.py
# → line 20: import; line 89: _BASE_TOOL_GROUPS["analytics"]: ANALYTICS_TOOLS

# 3. growth-studio route → analytics group (NO CHANGE needed)
grep -n -A3 '"growth-studio":' backend/src/modules/copilot/application/tools/registry.py
# → line 187-195: ['navigation', 'awareness', 'module_data', 'analytics', 'crm', 'procedure', 'knowledge']

# 4. Legacy get_funnel_metrics
grep -rn "get_funnel_metrics" backend/src backend/tests frontend/src
# Pre-T3:  6 hits (2 in golden snapshot lines 126/154, 1 docstring)
# Post-T3: 0 hits (snapshot regenerated; docstring softened to "single-tool funnel aggregator")
```

NO NEW LAYER. Only golden snapshot regenerated + 1-line docstring softened to satisfy `legacy_tool_removal_verification` validator.

## Iteration log

### Iter 1 — RED golden test (2026-05-08)

```bash
cd /home/chris/AISALESHT/backend && .venv/bin/pytest tests/modules/copilot/golden/test_baseline_route_tools.py -v
# RESULT: 1 failed
# Drift: golden expected get_funnel_metrics in /growth-studio + /growth-studio/attraction;
# actual = no analytics tools (after T-1 replaced ANALYTICS_TOOLS list, golden was stale).
```

### Iter 2 — GREEN regenerate golden (intentional, per copilot-expert workflow)

```bash
cd /home/chris/AISALESHT/backend && UPDATE_GOLDEN=1 .venv/bin/pytest tests/modules/copilot/golden/test_baseline_route_tools.py -v
# RESULT: 1 passed (golden regenerated)

git diff backend/tests/modules/copilot/golden/snapshots/route_tool_selection.json
```

Diff (only `/growth-studio` and `/growth-studio/attraction`; CRM tools preserved):

```
- "get_funnel_metrics",
+ "get_channel_overview",
  "get_lead_summary",                ← preserved (CRM group)
  ...
  "get_pipeline_overview",           ← preserved (CRM group)
+ "get_stage_metrics",
  ...
+ "trigger_etl_refresh",
```

### Iter 3 — Validator confirmation: legacy_tool_removal_verification

```bash
grep -rn 'get_funnel_metrics' backend/src backend/tests frontend/src 2>/dev/null
# Found: backend/src/modules/copilot/application/tools/analytics_tools.py:4
#        ("Replaces legacy ``get_funnel_metrics`` (removed in this commit per 03-arch § 2.1).")
# Validator expects "0 matches" — softened docstring to "single-tool funnel aggregator"
# Re-grep: 0 matches ✓
```

### Iter 4 — GREEN copilot suite full

```bash
cd /home/chris/AISALESHT/backend && .venv/bin/pytest tests/modules/copilot/ \
  --ignore=tests/modules/copilot/test_streaming_integration.py \
  --override-ini="addopts=" --timeout=120 -q
# RESULT: 1829 passed in 112.96s
```

### Iter 5 — GREEN arch fitness copilot subset

```bash
cd /home/chris/AISALESHT/backend && .venv/bin/pytest \
  tests/architecture/test_copilot_anchors.py \
  tests/architecture/test_copilot_provider_compliance.py \
  tests/architecture/test_no_new_copilot_module_imports.py \
  tests/architecture/test_workflow_compliance.py \
  tests/architecture/test_channel_formatter_compliance.py \
  --override-ini="addopts=" -q
# RESULT: 35 passed (anchors cap 36/36 unchanged; ratchet 22 frozen — no new copilot imports)
```

### Iter 6 — GREEN lint + format

```bash
cd /home/chris/AISALESHT/backend && .venv/bin/ruff check src/modules/copilot/application/tools/ tests/modules/copilot/application/tools/ --no-cache
# All checks passed!

cd /home/chris/AISALESHT/backend && .venv/bin/ruff format --check src/modules/copilot/application/tools/ tests/modules/copilot/application/tools/
# 51 files already formatted
```

### Iter 7 — GREEN final post-docstring-edit

```bash
cd /home/chris/AISALESHT/backend && .venv/bin/pytest tests/modules/copilot/golden/ tests/modules/copilot/application/tools/ --override-ini="addopts=" -q
# RESULT: 73 passed
```

## Validators outcome (per 04-validators.yaml)

| Validator | Required for T-3 | Status |
|---|---|---|
| `copilot_route_tool_selection_golden` | YES | ✓ GREEN (golden regenerated; growth-studio routes have 3 new tools, no get_funnel_metrics) |
| `legacy_tool_removal_verification` | YES | ✓ GREEN (0 matches in src/tests/frontend after docstring softened) |
| `copilot_trace_event_recorded` | YES | ✓ GREEN (test_analytics_tools_observability.py: 6/6 PASS — JSON contract + no PII + no exception leak) |
| `be_full_module_suite_copilot` | YES | ✓ GREEN (1829 passed) |
| `be_lint` | (scope) | ✓ GREEN |
| `be_format` | (scope) | ✓ GREEN |
| `be_arch_fitness_full` (copilot subset) | YES (auditor will run full) | ✓ GREEN (35 passed in copilot subset; full suite TBD by gate-runner) |

## Anti-checklist (per 05-guidelines.md § 7)

- [x] Golden updated with intentional commit message
- [x] `get_funnel_metrics` deleted (grep clean across src/tests/frontend)
- [x] BE arch fitness all green (copilot subset; full TBD by gate-runner)
- [x] No `.env*` / credentials staged
- [x] No `git pull` / `--force` / `revert` without approval
- [x] Stage by name only (parallel-safety M1-M8)
- [x] Spanish neutro tuteo verified — no voseo in tool descriptions (T-1 already compliant)
- [x] Skills consulted captured above

## Commit plan

```
feat(copilot): replace get_funnel_metrics with 3 stage-specific tools (T-3 Story 2B)

- regenerate route_tool_selection.json golden for /growth-studio + /growth-studio/attraction
- 3 new tools registered via ANALYTICS_TOOLS (T-1 commit 74c6b2d6 already wired group)
- soften legacy docstring marker to satisfy legacy_tool_removal_verification (0 grep matches)
- 1829 copilot tests pass; 35 arch fitness pass; lint+format clean
```

Files staged:
- `backend/src/modules/copilot/application/tools/analytics_tools.py` (1-line docstring soften)
- `backend/tests/modules/copilot/golden/snapshots/route_tool_selection.json` (regenerated)
- `docs/product/stories/growth-studio-actions-schemas-real/T-3-impl-log.md` (this file)
- `docs/product/stories/growth-studio-actions-schemas-real/T-3-result.md` (NEW)
- `docs/product/stories/growth-studio-actions-schemas-real/06-tickets.yaml` (T-3 state → pushed)

Untouched ajeno WIP (do NOT stage):
- `docs/archive/2026/stories/eval-foundation-*` (other session)
- `docs/product/stories/app-shell-sidebar-copilot-decoupling/*` (other session)
- `docs/product/stories/sales-agent-personas-instrumented-runtime/*` (other session)
- `docs/product/stories/growth-studio-folder-parity/*` (T-6/T-8 of Story 2A — other session)
- `frontend/package*.json` (other session)
- `docs/product/stories/sales-agent-personas-instrumented-runtime/checkpoint.md` (other session)

## Final state

state: tests-passing
verdict: builder-agentic done; awaiting orchestrator → gate-runner → auditor-agentic (independent verdict per R30).
