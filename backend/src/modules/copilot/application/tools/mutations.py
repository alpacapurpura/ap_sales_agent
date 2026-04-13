"""Mutation tools — allow the copilot to propose changes to form fields.

These tools emit proposal ui_actions that the frontend renders as
confirmation cards. The user must approve before any changes are applied.
"""

from langchain_core.tools import tool


@tool
def propose_field_updates(updates: list[dict]) -> dict:
    """Propose updates to form fields in the UI. The user must approve before saving.

    Args:
        updates: List of field updates, each with: field_id, new_value, reason

    Returns:
        A proposal payload that the frontend will render for confirmation.

    """
    validated = []
    for u in updates:
        if "field_id" not in u or "new_value" not in u:
            continue
        validated.append(
            {
                "field_id": u["field_id"],
                "new_value": u["new_value"],
                "reason": u.get("reason", ""),
            },
        )

    if not validated:
        return {
            "success": False,
            "message": "No se proporcionaron actualizaciones válidas. Cada una necesita field_id y new_value.",
        }

    return {
        "success": True,
        "ui_action": {
            "type": "proposal",
            "updates": validated,
        },
        "message": f"Propuesta de {len(validated)} cambio(s) enviada al usuario.",
    }


MUTATION_TOOLS = [propose_field_updates]
