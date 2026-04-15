"""Context window budget management for copilot conversations."""

from __future__ import annotations

from dataclasses import dataclass

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage

# Try to use tiktoken for accurate token counting (Claude uses ~cl100k_base tokens).
# Fall back to the char-based heuristic if tiktoken is not available.
try:
    import tiktoken as _tiktoken

    _ENCODING = _tiktoken.get_encoding("cl100k_base")

    def _count_tokens(text: str) -> int:
        return len(_ENCODING.encode(text))

except ImportError:  # pragma: no cover — only executed when tiktoken is absent

    def _count_tokens(text: str) -> int:  # type: ignore[misc]  # Function redefinition in except block (tiktoken fallback)
        # Conservative heuristic: ~2 chars per token (safer than the old //4).
        # Claude tokenises more aggressively than GPT-2 on mixed content.
        return max(1, len(text) // 2)


@dataclass(frozen=True)
class ContextBudget:
    """Token budget allocation for copilot context window."""

    system_prompt: int = 5_000
    entity_snapshot: int = 5_000
    interview_context: int = 3_000
    history: int = 15_000
    tool_results_per_turn: int = 2_000
    reserved_response: int = 2_000


# Default budget instance
DEFAULT_BUDGET = ContextBudget()

# Number of recent turns to always preserve (1 turn = 1 user + 1 assistant)
PRESERVE_LAST_TURNS = 3


def _estimate_tokens(text: str) -> int:
    """Token estimate using tiktoken (cl100k_base) when available.

    Falls back to a conservative heuristic of len(text) // 2 (not the old
    // 4) when tiktoken is absent. The old //4 underestimated Claude's
    tokenisation by ~2x, risking context-window overflows.
    """
    return _count_tokens(text)


def _message_tokens(msg: BaseMessage) -> int:
    """Estimate tokens for a single message."""
    content = msg.content if isinstance(msg.content, str) else str(msg.content)
    tokens = _estimate_tokens(content)
    # Tool calls add overhead
    if hasattr(msg, "tool_calls") and msg.tool_calls:
        for tc in msg.tool_calls:
            tokens += _estimate_tokens(str(tc.get("args", {})))
    return tokens


def sanitize_tool_calls(messages: list[BaseMessage]) -> list[BaseMessage]:
    """Remove orphaned tool_calls from the message history.

    An AIMessage with tool_calls is "orphaned" when the immediately following
    messages do not include ToolMessages for ALL of its tool_call_ids.
    OpenAI returns 400 in this case: "An assistant message with 'tool_calls'
    must be followed by tool messages responding to each 'tool_call_id'".

    This can happen when:
    - The conversation was persisted mid-graph (tool executor didn't finish)
    - truncate_history() cuts between an AIMessage and its ToolMessages
    - DB deserialization loses some messages

    Strategy: drop any AIMessage-with-tool_calls that is not followed by a
    complete set of ToolMessages, along with any partial ToolMessages after it.
    """
    result: list[BaseMessage] = list(messages)
    i = 0
    while i < len(result):
        msg = result[i]
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            expected_ids: set[str] = {tc["id"] for tc in msg.tool_calls}
            # Collect ToolMessages that immediately follow
            j = i + 1
            found_ids: set[str] = set()
            while j < len(result) and result[j].type == "tool":
                tool_call_id = getattr(result[j], "tool_call_id", None)
                if tool_call_id:
                    found_ids.add(tool_call_id)
                j += 1
            if found_ids < expected_ids:
                # Drop the orphaned AIMessage + any partial ToolMessages
                result = result[:i] + result[j:]
                continue  # Re-check from same index after deletion
        i += 1
    return result


def truncate_history(
    messages: list[BaseMessage],
    max_tokens: int = DEFAULT_BUDGET.history,
) -> list[BaseMessage]:
    """Truncate conversation history to fit within token budget.

    Strategy:
    - Always preserve the last PRESERVE_LAST_TURNS turns intact
    - If total exceeds max_tokens, summarize older messages into a SystemMessage
    - Never discard tool messages that belong to preserved turns
    """
    if not messages:
        return messages

    # Sanitize first: remove orphaned tool_calls that could cause OpenAI 400s
    # (e.g. from partial persistence or prior truncation at a bad boundary).
    messages = sanitize_tool_calls(messages)

    total = sum(_message_tokens(m) for m in messages)
    if total <= max_tokens:
        return messages

    # Preserve last N turns (counting from the end)
    # A "turn" boundary is a HumanMessage
    preserve_count = 0
    turns_found = 0
    for i in range(len(messages) - 1, -1, -1):
        preserve_count += 1
        if messages[i].type == "human":
            turns_found += 1
            if turns_found >= PRESERVE_LAST_TURNS:
                break

    split_idx = len(messages) - preserve_count
    if split_idx <= 0:
        return messages  # All messages are in preserved turns

    old_messages = messages[:split_idx]
    recent_messages = messages[split_idx:]

    # Build summary of old messages
    topics = []
    for msg in old_messages:
        content = msg.content if isinstance(msg.content, str) else ""
        if content and msg.type in ("human", "ai"):
            preview = content[:80].replace("\n", " ").strip()
            if preview:
                topics.append(preview)

    summary_text = "Previous conversation summary (older messages truncated for context):\n" + "\n".join(
        f"- {t}" for t in topics[:10]
    )

    truncated = [SystemMessage(content=summary_text), *recent_messages]
    # Sanitize again: the split boundary may have landed between an AIMessage
    # with tool_calls and its ToolMessages, introducing a new orphan.
    return sanitize_tool_calls(truncated)
