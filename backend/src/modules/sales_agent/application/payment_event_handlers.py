"""Sales-agent subscribers to payment-related domain events — S9.

``auto_grant_on_paid`` subscribes to ``PaymentReceivedEvent``.
When ``event.auto_grant=True`` it fires ``tool_grant_access`` to deliver
digital access to the lead.

Coupling discipline:
* Each handler opens a short-lived ``SessionLocal()`` (best-effort).
* Failures NEVER propagate back to the webhook endpoint.
* Idempotent: ``grant_access`` tool handles duplicate via audit UNIQUE key.
"""

from __future__ import annotations

import structlog

from src.core.database import SessionLocal
from src.shared.domain.events import (
    DomainEvent,
    EventBus,
    PaymentReceivedEvent,
)

logger = structlog.get_logger()


def auto_grant_on_paid(event: DomainEvent) -> None:
    """Grant access after payment confirmation if auto_grant=True."""
    if not isinstance(event, PaymentReceivedEvent):
        return

    if not event.auto_grant:
        logger.info(
            "auto_grant_skipped",
            tenant_id=str(event.tenant_id),
            reason="auto_grant=False",
        )
        return

    try:
        with SessionLocal() as db:
            _run_grant_access(
                db=db,
                tenant_id=event.tenant_id,
                lead_id=event.lead_id,
                offer_id=event.offer_id,
                payment_id=event.payment_id,
            )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "auto_grant_failed",
            error=str(exc),
            tenant_id=str(event.tenant_id),
        )


def _run_grant_access(*, db, tenant_id, lead_id, offer_id, payment_id) -> None:  # noqa: ANN001
    """Execute grant_access tool inside a DB session."""
    from src.modules.sales_agent.application.tools.payment.tools import (
        tool_grant_access,
    )

    state = {
        "tenant_id": str(tenant_id),
        "lead_id": str(lead_id),
        "active_product": {"id": str(offer_id)},
        "_tool_args": {"payment_id": str(payment_id)},
    }
    result = tool_grant_access(state, db)
    logger.info(
        "auto_grant_result",
        granted=result.get("granted"),
        duplicate=result.get("duplicate"),
        tenant_id=str(tenant_id),
    )


def register_payment_subscribers() -> None:
    """Register all payment event subscribers. Call once at startup."""
    EventBus.subscribe("payment_received", auto_grant_on_paid)
