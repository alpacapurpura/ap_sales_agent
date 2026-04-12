"""Advance block tool — persists confirmed data and moves to next block."""

import json

from langchain_core.tools import tool


@tool
def advance_block(
    block_id: str,
    persisted_fields: list[str],
    next_block_id: str | None = None,
    next_block_label: str | None = None,
) -> str:
    """Persist the confirmed block data to the domain model and advance to next block.

    Invoke ONLY after user confirms a checkpoint. This triggers actual persistence to
    BrandSettings (or equivalent domain model). The frontend uses persisted=true to
    show green highlights.

    Args:
        block_id: The block that was confirmed.
        persisted_fields: List of field_paths that were persisted.
        next_block_id: ID of the next block (None if this was the last).
        next_block_label: Human label of next block.

    Returns:
        JSON with confirmation text and preview_update with persisted=true.
    """
    text = "¡Guardado!"
    if next_block_label:
        text += f" Pasemos a {next_block_label}."
    else:
        text += " Todos los bloques completados."

    return json.dumps(
        {
            "text": text,
            "ui_action": {
                "type": "preview_update",
                "persisted_fields": persisted_fields,
                "persisted": True,
            },
            "metadata": {
                "block_completed": block_id,
                "next_block": next_block_id,
            },
        }
    )
