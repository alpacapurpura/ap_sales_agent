"""Enrollment-aware tools for the sales agent (Phase 6).

Seven tools that let the agent discover editions, inscribe leads, send
payment links, and manage waitlists. Every tool receives the agent state
and a synchronous ``Session``; every tool is tenant-safe via
``state['tenant_id']``.

Return shape matches the existing sales tools: a dict with ``status`` and
``message`` keys. Additional structured data (edition list, URL, etc.)
sits next to those keys so the LLM reads it verbatim.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

import structlog
from luana_core_platform.links.ports.offer import get_launch_edition_repository
from luana_core_sales_agent.application.services.enrollment_service import (
    EnrollmentService,
)
from luana_core_sales_agent.domain.enrollment import (
    EnrollmentCreate,
    EnrollmentStatus,
    PaymentProvider,
)
from luana_core_sales_agent.infrastructure.repositories.enrollment_repository import (
    EnrollmentRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = structlog.get_logger()


# ────────────────────────────────────────────────────────────────────────────
# helpers
# ────────────────────────────────────────────────────────────────────────────


def _require(state: dict[str, Any], key: str) -> Any:  # noqa: ANN401 — state values are heterogeneous
    value = state.get(key)
    if value is None:
        msg = f"missing '{key}' in agent state"
        raise ValueError(msg)
    return value


def _coerce_uuid(raw: Any) -> UUID:  # noqa: ANN401 — tools accept str/UUID
    return raw if isinstance(raw, UUID) else UUID(str(raw))


def _error(message: str) -> dict[str, str]:
    return {"status": "error", "message": message}


# ────────────────────────────────────────────────────────────────────────────
# 1. list_public_editions
# ────────────────────────────────────────────────────────────────────────────


def tool_list_public_editions(state: dict[str, Any], db: Session) -> dict[str, Any]:
    """List editions the agent may offer: UPCOMING/ACTIVE + PUBLIC."""
    if db is None:
        return _error("Sin conexión a base de datos.")
    product = state.get("active_product") or {}
    offer_id = product.get("id") or state.get("offer_id")
    if not offer_id:
        return _error("No hay oferta activa en el estado de la conversación.")

    tenant_id = _coerce_uuid(_require(state, "tenant_id"))
    repo = get_launch_edition_repository(db)
    editions = repo.list_public(_coerce_uuid(offer_id), tenant_id)

    serialised = [
        {
            "id": str(e.id),
            "edition_number": e.edition_number,
            "name": e.edition_name,
            "status": e.status.value,
            "start_date": e.start_date.isoformat() if e.start_date else None,
            "end_date": e.end_date.isoformat() if e.end_date else None,
            "capacity": e.capacity,
            "enrollment_count": e.enrollment_count,
            "seats_remaining": (e.capacity - e.enrollment_count) if e.capacity else None,
        }
        for e in editions
    ]
    msg = (
        f"Hay {len(serialised)} edición(es) pública(s) disponibles."
        if serialised
        else "No hay edición pública abierta. Ofrecé lista de espera."
    )
    return {"status": "success", "message": msg, "editions": serialised}


# ────────────────────────────────────────────────────────────────────────────
# 2. create_enrollment
# ────────────────────────────────────────────────────────────────────────────


def tool_create_enrollment(state: dict[str, Any], db: Session) -> dict[str, Any]:
    """Create an INTENT enrollment (or WAITLIST if edition_id missing)."""
    if db is None:
        return _error("Sin conexión a base de datos.")

    args = state.get("_tool_args", {}) or {}
    offer_id = args.get("offer_id") or (state.get("active_product") or {}).get("id")
    edition_id = args.get("edition_id")
    contact_id = args.get("contact_id") or state.get("lead_id")
    if not offer_id or not contact_id:
        return _error("Faltan offer_id o contact_id para crear inscripción.")

    tenant_id = _coerce_uuid(_require(state, "tenant_id"))
    service = EnrollmentService(EnrollmentRepository(db))
    payload = EnrollmentCreate(
        offer_id=_coerce_uuid(offer_id),
        contact_id=_coerce_uuid(contact_id),
        edition_id=_coerce_uuid(edition_id) if edition_id else None,
        conversation_id=_coerce_uuid(state["conversation_id"]) if state.get("conversation_id") else None,
        status=EnrollmentStatus.INTENT,
        source_channel=state.get("channel"),
    )
    try:
        result = service.create(payload, tenant_id)
    except Exception as exc:
        logger.exception("create_enrollment_failed", error=str(exc))
        return _error(f"No pude crear la inscripción: {exc}")

    db.commit()
    return {
        "status": "success",
        "message": (
            "Lead anotado en lista de espera."
            if result.enrollment.status == EnrollmentStatus.WAITLIST
            else "Intent de inscripción registrado."
        ),
        "enrollment_id": str(result.enrollment.id),
        "enrollment_status": result.enrollment.status.value,
    }


# ────────────────────────────────────────────────────────────────────────────
# 3. generate_payment_link
# ────────────────────────────────────────────────────────────────────────────


def tool_generate_payment_link(state: dict[str, Any], db: Session) -> dict[str, Any]:
    """Return (or stub) a payment URL for an enrollment.

    Until real Stripe/MP/Culqi webhook plumbing lands (tracked separately),
    we fall back to the static ``checkout_page_url`` on the offer and mark
    the enrollment status as ``PAYMENT_PENDING`` with that URL stored in
    ``payment_link_url``.
    """
    if db is None:
        return _error("Sin conexión a base de datos.")

    args = state.get("_tool_args", {}) or {}
    enrollment_id = args.get("enrollment_id")
    if not enrollment_id:
        return _error("Falta enrollment_id para generar link.")

    tenant_id = _coerce_uuid(_require(state, "tenant_id"))
    repo = EnrollmentRepository(db)
    enrollment = repo.get_by_id(_coerce_uuid(enrollment_id), tenant_id)
    if enrollment is None:
        return _error("No encontré la inscripción para generar el link.")

    product = state.get("active_product") or {}
    fallback_url = product.get("checkout_page_url")
    if not fallback_url:
        return _error("La oferta no tiene link de pago configurado.")

    repo.update(
        _coerce_uuid(enrollment_id),
        tenant_id,
        {
            "status": EnrollmentStatus.PAYMENT_PENDING,
            "payment_link_url": fallback_url,
        },
    )
    db.commit()
    return {
        "status": "success",
        "message": f"Link de pago generado: {fallback_url}",
        "url": fallback_url,
        "enrollment_id": str(enrollment_id),
    }


# ────────────────────────────────────────────────────────────────────────────
# 4. mark_enrollment_paid_manual
# ────────────────────────────────────────────────────────────────────────────


def tool_mark_enrollment_paid_manual(state: dict[str, Any], db: Session) -> dict[str, Any]:
    """Manual mark-paid path (used when webhook is absent or human confirms)."""
    if db is None:
        return _error("Sin conexión a base de datos.")

    args = state.get("_tool_args", {}) or {}
    enrollment_id = args.get("enrollment_id")
    if not enrollment_id:
        return _error("Falta enrollment_id.")

    tenant_id = _coerce_uuid(_require(state, "tenant_id"))
    service = EnrollmentService(EnrollmentRepository(db))
    try:
        result = service.mark_paid(
            _coerce_uuid(enrollment_id),
            tenant_id,
            provider=PaymentProvider(args.get("provider", "manual")),
            transaction_id=args.get("transaction_id"),
        )
    except Exception as exc:
        logger.exception("mark_paid_failed", error=str(exc))
        return _error(str(exc))

    db.commit()
    return {
        "status": "success",
        "message": "Inscripción marcada como pagada.",
        "enrollment_id": str(result.enrollment.id),
    }


# ────────────────────────────────────────────────────────────────────────────
# 5. list_waitlist
# ────────────────────────────────────────────────────────────────────────────


def tool_list_waitlist(state: dict[str, Any], db: Session) -> dict[str, Any]:
    """List the current waitlist for the active offer."""
    if db is None:
        return _error("Sin conexión a base de datos.")
    product = state.get("active_product") or {}
    offer_id = product.get("id") or state.get("offer_id")
    if not offer_id:
        return _error("No hay oferta activa.")

    tenant_id = _coerce_uuid(_require(state, "tenant_id"))
    repo = EnrollmentRepository(db)
    items = repo.list_waitlist(_coerce_uuid(offer_id), tenant_id)
    serialised = [
        {
            "id": str(e.id),
            "contact_id": str(e.contact_id),
            "created_at": e.created_at.isoformat() if e.created_at else None,
            "source_channel": e.source_channel,
        }
        for e in items
    ]
    return {
        "status": "success",
        "message": f"Waitlist actual: {len(serialised)} leads.",
        "waitlist": serialised,
    }


# ────────────────────────────────────────────────────────────────────────────
# 6. promote_waitlist_to_edition
# ────────────────────────────────────────────────────────────────────────────


def tool_promote_waitlist_to_edition(state: dict[str, Any], db: Session) -> dict[str, Any]:
    """Bulk-promote a list of waitlist enrollments to a target edition."""
    if db is None:
        return _error("Sin conexión a base de datos.")
    args = state.get("_tool_args", {}) or {}
    enrollment_ids = args.get("enrollment_ids") or []
    target_edition_id = args.get("target_edition_id")
    if not enrollment_ids or not target_edition_id:
        return _error("Faltan enrollment_ids o target_edition_id.")

    tenant_id = _coerce_uuid(_require(state, "tenant_id"))
    service = EnrollmentService(EnrollmentRepository(db))
    results = service.promote_waitlist(
        [_coerce_uuid(i) for i in enrollment_ids],
        _coerce_uuid(target_edition_id),
        tenant_id,
    )
    db.commit()
    return {
        "status": "success",
        "message": f"Promovidos {len(results)} de {len(enrollment_ids)}.",
        "promoted_ids": [str(r.enrollment.id) for r in results],
    }


# ────────────────────────────────────────────────────────────────────────────
# 7. check_payment_status
# ────────────────────────────────────────────────────────────────────────────


def tool_check_payment_status(state: dict[str, Any], db: Session) -> dict[str, Any]:
    """Return the current enrollment status (thin passthrough to DB)."""
    if db is None:
        return _error("Sin conexión a base de datos.")
    args = state.get("_tool_args", {}) or {}
    enrollment_id = args.get("enrollment_id")
    if not enrollment_id:
        return _error("Falta enrollment_id.")

    tenant_id = _coerce_uuid(_require(state, "tenant_id"))
    repo = EnrollmentRepository(db)
    enrollment = repo.get_by_id(_coerce_uuid(enrollment_id), tenant_id)
    if enrollment is None:
        return _error("Inscripción no encontrada.")
    return {
        "status": "success",
        "message": f"Estado actual: {enrollment.status.value}",
        "enrollment_status": enrollment.status.value,
        "paid_at": enrollment.paid_at.isoformat() if enrollment.paid_at else None,
    }


# ────────────────────────────────────────────────────────────────────────────
# registry
# ────────────────────────────────────────────────────────────────────────────


ENROLLMENT_TOOL_REGISTRY: dict[str, Any] = {
    "list_public_editions": tool_list_public_editions,
    "create_enrollment": tool_create_enrollment,
    "generate_payment_link": tool_generate_payment_link,
    "mark_enrollment_paid_manual": tool_mark_enrollment_paid_manual,
    "list_waitlist": tool_list_waitlist,
    "promote_waitlist_to_edition": tool_promote_waitlist_to_edition,
    "check_payment_status": tool_check_payment_status,
}
