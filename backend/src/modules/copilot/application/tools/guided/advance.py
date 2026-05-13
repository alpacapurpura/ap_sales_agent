"""``advance_guided_block`` tool.

Marks the current block complete and moves to the next one. When the user
reaches the final block the tool auto-ends the guided flow and emits a
``guided_completed`` UI action.

Fase 09.C: when transitioning to the next block, also computes a
best-effort ``suggested_question`` hint via the
``conversational_questioning`` algorithm and surfaces it in the
``ui_action`` payload. Hint is optional — guided flow keeps working
when it cannot be computed.
"""

from __future__ import annotations

import json

import structlog
from langchain_core.tools import tool
from luana_core_copilot.application.guided.block_generator import (
    build_blocks,
    next_block_after,
)
from luana_core_copilot.application.guided.persistence import read_state, write_state
from luana_core_copilot.application.guided.question_hint import build_question_hint
from luana_core_copilot.application.guided.state_reader import read_entity_state
from luana_core_platform.core.context import get_conversation_id, get_tenant_id
from luana_core_platform.core.database import SessionLocal

logger = structlog.get_logger()


@tool
def advance_guided_block(block_id: str, persisted_fields: list[str] | None = None) -> str:
    """Cierra el bloque actual del modo guiado y avanza al siguiente.

    Llamarlo SOLO cuando el usuario confirmó el checkpoint del bloque.
    Si no hay bloque siguiente, termina el modo guiado automáticamente.

    Args:
        block_id: ID del bloque que se acaba de completar.
        persisted_fields: Campos que efectivamente quedaron guardados
            (lo usa el frontend para pintar highlights verdes). Opcional.

    Returns:
        JSON con confirmación + ``ui_action`` ``guided_block_advanced`` o
        ``guided_completed`` cuando era el último.

    """
    conversation_id = get_conversation_id()
    tenant_id = get_tenant_id()
    state = read_state(conversation_id, tenant_id)

    if state is None:
        return json.dumps(
            {
                "text": "No hay un modo guiado activo. Usa start_guided_setup primero.",
                "error": "no_active_guided",
            },
        )

    if state.current_block_id != block_id:
        logger.info(
            "guided_advance_block_id_mismatch",
            expected=state.current_block_id,
            provided=block_id,
        )

    if block_id not in state.completed_blocks:
        state.completed_blocks.append(block_id)

    next_block = next_block_after(state.domain, block_id)  # type: ignore[arg-type]
    total = len(build_blocks(state.domain))  # type: ignore[arg-type]

    if next_block is None:
        # Flow finished — clear guided state.
        write_state(conversation_id, None, tenant_id)
        return json.dumps(
            {
                "text": "¡Tu configuración guiada quedó completa! Pasamos a chat libre.",
                "ui_action": {
                    "type": "guided_completed",
                    "domain": state.domain,
                    "entity_id": state.entity_id,
                    "blocks_completed": state.completed_blocks,
                    "total_blocks": total,
                },
            },
        )

    state.current_block_id = next_block.id
    write_state(conversation_id, state, tenant_id)

    suggested = _compute_suggested_question(
        domain=state.domain,
        entity_id=state.entity_id,
        tenant_id=tenant_id,
        section=next_block.id,
    )

    payload: dict = {
        "type": "guided_block_advanced",
        "domain": state.domain,
        "entity_id": state.entity_id,
        "persisted_fields": list(persisted_fields or []),
        "completed_blocks": state.completed_blocks,
        "total_blocks": total,
        "current_block": {
            "id": next_block.id,
            "label": next_block.label,
            "description": next_block.description,
            "field_paths": list(next_block.field_paths),
            "coverage_threshold": next_block.coverage_threshold,
        },
    }
    if suggested is not None:
        payload["suggested_question"] = suggested

    return json.dumps(
        {
            "text": f"Bloque guardado. Pasemos a **{next_block.label}**.",
            "ui_action": payload,
        },
    )


def _compute_suggested_question(
    *,
    domain: str,
    entity_id: str | None,
    tenant_id: object,
    section: str,
) -> dict | None:
    """Best-effort hint enrichment via FieldContract registry.

    Reads the entity state for the given guided ``domain`` and asks the
    channel-agnostic algorithm for the next missing required field
    inside ``section``. Returns ``None`` on any error so the guided
    flow keeps working unchanged.
    """
    if tenant_id is None:
        return None
    from uuid import UUID

    try:
        tenant_uuid = tenant_id if isinstance(tenant_id, UUID) else UUID(str(tenant_id))
    except (TypeError, ValueError):
        return None

    db = SessionLocal()
    try:
        entity_state = read_entity_state(
            domain,
            tenant_id=tenant_uuid,
            entity_id=entity_id,
            db=db,
        )
    finally:
        db.close()

    if entity_state is None:
        return None
    return build_question_hint(domain, entity_state, section=section)
