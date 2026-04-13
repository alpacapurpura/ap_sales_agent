"""
Brand read tools — allow the copilot to read the current brand configuration.

These tools give the copilot context about the user's brand so it can make
informed suggestions and proposals.
"""

import json
from uuid import UUID

import structlog
from langchain_core.tools import tool

from src.core.context import get_tenant_id
from src.core.database import SessionLocal

logger = structlog.get_logger()


def _get_brand_settings(db, tenant_id: UUID):
    """Fetch and return the BrandSettings model for a tenant."""
    from src.modules.brand.infrastructure.repositories.brand_repository import (
        BrandRepository,
    )

    repo = BrandRepository(db)
    try:
        return repo.get_settings(tenant_id)
    except Exception:
        logger.warning("brand_tools_get_settings_error", tenant_id=str(tenant_id))
        return None


def _format_section(section_name: str, data: dict) -> str:
    """Format a brand section as readable text for the LLM."""
    if not data or all(v in (None, "", [], {}) for v in data.values()):
        return f"### {section_name}\n(sin datos)\n"

    lines = [f"### {section_name}"]
    for key, value in data.items():
        if value in (None, "", [], {}):
            continue
        if isinstance(value, (dict, list)):
            lines.append(
                f"- **{key}:** {json.dumps(value, ensure_ascii=False, default=str)}"
            )
        else:
            lines.append(f"- **{key}:** {value}")
    lines.append("")
    return "\n".join(lines)


def _format_brand_section_detail(section: str, section_data: object) -> str:
    """Format a single brand section for display."""
    if section_data is None:
        return f"La sección '{section}' no tiene datos configurados."
    if isinstance(section_data, dict):
        return _format_section(section.title(), section_data)
    if isinstance(section_data, list):
        if not section_data:
            return f"La sección '{section}' está vacía."
        return f"### {section.title()}\n{json.dumps(section_data, ensure_ascii=False, indent=2, default=str)}"
    return f"### {section.title()}\n{section_data}"


@tool
def get_brand_data(section: str | None = None) -> str:
    """Read the current brand configuration for this tenant.

    Args:
        section: Optional specific section to read. One of: "identity", "story",
                 "positioning", "narrative", "visuals", "voice", "strategy",
                 "testimonials", "authority", "communication_assets".
                 If not provided, returns a summary of all sections.

    Returns:
        The brand data as formatted text.
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return "Error: No se pudo determinar el tenant. Asegúrate de estar autenticado."

    db = SessionLocal()
    try:
        settings = _get_brand_settings(db, tenant_id)
        if not settings:
            return "No hay datos de marca configurados para este tenant."

        data = settings.model_dump(mode="json")

        # Map section names to their data keys
        section_map = {
            "identity": "identity",
            "story": "story",
            "positioning": "positioning",
            "narrative": "narrative",
            "visuals": "visuals",
            "strategy": "strategy",
            "testimonials": "testimonials",
            "authority": "authority_vault",
            "communication_assets": "communication_assets",
            "voice": "identity",  # voice/tone lives inside identity
            "contact": "contact",
            "team": "team",
        }

        if section:
            section_key = section_map.get(section, section)
            return _format_brand_section_detail(section, data.get(section_key))

        # Return summary of all sections
        lines = ["## Datos de Marca\n"]
        for display_name, key in [
            ("Identidad", "identity"),
            ("Historia", "story"),
            ("Estrategia", "strategy"),
            ("Posicionamiento", "positioning"),
            ("Narrativa (StoryBrand)", "narrative"),
            ("Visuales", "visuals"),
            ("Activos de Comunicación", "communication_assets"),
            ("Testimonios", "testimonials"),
            ("Bóveda de Autoridad", "authority_vault"),
            ("Contacto", "contact"),
            ("Equipo", "team"),
        ]:
            section_data = data.get(key)
            if section_data is None:
                lines.append(f"### {display_name}\n(sin datos)\n")
            elif isinstance(section_data, dict):
                lines.append(_format_section(display_name, section_data))
            elif isinstance(section_data, list):
                if not section_data:
                    lines.append(f"### {display_name}\n(sin datos)\n")
                else:
                    lines.append(
                        f"### {display_name}\n{len(section_data)} elemento(s) configurado(s)\n"
                    )
            else:
                lines.append(f"### {display_name}\n{section_data}\n")

        return "\n".join(lines)
    finally:
        db.close()


BRAND_TOOLS = [get_brand_data]
