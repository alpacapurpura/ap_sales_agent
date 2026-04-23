"""Tool-output → MessageBlock adapters, registered at import time.

SSoT for every mapping ``tool_name → list[MessageBlock]``. Adding a new tool
that needs to emit typed blocks = write the handler here and call
``register_block_handler``. The orchestrator reads via ``tool_result_to_blocks``
and never needs to know which tools produce which block kinds.

Inverts the prior hardcoded ``_TOOL_BLOCK_HANDLERS`` dict that lived in
``orchestrator/chat.py`` — that required editing the orchestrator every time
a new block-emitting tool landed, which violated open/closed.

[COPILOT-CITATION-BLOCK] → docs/domains/copilot/message-blocks.md §citation
[COPILOT-OUTBOUND-ASSETS] → docs/domains/copilot/outbound-assets.md
"""

from __future__ import annotations

import json
from collections.abc import Callable
from uuid import uuid4

import structlog

logger = structlog.get_logger()

BlockHandler = Callable[[object], list[dict] | None]

_REGISTRY: dict[str, BlockHandler] = {}


def register_block_handler(tool_name: str, handler: BlockHandler) -> None:
    """Register a tool-output → blocks handler.

    Raises:
        ValueError: if ``tool_name`` already has a handler registered. Duplicate
            registration is treated as a bug — renaming the tool or sharing the
            same handler object is fine; registering two different handlers is
            not.

    """
    existing = _REGISTRY.get(tool_name)
    if existing is not None and existing is not handler:
        msg = f"block handler for {tool_name!r} already registered"
        raise ValueError(msg)
    _REGISTRY[tool_name] = handler


def get_block_handler(tool_name: str) -> BlockHandler | None:
    """Return the registered handler for ``tool_name`` or ``None``."""
    return _REGISTRY.get(tool_name)


def tool_result_to_blocks(tool_name: str, result: object) -> list[dict] | None:
    """Convert a tool result into a list of MessageBlock dicts.

    Returns ``None`` when the tool is not mapped (caller emits only the legacy
    ``tool_result`` event). Returns an empty list when the tool output is a
    valid empty collection.
    """
    handler = _REGISTRY.get(tool_name)
    if handler is None:
        return None

    result_str: str = result if isinstance(result, str) else json.dumps(result)
    try:
        parsed = json.loads(result_str)
    except (json.JSONDecodeError, ValueError):
        logger.debug("tool_result_to_block_invalid_json", tool_name=tool_name)
        return None

    return handler(parsed)


# ── Handlers ──────────────────────────────────────────────────────────────────


def _kb_to_citations(parsed: object) -> list[dict] | None:
    """Convert search_knowledge_base result to CitationBlock list."""
    if not isinstance(parsed, list):
        return None
    blocks: list[dict] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        blocks.append(
            {
                "id": str(uuid4()),
                "type": "citation",
                "source": str(item.get("source") or item.get("metadata", {}).get("title") or ""),
                "snippet": str(item.get("snippet") or item.get("content") or "")[:500],
                "score": item.get("score"),
                "url": item.get("url") or item.get("metadata", {}).get("url"),
            }
        )
    return blocks


def _asset_item_to_block(item: dict) -> dict | None:
    """Convert one asset dict to a typed block dict. Returns None for unknown kinds."""
    kind = str(item.get("kind", "")).lower()
    asset_id = str(item.get("asset_id", ""))
    public_url = str(item.get("public_url", ""))
    mime = str(item.get("mime", "application/octet-stream"))
    filename = str(item.get("filename", ""))

    if kind == "image":
        return {
            "id": str(uuid4()),
            "type": "image",
            "asset_id": asset_id,
            "url": public_url,
            "mime": mime,
            "alt": item.get("description") or filename or None,
        }
    if kind == "audio":
        return {
            "id": str(uuid4()),
            "type": "audio",
            "asset_id": asset_id,
            "url": public_url,
            "mime": mime,
            "transcript": "",
        }
    if kind == "video":
        return {
            "id": str(uuid4()),
            "type": "video",
            "asset_id": asset_id,
            "url": public_url,
            "mime": mime,
        }
    if kind == "document":
        return {
            "id": str(uuid4()),
            "type": "document",
            "asset_id": asset_id,
            "url": public_url,
            "mime": mime,
            "filename": filename,
            "size_bytes": int(item.get("size_bytes", 0)),
        }
    return None


def _assets_to_media_blocks(parsed: object) -> list[dict] | None:
    """Convert search_assets / get_asset result to asset block list."""
    if isinstance(parsed, dict):
        if "error" in parsed:
            return None
        items = [parsed]
    elif isinstance(parsed, list):
        items = [i for i in parsed if isinstance(i, dict) and "error" not in i]
    else:
        return None

    result_blocks: list[dict] = []
    for item in items:
        block = _asset_item_to_block(item)
        if block is not None:
            result_blocks.append(block)
    return result_blocks


# ── Registration ──────────────────────────────────────────────────────────────

register_block_handler("search_knowledge_base", _kb_to_citations)
register_block_handler("search_assets", _assets_to_media_blocks)
register_block_handler("get_asset", _assets_to_media_blocks)


__all__ = [
    "BlockHandler",
    "get_block_handler",
    "register_block_handler",
    "tool_result_to_blocks",
]
