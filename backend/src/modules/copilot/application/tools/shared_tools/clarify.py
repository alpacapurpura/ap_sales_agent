"""Clarify tool — generic ask-the-user primitive for the copilot.

Historically lived under ``tools/interview/`` and was scoped to the Interview
Engine. Promoted to the shared tool group so the orchestrator can use it
before dispatching **any** tool when the user intent is ambiguous — for
example, before calling ``extract_from_url`` to ask whether the user wants a
full brand extraction or an update to the currently visible section.

Frontend mapping: emits ``ui_action.type = "clarify_card"`` which renders via
``features/copilot/components/cards/ClarifyCard.tsx``.

Cap of 4 items aligns with:
- WhatsApp interactive list rows practical UX ceiling (10 rows hard cap).
- WhatsApp reply buttons hard limit (3) — list fallback when 4 items needed.
- ClarifyCard UI's button-row layout.
"""

from __future__ import annotations

import json

from langchain_core.tools import tool

MAX_CLARIFY_ITEMS: int = 4
"""Maximum clarification items per tool invocation.

Exposed as a constant so tests, docs and the frontend can reference the same
number. Changing this requires updating ``ClarifyCard.tsx`` at the same time.
"""


@tool
def clarify(items: list[dict]) -> str:
    """Ask the user to resolve contradictions or ambiguities with quick-reply options.

    ONLY use this when you detect a real contradiction or ambiguity that
    blocks you from picking a next action. NOT for confirming data the user
    already provided. Prefer acting when the intent is clear.

    Each item renders as a card with 2-4 quick-resolution buttons. Use this
    before calling tools whose behavior branches on scope (e.g. extract_from_url
    when the user did not specify full vs update vs section).

    Args:
        items: List of ambiguous/contradictory items. Each has:
            - field_path: The field or decision with the issue
            - issue: Brief description of the ambiguity (1-2 sentences, Spanish)
            - options: 2-4 quick resolution options (strings shown as buttons)

    Returns:
        JSON with brief visible text and a ``clarify_card`` ui_action.

    """
    capped_items = items[:MAX_CLARIFY_ITEMS]

    # Key name MUST stay `clarify_items` — the frontend CardBlock dispatcher
    # (features/copilot/components/blocks/CardBlock.tsx) reads
    # ``action.clarify_items`` to render the ClarifyCard buttons. A previous
    # version emitted ``items``, which silently fell back to plain text.
    return json.dumps(
        {
            "text": "Noté algo que quiero aclarar rápido:",
            "ui_action": {
                "type": "clarify_card",
                "clarify_items": capped_items,
            },
        },
    )
