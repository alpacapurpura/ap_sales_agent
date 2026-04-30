"""Cron worker: verify pending payment links + update status (S9).

Runs every 15 minutes (offset from verify_pending_bookings).
Reconciles ``payment_link`` rows still in ``pending`` status against
the payment provider — acts as fallback when webhooks are delayed or
dropped.

For each PENDING PaymentLinkModel:
1. Call ``provider.verify_payment(external_id)``.
2. If PAID: update local status + fire ``PaymentReceivedEvent`` so
   ``auto_grant_on_paid`` fires grant_access.
3. If FAILED / CANCELLED / EXPIRED: update status, no event.

Best-effort: one failed link never blocks the rest.
"""

from __future__ import annotations

import contextlib
import datetime as dt

import structlog
from sqlalchemy import select

from src.modules.sales_agent.application.tools.payment.providers import (
    PaymentStatusEnum,
    payment_provider_for_tenant,
)
from src.modules.sales_agent.infrastructure.models.payment_link_model import (
    PaymentLinkModel,
)
from src.shared.domain.events import PaymentReceivedEvent
from src.shared.domain_events.outbox.application.event_bus_adapter import (
    adapter_bus as EventBus,  # noqa: N812
)

logger = structlog.get_logger()

_TERMINAL_STATUSES = frozenset(
    {
        PaymentStatusEnum.PAID.value,
        PaymentStatusEnum.FAILED.value,
        PaymentStatusEnum.REFUNDED.value,
        PaymentStatusEnum.EXPIRED.value,
        PaymentStatusEnum.CANCELLED.value,
    }
)

_STALE_HOURS = 48


async def run_verify_pending_payments(ctx: dict) -> None:
    """ARQ cron entry point."""
    db_factory = ctx["db_factory"]
    with db_factory() as db:
        await _reconcile(db)


async def _reconcile(db) -> None:  # noqa: ANN001
    cutoff = dt.datetime.now(dt.UTC) - dt.timedelta(hours=_STALE_HOURS)
    rows = (
        db.execute(
            select(PaymentLinkModel).where(
                PaymentLinkModel.status == "pending",
                PaymentLinkModel.created_at >= cutoff,
            )
        )
        .scalars()
        .all()
    )

    logger.info("verify_pending_payments_start", count=len(rows))

    for link in rows:
        with contextlib.suppress(Exception):
            _check_one(db, link)

    logger.info("verify_pending_payments_done")


def _check_one(db, link: PaymentLinkModel) -> None:  # noqa: ANN001
    """Poll provider for a single pending link."""
    try:
        provider = payment_provider_for_tenant(db, link.tenant_id)
        remote_status = provider.verify_payment(link.external_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "verify_payment_provider_error",
            payment_id=str(link.id),
            error=str(exc),
        )
        return

    if remote_status.value == link.status:
        return

    link.status = remote_status.value
    db.flush()

    if remote_status == PaymentStatusEnum.PAID:
        try:
            EventBus.publish(
                PaymentReceivedEvent.create(
                    tenant_id=link.tenant_id,
                    lead_id=link.lead_id,
                    offer_id=link.offer_id,
                    payment_id=link.id,
                    auto_grant=True,
                ),
                session=db,
            )
            db.commit()
        except Exception as exc:  # noqa: BLE001
            logger.warning("payment_received_event_publish_failed", error=str(exc))
    else:
        db.commit()
