"""Tests for context window budget and history truncation."""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from src.modules.copilot.application.orchestrator.context_budget import (
    _estimate_tokens,
    truncate_history,
)


class TestEstimateTokens:
    def test_empty_string_returns_positive(self) -> None:
        # Should return at least 0 (max(1, ...) if using heuristic)
        assert _estimate_tokens("") >= 0

    def test_short_text_is_reasonable(self) -> None:
        # "Hello world" is ~2 tokens — estimate must be > 0
        result = _estimate_tokens("Hello world")
        assert result > 0

    def test_estimate_is_positive_for_real_content(self) -> None:
        # For typical prose content (not highly compressible), the estimate
        # must be strictly positive and less than the raw character count.
        text = "Hello world, this is a typical copilot conversation message about branding. " * 5
        result = _estimate_tokens(text)
        assert 0 < result < len(text)

    def test_repetitive_content_still_positive(self) -> None:
        # Even highly compressible content must yield a positive estimate.
        text = "a" * 400
        result = _estimate_tokens(text)
        assert result > 0

    def test_long_text_scales_proportionally(self) -> None:
        short = _estimate_tokens("word " * 10)
        long = _estimate_tokens("word " * 100)
        # More text → more tokens
        assert long > short

    def test_mixed_content_stays_within_range(self) -> None:
        # Mixed prose + JSON-like content typical of LLM conversations
        text = '{"brand_name": "Nicolify", "headline": "The best AI platform for creators"} ' * 20
        result = _estimate_tokens(text)
        # Sanity check: must be positive and less than raw char count
        assert 0 < result < len(text)


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

    # Prose-like content that tokenises ~1 token per 4-5 chars, avoiding
    # highly compressible repeated chars that tiktoken encodes in bulk tokens.
    _LONG_CONTENT = "The brand is a unique platform for creators who want to grow their audience. " * 30

    def test_long_history_truncated(self) -> None:
        # Each message uses prose-like content (~600 tokens), 20 turns = 40 msgs x 600 = 24000 tokens
        msgs = []
        for i in range(20):
            msgs.append(HumanMessage(content=f"Message {i}: {self._LONG_CONTENT}"))
            msgs.append(AIMessage(content=f"Reply {i}: {self._LONG_CONTENT}"))
        result = truncate_history(msgs, max_tokens=3000)
        assert len(result) < len(msgs)
        # Last message should be preserved
        assert result[-1].content == msgs[-1].content

    def test_preserves_last_3_turns(self) -> None:
        msgs = [
            HumanMessage(content="Old message: " + self._LONG_CONTENT),
            AIMessage(content="Old reply: " + self._LONG_CONTENT),
            HumanMessage(content="Recent 1"),
            AIMessage(content="Reply 1"),
            HumanMessage(content="Recent 2"),
            AIMessage(content="Reply 2"),
            HumanMessage(content="Current"),
            AIMessage(content="Current reply"),
        ]
        result = truncate_history(msgs, max_tokens=200)
        contents = [m.content for m in result if not isinstance(m, SystemMessage)]
        assert "Current reply" in contents
        assert "Reply 2" in contents
        assert "Recent 2" in contents

    def test_summary_message_added(self) -> None:
        # Need more than PRESERVE_LAST_TURNS (3) human turns so at least one
        # turn ends up in the "old" section and triggers summarisation.
        msgs = [
            HumanMessage(content="Old question 1: " + self._LONG_CONTENT),
            AIMessage(content="Old answer 1: " + self._LONG_CONTENT),
            HumanMessage(content="Old question 2: " + self._LONG_CONTENT),
            AIMessage(content="Old answer 2: " + self._LONG_CONTENT),
            HumanMessage(content="Recent"),
            AIMessage(content="Recent reply"),
            HumanMessage(content="Current"),
            AIMessage(content="Current reply"),
        ]
        result = truncate_history(msgs, max_tokens=200)
        system_msgs = [m for m in result if isinstance(m, SystemMessage)]
        assert len(system_msgs) >= 1
        assert "Previous conversation" in system_msgs[0].content

    def test_tool_messages_in_recent_turns_preserved(self) -> None:
        msgs = [
            HumanMessage(content="Old question: " + self._LONG_CONTENT),
            AIMessage(content="Old reply: " + self._LONG_CONTENT),
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
        result = truncate_history(msgs, max_tokens=200)
        tool_msgs = [m for m in result if isinstance(m, ToolMessage)]
        assert len(tool_msgs) >= 1
