"""Focus Mode tool — write a single field to the focused entity."""

import json
from uuid import UUID

import structlog
from langchain_core.tools import tool

from src.core.context import get_tenant_id
from src.core.database import SessionLocal
from src.modules.copilot.domain.schema_introspection import validate_field_path
from src.modules.copilot.infrastructure.persisters.persister_registry import get_persister

logger = structlog.get_logger()


@tool
def entity_write(
    domain: str,
    entity_id: str,
    field_path: str,
    value: str,
    reason: str,
) -> str:
    """Write a single field value to the focused entity and signal a UI preview update.

    Use this tool to persist individual field changes while the user reviews them
    in real-time in the preview pane. Every write emits a ``preview_update`` action
    so the frontend can highlight the changed field immediately.

    Args:
        domain: Entity domain — "brand" or "offer".
        entity_id: UUID string of the entity to update.
        field_path: Dot-notation path (e.g. "identity.brand_name") or flat field
            name (e.g. "headline_promise"). Must be a valid persistable field.
        value: New value to store. Always a string — complex types are serialised
            by the persister.
        reason: Short explanation of why this value was chosen (shown in the UI).

    Returns:
        JSON string with ``text`` confirmation and ``ui_action`` of type
        ``preview_update`` on success, or ``{"error": "..."}`` on failure.

    """
    # Validate field path before touching the DB.
    if not validate_field_path(domain, field_path):
        return json.dumps({"error": f"Campo '{field_path}' no es válido para el dominio '{domain}'."})

    tenant_id = get_tenant_id()
    if tenant_id is None:
        return json.dumps({"error": "No se pudo determinar el tenant."})

    db = SessionLocal()
    try:
        persister = get_persister(domain, db)
        eid = UUID(entity_id) if entity_id else None
        persister.persist(
            tenant_id=tenant_id,
            mapa_global={field_path: value},
            fields_to_persist=[field_path],
            entity_id=eid,
        )
        return json.dumps(
            {
                "text": f"Actualizado: {field_path}",
                "ui_action": {
                    "type": "preview_update",
                    "delta": {field_path: value},
                    "reason": reason,
                },
            }
        )
    except Exception:
        logger.exception("entity_write_error", domain=domain, field_path=field_path)
        return json.dumps({"error": f"No se pudo escribir el campo '{field_path}'."})
    finally:
        db.close()
