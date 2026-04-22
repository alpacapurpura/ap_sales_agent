"""Message read/write adapter for v1↔v2 backward-compatible persistence.

# [COPILOT-MESSAGE-CODEC] → docs/domains/copilot/message-blocks.md §3

Roles:
- decode_message: accepts both v1 (legacy role+content dict) and v2 shapes.
  When blocks are absent, synthesizes a TextBlock from content so downstream
  code always has a rich block representation when needed.
- encode_message: always emits v2 shape (id, role, content, blocks, status,
  created_at). New code paths MUST use this encoder.
- _flatten_blocks: converts a list of raw block dicts to plain-text for the
  content field (invariant 2.2.1: content is never null).

See CONTRACT-MULTIMODAL §3.3 and §3.4 for the full specification.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from src.modules.copilot.domain.message import Message
from src.modules.copilot.domain.message_blocks import TextBlock
from src.shared.domain.datetime_utils import utc_now


def decode_message(raw: dict, *, conversation_id: UUID) -> Message:
    """Read-side adapter. Accepts both v1 (legacy) and v2 shapes.

    v1 shape: {role, content, tool_calls?, tool_call_id?, name?}
    v2 shape: {id, role, content, blocks?, status, created_at, ...}

    When blocks missing but content present, synthesizes a single TextBlock
    from content so downstream code always sees blocks if opts into v2 rendering.
    When content missing but blocks present, flattens blocks to content.
    """
    mid = UUID(raw["id"]) if "id" in raw else uuid4()
    role = raw.get("role", "assistant")
    raw_content = raw.get("content") or ""
    blocks_raw = raw.get("blocks")
    status = raw.get("status", "sent")
    created = raw.get("created_at")

    if isinstance(created, str):
        created_dt: datetime = datetime.fromisoformat(created)
    else:
        created_dt = utc_now()

    # Determine content and synthesize blocks
    if blocks_raw is not None:
        # v2 shape: blocks present; compute content from blocks if content is empty
        content = raw_content or _flatten_blocks(blocks_raw)
        blocks = blocks_raw  # Pydantic validates via Message.model_validate
    elif raw_content:
        # v1 shape: synthesize a TextBlock from legacy content
        content = raw_content
        blocks = [TextBlock(id=uuid4(), markdown=raw_content)]
    else:
        content = ""
        blocks = None

    return Message.model_validate(
        {
            "id": mid,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "blocks": blocks,
            "status": status,
            "created_at": created_dt,
            "tool_calls": raw.get("tool_calls"),
            "tool_call_id": raw.get("tool_call_id"),
            "name": raw.get("name"),
            "tokens_used": raw.get("tokens_used"),
            "metadata": raw.get("metadata"),
        },
    )


def encode_message(msg: Message) -> dict:
    """Write-side adapter. Always emits v2 shape.

    New messages ALWAYS carry blocks[]. Legacy code paths that persisted via
    simple `role+content` dicts must be migrated to this encoder before cleanup.
    None fields are excluded to keep the JSONB compact.
    """
    return msg.model_dump(mode="json", exclude_none=True, by_alias=False)


def _flatten_text(b: dict) -> str:
    return b.get("markdown", "")


def _flatten_audio(b: dict) -> str:
    return b.get("transcript", "")


def _flatten_citation(b: dict) -> str:
    snippet = b.get("snippet", "")
    source = b.get("source", "")
    rendered = f'"{snippet}" — {source}'
    return rendered if rendered.strip() else ""


def _flatten_table(b: dict) -> str:
    cols = b.get("columns", [])
    rows = b.get("rows", [])
    if not cols:
        return ""
    header = " | ".join(cols)
    rows_text = "\n".join(" | ".join(r) for r in rows)
    return f"{header}\n{rows_text}" if rows_text else header


def _flatten_code(b: dict) -> str:
    lang = b.get("language", "")
    source = b.get("source", "")
    return f"```{lang}\n{source}\n```" if source else ""


def _flatten_quote_reply(b: dict) -> str:
    preview = b.get("preview", "")
    return f"> {preview}" if preview else ""


# Dispatch table for block types that yield plain text.
# Block types not listed (image, video, document, card, tool_result) → silently skipped.
_FLATTEN_HANDLERS: dict[str, object] = {
    "text": _flatten_text,
    "audio": _flatten_audio,
    "citation": _flatten_citation,
    "table": _flatten_table,
    "code": _flatten_code,
    "quote_reply": _flatten_quote_reply,
}


def _flatten_blocks(blocks: list[dict] | None) -> str:
    """Convert a list of raw block dicts to plain-text string.

    Used to populate `content` (invariant 2.2.1: content never null).
    Channels without block support (WA, email) use `content` as their payload.

    Block types that contribute to plain text:
    - text → markdown field
    - audio → transcript field
    - citation → snippet + source
    - table → columns and rows as pipe-separated text
    - code → fenced code block
    - quote_reply → blockquote prefix

    Block types that contribute nothing (image, video, document, card, tool_result)
    are silently skipped — they have no meaningful text equivalent for this purpose.
    """
    if not blocks:
        return ""
    parts: list[str] = []
    for b in blocks:
        handler = _FLATTEN_HANDLERS.get(b.get("type", ""))  # type: ignore[arg-type]
        if handler is not None:
            text = handler(b)  # type: ignore[operator]
            if text:
                parts.append(text)
    return "\n\n".join(parts)


__all__ = ["_flatten_blocks", "decode_message", "encode_message"]
