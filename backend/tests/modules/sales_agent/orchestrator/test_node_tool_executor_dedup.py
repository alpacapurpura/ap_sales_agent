"""``node_tool_executor`` integrates ``ToolCallDedupTracker``.

* Tracker absent → behaves as before (no dedup).
* Verdict WARN augments the result message with anti-loop directive.
* Hard-limit raise → tool message is an error + ``next_node='respond'``.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


def _build_state(*, pending: dict[str, Any], tracker: object | None) -> dict[str, Any]:
    state: dict[str, Any] = {
        "_pending_tool": pending,
        "_db": None,
        "messages": [],
    }
    if tracker is not None:
        state["_tool_dedup_tracker"] = tracker
    return state


@pytest.fixture(autouse=True)
def _mute_trace_node_writes(monkeypatch: pytest.MonkeyPatch) -> None:
    """The ``@trace_node`` decorator persists to ``agent_traces`` on real
    ``SessionLocal``; the unit test focuses on dedup logic, not legacy
    tracing. Mock the session factory + repo so the decorator no-ops.
    """
    fake_session = MagicMock()
    monkeypatch.setattr(
        "luana_core_sales_agent.infrastructure.monitoring.tracing.SessionLocal",
        lambda: fake_session,
    )

    class _NullRepo:
        def __init__(self, db: object) -> None:
            self.db = db

        def create_trace(self, **_kwargs: object) -> None:
            return None

        def close(self) -> None: ...

    monkeypatch.setattr(
        "luana_core_sales_agent.infrastructure.monitoring.tracing.AuditRepository",
        _NullRepo,
    )


class TestNoTracker:
    def test_executor_runs_tool_when_tracker_absent(self) -> None:
        from luana_core_sales_agent.application.agents.sales.nodes import node_tool_executor

        called = {}

        def _stub_tool(_state: dict, db: object) -> dict[str, Any]:
            called["yes"] = True
            return {"status": "ok", "data": "x"}

        registry = {"my_tool": _stub_tool}
        state = _build_state(pending={"tool": "my_tool", "args": {"k": "v"}}, tracker=None)

        with patch(
            "luana_core_sales_agent.application.agents.sales.tools.TOOL_REGISTRY",
            registry,
        ):
            out = node_tool_executor(state)

        assert called["yes"]
        assert out["_pending_tool"] is None
        # Plain JSON, no GUARD.
        assert "GUARD ANTI-LOOP" not in out["messages"][0]["content"]


class TestWithTracker:
    def test_warn_augments_tool_message(self) -> None:
        from luana_core_sales_agent.application.agents.sales.nodes import node_tool_executor
        from luana_core_sales_agent.application.orchestrator.tool_call_dedup import (
            ToolCallDedupTracker,
        )

        tracker = ToolCallDedupTracker(threshold=2, hard_limit=10)
        # Seed two prior observations so the next one returns WARN.
        tracker.observe("my_tool", {"k": "v"})
        tracker.observe("my_tool", {"k": "v"})

        registry = {"my_tool": lambda _state, _db: {"status": "ok"}}
        state = _build_state(pending={"tool": "my_tool", "args": {"k": "v"}}, tracker=tracker)

        with patch(
            "luana_core_sales_agent.application.agents.sales.tools.TOOL_REGISTRY",
            registry,
        ):
            out = node_tool_executor(state)

        # The dispatched call IS executed (data still flows back to the LLM)
        # — only the wrapper directive is added.
        assert "GUARD ANTI-LOOP" in out["messages"][0]["content"]
        assert "my_tool" in out["messages"][0]["content"]

    def test_hard_limit_aborts_with_error_message(self) -> None:
        from luana_core_sales_agent.application.agents.sales.nodes import node_tool_executor
        from luana_core_sales_agent.application.orchestrator.tool_call_dedup import (
            ToolCallDedupTracker,
        )

        tracker = ToolCallDedupTracker(threshold=2, hard_limit=3)
        tracker.observe("loopy", {})
        tracker.observe("loopy", {})  # next .observe raises

        registry = {"loopy": lambda _state, _db: {"status": "ok"}}
        state = _build_state(pending={"tool": "loopy", "args": {}}, tracker=tracker)

        with patch(
            "luana_core_sales_agent.application.agents.sales.tools.TOOL_REGISTRY",
            registry,
        ):
            out = node_tool_executor(state)

        # Tool was NOT executed; we got a synthetic error message.
        msg = json.loads(out["messages"][0]["content"])
        assert msg["status"] == "error"
        assert msg["tool_name"] == "loopy"
        assert msg["repeat_count"] == 3
        assert out["_pending_tool"] is None
        assert out["next_node"] == "respond"
