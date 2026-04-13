"""Tests for context window budget and history truncation."""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from src.modules.copilot.application.orchestrator.context_budget import (
    truncate_history,
)


class TestTruncateHistory:
    def test_short_history_unchanged(self) -> None:
        msgs = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!"),
        ]
        result = truncate_history(msgs, max_tokens=15000)
        assert len(result) == 2

    def test_empty_history(self) -> None:
        result = truncate_history([], max_tokens=15000)
        assert result == []

    def test_long_history_truncated(self) -> None:
        # Each message ~500 tokens (2000 chars), 30 turns = 60 msgs x 500 = 30000 tokens
        msgs = []
        for i in range(30):
            msgs.append(HumanMessage(content=f"Message {i} " + "x" * 1988))
            msgs.append(AIMessage(content=f"Reply {i} " + "y" * 1988))
        result = truncate_history(msgs, max_tokens=5000)
        assert len(result) < len(msgs)
        # Last message should be preserved
        assert result[-1].content == msgs[-1].content

    def test_preserves_last_3_turns(self) -> None:
        msgs = [
            HumanMessage(content="Old message " + "x" * 1000),
            AIMessage(content="Old reply " + "y" * 1000),
            HumanMessage(content="Recent 1"),
            AIMessage(content="Reply 1"),
            HumanMessage(content="Recent 2"),
            AIMessage(content="Reply 2"),
            HumanMessage(content="Current"),
            AIMessage(content="Current reply"),
        ]
        result = truncate_history(msgs, max_tokens=500)
        contents = [m.content for m in result if not isinstance(m, SystemMessage)]
        assert "Current reply" in contents
        assert "Reply 2" in contents
        assert "Recent 2" in contents

    def test_summary_message_added(self) -> None:
        msgs = [
            HumanMessage(content="Old question about pricing"),
            AIMessage(content="Old answer about pricing"),
            HumanMessage(content="Another old question " + "x" * 1000),
            AIMessage(content="Another old answer " + "y" * 1000),
            HumanMessage(content="Recent"),
            AIMessage(content="Recent reply"),
            HumanMessage(content="Current"),
            AIMessage(content="Current reply"),
        ]
        result = truncate_history(msgs, max_tokens=500)
        system_msgs = [m for m in result if isinstance(m, SystemMessage)]
        assert len(system_msgs) >= 1
        assert "Previous conversation" in system_msgs[0].content

    def test_tool_messages_in_recent_turns_preserved(self) -> None:
        msgs = [
            HumanMessage(content="Old " + "x" * 1000),
            AIMessage(content="Old reply"),
            HumanMessage(content="Use tool"),
            AIMessage(
                content="",
                additional_kwargs={
                    "tool_calls": [
                        {
                            "id": "1",
                            "function": {"name": "test", "arguments": "{}"},
                            "type": "function",
                        }
                    ]
                },
            ),
            ToolMessage(content="Tool result", tool_call_id="1"),
            AIMessage(content="Based on the tool..."),
            HumanMessage(content="Thanks"),
            AIMessage(content="You're welcome"),
        ]
        result = truncate_history(msgs, max_tokens=500)
        tool_msgs = [m for m in result if isinstance(m, ToolMessage)]
        assert len(tool_msgs) >= 1
