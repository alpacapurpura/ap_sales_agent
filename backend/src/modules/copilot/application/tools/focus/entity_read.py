"""Focus Mode tool — read the current state of the focused entity."""

import json

import structlog
from langchain_core.tools import tool

from src.core.context import get_tenant_id
from src.core.database import SessionLocal
from src.modules.copilot.infrastructure.context.focus_context_loader import FocusContextLoader

logger = structlog.get_logger()


@tool
def entity_read(
    domain: str,
    entity_id: str,
    section: str | None = None,
) -> str:
    """Read the current state of the focused entity, optionally filtered by section.

    Use this tool at the start of a Focus session to load the entity's current
    field values as context before making any writes.  When ``section`` is provided,
    only fields that belong to that section are returned, keeping the context
    window small.

    Section matching rules:
    - Dot-notation keys: key starts with ``"{section}."`` (e.g. ``"identity.brand_name"``
      is included when ``section="identity"``).
    - Underscore-prefixed keys: key starts with ``"{section}_"`` (e.g.
      ``"marketing_pain_points"`` is included when ``section="marketing"``).

    Args:
        domain: Entity domain — "brand" or "offer".
        entity_id: UUID string of the entity to load.
        section: Optional section name to filter returned fields.

    Returns:
        JSON string with ``{"data": {...}}`` on success, optionally with a
        ``"section"`` key when filtering was applied.  Returns
        ``{"error": "..."}`` on failure.

    """
    tenant_id = get_tenant_id()
    if tenant_id is None:
        return json.dumps({"error": "No se pudo determinar el tenant."})

    db = SessionLocal()
    try:
        loader = FocusContextLoader(db)
        data = loader.load(tenant_id=tenant_id, domain=domain, entity_id=entity_id)

        if section:
            dot_prefix = f"{section}."
            us_prefix = f"{section}_"
            filtered = {k: v for k, v in data.items() if k.startswith((dot_prefix, us_prefix)) or k == section}
            return json.dumps({"data": filtered, "section": section})

        return json.dumps({"data": data})
    except Exception:
        logger.exception("entity_read_error", domain=domain, entity_id=entity_id)
        return json.dumps({"error": f"No se pudo leer la entidad '{entity_id}' del dominio '{domain}'."})
    finally:
        db.close()
