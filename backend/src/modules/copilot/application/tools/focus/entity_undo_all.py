"""Focus Mode tool — restore the entity to its snapshot state (undo all changes)."""

import json
from uuid import UUID

import structlog
from langchain_core.tools import tool

from src.core.context import get_tenant_id
from src.core.database import SessionLocal
from src.modules.copilot.infrastructure.persisters.persister_registry import get_persister

logger = structlog.get_logger()


@tool
def entity_undo_all(
    domain: str,
    entity_id: str,
    snapshot: dict,
) -> str:
    """Restore the focused entity to its original state captured at session start.

    Invoke this tool when the user explicitly requests to discard all changes
    made during the current Focus session.  The snapshot must be the dict
    originally returned by ``entity_read`` at the beginning of the session.

    All snapshot fields are re-persisted atomically in a single ``persist`` call,
    and the frontend receives a ``preview_update`` action so the preview pane
    reflects the restored values immediately.

    Args:
        domain: Entity domain — "brand" or "offer".
        entity_id: UUID string of the entity to restore.
        snapshot: Dict of field_path -> value as loaded at session start.

    Returns:
        JSON string with ``text`` and ``ui_action`` of type ``preview_update``
        on success, or ``{"error": "..."}`` on failure.

    """
    tenant_id = get_tenant_id()
    if tenant_id is None:
        return json.dumps({"error": "No se pudo determinar el tenant."})

    db = SessionLocal()
    try:
        persister = get_persister(domain, db)
        eid = UUID(entity_id) if entity_id else None
        fields_to_restore = list(snapshot.keys())
        persister.persist(
            tenant_id=tenant_id,
            mapa_global=snapshot,
            fields_to_persist=fields_to_restore,
            entity_id=eid,
        )
        return json.dumps(
            {
                "text": "Entidad restaurada al estado inicial del focus.",
                "ui_action": {
                    "type": "preview_update",
                    "delta": snapshot,
                },
            }
        )
    except Exception:
        logger.exception("entity_undo_all_error", domain=domain, entity_id=entity_id)
        return json.dumps({"error": f"No se pudo restaurar la entidad '{entity_id}'."})
    finally:
        db.close()
