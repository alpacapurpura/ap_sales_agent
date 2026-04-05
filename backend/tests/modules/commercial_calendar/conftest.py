"""Fixtures for commercial_calendar module tests."""

import uuid
from datetime import date

import pytest

from src.modules.commercial_calendar.domain.calendar_event import CalendarEvent


@pytest.fixture
def sample_event(tenant_id):
    return CalendarEvent(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        country_code="PE",
        date=date(2026, 7, 28),
        year=2026,
        week_number=date(2026, 7, 28).isocalendar()[1],
        name="Fiestas Patrias",
        category="feriado_nacional",
        description="Dia de la Independencia del Peru",
    )
