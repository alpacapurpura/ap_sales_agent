"""Clarify tool — surfaces contradictions or ambiguities for user resolution."""

import json

from langchain_core.tools import tool


@tool
def clarify(items: list[dict]) -> str:
    """Present contradictions or ambiguities to the user for quick resolution.

    ONLY use when you detect a real contradiction or ambiguity. NOT for confirming data.
    Max 2 items per invocation. Each item should have 2-4 quick-resolution options.

    Args:
        items: List of ambiguous/contradictory items. Each has:
            - field_path: The field with the issue
            - issue: Brief description of the contradiction (1-2 sentences)
            - options: 2-4 quick resolution options (strings)

    Returns:
        JSON with brief visible text and a clarify_card ui_action.

    """
    capped_items = items[:2]

    return json.dumps(
        {
            "text": "Noté algo que quiero aclarar rápido:",
            "ui_action": {
                "type": "clarify_card",
                "items": capped_items,
            },
        },
    )
