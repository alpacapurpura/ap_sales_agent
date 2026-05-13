"""Tests for the canonical MessageBlock domain types.

RED phase: these tests define the contract. They fail until the
implementation is created in src/modules/copilot/domain/message_blocks.py.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from luana_core_copilot.domain.message_blocks import (
    BLOCK_TYPES,
    AudioBlock,
    CardBlock,
    CitationBlock,
    CodeBlock,
    DocumentBlock,
    ImageBlock,
    MessageBlock,
    QuoteReplyBlock,
    TableBlock,
    TextBlock,
    ToolResultBlock,
    VideoBlock,
)

# ── BLOCK_TYPES tuple ─────────────────────────────────────────────────


def test_block_types_tuple_has_all_11_types() -> None:
    """BLOCK_TYPES must enumerate all 11 canonical types."""
    assert len(BLOCK_TYPES) == 11
    expected = {
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
    }
    assert set(BLOCK_TYPES) == expected


# ── TextBlock ─────────────────────────────────────────────────────────


def test_text_block_creates_correctly() -> None:
    """TextBlock requires id and markdown."""
    block = TextBlock(id=uuid4(), markdown="Hello **world**")
    assert block.type == "text"
    assert block.markdown == "Hello **world**"


def test_text_block_rejects_extra_fields() -> None:
    """Extra fields are forbidden (extra='forbid')."""
    with pytest.raises(ValidationError):
        TextBlock(id=uuid4(), markdown="hi", unknown_field="x")  # type: ignore[call-arg]


# ── ImageBlock ────────────────────────────────────────────────────────


def test_image_block_creates_correctly() -> None:
    asset_id = uuid4()
    block = ImageBlock(
        id=uuid4(),
        asset_id=asset_id,
        url="https://cdn.example.com/img.png",
        mime="image/png",
        alt="A test image",
    )
    assert block.type == "image"
    assert block.asset_id == asset_id
    assert block.mime == "image/png"
    assert block.alt == "A test image"
    # Optional fields default to None
    assert block.width is None
    assert block.height is None


# ── AudioBlock ────────────────────────────────────────────────────────


def test_audio_block_requires_transcript() -> None:
    """transcript is a required field (may be empty string, not None)."""
    block = AudioBlock(
        id=uuid4(),
        asset_id=uuid4(),
        url="https://cdn.example.com/voice.webm",
        mime="audio/webm",
        transcript="",
    )
    assert block.transcript == ""


def test_audio_block_optional_fields() -> None:
    block = AudioBlock(
        id=uuid4(),
        asset_id=uuid4(),
        url="https://cdn.example.com/voice.webm",
        mime="audio/webm",
        transcript="Hola mundo",
        duration_ms=3000,
        transcript_language="es",
    )
    assert block.duration_ms == 3000
    assert block.transcript_language == "es"
    assert block.waveform is None


# ── VideoBlock ────────────────────────────────────────────────────────


def test_video_block_creates_correctly() -> None:
    block = VideoBlock(
        id=uuid4(),
        asset_id=uuid4(),
        url="https://cdn.example.com/clip.mp4",
        mime="video/mp4",
    )
    assert block.type == "video"
    assert block.poster_url is None


# ── DocumentBlock ─────────────────────────────────────────────────────


def test_document_block_creates_correctly() -> None:
    block = DocumentBlock(
        id=uuid4(),
        asset_id=uuid4(),
        url="https://cdn.example.com/doc.pdf",
        mime="application/pdf",
        filename="report.pdf",
        size_bytes=1024,
    )
    assert block.type == "document"
    assert block.page_count is None
    assert block.preview_url is None


# ── TableBlock ────────────────────────────────────────────────────────


def test_table_block_creates_correctly() -> None:
    block = TableBlock(
        id=uuid4(),
        columns=["Name", "Age"],
        rows=[["Alice", "30"], ["Bob", "25"]],
    )
    assert block.type == "table"
    assert len(block.columns) == 2


# ── CodeBlock ─────────────────────────────────────────────────────────


def test_code_block_creates_correctly() -> None:
    block = CodeBlock(
        id=uuid4(),
        language="python",
        source="print('hello')",
    )
    assert block.type == "code"
    assert block.filename is None


# ── CitationBlock ─────────────────────────────────────────────────────


def test_citation_block_snippet_max_500_chars() -> None:
    """CitationBlock.snippet must be <= 500 chars."""
    long_snippet = "x" * 501
    with pytest.raises(ValidationError):
        CitationBlock(
            id=uuid4(),
            source="Doc: test.md",
            snippet=long_snippet,
        )


def test_citation_block_exact_500_chars_ok() -> None:
    block = CitationBlock(
        id=uuid4(),
        source="Doc: test.md",
        snippet="x" * 500,
    )
    assert len(block.snippet) == 500


def test_citation_block_optional_fields() -> None:
    block = CitationBlock(
        id=uuid4(),
        source="Doc: brand-book.md",
        snippet="La voz de la marca es cálida.",
        score=0.87,
    )
    assert block.score == pytest.approx(0.87)
    assert block.url is None


# ── QuoteReplyBlock ───────────────────────────────────────────────────


def test_quote_reply_block_preview_max_140_chars() -> None:
    """preview must be <= 140 chars."""
    long_preview = "a" * 141
    with pytest.raises(ValidationError):
        QuoteReplyBlock(
            id=uuid4(),
            ref_message_id=uuid4(),
            preview=long_preview,
            ref_author_role="user",
        )


def test_quote_reply_block_creates_correctly() -> None:
    block = QuoteReplyBlock(
        id=uuid4(),
        ref_message_id=uuid4(),
        preview="Hola, ¿cómo puedo ayudarte?",
        ref_author_role="assistant",
    )
    assert block.type == "quote_reply"


def test_quote_reply_block_invalid_role_rejected() -> None:
    with pytest.raises(ValidationError):
        QuoteReplyBlock(
            id=uuid4(),
            ref_message_id=uuid4(),
            preview="hi",
            ref_author_role="admin",  # type: ignore[arg-type]
        )


# ── CardBlock ─────────────────────────────────────────────────────────


def test_card_block_creates_correctly() -> None:
    block = CardBlock(
        id=uuid4(),
        card_kind="proposal",
        payload={"title": "Propuesta A", "fields": []},
    )
    assert block.type == "card"
    assert block.status is None


def test_card_block_invalid_kind_rejected() -> None:
    with pytest.raises(ValidationError):
        CardBlock(
            id=uuid4(),
            card_kind="unknown_kind",  # type: ignore[arg-type]
            payload={},
        )


# ── ToolResultBlock ───────────────────────────────────────────────────


def test_tool_result_block_creates_correctly() -> None:
    block = ToolResultBlock(
        id=uuid4(),
        tool_name="search_knowledge_base",
        arguments={"query": "brand colors"},
        result_preview="Found 3 results.",
        ok=True,
    )
    assert block.type == "tool_result"
    assert block.ok is True


# ── MessageBlock discriminated union ──────────────────────────────────


def test_message_block_discriminated_union_text() -> None:
    """MessageBlock union resolves TextBlock via type discriminator."""
    from pydantic import TypeAdapter

    adapter = TypeAdapter(MessageBlock)
    block = adapter.validate_python({"type": "text", "id": str(uuid4()), "markdown": "hi"})
    assert isinstance(block, TextBlock)


def test_message_block_discriminated_union_citation() -> None:
    from pydantic import TypeAdapter

    adapter = TypeAdapter(MessageBlock)
    raw = {
        "type": "citation",
        "id": str(uuid4()),
        "source": "doc.md",
        "snippet": "relevant text",
    }
    block = adapter.validate_python(raw)
    assert isinstance(block, CitationBlock)


def test_message_block_discriminated_union_unknown_type_raises() -> None:
    from pydantic import TypeAdapter

    adapter = TypeAdapter(MessageBlock)
    with pytest.raises(ValidationError):
        adapter.validate_python({"type": "unknown_block_type", "id": str(uuid4())})


# ── Asset blocks have asset_id field ─────────────────────────────────


@pytest.mark.parametrize(
    "block_class",
    [ImageBlock, AudioBlock, VideoBlock, DocumentBlock],
)
def test_asset_blocks_have_asset_id_field(block_class: type) -> None:
    """All asset-referencing blocks must have an asset_id field."""
    assert "asset_id" in block_class.model_fields
