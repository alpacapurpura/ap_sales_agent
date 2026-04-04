import uuid
from datetime import date

import pytest

from src.modules.commercial_calendar.domain.calendar_event import CalendarEvent

TENANT_A = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")
TENANT_B = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")


@pytest.fixture
def tenant_id():
    return TENANT_A


@pytest.fixture
def other_tenant_id():
    return TENANT_B


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
