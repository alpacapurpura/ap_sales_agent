"""``start_guided_setup`` tool.

Activates guided mode: persists initial state, emits a ``guided_started``
UI action that the frontend uses to paint the header differently and show a
progress chip.
"""

from __future__ import annotations

import json

import structlog
from langchain_core.tools import tool

from src.core.context import get_conversation_id, get_tenant_id
from src.modules.copilot.application.guided.block_generator import build_blocks
from src.modules.copilot.application.guided.persistence import write_state
from src.modules.copilot.application.guided.state import GuidedState
from src.shared.domain.datetime_utils import utc_now

logger = structlog.get_logger()

_SUPPORTED_DOMAINS: frozenset[str] = frozenset({"brand", "offer", "buyer_persona"})


@tool
def start_guided_setup(domain: str, entity_id: str | None = None) -> str:
    """Activa el modo guiado para completar una entidad paso a paso.

    Úsalo cuando el usuario pide "guíame", "ayúdame a completar mi
    marca/oferta/persona" o cuando entra a un studio con datos vacíos y
    acepta la propuesta de guía.

    Args:
        domain: Uno de "brand", "offer", "buyer_persona".
        entity_id: UUID de la entidad a completar (opcional para brand).

    Returns:
        JSON con el primer bloque, total de bloques y la ui_action
        ``guided_started`` para que el frontend pinte el chip de progreso.

    """
    if domain not in _SUPPORTED_DOMAINS:
        supported = ", ".join(sorted(_SUPPORTED_DOMAINS))
        return json.dumps(
            {
                "text": (f"Dominio '{domain}' no soportado. Opciones: {supported}."),
                "error": "unsupported_domain",
            },
        )

    blocks = build_blocks(domain)  # type: ignore[arg-type]
    if not blocks:
        return json.dumps(
            {
                "text": (f"No hay bloques configurados para '{domain}'. Revisa el catálogo editable-fields."),
                "error": "empty_flow",
            },
        )

    first = blocks[0]
    conversation_id = get_conversation_id()
    tenant_id = get_tenant_id()

    state = GuidedState(
        domain=domain,
        entity_id=entity_id,
        current_block_id=first.id,
        completed_blocks=[],
        started_at=utc_now().isoformat(),
    )
    write_state(conversation_id, state, tenant_id)

    return json.dumps(
        {
            "text": (
                f"Listo, modo guiado activado para {domain}. Empecemos con: **{first.label}** ({first.description})"
            ),
            "ui_action": {
                "type": "guided_started",
                "domain": domain,
                "entity_id": entity_id,
                "total_blocks": len(blocks),
                "current_block": {
                    "id": first.id,
                    "label": first.label,
                    "description": first.description,
                    "field_paths": list(first.field_paths),
                    "coverage_threshold": first.coverage_threshold,
                },
            },
            "metadata": {
                "blocks": [{"id": b.id, "label": b.label} for b in blocks],
            },
        },
    )
