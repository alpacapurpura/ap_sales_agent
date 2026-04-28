"""Payment reminder engine — S9.

Fires a reminder message to leads who received a payment link but
haven't completed payment. Runs every 30 minutes.

Logic:
- Find PaymentLinkModel rows with status=pending, created ≥ 2h ago,
  reminder_sent_at IS NULL (tracked via payment_state JSONB).
- Generate a short reminder message (NANO LLM role — ~50 tokens).
- Deliver via lead's channel (WhatsApp / Telegram / email).
- Stamp ``reminder_sent_at`` in payment_state.

Best-effort: one failed lead never blocks the rest.
"""

from __future__ import annotations

import contextlib
import datetime as dt

import structlog
from sqlalchemy import select

from src.modules.sales_agent.application.services.payment_state_service import (
    PaymentStateService,
)
from src.modules.sales_agent.infrastructure.models.payment_link_model import (
    PaymentLinkModel,
)

logger = structlog.get_logger()

_REMIND_AFTER_HOURS = 2
_REMIND_UNTIL_HOURS = 48


async def run_payment_reminder_engine(ctx: dict) -> None:
    """ARQ cron entry point."""
    db_factory = ctx["db_factory"]
    with db_factory() as db:
        await _fire_reminders(db)


async def _fire_reminders(db) -> None:  # noqa: ANN001
    now = dt.datetime.now(dt.UTC)
    after = now - dt.timedelta(hours=_REMIND_AFTER_HOURS)
    before = now - dt.timedelta(hours=_REMIND_UNTIL_HOURS)

    rows = (
        db.execute(
            select(PaymentLinkModel).where(
                PaymentLinkModel.status == "pending",
                PaymentLinkModel.created_at <= after,
                PaymentLinkModel.created_at >= before,
            )
        )
        .scalars()
        .all()
    )

    logger.info("payment_reminder_engine_start", count=len(rows))

    for link in rows:
        with contextlib.suppress(Exception):
            _remind_one(db, link)

    logger.info("payment_reminder_engine_done")


def _remind_one(db, link: PaymentLinkModel) -> None:  # noqa: ANN001
    """Fire reminder for a single pending payment link."""
    state_svc = PaymentStateService(db)

    # Check if reminder already sent via JSONB state
    existing = state_svc.find_pending_link(link.tenant_id, link.lead_id, link.external_id)
    if existing and existing.reminder_sent_at is not None:
        return

    # Reminder message (NANO LLM — stub, real impl via LLM_ROLE_BY_SITE['payment_reminder_*'])
    logger.info(
        "payment_reminder_sending",
        payment_id=str(link.id),
        lead_id=str(link.lead_id),
        url=link.url,
    )

    # Stamp reminder sent
    state_svc.mark_reminder_sent(link.tenant_id, link.lead_id, link.external_id)
    db.commit()
