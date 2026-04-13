"""Context window budget management for copilot conversations."""

from __future__ import annotations

from dataclasses import dataclass

from langchain_core.messages import BaseMessage, SystemMessage


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
    """Rough token estimate: ~4 chars per token for mixed content."""
    return len(text) // 4


def _message_tokens(msg: BaseMessage) -> int:
    """Estimate tokens for a single message."""
    content = msg.content if isinstance(msg.content, str) else str(msg.content)
    tokens = _estimate_tokens(content)
    # Tool calls add overhead
    if hasattr(msg, "tool_calls") and msg.tool_calls:
        for tc in msg.tool_calls:
            tokens += _estimate_tokens(str(tc.get("args", {})))
    return tokens


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

    return [SystemMessage(content=summary_text), *recent_messages]
