"""S8 — MeetingStateService unit tests.

Round-trips the JSONB schema, idempotency lookup, and stamp updates.
"""

from __future__ import annotations

import datetime as dt
import uuid

import pytest

from src.modules.sales_agent.application.services.meeting_state_service import (
    MeetingEntry,
    MeetingEntryStatus,
    MeetingStateService,
)
from src.modules.sales_agent.application.tools.scheduling.providers import (
    BookingLinkOutput,
)
from src.modules.sales_agent.infrastructure.models.agent_state_checkpoint_model import (
    AgentStateCheckpointModel,
)


@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.UUID("aaaa0000-0000-0000-0000-000000000001")


@pytest.fixture
def lead_id() -> uuid.UUID:
    return uuid.UUID("bbbb0000-0000-0000-0000-000000000002")


@pytest.fixture
def checkpoint(db, tenant_id: uuid.UUID, lead_id: uuid.UUID) -> AgentStateCheckpointModel:
    cp = AgentStateCheckpointModel(
        id=uuid.uuid4(),
        session_id="s8-test",
        tenant_id=tenant_id,
        lead_id=lead_id,
        channel_type="whatsapp",
        current_stage="presentation",
        scheduled_meetings=[],
    )
    db.add(cp)
    db.commit()
    return cp


def _booking(provider_id: str = "internal") -> BookingLinkOutput:
    return BookingLinkOutput(
        tracking_id="tok-" + uuid.uuid4().hex[:8],
        url="https://example.com/book/tenant/discovery?token=tok",
        event_slug="discovery-call",
        expires_at=dt.datetime.now(dt.UTC) + dt.timedelta(hours=72),
        provider_id=provider_id,
    )


def test_append_link_persists_jsonb_entry(db, tenant_id, lead_id, checkpoint) -> None:
    service = MeetingStateService(db)
    booking = _booking()

    entry = service.append_link(tenant_id, lead_id, booking)
    db.commit()
    db.refresh(checkpoint)

    assert entry.tracking_id == booking.tracking_id
    assert entry.status == MeetingEntryStatus.LINK_CREATED
    assert len(checkpoint.scheduled_meetings) == 1
    assert checkpoint.scheduled_meetings[0]["tracking_id"] == booking.tracking_id


def test_find_active_link_idempotency(db, tenant_id, lead_id, checkpoint) -> None:
    service = MeetingStateService(db)
    booking = _booking()
    service.append_link(tenant_id, lead_id, booking)
    db.commit()

    found = service.find_active_link(tenant_id, lead_id, "discovery-call")
    assert found is not None
    assert found.tracking_id == booking.tracking_id


def test_find_active_link_excludes_expired(db, tenant_id, lead_id, checkpoint) -> None:
    service = MeetingStateService(db)
    expired_booking = BookingLinkOutput(
        tracking_id="tok-old",
        url="https://example.com/book/tenant/x?token=tok-old",
        event_slug="discovery-call",
        expires_at=dt.datetime.now(dt.UTC) - dt.timedelta(hours=1),
    )
    service.append_link(tenant_id, lead_id, expired_booking)
    db.commit()

    assert service.find_active_link(tenant_id, lead_id, "discovery-call") is None


def test_update_status_by_tracking_promotes_entry(db, tenant_id, lead_id, checkpoint) -> None:
    service = MeetingStateService(db)
    booking = _booking()
    service.append_link(tenant_id, lead_id, booking)
    db.commit()

    appt_id = uuid.uuid4()
    scheduled = dt.datetime.now(dt.UTC) + dt.timedelta(days=1)

    updated = service.update_status_by_tracking(
        tenant_id,
        lead_id,
        tracking_id=booking.tracking_id,
        status=MeetingEntryStatus.CONFIRMED,
        appointment_id=appt_id,
        scheduled_at=scheduled,
    )
    db.commit()

    assert updated is not None
    assert updated.status == MeetingEntryStatus.CONFIRMED
    assert updated.appointment_id == appt_id


def test_mark_reminder_sent_stamps_field(db, tenant_id, lead_id, checkpoint) -> None:
    service = MeetingStateService(db)
    booking = _booking()
    service.append_link(tenant_id, lead_id, booking)
    db.commit()

    updated = service.mark_reminder_sent(
        tenant_id,
        lead_id,
        booking.tracking_id,
        reminder_kind="24h",
    )
    db.commit()

    assert updated is not None
    assert updated.reminder_24h_sent_at is not None


def test_mark_reminder_sent_unknown_kind_raises(db, tenant_id, lead_id, checkpoint) -> None:
    service = MeetingStateService(db)
    booking = _booking()
    service.append_link(tenant_id, lead_id, booking)
    db.commit()

    with pytest.raises(ValueError):
        service.mark_reminder_sent(
            tenant_id,
            lead_id,
            booking.tracking_id,
            reminder_kind="bogus",
        )


def test_meeting_entry_jsonb_round_trip() -> None:
    now = dt.datetime.now(dt.UTC)
    expires = now + dt.timedelta(hours=24)
    entry = MeetingEntry(
        tracking_id="tok-rt",
        event_slug="discovery",
        expires_at=expires,
        status=MeetingEntryStatus.CONFIRMED,
        appointment_id=uuid.uuid4(),
        scheduled_at=now,
        reminder_24h_sent_at=None,
        reminder_1h_sent_at=None,
        postcheck_sent_at=None,
        created_at=now,
        provider_id="internal",
    )
    rebuilt = MeetingEntry.from_jsonb(entry.to_jsonb())
    assert rebuilt == entry
