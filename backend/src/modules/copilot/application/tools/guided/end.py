"""``end_guided_setup`` tool — user exits guided mode."""

from __future__ import annotations

import json

from langchain_core.tools import tool
from luana_core_copilot.application.guided.persistence import read_state, write_state
from luana_core_platform.core.context import get_conversation_id, get_tenant_id


@tool
def end_guided_setup(reason: str = "user_request") -> str:
    """Termina el modo guiado y vuelve al chat libre.

    Úsalo cuando el usuario dice "para", "vamos libre", "salgo de la guía" o
    cuando detectes que ya completó todo. No requiere argumentos complejos:
    el estado se lee del contexto de conversación.

    Args:
        reason: Motivo corto ("user_request" | "completed" | "abandoned").

    Returns:
        JSON con mensaje de cierre y ``ui_action`` ``guided_ended``.

    """
    conversation_id = get_conversation_id()
    tenant_id = get_tenant_id()
    state = read_state(conversation_id, tenant_id)

    if state is None:
        return json.dumps(
            {
                "text": "Ya estabas en chat libre. No hay nada que terminar.",
                "ui_action": {"type": "guided_ended", "reason": "no_active"},
            },
        )

    write_state(conversation_id, None, tenant_id)

    return json.dumps(
        {
            "text": "Listo, volvemos a chat libre. Puedes retomar la guía cuando quieras.",
            "ui_action": {
                "type": "guided_ended",
                "reason": reason,
                "domain": state.domain,
                "entity_id": state.entity_id,
                "blocks_completed": state.completed_blocks,
            },
        },
    )
