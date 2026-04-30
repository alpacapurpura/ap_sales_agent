"""Cron worker: verify pending bookings + flag missed appointments (S8).

Runs every 15 minutes. Two responsibilities, kept in one worker for
cohesion (both read the same JSONB list and reconcile against the
scheduler's source of truth):

1. **Expire unused booking links.** ``BookingLink`` rows past their
   ``expires_at`` whose ``MeetingEntry`` is still ``LINK_CREATED`` are
   transitioned to ``EXPIRED`` locally. Provides offline reconciliation
   when no webhook arrives (Internal scheduler emits via book endpoint
   but external providers may drop events).

2. **Detect missed meetings.** ``Appointment`` rows past
   ``start_time + grace`` (default 30 min) whose status is still
   ``SCHEDULED`` are surfaced via ``BookingMissedEvent`` so the reminder
   engine can fire the postcheck nudge. Distinct from
   ``appointment_no_show`` (admin-set status) — this is *inferred* lag
   between calendar and reality.

Cohesion: pure reconciler — no LLM, no message send, no external HTTP.
Best-effort writes; one failed checkpoint never blocks the rest.
"""

# [SALES-AGENT-S8-CRON]  # noqa: ERA001

from __future__ import annotations

import contextlib

import structlog
from sqlalchemy import select

from src.modules.sales_agent.application.services.meeting_state_service import (
    MeetingEntry,
    MeetingEntryStatus,
    MeetingStateService,
)
from src.modules.sales_agent.application.tools.scheduling.providers import (
    BookingStatusValue,
    InternalSchedulerProvider,
)
from src.modules.sales_agent.infrastructure.models.agent_state_checkpoint_model import (
    AgentStateCheckpointModel,
)
from src.shared.domain.events import BookingMissedEvent
from src.shared.domain_events.outbox.application.event_bus_adapter import (
    adapter_bus as EventBus,  # noqa: N812
)

logger = structlog.get_logger()


_TERMINAL = frozenset(
    {
        MeetingEntryStatus.COMPLETED,
        MeetingEntryStatus.NO_SHOW,
        MeetingEntryStatus.CANCELLED,
        MeetingEntryStatus.EXPIRED,
        MeetingEntryStatus.MISSED,
    },
)


async def run_verify_pending_bookings(ctx: dict) -> None:
    """Reconcile scheduled_meetings against scheduler ground truth."""
    db_factory = ctx["db_factory"]
    db = db_factory()

    expired_count = 0
    missed_count = 0
    confirmed_count = 0

    try:
        stmt = select(AgentStateCheckpointModel).where(
            AgentStateCheckpointModel.is_active.is_(True),
            AgentStateCheckpointModel.deleted_at.is_(None),
            AgentStateCheckpointModel.scheduled_meetings.isnot(None),
        )
        checkpoints = db.execute(stmt).scalars().all()

        provider = InternalSchedulerProvider(db)
        state_service = MeetingStateService(db)

        for cp in checkpoints:
            try:
                stats = _process_checkpoint(cp, provider, state_service)
                expired_count += stats[0]
                missed_count += stats[1]
                confirmed_count += stats[2]
            except Exception as exc:
                logger.exception(
                    "verify_pending_bookings_checkpoint_failed",
                    lead_id=str(cp.lead_id),
                    error=str(exc),
                )
                continue

        db.commit()
        logger.info(
            "verify_pending_bookings_complete",
            expired=expired_count,
            missed=missed_count,
            confirmed=confirmed_count,
        )
    except Exception as exc:
        logger.exception("verify_pending_bookings_failed", error=str(exc))
        with contextlib.suppress(Exception):
            db.rollback()
    finally:
        db.close()


def _process_checkpoint(
    cp: AgentStateCheckpointModel,
    provider: InternalSchedulerProvider,
    state_service: MeetingStateService,
) -> tuple[int, int, int]:
    """Return (expired_added, missed_added, confirmed_added) deltas."""
    expired_added = 0
    missed_added = 0
    confirmed_added = 0

    raw_list = cp.scheduled_meetings or []
    for raw in list(raw_list):
        entry = MeetingEntry.from_jsonb(raw)
        if entry.status in _TERMINAL:
            continue

        # Pull canonical status from provider (handles link expiry + appt
        # status promotion + missed inference in one place).
        status = provider.verify_booking_status(
            tenant_id=cp.tenant_id,
            lead_id=cp.lead_id,
            tracking_id=entry.tracking_id,
        )

        new_status = _map_status(status.status)
        if new_status is None or new_status == entry.status:
            continue

        state_service.update_status_by_tracking(
            cp.tenant_id,
            cp.lead_id,
            tracking_id=entry.tracking_id,
            status=new_status,
            appointment_id=status.appointment_id,
            scheduled_at=status.scheduled_at,
        )

        if new_status == MeetingEntryStatus.EXPIRED:
            expired_added += 1
        elif new_status == MeetingEntryStatus.MISSED and status.appointment_id and status.scheduled_at:
            missed_added += 1
            EventBus.publish(
                BookingMissedEvent.create(
                    tenant_id=cp.tenant_id,
                    lead_id=cp.lead_id,
                    appointment_id=status.appointment_id,
                    scheduled_at=status.scheduled_at,
                ),
                session=None,
            )
        elif new_status == MeetingEntryStatus.CONFIRMED:
            confirmed_added += 1

    return expired_added, missed_added, confirmed_added


def _map_status(value: BookingStatusValue) -> MeetingEntryStatus | None:
    """Translate provider-level status to local entry status."""
    return {
        BookingStatusValue.CONFIRMED: MeetingEntryStatus.CONFIRMED,
        BookingStatusValue.COMPLETED: MeetingEntryStatus.COMPLETED,
        BookingStatusValue.NO_SHOW: MeetingEntryStatus.NO_SHOW,
        BookingStatusValue.MISSED: MeetingEntryStatus.MISSED,
        BookingStatusValue.CANCELLED: MeetingEntryStatus.CANCELLED,
        BookingStatusValue.EXPIRED: MeetingEntryStatus.EXPIRED,
    }.get(value)


__all__ = ["run_verify_pending_bookings"]
