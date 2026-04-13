"""Checkpoint tool — presents block summary for user confirmation."""

import json

from langchain_core.tools import tool


@tool
def checkpoint(
    block_id: str,
    block_label: str,
    summary: dict,
    health_score: int,
    blocks_completed: int,
    blocks_total: int,
) -> str:
    """Present a compact summary of the current block for user confirmation.

    Use when block coverage > 80%. Keep summary brief — 1 line per field, not paragraphs.
    The user will either confirm (triggers advance_block) or ask to revise.

    Args:
        block_id: ID of the block being closed.
        block_label: Human-readable block name.
        summary: Dict of field_path to short value summary (max 60 chars each).
        health_score: Overall brand health percentage after this block.
        blocks_completed: Number of blocks completed (including this one).
        blocks_total: Total number of blocks.

    Returns:
        JSON with brief text and a checkpoint_card ui_action.

    """
    return json.dumps(
        {
            "text": f"Tengo lo que necesito de {block_label}. Mira cómo quedó:",
            "ui_action": {
                "type": "checkpoint_card",
                "block_id": block_id,
                "block_label": block_label,
                "summary": summary,
                "health_score": health_score,
                "blocks_progress": {
                    "completed": blocks_completed,
                    "total": blocks_total,
                },
            },
        },
    )
