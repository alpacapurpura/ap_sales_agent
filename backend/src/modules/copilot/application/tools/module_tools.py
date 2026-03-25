"""
Generic Module Data Tool — reads data from ANY module via MODULE_REGISTRY.

Replaces brand_tools.py and offer_tools.py with a single dynamic tool.
When you add a field to BrandIdentity, the copilot sees it automatically
via model_dump(). No copilot code changes needed.
"""

import json
from typing import Optional

from langchain_core.tools import tool

from src.core.context import get_tenant_id
from src.core.database import SessionLocal
from src.modules.copilot.domain.module_registry import get_module_registry
from src.modules.copilot.domain.schema_introspection import (
    get_model_sections,
)

import structlog

logger = structlog.get_logger()


def _format_section_data(section_name: str, data) -> str:
    """Format a section's data as readable text for the LLM."""
    if data is None:
        return f"### {section_name}\n(sin datos)\n"

    if isinstance(data, list):
        if not data:
            return f"### {section_name}\n(vacío — 0 elementos)\n"
        return f"### {section_name}\n{len(data)} elemento(s)\n{json.dumps(data, ensure_ascii=False, indent=2, default=str)}"

    if isinstance(data, dict):
        if all(v in (None, "", [], {}) for v in data.values()):
            return f"### {section_name}\n(sin datos)\n"

        lines = [f"### {section_name}"]
        for key, value in data.items():
            if value in (None, "", [], {}):
                continue
            if isinstance(value, (dict, list)):
                lines.append(f"- **{key}:** {json.dumps(value, ensure_ascii=False, default=str)}")
            else:
                lines.append(f"- **{key}:** {value}")
        lines.append("")
        return "\n".join(lines)

    return f"### {section_name}\n{data}\n"


def _format_module_summary(label: str, raw: dict, sections: dict) -> str:
    """Format a full module summary using introspected sections."""
    lines = [f"## {label}\n"]
    for name, section_info in sections.items():
        section_data = raw.get(name)
        display_label = section_info.label
        lines.append(_format_section_data(display_label, section_data))
    return "\n".join(lines)


def _format_offer_list(offers: list) -> str:
    """Format a list of Offer domain objects or dicts."""
    if not offers:
        return "No hay ofertas configuradas para este tenant."

    lines = [f"## Ofertas ({len(offers)} activa(s))\n"]
    for i, offer in enumerate(offers, 1):
        # Handle both domain objects and dicts
        if hasattr(offer, "model_dump"):
            o = offer.model_dump(mode="json") if hasattr(offer, "model_dump") else {}
        elif hasattr(offer, "__dict__"):
            o = {k: v for k, v in offer.__dict__.items() if not k.startswith("_")}
        else:
            o = offer if isinstance(offer, dict) else {"data": str(offer)}

        offer_id = o.get("id", "")
        name = o.get("name") or o.get("public_name", "Sin nombre")
        offer_type = o.get("type", "N/A")
        status = o.get("status", "N/A")

        lines.append(f"{i}. **{name}** [ID: {offer_id}]")
        lines.append(f"   Tipo: {offer_type} | Estado: {status}")

        if o.get("headline_promise"):
            lines.append(f"   Promesa: {o['headline_promise']}")
        if o.get("primary_outcome"):
            lines.append(f"   Resultado: {o['primary_outcome']}")
        if o.get("value_level"):
            lines.append(f"   Nivel: {o['value_level']}")
        if o.get("pricing"):
            pricing = o["pricing"]
            currency = o.get("currency", "USD")
            lines.append(f"   Precios ({currency}): {json.dumps(pricing, ensure_ascii=False, default=str)}")
        lines.append("")

    return "\n".join(lines)


