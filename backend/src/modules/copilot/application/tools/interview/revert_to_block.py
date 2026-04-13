"""Tool to revert interview to a previous block."""

import json

from langchain_core.tools import tool


@tool
def revert_to_block(block_id: str) -> str:
    """Revert the interview to a previous block when the user wants to revisit it.

    Use this when the user says things like "volvamos a la promesa",
    "quiero cambiar lo de estrategia", "regresemos al pricing".

    Args:
        block_id: The ID of the block to revert to (e.g., "strategy", "promise").

    Returns:
        JSON confirming the revert with the new current block.

    """
    return json.dumps(
        {
            "text": "",
            "ui_action": {
                "type": "block_reverted",
                "block_id": block_id,
            },
        },
    )
