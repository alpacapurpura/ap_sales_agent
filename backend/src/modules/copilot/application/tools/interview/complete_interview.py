"""Complete interview tool — closes the session and redirects."""

import json

from langchain_core.tools import tool


@tool
def complete_interview(
    session_id: str,
    health_score: int,
    redirect_path: str = "/brand-studio",
) -> str:
    """Close the interview session. All blocks must be completed or the message limit reached.

    This marks the session as COMPLETED, returns copilot to chat mode, and redirects
    the user to the studio page.

    Args:
        session_id: The interview session UUID.
        health_score: Final health percentage of the domain model.
        redirect_path: Where to redirect the user after completion.

    Returns:
        JSON with celebration text and interview_complete ui_action.

    """
    return json.dumps(
        {
            "text": f"¡Tu marca está lista! {health_score}% completa.",
            "ui_action": {
                "type": "interview_complete",
                "session_id": session_id,
                "health_score": health_score,
                "redirect": redirect_path,
            },
        },
    )
