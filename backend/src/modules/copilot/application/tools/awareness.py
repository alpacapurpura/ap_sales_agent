"""
Awareness tools — check completion status across modules dynamically.

Uses MODULE_REGISTRY + schema_introspection to discover fields at runtime.
NEVER hardcodes field names — if you add a section to BrandSettings,
the copilot detects it automatically.
"""

import json
from uuid import UUID

import structlog
from langchain_core.tools import tool
from sqlalchemy import text

from src.core.context import get_tenant_id
from src.core.database import SessionLocal
from src.modules.copilot.domain.module_registry import get_module_registry
from src.modules.copilot.domain.schema_introspection import (
    check_section_completion,
    format_completion_markdown,
    get_model_sections,
)

logger = structlog.get_logger()


def _check_introspectable_module(db, tenant_id: UUID, descriptor) -> dict:
    """Check completion for a module that has a Pydantic model_class."""
    try:
        repo = descriptor.repo_factory(db)
        data = descriptor.read_fn(repo, tenant_id)
    except Exception as e:
        logger.warning(
            "awareness_read_error", module=descriptor.module_id, error=str(e)
        )
        return {"configured": False, "message": f"Error leyendo {descriptor.label}"}

    if not data:
        return {"configured": False, "message": f"Sin datos de {descriptor.label}"}

    raw = data.model_dump(mode="json") if hasattr(data, "model_dump") else {}
    sections = get_model_sections(descriptor.model_class)
    completion = check_section_completion(raw, sections)

    return {
        "configured": any(s.is_configured for s in completion.values()),
        "markdown": format_completion_markdown(descriptor.label, completion, sections),
    }


def _check_offer_completion(db, tenant_id: UUID) -> dict:
    """Check offer configuration status via SQL count."""
    try:
        count = (
            db.execute(
                text(
                    "SELECT COUNT(*) FROM products WHERE tenant_id = :tid AND is_active = true"
                ),
                {"tid": str(tenant_id)},
            ).scalar()
            or 0
        )
    except Exception:
        count = 0

    configured = count > 0
    return {
        "configured": configured,
        "markdown": f"### {'✅' if configured else '⚠️'} Offer Studio\n  {count} oferta(s) configurada(s)"
        if count
        else "### ⚠️ Offer Studio\n  Sin ofertas configuradas",
    }


def _check_connections_completion(db, tenant_id: UUID) -> dict:
    """Check which integrations are connected."""
    try:
        rows = (
            db.execute(
                text(
                    "SELECT channel_type, is_active FROM channel_connections WHERE tenant_id = :tid"
                ),
                {"tid": str(tenant_id)},
            )
            .mappings()
            .all()
        )
    except Exception:
        rows = []

    connected = [r["channel_type"] for r in rows if r.get("is_active")]
    configured = len(connected) > 0

    if connected:
        channels_str = ", ".join(connected)
        markdown = f"### ✅ Conexiones\n  {len(connected)} activa(s): {channels_str}"
    else:
        markdown = "### ⚠️ Conexiones\n  Sin conexiones configuradas"

    return {"configured": configured, "markdown": markdown}


def _check_landing_completion(db, tenant_id: UUID) -> dict:
    """Check landing page status."""
    try:
        total = (
            db.execute(
                text("SELECT COUNT(*) FROM landing_pages WHERE tenant_id = :tid"),
                {"tid": str(tenant_id)},
            ).scalar()
            or 0
        )
        published = (
            db.execute(
                text(
                    "SELECT COUNT(*) FROM landing_pages WHERE tenant_id = :tid AND is_published = true"
                ),
                {"tid": str(tenant_id)},
            ).scalar()
            or 0
        )
    except Exception:
        total, published = 0, 0

    configured = total > 0
    markdown = f"### {'✅' if published > 0 else '⚠️'} Landing Pages\n  {total} total, {published} publicada(s)"
    return {"configured": configured, "markdown": markdown}


def _check_crm_completion(db, tenant_id: UUID) -> dict:
    """Check CRM data status."""
    try:
        lead_count = (
            db.execute(
                text("SELECT COUNT(*) FROM leads WHERE tenant_id = :tid"),
                {"tid": str(tenant_id)},
            ).scalar()
            or 0
        )
        sale_count = (
            db.execute(
                text("SELECT COUNT(*) FROM sales WHERE tenant_id = :tid"),
                {"tid": str(tenant_id)},
            ).scalar()
            or 0
        )
    except Exception:
        lead_count, sale_count = 0, 0

    configured = lead_count > 0
    markdown = f"### {'✅' if configured else '⚠️'} CRM\n  {lead_count} lead(s), {sale_count} venta(s)"
    return {"configured": configured, "markdown": markdown}


# Map of module_id -> checker function for modules without Pydantic model_class
_SPECIAL_CHECKERS = {
    "offer": _check_offer_completion,
    "connections": _check_connections_completion,
    "landing": _check_landing_completion,
    "crm": _check_crm_completion,
}


@tool
def get_module_completion_status(module: str | None = None) -> str:
    """Verifica el estado de configuración de los módulos del sistema.

    Args:
        module: Módulo específico a verificar. Uno de: "brand", "offer",
                "connections", "landing", "crm", "all".
                Si no se proporciona o es "all", verifica todos.

    Returns:
        Resumen de qué está configurado y qué falta, por módulo.
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return "Error: No se pudo determinar el tenant. Asegúrate de estar autenticado."

    registry = get_module_registry()
    db = SessionLocal()
    try:
        # Determine which modules to check
        checkable_modules = ["brand", "offer", "connections", "landing", "crm"]
        if module and module != "all":
            modules_to_check = [module] if module in checkable_modules else []
        else:
            modules_to_check = checkable_modules

        if not modules_to_check:
            return f"Módulo '{module}' no reconocido. Disponibles: {', '.join(checkable_modules)}"

        lines = ["## Estado de Configuración\n"]
        checklist_items = []

        for mod_id in modules_to_check:
            descriptor = registry.get(mod_id)
            if not descriptor:
                continue

            # Use special checker if module has no Pydantic model_class
            if mod_id in _SPECIAL_CHECKERS:
                result = _SPECIAL_CHECKERS[mod_id](db, tenant_id)
            elif descriptor.model_class and descriptor.repo_factory:
                result = _check_introspectable_module(db, tenant_id, descriptor)
            else:
                continue

            lines.append(result["markdown"])
            lines.append("")

            checklist_items.append(
                {
                    "label": descriptor.label,
                    "done": result["configured"],
                    "route": f"/{{tenantId}}/{descriptor.route_prefix}",
                }
            )

        return json.dumps(
            {
                "text": "\n".join(lines),
                "ui_action": {
                    "type": "checklist",
                    "items": checklist_items,
                },
            }
        )
    finally:
        db.close()


AWARENESS_TOOLS = [get_module_completion_status]
