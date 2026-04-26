"""Canonical Message Block schema for the Copilot multimodal content system.

# [COPILOT-CANONICAL-BLOCKS] → docs/domains/copilot/message-blocks.md

All 11 block types form a discriminated union (MessageBlock) that is:
- Channel-agnostic: WhatsApp, Telegram, email adapters translate to native APIs.
- Backward-compatible: existing plain-text messages are synthesized into TextBlock.
- Pydantic v2 validated at write time.

Adding a new block type requires:
1. Add XxxBlock(_BlockBase) with `type: Literal["xxx"]` discriminator.
2. Append to MessageBlock union and BLOCK_TYPES tuple.
3. Update message_codec._flatten_blocks if it contributes to plain text.
4. Mirror in frontend types/message-blocks.ts.
5. Update BLOCK_TYPE_METADATA in architecture test.

See docs/domains/copilot/message-blocks.md for the full checklist.
"""

from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator


class _BlockBase(BaseModel):
    """Common envelope for all block types.

    Every block carries a stable client-generated UUID that persists
    across streaming update events (block_start → block_delta → block_end).
    """

    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: UUID  # stable across streaming updates; never null


# ── 1. text (markdown) ────────────────────────────────────────────────────────


class TextBlock(_BlockBase):
    """Markdown prose block — the most common type.

    Supports streaming via block_delta events (§6 of the SSE protocol).
    Frontend renders with a markdown renderer (GFM subset).
    """

    type: Literal["text"] = "text"
    markdown: str  # raw markdown; UTF-8


# ── 2. image ─────────────────────────────────────────────────────────────────


class ImageBlock(_BlockBase):
    """Reference to an image asset already stored in the Assets module.

    asset_id MUST exist in the assets table for the same tenant.
    url is a snapshot of Asset.public_url at emit time.
    """

    type: Literal["image"] = "image"
    asset_id: UUID  # MUST exist in assets table, same tenant
    url: HttpUrl  # snapshot of Asset.public_url at emit time
    mime: str  # e.g. "image/png"
    width: int | None = None
    height: int | None = None
    alt: str | None = None  # accessibility + LLM context


# ── 3. audio ─────────────────────────────────────────────────────────────────


class AudioBlock(_BlockBase):
    """Voice note or audio file.

    Dual-mode is mandatory: url (playback) + transcript (accessibility/text).
    transcript may be an empty string when STT is unavailable; it is never None.
    See CONTRACT-MULTIMODAL §9 for the combined upload+transcribe flow.
    """

    type: Literal["audio"] = "audio"
    asset_id: UUID
    url: HttpUrl
    mime: str  # "audio/webm", "audio/mpeg", etc.
    duration_ms: int | None = None
    transcript: str  # ALWAYS populated; empty string if STT failed
    transcript_language: str | None = None  # ISO 639-1 e.g. "es"
    waveform: list[float] | None = None  # optional 0..1 normalized samples for UI


# ── 4. video ─────────────────────────────────────────────────────────────────


class VideoBlock(_BlockBase):
    """Reference to a video asset. poster_url is optional thumbnail."""

    type: Literal["video"] = "video"
    asset_id: UUID
    url: HttpUrl
    mime: str
    width: int | None = None
    height: int | None = None
    duration_ms: int | None = None
    poster_url: HttpUrl | None = None  # thumbnail


# ── 5. document ───────────────────────────────────────────────────────────────


class DocumentBlock(_BlockBase):
    """Reference to a document asset (PDF, CSV, DOCX, etc.)."""

    type: Literal["document"] = "document"
    asset_id: UUID
    url: HttpUrl
    mime: str  # "application/pdf", "text/csv", etc.
    filename: str
    size_bytes: int
    page_count: int | None = None  # PDFs
    preview_url: HttpUrl | None = None  # optional first-page thumbnail


# ── 6. table ─────────────────────────────────────────────────────────────────


class TableBlock(_BlockBase):
    """Structured tabular data. Every row must have the same length as columns."""

    type: Literal["table"] = "table"
    caption: str | None = None
    columns: list[str]  # header labels
    rows: list[list[str]]  # rows[i][j] is a string cell

    @model_validator(mode="after")
    def validate_row_lengths(self) -> TableBlock:
        """Enforce that every row has the same number of cells as columns."""
        for i, row in enumerate(self.rows):
            if len(row) != len(self.columns):
                msg = f"Row {i} has {len(row)} cells but {len(self.columns)} columns are defined."
                raise ValueError(msg)
        return self


# ── 7. code ───────────────────────────────────────────────────────────────────


