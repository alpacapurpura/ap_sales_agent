# T-7 Implementation Log

**Story:** eval-foundation-simulator-homologation
**Ticket:** T-7
**Owner:** builder-agentic Opus 4.7
**Started:** 2026-05-08T00:30:00Z
**State:** developing

## Skills Consulted

- **`copilot-expert`** (auto-loaded) — `Stop. Lee primero` discipline + best-effort observability invariant + `set_turn_error` honesty cement applied to agent_bridge failure paths. Decision: every except branch in agent_bridge logs structured event AND returns is_finished=True with explicit error_subtype (per H7 taxonomy in T-4 enum). No silent catches.
- **`sales-agent-expert`** (auto-loaded) — §3 "NO se toca" verified: agent_bridge does NOT touch closer_studio, SmartBufferService, OutputManager, enrollment_*, follow_up_engine, PromptVersionModel. agent_app entrypoint READ-ONLY. ConversationPipeline helpers (build_identity, build_brand_voice, create_initial_state) READ-ONLY. anti-duplication §0 cardinal: zero mirror — all REUSE via direct import.
- **`tessl__langgraph`** (auto-loaded) — Async node returning partial state dict (NEVER mutate). transcript reducer Annotated[list[ConversationTurn], operator.add] — node returns `{"transcript": [new_turn]}`. NO `from __future__ import annotations` cement. Failure path returns `{"is_finished": True, "termination_reason": ..., "error_subtype": ...}` — graph conditional edge picks up via should_continue (T-8).
- **`tessl__graceful-degradation`** (auto-loaded) — Rule 1 every external call timeout: agent_app.ainvoke wrapped in `asyncio.wait_for` with 60s default (env override). Rule 2 every timeout needs fallback: graceful termination via H7 taxonomy (TIMEOUT/EMPTY_RESPONSE/HTTP_ERROR/INVALID_STATE), no bubble. Rule 5 per-dependency error isolation: customer_node failure (T-6) does NOT block agent_bridge. Rule 6 structured logs with simulation_id + turn + error_class context.
- **`tessl__pytest-api-testing`** (auto-loaded) — Async tests use `pytest.mark.asyncio`. Factory fixtures for ActorProfile + SimulationState. monkeypatch for swapping agent_app symbol at module level (`cn_mod` pattern from T-6 customer_node tests). `pytest.mark.no_eval` opt-out for default CI.

## Step 0 — Anti-duplication grep evidence

```bash
$ grep -rn "agent_bridge\|FORBIDDEN_LEAK_STRINGS\|assert_no_leak" /home/chris/AISALESHT/backend/ 2>/dev/null | grep -v __pycache__
# Only references found: docstrings + termination.py mentioning T-7 implements + observability.py factory comment
# Zero implementation files exist — primera vez implementing
```

Step 0 PASS — no mirror risk. Implementation creates 4 new files:
1. `_internal/leak_assertions.py` (new — H10 defense in depth)
2. `_internal/agent_bridge.py` (new — D1 in-process invocation)
3. `test_agent_bridge_unit.py` (new — A1, A2 acceptance)
4. `test_leak_assertions_unit.py` (new — A3 acceptance)

## Step 0.5 — Default-flip detection

NA — T-7 does NOT touch `core/config.py` or any feature flag. Pure test-infrastructure addition consuming production agent_app entrypoint READ-ONLY.

## Cross-module systems audit (NO-NEW-LAYER)

NA — T-7 lives entirely under `tests/agentic_evals/`. Imports:
- `agent_app` (sales_agent application orchestrator) — READ-ONLY
- `ConversationPipeline.{build_identity, build_brand_voice, create_initial_state}` — READ-ONLY (paridad with `backend/tests/agentic_evals/sales_agent/fixtures/entrypoint.py`)
- `build_eval_simulator_observability_context` (T-5) — REUSE via factory
- `SimulationState`, `ConversationTurn`, `AgentErrorSubtype`, `TerminationReason` (T-4) — REUSE via direct import

Zero new layer introduced. Zero shared abstractions duplicated.

## Implementation plan

### Phase 1 — Tests RED (TDD)

1. Write `test_leak_assertions_unit.py` — RED on import (no module yet)
2. Write `test_agent_bridge_unit.py` — RED on import (no module yet)

### Phase 2 — leak_assertions.py implementation

- `FORBIDDEN_LEAK_STRINGS: frozenset[str]` — 6 verbatim entries from spec
- `assert_no_leak(transcript_content: str) → None` — case-insensitive substring scan, AssertionError on match
- structlog warning `simulator.system_prompt_leak_detected` on match (always logs even when assertion fires)

### Phase 3 — agent_bridge.py implementation

- `async def agent_bridge(state: SimulationState) -> dict[str, Any]` — LangGraph node
- Step 1: extract last customer turn or fail INVALID_STATE
- Step 2: lazy imports (paridad customer_node + outbound_orchestrator pattern)
- Step 3: build_identity + build_brand_voice via TenantKnowledgeBuilder
- Step 4: create_initial_state with channel_type="eval_simulator"
- Step 5: build_eval_simulator_observability_context (T-5 factory)
- Step 6: agent_app.ainvoke in-process (NEVER httpx) under observe_turn
- Step 7: extract response text
- Step 8: assert_no_leak (warning only, no raise)
- Step 9: append agent turn to transcript via `{"transcript": [agent_turn]}`
- Step 10: H7 failure taxonomy on every except branch

### Phase 4 — Quality gates

- `ruff check` + `ruff format --check`
- `mypy --strict` (file-level)
- `pytest test_agent_bridge_unit.py test_leak_assertions_unit.py -v`
- Full simulator suite regression
- arch fitness regression smoke

## CONTEXT-BRIEF.md acceptance gate (R24)

**Validator pass:** `_pending_` — brief was generated with `_pending_` and not validated by context-validator. However, T-1..T-6 all proceeded successfully against this brief (6 prior tickets shipped clean), providing empirical proof of brief accuracy. Documenting this as §11 gap per R24 partial flag handling.

**Faithfulness flag:** `_pending_` (not blocking) — proceeding under partial flag rules.

## R30 final-line discipline

Builder phase output state = `tests-passing`. Auditor verdict is ORCHESTRATOR's call (independent contract). No "PASS" or "APPROVED" claim in final reply.

---
