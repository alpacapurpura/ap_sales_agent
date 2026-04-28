"""Sales-agent scheduling tools (S8).

Three dict-style tools that the LLM invokes via
``[TOOL_REQUEST: {"tool": "<name>", "args": {...}}]`` blocks:

* ``create_booking_link``       — issue single-use booking URL.
* ``verify_booking_status``     — resolve status by tracking_id.
* ``get_available_slots``       — list upcoming slots for an event slug.

They follow the **existing pattern** (``application/agents/sales/tools.py``):
``def tool_xxx(state: dict, db: Session) -> dict`` returning
``{"status": "...", "message": "...", ...}``. No ``@tool`` decorator —
LangChain ToolNode is not used by the sales orchestrator.

Cohesion + DRY:

* All persistence goes through ``MeetingStateService``.
* All scheduler I/O goes through ``SchedulerProvider`` (Strategy).
* Domain events go through ``EventBus``.
* No tool branches on ``provider_id`` — registry-based dispatch.
"""

# [SALES-AGENT-S8-TOOLS]  # noqa: ERA001

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

import structlog

from src.modules.sales_agent.application.services.meeting_state_service import (
    MeetingEntryStatus,
    MeetingStateService,
)
from src.modules.sales_agent.application.tools.scheduling.providers import (
    BookingStatusValue,
    scheduler_provider_for_tenant,
)
from src.shared.domain.events import (
    BookingLinkCreatedEvent,
    EventBus,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = structlog.get_logger()


# ──────────────────────────────────────────────────────────────
# helpers (mirror enrollment_tools.py pattern)
# ──────────────────────────────────────────────────────────────


def _coerce_uuid(raw: Any) -> UUID:  # noqa: ANN401 — heterogeneous state values
    return raw if isinstance(raw, UUID) else UUID(str(raw))


def _require(state: dict[str, Any], key: str) -> Any:  # noqa: ANN401
    value = state.get(key)
    if value is None:
        msg = f"missing '{key}' in agent state"
        raise ValueError(msg)
    return value


def _error(message: str) -> dict[str, str]:
    return {"status": "error", "message": message}


def _infer_event_slug(state: dict[str, Any]) -> str | None:
    """Pick the event_slug from active offer when the LLM omits it."""
    product = state.get("active_product") or {}
    return product.get("scheduling_event_slug") or product.get("calendar_event_slug")


# ──────────────────────────────────────────────────────────────
# 1. create_booking_link
# ──────────────────────────────────────────────────────────────


def tool_create_booking_link(state: dict[str, Any], db: Session) -> dict[str, Any]:
    """Generate a single-use booking URL for the lead.

    Idempotency: if an ACTIVE non-expired link for the same
    ``(tenant, lead, event_slug)`` exists, the same URL is returned
    instead of issuing a new token. Avoids double-link spam if the LLM
    re-fires the tool inside one turn.
    """
    if db is None:
        return _error("Sin conexión a base de datos.")

    args = state.get("_tool_args") or {}
    tenant_id = _coerce_uuid(_require(state, "tenant_id"))
    lead_id = _coerce_uuid(_require(state, "lead_id"))

    event_slug = args.get("event_slug") or _infer_event_slug(state)
    if not event_slug:
        return _error(
            "No hay event_slug configurado para esta oferta. "
            "Pídele al equipo que conecte un tipo de evento al producto.",
        )

    expires_in_hours = int(args.get("expires_in_hours", 72))
    if expires_in_hours <= 0 or expires_in_hours > 720:  # cap 30 days
        return _error("expires_in_hours fuera de rango (1..720).")

    state_service = MeetingStateService(db)
    existing = state_service.find_active_link(tenant_id, lead_id, event_slug)
    if existing is not None:
        return {
            "status": "success",
            "url": _reconstruct_url_from_existing(state, existing.tracking_id, event_slug),
            "tracking_id": existing.tracking_id,
            "expires_at": existing.expires_at.isoformat(),
            "reused": True,
            "message": "Link de agenda activo reutilizado.",
        }

    provider = scheduler_provider_for_tenant(db, tenant_id)
    try:
        booking = provider.create_booking_link(
            tenant_id=tenant_id,
            lead_id=lead_id,
            event_slug=event_slug,
            expires_in_hours=expires_in_hours,
        )
    except Exception as exc:
        logger.exception("create_booking_link_failed", error=str(exc))
        return _error("No pude generar el link de agenda. Intentemos en un momento.")

    state_service.append_link(tenant_id, lead_id, booking)
    db.commit()

    EventBus.publish(
        BookingLinkCreatedEvent.create(
            tenant_id=tenant_id,
            lead_id=lead_id,
            tracking_id=booking.tracking_id,
            event_slug=booking.event_slug,
            expires_at=booking.expires_at,
            provider_id=booking.provider_id,
        ),
        session=None,
    )

    response = booking.as_tool_response()
    response.update(
        {
            "status": "success",
            "reused": False,
            "message": f"Link de agenda generado: {booking.url}",
        },
    )
    return response


# ──────────────────────────────────────────────────────────────
# 2. verify_booking_status
# ──────────────────────────────────────────────────────────────


def tool_verify_booking_status(state: dict[str, Any], db: Session) -> dict[str, Any]:
    """Resolve current high-level status of a tracking_id."""
    if db is None:
        return _error("Sin conexión a base de datos.")

    args = state.get("_tool_args") or {}
    tracking_id = args.get("tracking_id")
    if not tracking_id:
        return _error("Falta tracking_id.")

    tenant_id = _coerce_uuid(_require(state, "tenant_id"))
    lead_id = _coerce_uuid(_require(state, "lead_id"))

    provider = scheduler_provider_for_tenant(db, tenant_id)
    try:
        status = provider.verify_booking_status(
            tenant_id=tenant_id,
            lead_id=lead_id,
            tracking_id=str(tracking_id),
        )
    except Exception as exc:
        logger.exception("verify_booking_status_failed", error=str(exc))
        return _error("No pude verificar el estado de la reserva.")

    # Reflect status into local JSONB if the provider says it transitioned.
    state_service = MeetingStateService(db)
    if status.status == BookingStatusValue.CONFIRMED:
        state_service.update_status_by_tracking(
            tenant_id,
            lead_id,
            tracking_id=status.tracking_id,
            status=MeetingEntryStatus.CONFIRMED,
            appointment_id=status.appointment_id,
            scheduled_at=status.scheduled_at,
        )
        db.commit()
    elif status.status == BookingStatusValue.EXPIRED:
        state_service.update_status_by_tracking(
            tenant_id,
            lead_id,
            tracking_id=status.tracking_id,
            status=MeetingEntryStatus.EXPIRED,
        )
        db.commit()

    response = status.as_tool_response()
    response.update(
        {
            "status": "success",
            "message": _humanize_status(status.status),
        },
    )
    return response


# ──────────────────────────────────────────────────────────────
# 3. get_available_slots
# ──────────────────────────────────────────────────────────────


def tool_get_available_slots(state: dict[str, Any], db: Session) -> dict[str, Any]:
    """List upcoming slots for an event slug."""
    if db is None:
        return _error("Sin conexión a base de datos.")

    args = state.get("_tool_args") or {}
    tenant_id = _coerce_uuid(_require(state, "tenant_id"))
    event_slug = args.get("event_slug") or _infer_event_slug(state)
    if not event_slug:
        return _error("No hay event_slug configurado para esta oferta.")

    days_ahead = int(args.get("days_ahead", 14))
    days_ahead = max(1, min(days_ahead, 60))

    provider = scheduler_provider_for_tenant(db, tenant_id)
    try:
        slots = provider.get_available_slots(
            tenant_id=tenant_id,
            event_slug=event_slug,
            days_ahead=days_ahead,
        )
    except Exception as exc:
        logger.exception("get_available_slots_failed", error=str(exc))
        return _error("No pude consultar disponibilidad.")

    if not slots:
        return {
            "status": "success",
            "slots": [],
            "message": ("No hay horarios disponibles en los próximos días. ¿Te aviso cuando se abra un nuevo bloque?"),
        }

    serialized = [s.as_tool_response() for s in slots[:25]]  # cap LLM payload
    return {
        "status": "success",
        "slots": serialized,
        "message": f"{len(serialized)} horario(s) disponible(s) en los próximos {days_ahead} días.",
    }


# ──────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────


def _humanize_status(status: BookingStatusValue) -> str:
    """Spanish-neutro LATAM message describing a status (default voice).

    The reminder engine renders **brand-voice** messages via Jinja + LLM;
    this is the bare default the LLM sees in the tool result for context.
    """
    return {
        BookingStatusValue.PENDING: "Aún no completó la reserva.",
        BookingStatusValue.CONFIRMED: "Reserva confirmada.",
        BookingStatusValue.COMPLETED: "Reunión completada.",
        BookingStatusValue.NO_SHOW: "El lead no asistió.",
        BookingStatusValue.MISSED: "Pasó la hora sin marcar asistencia.",
        BookingStatusValue.CANCELLED: "Reserva cancelada.",
        BookingStatusValue.EXPIRED: "El link expiró sin uso.",
        BookingStatusValue.UNKNOWN: "No encontré información del tracking_id.",
    }[status]


def _reconstruct_url_from_existing(
    state: dict[str, Any],
    tracking_id: str,
    event_slug: str,
) -> str:
    """Rebuild a known booking URL when reusing an active link.

    The token + slug + tenant_slug are stable; the URL composition is
    deterministic. We piggy-back on the active product's scheduler URL
    snapshot if present, else compose against ``DASHBOARD_DOMAIN``.
    """
    product = state.get("active_product") or {}
    base = product.get("booking_base_url")
    tenant_slug = state.get("tenant_slug") or product.get("tenant_slug") or "tenant"
    if base:
        return f"{base}/book/{tenant_slug}/{event_slug}?token={tracking_id}"
    from src.core.config import settings

    return f"{settings.DASHBOARD_DOMAIN}/book/{tenant_slug}/{event_slug}?token={tracking_id}"


# ──────────────────────────────────────────────────────────────
# registry export
# ──────────────────────────────────────────────────────────────


SCHEDULING_TOOL_REGISTRY: dict[str, Any] = {
    "create_booking_link": tool_create_booking_link,
    "verify_booking_status": tool_verify_booking_status,
    "get_available_slots": tool_get_available_slots,
}
