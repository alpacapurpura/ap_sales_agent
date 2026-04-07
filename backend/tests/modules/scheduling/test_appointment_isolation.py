"""Tenant isolation tests for AppointmentRepository.

Proves that Tenant B cannot see or retrieve appointments belonging to Tenant A.
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from src.modules.scheduling.infrastructure.models.appointment_model import (
    AppointmentModel,
)
from src.modules.scheduling.infrastructure.repositories.appointment_repository import (
    AppointmentRepository,
)

TENANT_A = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")
TENANT_B = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")

_BASE_TIME = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)


def _create_appointment(
    db: Session,
    tenant_id: uuid.UUID,
    offset_hours: int = 0,
) -> AppointmentModel:
    appt = AppointmentModel(
        tenant_id=tenant_id,
        lead_id=None,
        summary=f"Appointment for tenant {tenant_id}",
        start_time=_BASE_TIME + timedelta(hours=offset_hours),
        end_time=_BASE_TIME + timedelta(hours=offset_hours + 1),
        status="SCHEDULED",
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return appt


class TestGetAppointmentsByDateRangeTenantIsolation:
    def test_tenant_b_cannot_see_tenant_a_appointments(self, db: Session):
        _create_appointment(db, TENANT_A, offset_hours=0)
        repo = AppointmentRepository(db)

        results = repo.get_appointments_by_date_range(
            start=_BASE_TIME - timedelta(hours=1),
            end=_BASE_TIME + timedelta(hours=2),
            tenant_id=TENANT_B,
        )
        assert len(results) == 0

    def test_tenant_a_sees_own_appointments(self, db: Session):
        _create_appointment(db, TENANT_A, offset_hours=0)
        repo = AppointmentRepository(db)

        results = repo.get_appointments_by_date_range(
            start=_BASE_TIME - timedelta(hours=1),
            end=_BASE_TIME + timedelta(hours=2),
            tenant_id=TENANT_A,
        )
        assert len(results) == 1
        assert results[0].tenant_id == TENANT_A

    def test_both_tenants_see_only_own_appointments(self, db: Session):
        _create_appointment(db, TENANT_A, offset_hours=0)
        _create_appointment(db, TENANT_A, offset_hours=2)
        _create_appointment(db, TENANT_B, offset_hours=1)
        repo = AppointmentRepository(db)

        window_start = _BASE_TIME - timedelta(hours=1)
        window_end = _BASE_TIME + timedelta(hours=4)

        results_a = repo.get_appointments_by_date_range(
            window_start, window_end, TENANT_A
        )
        results_b = repo.get_appointments_by_date_range(
            window_start, window_end, TENANT_B
        )

        assert len(results_a) == 2
        assert all(r.tenant_id == TENANT_A for r in results_a)
        assert len(results_b) == 1
        assert results_b[0].tenant_id == TENANT_B

    def test_out_of_range_returns_empty(self, db: Session):
        _create_appointment(db, TENANT_A, offset_hours=0)
        repo = AppointmentRepository(db)

        results = repo.get_appointments_by_date_range(
            start=_BASE_TIME + timedelta(hours=5),
            end=_BASE_TIME + timedelta(hours=10),
            tenant_id=TENANT_A,
        )
        assert len(results) == 0
