"""Last-line-of-defense sanitizer for assistant text blocks.

The system prompt forbids JSON blocks in assistant responses. When the LLM
breaks that rule anyway, we strip the offending code fences before the
text reaches the user (SSE ``block_end``) and before it is persisted in
``copilot_conversations.messages``.

Rationale:
  - Tool payloads travel via ``ui_action`` cards — not assistant text.
  - Users should never see raw JSON; they see interactive cards instead.
  - Persisted JSON in messages bloats the context window and invites the
    next ReAct turn to regurgitate it again.
"""

from __future__ import annotations

import re

# ``` ```json {...} ``` `` or ``` ``` {...} ``` `` blocks with any whitespace/newlines.
_CODE_FENCE_JSON = re.compile(
    r"```(?:json|JSON)?\s*(\{[\s\S]*?\}|\[[\s\S]*?\])\s*```",
    re.MULTILINE,
)

# Bare ``` {...} ``` without a fence close (streamed/truncated leftover).
_BARE_BALANCED_OBJECT = re.compile(
    r"(?<![A-Za-z0-9_])\{[\s\S]{40,}?\}(?![A-Za-z0-9_])",
)


def sanitize_assistant_text(text: str) -> str:
    """Remove JSON code fences and dangling raw objects from an assistant block.

    Conservative: only drops fenced code blocks whose content parses as a
    JSON object/array, plus bare top-level ``{…}`` blobs over ~40 chars
    that clearly aren't part of natural prose.

    Keeps inline short ``{x}`` templates (under 40 chars) and any markdown
    that isn't JSON-shaped.
    """
    if not text:
        return text

    cleaned = _CODE_FENCE_JSON.sub("", text)
    cleaned = _BARE_BALANCED_OBJECT.sub("", cleaned)

    # Collapse 3+ consecutive blank lines left by the substitutions.
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


__all__ = ["sanitize_assistant_text"]
