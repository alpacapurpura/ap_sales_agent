"""
Awareness tools — allow the copilot to understand the current state of the app.

These tools check completion status across modules so the copilot can guide
the user through setup and identify gaps.
"""

from typing import Optional
from uuid import UUID

from langchain_core.tools import tool

from src.core.context import get_tenant_id
from src.core.database import SessionLocal


def _check_brand_completion(db, tenant_id: UUID) -> dict:
    """Check which brand sections have data."""
    from src.modules.brand.infrastructure.repositories.brand_repository import BrandRepository

    repo = BrandRepository(db)
    try:
        settings = repo.get_settings(tenant_id)
    except Exception:
        return {"configured": False, "sections": {}, "message": "Sin datos de marca"}

    if not settings:
        return {"configured": False, "sections": {}, "message": "Sin datos de marca"}

    data = settings.model_dump() if hasattr(settings, "model_dump") else {}

    section_checks = {
        "identity": ["brand_name", "industry", "tagline"],
        "story": ["origin_story", "mission", "vision"],
        "positioning": ["uvp", "brand_essence", "discriminator"],
        "narrative": ["storybrand"],
        "visuals": ["colors", "typography"],
        "voice": ["voice_tone", "communication_style"],
        "testimonials": ["testimonials"],
        "authority": ["authority_vault"],
    }

    sections = {}
    for section, fields in section_checks.items():
        has_data = any(
            data.get(f) not in (None, "", [], {}) for f in fields
        )
        sections[section] = "configurado" if has_data else "pendiente"

    configured_count = sum(1 for v in sections.values() if v == "configurado")
    total = len(sections)

    return {
        "configured": configured_count > 0,
        "completion": f"{configured_count}/{total}",
        "sections": sections,
    }


def _check_offer_completion(db, tenant_id: UUID) -> dict:
    """Check offer configuration status."""
    from sqlalchemy import text

    try:
        count = db.execute(
            text("SELECT COUNT(*) FROM products WHERE tenant_id = :tid AND is_active = true"),
            {"tid": str(tenant_id)},
        ).scalar() or 0
    except Exception:
        count = 0

    return {
        "configured": count > 0,
        "offer_count": count,
        "message": f"{count} oferta(s) configurada(s)" if count else "Sin ofertas configuradas",
    }


def _check_connections_completion(db, tenant_id: UUID) -> dict:
    """Check which integrations are connected."""
    from sqlalchemy import text

    try:
        rows = db.execute(
            text("SELECT channel_type, is_active FROM connections WHERE tenant_id = :tid"),
            {"tid": str(tenant_id)},
        ).mappings().all()
    except Exception:
        rows = []

    connected = [r["channel_type"] for r in rows if r.get("is_active")]
    return {
        "configured": len(connected) > 0,
        "connected_channels": connected,
        "count": len(connected),
        "message": f"{len(connected)} conexión(es) activa(s): {', '.join(connected)}"
        if connected
        else "Sin conexiones configuradas",
    }


@tool
def get_module_completion_status(module: Optional[str] = None) -> str:
    """Check the configuration/completion status of app modules.

    Args:
        module: Optional specific module to check. One of: "brand", "offer", "connections", "all".
               If not provided or "all", checks all modules.

    Returns:
        A summary of what is configured and what is pending across modules.
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return "Error: No se pudo determinar el tenant. Asegúrate de estar autenticado."

    db = SessionLocal()
    try:
        results = {}

        if module in (None, "all", "brand"):
            results["Brand Studio"] = _check_brand_completion(db, tenant_id)

        if module in (None, "all", "offer"):
            results["Offer Studio"] = _check_offer_completion(db, tenant_id)

        if module in (None, "all", "connections"):
            results["Conexiones"] = _check_connections_completion(db, tenant_id)

        # Format for LLM consumption
        lines = ["## Estado de Configuración\n"]
        for name, status in results.items():
            emoji = "✅" if status.get("configured") else "⚠️"
            lines.append(f"### {emoji} {name}")
            if "sections" in status:
                for section, state in status["sections"].items():
                    icon = "✓" if state == "configurado" else "✗"
                    lines.append(f"  {icon} {section}: {state}")
                if "completion" in status:
                    lines.append(f"  Progreso: {status['completion']}")
            elif "message" in status:
                lines.append(f"  {status['message']}")
            lines.append("")

        return "\n".join(lines)
    finally:
        db.close()


AWARENESS_TOOLS = [get_module_completion_status]
