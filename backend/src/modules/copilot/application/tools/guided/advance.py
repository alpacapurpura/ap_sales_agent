"""``advance_guided_block`` tool.

Marks the current block complete and moves to the next one. When the user
reaches the final block the tool auto-ends the guided flow and emits a
``guided_completed`` UI action.
"""

from __future__ import annotations

import json

import structlog
from langchain_core.tools import tool

from src.core.context import get_conversation_id, get_tenant_id
from src.modules.copilot.application.guided.block_generator import (
    build_blocks,
    next_block_after,
)
from src.modules.copilot.application.guided.persistence import read_state, write_state

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

    return json.dumps(
        {
            "text": f"Bloque guardado. Pasemos a **{next_block.label}**.",
            "ui_action": {
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
            },
        },
    )
