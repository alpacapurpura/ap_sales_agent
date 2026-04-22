"""Architecture fitness: MessageBlock union is exhaustive vs expected 11 types.

If a new block type is added to the union, EXPECTED_BLOCK_TYPES must be
updated here. This prevents silently shrinking the contract.
"""

from __future__ import annotations

# The canonical set of 11 block types (CONTRACT-MULTIMODAL §1)
EXPECTED_BLOCK_TYPES: frozenset[str] = frozenset(
    {
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
)


def test_block_types_tuple_is_exhaustive() -> None:
    """BLOCK_TYPES tuple in message_blocks.py exactly matches EXPECTED_BLOCK_TYPES."""
    from src.modules.copilot.domain.message_blocks import BLOCK_TYPES

    actual = frozenset(BLOCK_TYPES)
    missing = EXPECTED_BLOCK_TYPES - actual
    extra = actual - EXPECTED_BLOCK_TYPES

    assert not missing, (
        f"Block types missing from BLOCK_TYPES: {missing}. Add them to BLOCK_TYPES in message_blocks.py."
    )
    assert not extra, (
        f"Extra block types in BLOCK_TYPES not in expected set: {extra}. "
        "Update EXPECTED_BLOCK_TYPES in this test if you added a new block type "
        "(requires arch review per CONTRACT-MULTIMODAL §14.9)."
    )


def test_message_block_union_includes_all_types() -> None:
    """The MessageBlock discriminated union must accept all 11 block type literals."""
    from uuid import uuid4

    from pydantic import TypeAdapter

    from src.modules.copilot.domain.message_blocks import MessageBlock

    adapter = TypeAdapter(MessageBlock)

    # Minimal valid payloads for each type
    type_payloads: dict[str, dict] = {
        "text": {"type": "text", "id": str(uuid4()), "markdown": "hello"},
        "image": {
            "type": "image",
            "id": str(uuid4()),
            "asset_id": str(uuid4()),
            "url": "https://cdn.example.com/img.png",
            "mime": "image/png",
        },
        "audio": {
            "type": "audio",
            "id": str(uuid4()),
            "asset_id": str(uuid4()),
            "url": "https://cdn.example.com/voice.webm",
            "mime": "audio/webm",
            "transcript": "",
        },
        "video": {
            "type": "video",
            "id": str(uuid4()),
            "asset_id": str(uuid4()),
            "url": "https://cdn.example.com/clip.mp4",
            "mime": "video/mp4",
        },
        "document": {
            "type": "document",
            "id": str(uuid4()),
            "asset_id": str(uuid4()),
            "url": "https://cdn.example.com/doc.pdf",
            "mime": "application/pdf",
            "filename": "doc.pdf",
            "size_bytes": 1024,
        },
        "table": {
            "type": "table",
            "id": str(uuid4()),
            "columns": ["A"],
            "rows": [["1"]],
        },
        "code": {
            "type": "code",
            "id": str(uuid4()),
            "language": "python",
            "source": "print('hi')",
        },
        "citation": {
            "type": "citation",
            "id": str(uuid4()),
            "source": "Doc",
            "snippet": "text",
        },
        "quote_reply": {
            "type": "quote_reply",
            "id": str(uuid4()),
            "ref_message_id": str(uuid4()),
            "preview": "Hi there",
            "ref_author_role": "user",
        },
        "card": {
            "type": "card",
            "id": str(uuid4()),
            "card_kind": "proposal",
            "payload": {},
        },
        "tool_result": {
            "type": "tool_result",
            "id": str(uuid4()),
            "tool_name": "search_knowledge_base",
            "arguments": {},
            "result_preview": "Found results.",
            "ok": True,
        },
    }

    for block_type, payload in type_payloads.items():
        block = adapter.validate_python(payload)
        assert block.type == block_type, f"Type mismatch for block_type={block_type}"


def test_asset_blocks_have_asset_id_field() -> None:
    """All blocks that reference an Asset must expose an asset_id field."""
    from src.modules.copilot.domain.message_blocks import (
        AudioBlock,
        DocumentBlock,
        ImageBlock,
        VideoBlock,
    )

    asset_block_classes = [ImageBlock, AudioBlock, VideoBlock, DocumentBlock]
    for cls in asset_block_classes:
        assert "asset_id" in cls.model_fields, (
            f"{cls.__name__} must have an asset_id field (required for tenant-scoped asset validation)."
        )
