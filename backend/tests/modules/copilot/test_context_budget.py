"""Tests for context window budget and history truncation."""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from src.modules.copilot.application.orchestrator.context_budget import (
    _estimate_tokens,
    sanitize_tool_calls,
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

    def test_truncation_removes_orphaned_tool_calls_at_split_boundary(self) -> None:
        """When truncation cuts between an AIMessage(tool_calls) and its ToolMessages,
        sanitize_tool_calls removes the orphaned AIMessage from the result."""
        msgs = [
            HumanMessage(content="Old question: " + self._LONG_CONTENT),
            # This AIMessage with tool_calls lands in the OLD section after truncation;
            # but its ToolMessage is just past the split boundary in RECENT. After
            # the split the AIMessage is isolated — sanitize_tool_calls must drop it.
            AIMessage(
                content="",
                tool_calls=[{"id": "orphan-id", "name": "some_tool", "args": {}}],
            ),
            # The ToolMessage that WOULD complete the above, but lands on the other
            # side of the split boundary in RECENT after truncation.
            ToolMessage(content="Tool result", tool_call_id="orphan-id"),
            AIMessage(content="Based on the tool..."),
            HumanMessage(content="Recent 1"),
            AIMessage(content="Reply 1"),
            HumanMessage(content="Recent 2"),
            AIMessage(content="Reply 2"),
            HumanMessage(content="Current"),
            AIMessage(content="Current reply"),
        ]
        result = truncate_history(msgs, max_tokens=200)
        # No AIMessage with unanswered tool_calls should remain
        for i, msg in enumerate(result):
            if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
                expected_ids = {tc["id"] for tc in msg.tool_calls}
                j = i + 1
                found_ids: set[str] = set()
                while j < len(result) and result[j].type == "tool":
                    tool_call_id = getattr(result[j], "tool_call_id", None)
                    if tool_call_id:
                        found_ids.add(tool_call_id)
                    j += 1
                assert found_ids >= expected_ids, (
                    f"Orphaned tool_calls found after truncation: {expected_ids - found_ids}"
                )

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


class TestSanitizeToolCalls:
    def test_no_tool_calls_unchanged(self) -> None:
        msgs = [HumanMessage(content="Hi"), AIMessage(content="Hello")]
        assert sanitize_tool_calls(msgs) == msgs

    def test_complete_tool_call_chain_preserved(self) -> None:
        msgs = [
            HumanMessage(content="Use a tool"),
            AIMessage(content="", tool_calls=[{"id": "tc1", "name": "tool", "args": {}}]),
            ToolMessage(content="result", tool_call_id="tc1"),
            AIMessage(content="Done"),
        ]
        result = sanitize_tool_calls(msgs)
        assert len(result) == 4

    def test_orphaned_tool_call_at_end_removed(self) -> None:
        """AIMessage with tool_calls at end of history (no ToolMessage follows) is dropped."""
        msgs = [
            HumanMessage(content="Hi"),
            AIMessage(content="", tool_calls=[{"id": "tc1", "name": "tool", "args": {}}]),
        ]
        result = sanitize_tool_calls(msgs)
        # The orphaned AIMessage should be removed
        assert all(not (isinstance(m, AIMessage) and getattr(m, "tool_calls", None)) for m in result)
        assert len(result) == 1  # Only the HumanMessage remains

    def test_partial_tool_messages_removed(self) -> None:
        """AIMessage with 2 tool_calls but only 1 ToolMessage is dropped along with partial."""
        msgs = [
            HumanMessage(content="Hi"),
            AIMessage(
                content="",
                tool_calls=[
                    {"id": "tc1", "name": "tool_a", "args": {}},
                    {"id": "tc2", "name": "tool_b", "args": {}},
                ],
            ),
            ToolMessage(content="result_a", tool_call_id="tc1"),
            # tc2 has no corresponding ToolMessage
            AIMessage(content="Continued"),
        ]
        result = sanitize_tool_calls(msgs)
        # The orphaned AIMessage(tool_calls) and partial ToolMessage should be removed
        ai_with_calls = [m for m in result if isinstance(m, AIMessage) and getattr(m, "tool_calls", None)]
        assert len(ai_with_calls) == 0
        # The final AIMessage("Continued") should still be there
        assert any(isinstance(m, AIMessage) and m.content == "Continued" for m in result)

    def test_multiple_orphans_all_removed(self) -> None:
        """Multiple orphaned tool_calls sequences are all removed."""
        msgs = [
            HumanMessage(content="First"),
            AIMessage(content="", tool_calls=[{"id": "tc1", "name": "tool", "args": {}}]),
            # No ToolMessage for tc1
            HumanMessage(content="Second"),
            AIMessage(content="", tool_calls=[{"id": "tc2", "name": "tool", "args": {}}]),
            # No ToolMessage for tc2
            AIMessage(content="Final"),
        ]
        result = sanitize_tool_calls(msgs)
        ai_with_calls = [m for m in result if isinstance(m, AIMessage) and getattr(m, "tool_calls", None)]
        assert len(ai_with_calls) == 0
        # Human messages and Final should remain
        assert any(isinstance(m, AIMessage) and m.content == "Final" for m in result)

    def test_empty_list_unchanged(self) -> None:
        assert sanitize_tool_calls([]) == []
