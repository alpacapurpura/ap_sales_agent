"""
Offer read tools — allow the copilot to read the current offers/products.

These tools give the copilot context about the user's offer ladder so it can
make informed suggestions and proposals.
"""

import contextlib
import json
from uuid import UUID

import structlog
from langchain_core.tools import tool
from sqlalchemy import text

from src.core.context import get_tenant_id
from src.core.database import SessionLocal

logger = structlog.get_logger()


def _fetch_offers(db, tenant_id: UUID, offer_id: str | None = None) -> list[dict]:
    """Fetch offers from the products table."""
    try:
        if offer_id:
            rows = (
                db.execute(
                    text(
                        "SELECT id, name, archetype, format_hint, status, headline_promise, primary_outcome, "
                        "pricing, currency, offer_value_level AS value_level, delivery_model, access_duration, "
                        "access_duration_text, guarantee_type, guarantee_terms, "
                        "marketing_pain_points, marketing_desires, objections, "
                        "target_avatar_match, requires_application, checkout_page_url "
                        "FROM products WHERE tenant_id = :tid AND id = :oid AND is_active = true",
                    ),
                    {"tid": str(tenant_id), "oid": offer_id},
                )
                .mappings()
                .all()
            )
        else:
            rows = (
                db.execute(
                    text(
                        "SELECT id, name, archetype, format_hint, status, headline_promise, primary_outcome, "
                        "pricing, currency, offer_value_level AS value_level, delivery_model, access_duration "
                        "FROM products WHERE tenant_id = :tid AND is_active = true "
                        "ORDER BY created_at DESC",
                    ),
                    {"tid": str(tenant_id)},
                )
                .mappings()
                .all()
            )
    except Exception as e:
        logger.warning(
            "offer_tools_fetch_error",
            tenant_id=str(tenant_id),
            error=str(e),
        )
        return []

    return [dict(r) for r in rows]


def _format_offer_summary(offer: dict) -> str:
    """Format a single offer as readable text."""
    lines = []
    name = offer.get("name", "Sin nombre")
    archetype = offer.get("archetype", "N/A")
    status = offer.get("status", "N/A")
    lines.append(f"**{name}** (Archetype: {archetype}, Estado: {status})")

    if offer.get("headline_promise"):
        lines.append(f"  Promesa: {offer['headline_promise']}")
    if offer.get("primary_outcome"):
        lines.append(f"  Resultado principal: {offer['primary_outcome']}")
    if offer.get("value_level"):
        lines.append(f"  Nivel de valor: {offer['value_level']}")
    if offer.get("delivery_model"):
        lines.append(f"  Modelo de entrega: {offer['delivery_model']}")

    pricing = offer.get("pricing")
    if pricing:
        if isinstance(pricing, str):
            with contextlib.suppress(json.JSONDecodeError, TypeError):
                pricing = json.loads(pricing)
        if isinstance(pricing, list) and pricing:
            currency = offer.get("currency", "USD")
            lines.append(
                f"  Precios ({currency}): {json.dumps(pricing, ensure_ascii=False, default=str)}",
            )

    if offer.get("access_duration"):
        lines.append(f"  Duración de acceso: {offer['access_duration']}")

    return "\n".join(lines)


def _parse_json_list(value) -> list | None:
    """Parse a value that may be a JSON string or list, return list or None."""
    if isinstance(value, str):
        with contextlib.suppress(json.JSONDecodeError, TypeError):
            value = json.loads(value)
    if isinstance(value, list) and value:
        return value
    return None


def _format_offer_detail(offer: dict) -> str:
    """Format a single offer with full details."""
    lines = [_format_offer_summary(offer)]

    if offer.get("guarantee_type"):
        lines.append(f"  Garantía: {offer['guarantee_type']}")
        if offer.get("guarantee_terms"):
            lines.append(f"  Términos: {offer['guarantee_terms']}")

    # JSON-list fields: label → offer key
    _list_fields = [
        ("Puntos de dolor", "marketing_pain_points"),
        ("Deseos", "marketing_desires"),
        ("Objeciones", "objections"),
    ]
    for label, key in _list_fields:
        parsed = _parse_json_list(offer.get(key))
        if parsed:
            lines.append(f"  {label}: {', '.join(str(v) for v in parsed)}")

    if offer.get("requires_application"):
        lines.append("  Requiere aplicación: Sí")
    if offer.get("checkout_page_url"):
        lines.append(f"  Checkout URL: {offer['checkout_page_url']}")

    return "\n".join(lines)


@tool
def get_offer_data(offer_id: str | None = None) -> str:
    """Read the current offers/products for this tenant.

    Args:
        offer_id: Optional specific offer ID to read details for.
                  If not provided, returns a summary of all offers.

    Returns:
        The offer data as formatted text.
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return "Error: No se pudo determinar el tenant. Asegúrate de estar autenticado."

    db = SessionLocal()
    try:
        offers = _fetch_offers(db, tenant_id, offer_id)

        if not offers:
            if offer_id:
                return f"No se encontró la oferta con ID '{offer_id}'."
            return "No hay ofertas configuradas para este tenant."

        if offer_id:
            return f"## Detalle de Oferta\n\n{_format_offer_detail(offers[0])}"

        lines = [f"## Ofertas ({len(offers)} activa(s))\n"]
        for i, offer in enumerate(offers, 1):
            offer_id_str = str(offer.get("id", ""))
            lines.append(f"{i}. [ID: {offer_id_str}]")
            lines.append(_format_offer_summary(offer))
            lines.append("")

        return "\n".join(lines)
    finally:
        db.close()


OFFER_TOOLS = [get_offer_data]
