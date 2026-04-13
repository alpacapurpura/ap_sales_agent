"""Offers 2-4 alternatives with recommendation when user is unsure."""

import json

from langchain_core.tools import tool


@tool
def offer_alternatives(
    field_path: str,
    question: str,
    alternatives: list[dict],
    allow_custom: bool = True,
) -> str:
    """Present 2-4 options with your expert recommendation when the user is unsure.

    Use this instead of plain text when offering choices. The frontend renders an interactive card.
    Exactly ONE alternative should have recommended=true.

    Args:
        field_path: The mapa_global field this selection will fill.
        question: Brief context for the user (1-2 sentences max).
        alternatives: 2-4 options. Each has:
            - id: Short identifier ("a", "b", "c")
            - title: Option name
            - description: 1-2 sentence explanation
            - recommended: Boolean (exactly one should be true)
            - recommendation_reason: Why you recommend this (only if recommended=true)
        allow_custom: Whether user can type a custom answer instead.

    Returns:
        JSON with empty text and an alternatives_card ui_action.

    """
    return json.dumps(
        {
            "text": "",
            "ui_action": {
                "type": "alternatives_card",
                "field_path": field_path,
                "question": question,
                "alternatives": alternatives,
                "allow_custom": allow_custom,
            },
        },
    )
