"""Scheduling test fixtures.

Fixtures compartidos para tests de scheduling:
- tenant fixture con config_json limpio
- event_type_factory para crear EventType reutilizables
- appointment_factory para crear AppointmentModel

Usa el `db` fixture del conftest raíz (Session SQLite in-memory + rollback).
"""

import uuid
from datetime import datetime, timezone

import pytest

from tests.factories import TenantFactory

SCHEDULING_TENANT_ID = uuid.UUID("bbbb0000-0000-0000-0000-000000000001")


@pytest.fixture
def scheduling_tenant(db):
    """Crea un TenantModel con config_json vacío para tests de scheduling."""
    t = TenantFactory.build(
        id=SCHEDULING_TENANT_ID,
        name="Scheduling Test Tenant",
        slug="scheduling-test",
        config_json={},
    )
    db.add(t)
    db.commit()
    return t


@pytest.fixture
def scheduling_tenant_with_tz(db):
    """TenantModel con timezone America/Mexico_City para tests de timezone."""
    tenant_id = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")
    t = TenantFactory.build(
        id=tenant_id,
        name="MX Scheduling Tenant",
        slug="mx-scheduling-test",
        config_json={},
        timezone="America/Mexico_City",
    )
    db.add(t)
    db.commit()
    return t
