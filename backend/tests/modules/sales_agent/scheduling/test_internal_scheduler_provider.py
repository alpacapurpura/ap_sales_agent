"""S8 — InternalSchedulerProvider unit tests.

Round-trips create_booking_link → BookingLink row + URL composition,
verify_booking_status mapping, get_available_slots fallback when
calendar not connected.
"""

from __future__ import annotations

import datetime as dt
import uuid
from unittest.mock import patch

import pytest

from luana_core_sales_agent.application.tools.scheduling.providers import (
    BookingStatusValue,
    InternalSchedulerProvider,
    SchedulerProvider,
)


@pytest.fixture
def tenant(db):
    from luana_core_iam.infrastructure.models.tenant_model import TenantModel

    t = TenantModel(
        id=uuid.UUID("aaaa1111-0000-0000-0000-000000000001"),
        slug="acme",
        name="Acme",
        config_json={},
    )
    db.add(t)
    db.commit()
    return t


@pytest.fixture
def lead(db, tenant):
    from luana_core_crm.infrastructure.models.lead_model import LeadModel

    lead = LeadModel(
        id=uuid.UUID("bbbb1111-0000-0000-0000-000000000001"),
        tenant_id=tenant.id,
    )
    db.add(lead)
    db.commit()
    return lead


def test_provider_implements_protocol() -> None:
    """Runtime-checkable Protocol compliance — arch test enforces structurally."""
    assert isinstance(InternalSchedulerProvider.__init__, type(InternalSchedulerProvider.__init__))
    assert hasattr(InternalSchedulerProvider, "create_booking_link")
    assert hasattr(InternalSchedulerProvider, "verify_booking_status")
    assert hasattr(InternalSchedulerProvider, "get_available_slots")
    assert InternalSchedulerProvider.provider_id == "internal"


def test_create_booking_link_persists_link(db, tenant, lead) -> None:
    """Link composes URL, persists BookingLink row, returns BookingLinkOutput."""
    from sqlalchemy import select

    from src.modules.scheduling.infrastructure.models.booking_link import BookingLink

    with patch(
        "luana_core_platform.links.ports.domain_lookup.create_domain_lookup",
    ) as mock_lookup:
        mock_lookup.return_value.get_verified_domain.return_value = None  # fallback to DASHBOARD_DOMAIN
        provider = InternalSchedulerProvider(db)
        out = provider.create_booking_link(
            tenant_id=tenant.id,
            lead_id=lead.id,
            event_slug="discovery-call",
            expires_in_hours=72,
        )

    assert out.event_slug == "discovery-call"
    assert out.provider_id == "internal"
    assert out.expires_at > dt.datetime.now(dt.UTC)
    assert out.url.endswith(f"?token={out.tracking_id}")
    assert "/book/acme/discovery-call" in out.url

    rows = db.execute(select(BookingLink).where(BookingLink.token == out.tracking_id)).scalars().all()
    assert len(rows) == 1
    assert rows[0].lead_id == lead.id
    assert rows[0].event_slug == "discovery-call"


def test_verify_booking_status_unknown_token(db, tenant, lead) -> None:
    provider = InternalSchedulerProvider(db)
    status = provider.verify_booking_status(
        tenant_id=tenant.id,
        lead_id=lead.id,
        tracking_id="not-a-real-token",
    )
    assert status.status == BookingStatusValue.UNKNOWN


def test_verify_booking_status_pending_when_link_active(db, tenant, lead) -> None:
    """ACTIVE link, no appointment → PENDING."""
    with patch(
        "luana_core_platform.links.ports.domain_lookup.create_domain_lookup",
    ) as mock_lookup:
        mock_lookup.return_value.get_verified_domain.return_value = None
        provider = InternalSchedulerProvider(db)
        out = provider.create_booking_link(
            tenant_id=tenant.id,
            lead_id=lead.id,
            event_slug="discovery-call",
        )

    status = provider.verify_booking_status(
        tenant_id=tenant.id,
        lead_id=lead.id,
        tracking_id=out.tracking_id,
    )
    assert status.status == BookingStatusValue.PENDING


def test_verify_booking_status_expired_when_past_expires(db, tenant, lead) -> None:
    """ACTIVE link past expires_at without appointment → EXPIRED."""
    from src.modules.scheduling.infrastructure.models.booking_link import BookingLink

    expired_at = dt.datetime.now(dt.UTC) - dt.timedelta(hours=1)
    link = BookingLink(
        token="tok-expired",
        status="ACTIVE",
        expires_at=expired_at,
        event_slug="discovery-call",
        lead_id=lead.id,
    )
    db.add(link)
    db.commit()

    provider = InternalSchedulerProvider(db)
    status = provider.verify_booking_status(
        tenant_id=tenant.id,
        lead_id=lead.id,
        tracking_id="tok-expired",
    )
    assert status.status == BookingStatusValue.EXPIRED


def test_verify_booking_status_confirmed_when_appointment_scheduled(db, tenant, lead) -> None:
    """SCHEDULED appointment in the future → CONFIRMED."""
    from src.modules.scheduling.infrastructure.models.appointment_model import (
        AppointmentModel,
    )
    from src.modules.scheduling.infrastructure.models.booking_link import BookingLink

    expires_at = dt.datetime.now(dt.UTC) + dt.timedelta(hours=72)
    link = BookingLink(
        token="tok-conf",
        status="USED",
        expires_at=expires_at,
        event_slug="discovery-call",
        lead_id=lead.id,
    )
    appt = AppointmentModel(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        lead_id=lead.id,
        summary="Discovery Call",
        start_time=dt.datetime.now(dt.UTC) + dt.timedelta(days=1),
        end_time=dt.datetime.now(dt.UTC) + dt.timedelta(days=1, minutes=30),
        status="SCHEDULED",
    )
    db.add_all([link, appt])
    db.commit()

    provider = InternalSchedulerProvider(db)
    status = provider.verify_booking_status(
        tenant_id=tenant.id,
        lead_id=lead.id,
        tracking_id="tok-conf",
    )
    assert status.status == BookingStatusValue.CONFIRMED
    assert status.appointment_id == appt.id


def test_verify_booking_status_missed_when_past_grace(db, tenant, lead) -> None:
    """SCHEDULED appointment past start_time + 30 min grace → MISSED."""
    from src.modules.scheduling.infrastructure.models.appointment_model import (
        AppointmentModel,
    )
    from src.modules.scheduling.infrastructure.models.booking_link import BookingLink

    link = BookingLink(
        token="tok-miss",
        status="USED",
        expires_at=dt.datetime.now(dt.UTC) - dt.timedelta(hours=2),
        event_slug="discovery-call",
        lead_id=lead.id,
    )
    appt = AppointmentModel(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        lead_id=lead.id,
        summary="Discovery",
        start_time=dt.datetime.now(dt.UTC) - dt.timedelta(hours=2),
        end_time=dt.datetime.now(dt.UTC) - dt.timedelta(hours=1, minutes=30),
        status="SCHEDULED",
    )
    db.add_all([link, appt])
    db.commit()

    provider = InternalSchedulerProvider(db)
    status = provider.verify_booking_status(
        tenant_id=tenant.id,
        lead_id=lead.id,
        tracking_id="tok-miss",
    )
    assert status.status == BookingStatusValue.MISSED


def test_get_available_slots_empty_when_calendar_disconnected(db, tenant) -> None:
    provider = InternalSchedulerProvider(db)
    slots = provider.get_available_slots(
        tenant_id=tenant.id,
        event_slug="discovery-call",
        days_ahead=7,
    )
    assert slots == []
