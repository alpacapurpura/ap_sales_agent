"""Tests for agenda API endpoints — PR-2 PI-11.

Coverage lift: agenda.py 0% → ≥80%.
Cubre los 2 endpoints de scheduling/agenda/:
- GET /scheduling/agenda/ — range=today, range=week, enrich lead names
- PATCH /scheduling/agenda/{id}/status — valid status, invalid status, 404, no lead_id

Estrategia: endpoints son async def. Usa httpx.AsyncClient con ASGITransport,
override de get_db y get_current_user. EventBus.publish mockeado para evitar
side-effects cross-module.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.core.database import get_db
from src.main import app
from src.modules.iam.api.dependencies import get_current_user

TENANT_ID = uuid.UUID("dddd0000-0000-0000-0000-000000000001")


# ---------------------------------------------------------------------------
# Factories helpers
# ---------------------------------------------------------------------------


def _make_user(tenant_id: uuid.UUID = TENANT_ID):
    """Crea un User mock para overriding get_current_user."""
    user = MagicMock()
    user.tenant_id = tenant_id
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    return user


def _make_appointment_model(
    tenant_id: uuid.UUID = TENANT_ID,
    lead_id: uuid.UUID | None = None,
    status: str = "SCHEDULED",
    hours_from_now: int = 1,
):
    """Crea un AppointmentModel en la DB de test."""
    from src.modules.scheduling.infrastructure.models.appointment_model import AppointmentModel

    now = datetime.now(UTC)
    return AppointmentModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        lead_id=lead_id,
        summary="Test Meeting",
        start_time=now + timedelta(hours=hours_from_now),
        end_time=now + timedelta(hours=hours_from_now + 1),
        status=status,
        meeting_link="https://meet.example.com/test",
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db_tenant(db):
    """Crea TenantModel para los tests de agenda."""
    from tests.factories import TenantFactory

    t = TenantFactory.build(
        id=TENANT_ID,
        name="Agenda Test Tenant",
        slug="agenda-test",
        config_json={},
    )
    db.add(t)
    db.commit()
    return t


@pytest.fixture
def mock_user():
    """User mock con tenant_id TENANT_ID."""
    return _make_user(TENANT_ID)


@pytest_asyncio.fixture
async def async_client(db, db_tenant, mock_user):
    """AsyncClient con overrides de get_db y get_current_user."""

    def override_get_db():
        yield db

    def override_get_current_user():
        return mock_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


# ---------------------------------------------------------------------------
# GET /scheduling/agenda/
# ---------------------------------------------------------------------------


class TestGetAgenda:
    """GET /api/v1/scheduling/agenda/."""

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_appointments(self, async_client: AsyncClient):
        """Lista vacía cuando no hay citas en el rango."""
        resp = await async_client.get("/api/v1/scheduling/agenda/")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_returns_appointments_today_range(self, async_client: AsyncClient):
        """range=today retorna citas del día actual — repo mockeado (SQLite tz-aware issue)."""
        from src.modules.scheduling.domain.appointment import Appointment
        from src.modules.scheduling.domain.enums import AppointmentStatus
        from src.modules.scheduling.infrastructure.repositories.appointment_repository import AppointmentRepository

        now = datetime.now(UTC)
        appt_id = uuid.uuid4()
        mock_appt = Appointment(
            id=appt_id,
            tenant_id=TENANT_ID,
            lead_id=None,
            summary="Test Meeting",
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            status=AppointmentStatus.SCHEDULED,
            meeting_link="https://meet.example.com/test",
        )

        with (
            patch.object(AppointmentRepository, "get_appointments_by_date_range", return_value=[mock_appt]),
            patch("src.shared.links.ports.lead_resolution.get_lead_names", return_value={}),
        ):
            resp = await async_client.get("/api/v1/scheduling/agenda/?range=today")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["summary"] == "Test Meeting"
        assert data[0]["status"] == "SCHEDULED"
        assert data[0]["meeting_link"] == "https://meet.example.com/test"

    @pytest.mark.asyncio
    async def test_returns_appointments_week_range(self, async_client: AsyncClient):
        """range=week retorna citas de los próximos 7 días — repo mockeado."""
        from src.modules.scheduling.domain.appointment import Appointment
        from src.modules.scheduling.domain.enums import AppointmentStatus
        from src.modules.scheduling.infrastructure.repositories.appointment_repository import AppointmentRepository

        now = datetime.now(UTC)
        appt_id = uuid.uuid4()
        mock_appt = Appointment(
            id=appt_id,
            tenant_id=TENANT_ID,
            lead_id=None,
            summary="Week Meeting",
            start_time=now + timedelta(hours=48),
            end_time=now + timedelta(hours=49),
            status=AppointmentStatus.SCHEDULED,
            meeting_link=None,
        )

        with (
            patch.object(AppointmentRepository, "get_appointments_by_date_range", return_value=[mock_appt]),
            patch("src.shared.links.ports.lead_resolution.get_lead_names", return_value={}),
        ):
            resp = await async_client.get("/api/v1/scheduling/agenda/?range=week")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == str(appt_id)

    @pytest.mark.asyncio
    async def test_today_range_excludes_future_appointments(self, async_client: AsyncClient, db):
        """range=today excluye citas fuera del día (ej. en 3 días)."""
        appt_far = _make_appointment_model(tenant_id=TENANT_ID, hours_from_now=72)
        db.add(appt_far)
        db.commit()

        with patch("src.shared.links.ports.lead_resolution.get_lead_names", return_value={}):
            resp = await async_client.get("/api/v1/scheduling/agenda/?range=today")

        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_tenant_isolation_in_agenda(self, async_client: AsyncClient, db):
        """Citas de otro tenant no aparecen."""
        other_tenant = uuid.UUID("dddd0000-0000-0000-0000-000000000099")
        appt_other = _make_appointment_model(tenant_id=other_tenant, hours_from_now=1)
        db.add(appt_other)
        db.commit()

        with patch("src.shared.links.ports.lead_resolution.get_lead_names", return_value={}):
            resp = await async_client.get("/api/v1/scheduling/agenda/?range=today")

        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_enriches_lead_name_when_lead_id_present(self, async_client: AsyncClient):
        """Lead name se enriquece via get_lead_names cuando hay lead_id — repo mockeado."""
        from src.modules.scheduling.domain.appointment import Appointment
        from src.modules.scheduling.domain.enums import AppointmentStatus
        from src.modules.scheduling.infrastructure.repositories.appointment_repository import AppointmentRepository

        now = datetime.now(UTC)
        lead_id = uuid.uuid4()
        mock_appt = Appointment(
            id=uuid.uuid4(),
            tenant_id=TENANT_ID,
            lead_id=lead_id,
            summary="Meeting With Lead",
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            status=AppointmentStatus.SCHEDULED,
            meeting_link=None,
        )

        lead_map = {lead_id: "Juan García"}
        with (
            patch.object(AppointmentRepository, "get_appointments_by_date_range", return_value=[mock_appt]),
            patch("src.shared.links.ports.lead_resolution.get_lead_names", return_value=lead_map),
        ):
            resp = await async_client.get("/api/v1/scheduling/agenda/?range=today")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["lead_name"] == "Juan García"

    @pytest.mark.asyncio
    async def test_lead_name_defaults_unknown_when_not_in_map(self, async_client: AsyncClient):
        """Cuando lead_id no está en map, lead_name = 'Unknown Lead' — repo mockeado."""
        from src.modules.scheduling.domain.appointment import Appointment
        from src.modules.scheduling.domain.enums import AppointmentStatus
        from src.modules.scheduling.infrastructure.repositories.appointment_repository import AppointmentRepository

        now = datetime.now(UTC)
        lead_id = uuid.uuid4()
        mock_appt = Appointment(
            id=uuid.uuid4(),
            tenant_id=TENANT_ID,
            lead_id=lead_id,
            summary="Meeting Unknown Lead",
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            status=AppointmentStatus.SCHEDULED,
            meeting_link=None,
        )

        # get_lead_names retorna mapa vacío (lead_id no encontrado)
        with (
            patch.object(AppointmentRepository, "get_appointments_by_date_range", return_value=[mock_appt]),
            patch("src.shared.links.ports.lead_resolution.get_lead_names", return_value={}),
        ):
            resp = await async_client.get("/api/v1/scheduling/agenda/?range=today")

        assert resp.status_code == 200
        data = resp.json()
        assert data[0]["lead_name"] == "Unknown Lead"

    @pytest.mark.asyncio
    async def test_no_lead_id_skips_enrichment(self, async_client: AsyncClient):
        """Cuando appointment no tiene lead_id, get_lead_names no se llama — repo mockeado."""
        from src.modules.scheduling.domain.appointment import Appointment
        from src.modules.scheduling.domain.enums import AppointmentStatus
        from src.modules.scheduling.infrastructure.repositories.appointment_repository import AppointmentRepository

        now = datetime.now(UTC)
        mock_appt = Appointment(
            id=uuid.uuid4(),
            tenant_id=TENANT_ID,
            lead_id=None,
            summary="Meeting No Lead",
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            status=AppointmentStatus.SCHEDULED,
            meeting_link=None,
        )

        with patch.object(AppointmentRepository, "get_appointments_by_date_range", return_value=[mock_appt]):
            resp = await async_client.get("/api/v1/scheduling/agenda/?range=today")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        # lead_id es None → no llama get_lead_names → lead_map vacío → lead_name = "Unknown Lead"
        assert data[0]["lead_name"] == "Unknown Lead"


class TestUpdateAppointmentStatus:
    """PATCH /api/v1/scheduling/agenda/{id}/status."""

    @pytest.mark.asyncio
    async def test_returns_404_when_appointment_not_found(self, async_client: AsyncClient):
        """404 cuando el appointment no existe para el tenant."""
        non_existent_id = uuid.uuid4()
        resp = await async_client.patch(
            f"/api/v1/scheduling/agenda/{non_existent_id}/status",
            json={"status": "COMPLETED"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_returns_400_for_invalid_status(self, async_client: AsyncClient, db):
        """400 cuando status no es válido."""
        appt = _make_appointment_model(tenant_id=TENANT_ID, hours_from_now=1)
        db.add(appt)
        db.commit()

        resp = await async_client.patch(
            f"/api/v1/scheduling/agenda/{appt.id}/status",
            json={"status": "INVALID_STATUS"},
        )
        assert resp.status_code == 400
        assert "Invalid status" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_updates_status_to_completed(self, async_client: AsyncClient, db):
        """Actualiza status SCHEDULED → COMPLETED correctamente."""
        appt = _make_appointment_model(tenant_id=TENANT_ID, hours_from_now=1, status="SCHEDULED")
        db.add(appt)
        db.commit()
        appt_id = appt.id

        with patch("src.modules.scheduling.api.agenda._publish_appointment_event") as mock_publish:
            resp = await async_client.patch(
                f"/api/v1/scheduling/agenda/{appt_id}/status",
                json={"status": "COMPLETED"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "updated"
        assert data["old_status"] == "SCHEDULED"
        assert data["new_status"] == "COMPLETED"
        assert data["appointment_id"] == str(appt_id)
        mock_publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_updates_status_to_no_show(self, async_client: AsyncClient, db):
        """Actualiza status a NO_SHOW."""
        appt = _make_appointment_model(tenant_id=TENANT_ID, hours_from_now=1, status="SCHEDULED")
        db.add(appt)
        db.commit()

        with patch("src.modules.scheduling.api.agenda._publish_appointment_event"):
            resp = await async_client.patch(
                f"/api/v1/scheduling/agenda/{appt.id}/status",
                json={"status": "NO_SHOW"},
            )

        assert resp.status_code == 200
        assert resp.json()["new_status"] == "NO_SHOW"

    @pytest.mark.asyncio
    async def test_updates_status_to_cancelled(self, async_client: AsyncClient, db):
        """Actualiza status a CANCELLED."""
        appt = _make_appointment_model(tenant_id=TENANT_ID, hours_from_now=1, status="SCHEDULED")
        db.add(appt)
        db.commit()

        with patch("src.modules.scheduling.api.agenda._publish_appointment_event"):
            resp = await async_client.patch(
                f"/api/v1/scheduling/agenda/{appt.id}/status",
                json={"status": "CANCELLED"},
            )

        assert resp.status_code == 200
        assert resp.json()["new_status"] == "CANCELLED"

    @pytest.mark.asyncio
    async def test_tenant_isolation_status_update(self, async_client: AsyncClient, db):
        """Appointment de otro tenant retorna 404."""
        other_tenant = uuid.UUID("dddd0000-0000-0000-0000-000000000088")
        appt = _make_appointment_model(tenant_id=other_tenant, hours_from_now=1)
        db.add(appt)
        db.commit()

        resp = await async_client.patch(
            f"/api/v1/scheduling/agenda/{appt.id}/status",
            json={"status": "COMPLETED"},
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# _publish_appointment_event helper
# ---------------------------------------------------------------------------


class TestPublishAppointmentEvent:
    """Tests unitarios de la helper _publish_appointment_event.

    # arch-bypass: testing legacy capability
    scheduling module llama EventBus.publish directamente (no outbox adapter).
    scheduling NO está en USE_OUTBOX_PATTERN_* flags — este path es canónico para scheduling.
    Migración pendiente cuando scheduling sea incorporado al outbox adapter.
    """

    def test_skips_publish_when_no_lead_id(self):
        """Si lead_id es None, no se publica evento."""
        from src.modules.scheduling.api.agenda import _publish_appointment_event

        mock_db = MagicMock()
        with patch("src.shared.domain.events.EventBus.publish") as mock_bus:
            _publish_appointment_event(
                db=mock_db,
                tenant_id=TENANT_ID,
                lead_id=None,
                appointment_id=uuid.uuid4(),
                status="COMPLETED",
            )
        mock_bus.assert_not_called()

    def test_publishes_event_when_lead_id_present(self):
        """Cuando lead_id existe, publica AppointmentEvent via EventBus."""
        from src.modules.scheduling.api.agenda import _publish_appointment_event

        mock_db = MagicMock()
        lead_id = uuid.uuid4()
        appt_id = uuid.uuid4()

        with patch("src.shared.domain.events.EventBus.publish") as mock_bus:
            _publish_appointment_event(
                db=mock_db,
                tenant_id=TENANT_ID,
                lead_id=lead_id,
                appointment_id=appt_id,
                status="COMPLETED",
            )
        mock_bus.assert_called_once()
        call_args = mock_bus.call_args
        event = call_args[0][0]
        # AppointmentEvent almacena datos en payload dict, no como atributos directos
        assert hasattr(event, "payload")
        assert str(lead_id) == event.payload.get("lead_id")
