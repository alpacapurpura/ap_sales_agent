"""Silent extraction tool — captures structured data from user messages."""

import json

from langchain_core.tools import tool

from src.modules.copilot.domain.schema_introspection import validate_field_path


@tool
def extract_structured(session_id: str, domain: str, extractions: list[dict]) -> str:
    """Extract structured data from the conversation into the mapa_global.

    INVOKE THIS ON EVERY TURN where the user provides factual information.
    This tool is SILENT — the user does not see any text output.

    CRITICAL: Extract data for ANY section, not just the current block.
    If the user mentions pricing while you are on the promise block,
    extract the pricing data here. The mapa_global is your global memory.
    Never let information pass uncaptured.

    Args:
        session_id: The interview session UUID.
        domain: The entity domain ("brand", "offer", "buyer_persona").
        extractions: List of extracted data items. Each has:
            - field_path: Dot-notation path (e.g., "strategy.offer_name",
              "pricing.total_amount", "program_details.total_sessions").
              Can be from ANY section regardless of current block.
            - value: The extracted value (string, list, or dict).
            - confidence: Float 0.0-1.0. Below 0.8 means pending clarification.
            - source: "user_explicit" | "inferred" | "recommended"

    Returns:
        JSON with empty text and a preview_update ui_action containing the delta.
        Includes skipped_fields if any field_paths were invalid.

    """
    delta = {}
    confidence_map = {}
    skipped: list[str] = []

    for item in extractions:
        field_path = item.get("field_path", "")
        value = item.get("value")
        confidence = item.get("confidence", 1.0)

        if not field_path or value is None:
            continue

        if not validate_field_path(domain, field_path):
            skipped.append(field_path)
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
                "skipped": skipped,
            },
        },
    )
