"""Silent extraction tool — captures structured data from user messages."""

import json

from langchain_core.tools import tool


@tool
def extract_structured(session_id: str, extractions: list[dict]) -> str:
    """Extract structured data from the user's last message into the mapa_global.

    INVOKE THIS ON EVERY TURN. It is silent — the user does not see any text output.
    Use field_path with dot notation to place data in the correct section regardless of current block.

    Args:
        session_id: The interview session UUID.
        extractions: List of extracted data items. Each has:
            - field_path: Dot-notation path (e.g., "story.origin_story", "positioning.competitors")
            - value: The extracted value (string, list, or dict) — redacted with expert frameworks
            - confidence: Float 0.0-1.0. Below 0.8 means pending clarification.
            - source: "user_explicit" | "inferred" | "recommended"

    Returns:
        JSON with empty text and a preview_update ui_action containing the delta.
    """
    delta = {}
    confidence_map = {}

    for item in extractions:
        field_path = item.get("field_path", "")
        value = item.get("value")
        confidence = item.get("confidence", 1.0)

        if not field_path or value is None:
            continue

        delta[field_path] = value
        if confidence < 0.8:
            confidence_map[field_path] = confidence

    return json.dumps(
        {
            "text": "",
            "ui_action": {
                "type": "preview_update",
                "session_id": session_id,
                "delta": delta,
                "confidence_map": confidence_map,
            },
        },
    )
