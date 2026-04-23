"""Regression: ``tool_executor_node`` must handle async LangChain tools.

Prior bug: the node was ``def`` + ``tool.invoke(args)``. A ``StructuredTool``
built from an ``async def`` (such as ``extract_from_url``) raised
``NotImplementedError: StructuredTool does not support sync invocation`` at
runtime, so the LLM got a tool error back instead of the dispatched job_id.

Fix: node is ``async def`` and uses ``await tool.ainvoke(args)``. ``ainvoke``
works for both sync and async tools — sync tools are wrapped transparently —
so the node is universal.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool as lc_tool

from src.modules.copilot.application.orchestrator.graph import tool_executor_node

if TYPE_CHECKING:
    import pytest


def _state_with_tool_call(tool_name: str, tool_args: dict) -> dict:
    ai_message = AIMessage(
        content="",
        tool_calls=[
            {
                "name": tool_name,
                "args": tool_args,
                "id": "call_1",
                "type": "tool_call",
            },
        ],
    )
    return {"messages": [ai_message], "client_context": {}}


class TestAsyncToolSupport:
    async def test_async_tool_runs_successfully(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[dict] = []

        @lc_tool
        async def probe_async_tool(payload: str) -> str:
            """Regression probe — an async tool the executor must await."""
            calls.append({"payload": payload})
            return f"async-ok:{payload}"

        monkeypatch.setattr(
            "src.modules.copilot.application.orchestrator.graph.get_all_tools",
            lambda: [probe_async_tool],
        )
        monkeypatch.setattr(
            "src.modules.copilot.application.orchestrator.graph.get_tools_for_context",
            lambda ctx: [probe_async_tool],
        )

        state = _state_with_tool_call("probe_async_tool", {"payload": "hello"})
        result = await tool_executor_node(state)

        assert len(result["messages"]) == 1
        msg = result["messages"][0]
        assert isinstance(msg, ToolMessage)
        assert msg.content == "async-ok:hello"
        assert calls == [{"payload": "hello"}]

    async def test_sync_tool_still_works(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Sync tools must keep working — the fix is additive."""

        @lc_tool
        def probe_sync_tool(payload: str) -> str:
            """Sync probe."""
            return f"sync-ok:{payload}"

        monkeypatch.setattr(
            "src.modules.copilot.application.orchestrator.graph.get_all_tools",
            lambda: [probe_sync_tool],
        )
        monkeypatch.setattr(
            "src.modules.copilot.application.orchestrator.graph.get_tools_for_context",
            lambda ctx: [probe_sync_tool],
        )

        state = _state_with_tool_call("probe_sync_tool", {"payload": "world"})
        result = await tool_executor_node(state)

        assert len(result["messages"]) == 1
        assert result["messages"][0].content == "sync-ok:world"

    async def test_tool_node_is_coroutine(self) -> None:
        """If somebody reverts to a sync def, this test fails fast."""
        assert asyncio.iscoroutinefunction(tool_executor_node)
