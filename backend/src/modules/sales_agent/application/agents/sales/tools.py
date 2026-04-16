"""Tool functions for the sales agent subgraph.

Each tool receives the full agent state dict and an optional DB session.
Tools return a dict with at minimum {"status": "...", "message": "..."}.

The TOOL_REGISTRY maps tool names (as emitted by specialists in
[TOOL_REQUEST: {"tool": "<name>"}] blocks) to their implementations.
"""

from typing import Any
from uuid import UUID

import structlog

logger = structlog.get_logger()


def tool_send_payment_link(state: dict[str, Any], db: Any = None) -> dict[str, str]:  # noqa: ANN401 — dynamic type (optional DB session)
    """Return the checkout URL for the active offer."""
    product = state.get("active_product") or {}
    url = product.get("checkout_page_url")
    if not url:
        return {
            "status": "error",
            "message": "No hay link de pago configurado para esta oferta.",
        }
    offer_name = product.get("name", "la oferta")
    return {
        "status": "success",
        "url": url,
        "message": f"Link de pago para {offer_name}: {url}",
    }


def tool_check_schedule(state: dict[str, Any], db: Any = None) -> dict[str, Any]:  # noqa: ANN401 — dynamic type (optional DB session)
    """Return scheduling availability info."""
    product = state.get("active_product") or {}
    calendar_type_id = product.get("calendar_type_id")
    if not calendar_type_id:
        return {
            "status": "error",
            "message": "Esta oferta no tiene agenda configurada.",
        }

    tenant_id = state.get("tenant_id")
    if not tenant_id or not db:
        return {
            "status": "error",
            "message": "No se pudo verificar disponibilidad (sin conexión a base de datos).",
        }

    try:
        from src.shared.links.ports.scheduling import create_scheduling_port

        tid = UUID(str(tenant_id)) if not isinstance(tenant_id, UUID) else tenant_id
        service = create_scheduling_port(db=db, tenant_id=tid)
        if service is None or not service.is_connected():
            return {
                "status": "error",
                "message": "Google Calendar no está conectado para este tenant.",
            }
        return {
            "status": "success",
            "message": "Agenda disponible. Puedo ayudarte a agendar una llamada.",
            "calendar_type_id": str(calendar_type_id),
        }
    except Exception as e:
        logger.exception("tool_check_schedule_error", error=str(e))
        return {"status": "error", "message": "Error verificando disponibilidad."}


def tool_recommend_product(state: dict[str, Any], db: Any = None) -> dict[str, Any]:  # noqa: ANN401 — dynamic type (optional DB session)
    """Recommends best-fit offer based on lead profile."""
    qa = state.get("qualification_answers") or {}
    return {
        "status": "success",
        "message": "Basado en lo que me cuentas, la mejor opción para ti sería...",
        "lead_context": {
            "pain": qa.get("main_pain", ""),
            "budget": qa.get("budget_range", ""),
            "timeline": qa.get("timeline", ""),
        },
    }


def tool_escalate_to_human(state: dict[str, Any], db: Any = None) -> dict[str, str]:  # noqa: ANN401 — dynamic type (optional DB session)
    """Flag the conversation for human takeover."""
    return {
        "status": "escalated",
        "message": (
            "Entiendo perfectamente. Voy a conectarte con alguien de nuestro "
            "equipo que puede ayudarte mejor con esto. Dame un momento."
        ),
    }


TOOL_REGISTRY: dict[str, Any] = {
    "send_payment_link": tool_send_payment_link,
    "check_schedule": tool_check_schedule,
    "recommend_product": tool_recommend_product,
    "escalate_to_human": tool_escalate_to_human,
}
