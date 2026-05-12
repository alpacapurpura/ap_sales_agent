---
story_id: luana-sales-agent-engine
ticket_id: T-8
result: done
commit_sha: 4129ce9
last_modified: 2026-05-11
---

# T-8 result

**Status:** done

**Commit:** `4129ce9 feat(luana-core-sales-agent): lift application orchestrator (10 files — LangGraph supervisor + §3 smart_debounce_runner + tool_call_dedup hash-stable)`

**Tests:** 31/31 PASS isolated subset (test_state_additive + test_tool_call_dedup + test_identity_resolver). 7 additional tests deferred to T-9+ (require sales subgraph + monitoring/tracing).

**§3 sha256 baselines POST-sed POST-ruff (CANONICAL for T-18 V-AG-8):**
- `smart_debounce_runner.py`: `7c4201466c9b2d05ff68889015d069ab154657ea731f7220693e67745c190faa`
- `tool_call_dedup.py`: `8a9e3895fe8cc863273ab3a92fbf665b7882b3854be57432900a8425db5ab5be`

**Halt criteria — none triggered.** AISALESHT untouched. Zero cross-module leaks. R23 honored.

**Next:** T-9 — lift application/agents/sales/ subgraph.