class CodeBlock(_BlockBase):
    """Code snippet with syntax highlighting hint."""

    type: Literal["code"] = "code"
    language: str  # "python", "sql", "text", etc.
    source: str
    filename: str | None = None  # optional file hint


# ── 8. citation ───────────────────────────────────────────────────────────────


class CitationBlock(_BlockBase):
    """RAG / knowledge-base source attribution.

    # [COPILOT-CITATION-BLOCK] → docs/domains/copilot/message-blocks.md

    Emitted by the search_knowledge_base tool interceptor in the orchestrator.
    snippet is capped at 500 chars (enforced by field validator).
    """

    type: Literal["citation"] = "citation"
    source: str  # human-readable label e.g. "Doc: onboarding-playbook.md"
    snippet: str  # quoted passage
    url: HttpUrl | None = None  # optional deep link
    score: float | None = None  # retrieval score 0..1

    @field_validator("snippet")
    @classmethod
    def snippet_max_500(cls, v: str) -> str:
        """Snippet must not exceed 500 characters."""
        if len(v) > 500:
            msg = f"snippet exceeds 500 chars (got {len(v)})."
            raise ValueError(msg)
        return v


# ── 9. quote_reply ────────────────────────────────────────────────────────────


class QuoteReplyBlock(_BlockBase):
    """Reply pointing to a previous message in the same conversation.

    # [COPILOT-QUOTE-REPLY] → docs/domains/copilot/message-blocks.md

    preview is capped at 140 chars (enforced by field validator).
    Transport mapping: WA uses context.message_id; Telegram uses reply_to_message_id.
    """

    type: Literal["quote_reply"] = "quote_reply"
    ref_message_id: UUID  # target message in same conversation
    preview: str  # ≤140 chars, truncated by composer
    ref_author_role: Literal["user", "assistant"]

    @field_validator("preview")
    @classmethod
    def preview_max_140(cls, v: str) -> str:
        """Preview must not exceed 140 characters."""
        if len(v) > 140:
            msg = f"preview exceeds 140 chars (got {len(v)})."
            raise ValueError(msg)
        return v


# ── 10. card ─────────────────────────────────────────────────────────────────


class CardBlock(_BlockBase):
    """Thin wrapper around existing UI action cards.

    Wraps the existing UIAction card family (proposal, alternatives, etc.).
    card_kind determines the payload schema (open — typed per-kind in a future PR).
    """

    type: Literal["card"] = "card"
    card_kind: Literal[
        "proposal",
        "alternatives",
        "clarify",
        "checkpoint",
        "interview_complete",
        "metric_summary",
        "comparison",
        "checklist",
        "multi_option",
        "navigation",
        "extraction_summary",
        "inspiration_saved",
        "memory_pinned",
    ]
    payload: dict  # shape matches UIAction subset for card_kind
    status: Literal["pending", "resolved", "confirmed", "revising"] | None = None


# ── 11. tool_result ───────────────────────────────────────────────────────────


class ToolResultBlock(_BlockBase):
    """Transparent tool-call trace rendered compactly in UI.

    Never shown outside web (tool_result blocks are dropped by WA adapter).
    result_preview is capped at 500 chars by convention (not enforced at block level).
    """

    type: Literal["tool_result"] = "tool_result"
    tool_name: str
    arguments: dict
    result_preview: str  # truncated human-readable summary ≤500 chars
    ok: bool


# ── Discriminated union ───────────────────────────────────────────────────────

MessageBlock = Annotated[
    TextBlock
    | ImageBlock
    | AudioBlock
    | VideoBlock
    | DocumentBlock
    | TableBlock
    | CodeBlock
    | CitationBlock
    | QuoteReplyBlock
    | CardBlock
    | ToolResultBlock,
    Field(discriminator="type"),
]
"""Canonical discriminated union of all 11 block types.

Pydantic v2 resolves the concrete class via the `type` literal discriminator.
Use `TypeAdapter(MessageBlock).validate_python(raw_dict)` to parse from JSON.
"""


BLOCK_TYPES: tuple[str, ...] = (
    "text",
    "image",
    "audio",
    "video",
    "document",
    "table",
    "code",
    "citation",
    "quote_reply",
    "card",
    "tool_result",
)
"""Ordered tuple of all canonical block type strings.

Used by architecture tests to verify exhaustiveness and by the SSE producer
to validate block_start events.
"""


__all__ = [
    "BLOCK_TYPES",
    "AudioBlock",
    "CardBlock",
    "CitationBlock",
    "CodeBlock",
    "DocumentBlock",
    "ImageBlock",
    "MessageBlock",
    "QuoteReplyBlock",
    "TableBlock",
    "TextBlock",
    "ToolResultBlock",
    "VideoBlock",
]
