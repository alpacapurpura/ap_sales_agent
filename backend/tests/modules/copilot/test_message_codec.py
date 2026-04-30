"""Tests for the message_codec read/write adapter.

RED phase: validates the v1↔v2 round-trip behavior of message_codec.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from src.modules.copilot.domain.message_blocks import TextBlock
from src.modules.copilot.infrastructure.repositories.message_codec import (
    _flatten_blocks,
    decode_message,
    encode_message,
)

# ── decode_message ────────────────────────────────────────────────────


def test_decode_message_v1_shape_creates_text_block() -> None:
    """Legacy v1 message (no id, no blocks) is decoded with synthesized TextBlock."""
    conv_id = uuid4()
    raw = {"role": "user", "content": "Hola copilot"}
    msg = decode_message(raw, conversation_id=conv_id)

    assert msg.conversation_id == conv_id
    assert msg.role == "user"
    assert msg.content == "Hola copilot"
    # blocks synthesized from content
    assert msg.blocks is not None
    assert len(msg.blocks) == 1
    assert isinstance(msg.blocks[0], TextBlock)
    assert msg.blocks[0].markdown == "Hola copilot"


def test_decode_message_v1_assigns_random_id() -> None:
    """v1 messages without id get a random UUID assigned."""
    raw = {"role": "assistant", "content": "Respuesta"}
    msg = decode_message(raw, conversation_id=uuid4())
    assert isinstance(msg.id, UUID)


def test_decode_message_v2_shape_preserves_id() -> None:
    """v2 message (has id) keeps the provided id."""
    message_id = uuid4()
    conv_id = uuid4()
    raw = {
        "id": str(message_id),
        "role": "assistant",
        "content": "Hola",
        "status": "sent",
        "created_at": "2026-04-21T12:00:00+00:00",
        "blocks": [
            {
                "type": "text",
                "id": str(uuid4()),
                "markdown": "Hola",
            }
        ],
    }
    msg = decode_message(raw, conversation_id=conv_id)

    assert msg.id == message_id
    assert msg.status == "sent"
    assert msg.blocks is not None
    assert len(msg.blocks) == 1


def test_decode_message_empty_content_fallback() -> None:
    """Message with empty content but blocks should flatten blocks to content."""
    conv_id = uuid4()
    block_id = str(uuid4())
    raw = {
        "id": str(uuid4()),
        "role": "assistant",
        "content": "",
        "status": "sent",
        "created_at": "2026-04-21T12:00:00+00:00",
        "blocks": [
            {"type": "text", "id": block_id, "markdown": "Auto-generated content"},
        ],
    }
    msg = decode_message(raw, conversation_id=conv_id)
    # content must be populated from blocks (invariant 2.2.1)
    assert msg.content == "Auto-generated content"


def test_decode_message_tool_role_preserved() -> None:
    """Tool-role messages keep tool_call_id and name."""
    raw = {
        "role": "tool",
        "content": "result",
        "tool_call_id": "call_123",
        "name": "search_knowledge_base",
    }
    msg = decode_message(raw, conversation_id=uuid4())
    assert msg.role == "tool"
    assert msg.tool_call_id == "call_123"
    assert msg.name == "search_knowledge_base"


# ── encode_message ────────────────────────────────────────────────────


def test_encode_message_produces_v2_shape() -> None:
    """Encoded message always has v2 fields (id, status, created_at, blocks)."""
    raw = {"role": "user", "content": "test"}
    msg = decode_message(raw, conversation_id=uuid4())
    encoded = encode_message(msg)

    assert "id" in encoded
    assert "role" in encoded
    assert "content" in encoded
    assert "status" in encoded
    assert "created_at" in encoded


def test_encode_decode_roundtrip() -> None:
    """Round-trip: decode → encode → re-decode produces equivalent message."""
    raw = {"role": "assistant", "content": "Hola mundo"}
    conv_id = uuid4()
    msg1 = decode_message(raw, conversation_id=conv_id)
    encoded = encode_message(msg1)
    msg2 = decode_message(encoded, conversation_id=conv_id)

    assert msg2.content == msg1.content
    assert msg2.role == msg1.role


# ── _flatten_blocks ───────────────────────────────────────────────────


def test_flatten_blocks_text() -> None:
    blocks = [{"type": "text", "id": str(uuid4()), "markdown": "Hello **world**"}]
    result = _flatten_blocks(blocks)
    assert result == "Hello **world**"


def test_flatten_blocks_audio_uses_transcript() -> None:
    blocks = [
        {
            "type": "audio",
            "id": str(uuid4()),
            "asset_id": str(uuid4()),
            "url": "https://cdn.example.com/voice.webm",
            "mime": "audio/webm",
            "transcript": "Buenos días",
        }
    ]
    result = _flatten_blocks(blocks)
    assert "Buenos días" in result


def test_flatten_blocks_citation() -> None:
    blocks = [
        {
            "type": "citation",
            "id": str(uuid4()),
            "source": "Doc: brand.md",
            "snippet": "Voz cálida",
        }
    ]
    result = _flatten_blocks(blocks)
    assert "Voz cálida" in result
    assert "Doc: brand.md" in result


def test_flatten_blocks_table() -> None:
    blocks = [
        {
            "type": "table",
            "id": str(uuid4()),
            "columns": ["A", "B"],
            "rows": [["1", "2"]],
        }
    ]
    result = _flatten_blocks(blocks)
    assert "A" in result
    assert "B" in result


def test_flatten_blocks_code() -> None:
    blocks = [
        {
            "type": "code",
            "id": str(uuid4()),
            "language": "python",
            "source": "print('hi')",
        }
    ]
    result = _flatten_blocks(blocks)
    assert "print('hi')" in result


def test_flatten_blocks_image_contributes_no_text() -> None:
    """image/video/document blocks contribute nothing to plain text."""
    blocks = [
        {
            "type": "image",
            "id": str(uuid4()),
            "asset_id": str(uuid4()),
            "url": "https://cdn.example.com/img.png",
            "mime": "image/png",
        }
    ]
    result = _flatten_blocks(blocks)
    assert result == ""


def test_flatten_blocks_quote_reply() -> None:
    blocks = [
        {
            "type": "quote_reply",
            "id": str(uuid4()),
            "ref_message_id": str(uuid4()),
            "preview": "Mensaje anterior",
            "ref_author_role": "assistant",
        }
    ]
    result = _flatten_blocks(blocks)
    assert "Mensaje anterior" in result


def test_flatten_blocks_none_returns_empty() -> None:
    assert _flatten_blocks(None) == ""


def test_flatten_blocks_empty_list_returns_empty() -> None:
    assert _flatten_blocks([]) == ""


def test_flatten_blocks_multiple_blocks_joined() -> None:
    blocks = [
        {"type": "text", "id": str(uuid4()), "markdown": "Parte uno"},
        {"type": "text", "id": str(uuid4()), "markdown": "Parte dos"},
    ]
    result = _flatten_blocks(blocks)
    assert "Parte uno" in result
    assert "Parte dos" in result


# ── legacy v1 sampled warning ─────────────────────────────────────────


def test_legacy_read_emits_sampled_warning() -> None:
    """Decoding 200 v1 messages should emit exactly 2 structlog warnings (sample rate 1/100).

    The counter is per-process (module-level) so we reset it before the test
    to guarantee deterministic sampling independent of test ordering.
    """
    import src.modules.copilot.infrastructure.repositories.message_codec as _codec_mod

    # Reset the per-process counter so sampling is deterministic
    _codec_mod._LEGACY_READ_COUNTER["count"] = 0

    conv_id = uuid4()

    from structlog.testing import capture_logs

    with capture_logs() as cap:
        for _ in range(200):
            decode_message({"role": "user", "content": "legacy message"}, conversation_id=conv_id)

    # Filter to only our specific warning event
    warnings = [
        entry
        for entry in cap
        if entry.get("event") == "copilot_message_legacy_v1_read" and entry.get("log_level") == "warning"
    ]
    # Sample rate 1/100 → 200 legacy reads → exactly 2 warnings (count=1 and count=101)
    assert len(warnings) == 2, f"Expected 2 sampled warnings for 200 v1 reads (rate 1/100), got {len(warnings)}"
    # Verify no PII in log: content should NOT appear in any warning
    for w in warnings:
        assert "legacy message" not in str(w), "PII (content) must not appear in warning log"
        assert "conversation_id" in w
        assert "sampled_count" in w