def _format_connections_list(connections: list) -> str:
    """Format a list of ChannelConnection objects."""
    if not connections:
        return "No hay conexiones configuradas."

    active = [c for c in connections if getattr(c, "is_active", True)]
    inactive = [c for c in connections if not getattr(c, "is_active", True)]

    lines = [f"## Conexiones ({len(active)} activa(s), {len(inactive)} inactiva(s))\n"]
    for c in connections:
        channel = getattr(c, "channel_type", "unknown")
        is_active = getattr(c, "is_active", False)
        icon = "✓" if is_active else "✗"
        lines.append(f"  {icon} {channel}: {'activa' if is_active else 'inactiva'}")

    return "\n".join(lines)


def _format_landing_list(pages: list) -> str:
    """Format a list of LandingPage objects."""
    if not pages:
        return "No hay landing pages configuradas."

    lines = [f"## Landing Pages ({len(pages)})\n"]
    for p in pages:
        if hasattr(p, "model_dump"):
            d = p.model_dump(mode="json")
        elif hasattr(p, "__dict__"):
            d = {k: v for k, v in p.__dict__.items() if not k.startswith("_")}
        else:
            d = p if isinstance(p, dict) else {}

        slug = d.get("slug", "N/A")
        published = d.get("is_published", False)
        offer_id = d.get("offer_id", "")
        icon = "✓" if published else "✗"
        lines.append(f"  {icon} /{slug} — {'publicada' if published else 'borrador'}")
        if offer_id:
            lines.append(f"    Oferta vinculada: {offer_id}")

    return "\n".join(lines)


@tool
def get_module_data(module: str, section: Optional[str] = None) -> str:
    """Lee datos de cualquier módulo del sistema.

    Args:
        module: Módulo a consultar. Uno de: "brand", "offer", "connections",
                "landing".
        section: Sección específica (solo para módulos con secciones como brand).
                 Ejemplo: "identity", "story", "positioning", "narrative",
                 "visuals", "contact", "testimonials", "authority_vault",
                 "communication_assets", "strategy", "team".

    Returns:
        Los datos del módulo formateados como texto.
    """
    registry = get_module_registry()
    descriptor = registry.get(module)
    if not descriptor:
        available = ", ".join(
            k for k, v in registry.items() if v.repo_factory is not None
        )
        return f"Módulo '{module}' no encontrado o no tiene lectura directa. Disponibles: {available}"

    if not descriptor.repo_factory or not descriptor.read_fn:
        return f"El módulo '{descriptor.label}' no soporta lectura directa. Usa herramientas específicas."

    tenant_id = get_tenant_id()
    if not tenant_id:
        return "Error: No se pudo determinar el tenant. Asegúrate de estar autenticado."

    db = SessionLocal()
    try:
        repo = descriptor.repo_factory(db)
        data = descriptor.read_fn(repo, tenant_id)

        if data is None:
            return f"No hay datos configurados para {descriptor.label}."

        # Handle list results (offers, connections, landing pages)
        if isinstance(data, list):
            if module == "offer":
                return _format_offer_list(data)
            elif module == "connections":
                return _format_connections_list(data)
            elif module == "landing":
                return _format_landing_list(data)
            else:
                return f"## {descriptor.label}\n{len(data)} elemento(s) encontrado(s)"

        # Handle Pydantic model with introspection
        if hasattr(data, "model_dump"):
            raw = data.model_dump(mode="json")
        else:
            raw = data if isinstance(data, dict) else {}

        if section:
            section_data = raw.get(section)
            if section_data is None:
                available_sections = ", ".join(raw.keys())
                return f"La sección '{section}' no tiene datos. Secciones disponibles: {available_sections}"
            return _format_section_data(section.replace("_", " ").title(), section_data)

        # Full module summary with introspection
        if descriptor.model_class:
            sections = get_model_sections(descriptor.model_class)
            return _format_module_summary(descriptor.label, raw, sections)
        else:
            return _format_section_data(descriptor.label, raw)

    except Exception as e:
        logger.error("module_tools_error", module=module, error=str(e))
        return f"Error leyendo {descriptor.label}: {str(e)}"
    finally:
        db.close()


MODULE_TOOLS = [get_module_data]
