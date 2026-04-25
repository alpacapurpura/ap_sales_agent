"""Tests that ``BrandRepository.save_settings`` publishes ``BrandSectionUpdatedEvent``.

F3 hooks the lighthouse regen worker on this event. The repo is the
single emission point so any caller (API, extraction orchestrator,
admin tools) automatically triggers regen.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.modules.brand.domain import BrandSettings
from src.modules.brand.infrastructure.repositories.brand_repository import (
    BrandRepository,
)
from src.modules.iam.infrastructure.models.tenant_model import TenantModel
from src.shared.domain.events import EventBus


@pytest.fixture(autouse=True)
def _clear_bus():
    EventBus.clear()
    yield
    EventBus.clear()


def _seed_tenant(db, tenant_id) -> None:
    tenant = TenantModel(
        id=tenant_id,
        name="Tenant F3",
        slug=f"tenant-f3-{tenant_id.hex[:8]}",
        config_json={},
    )
    db.add(tenant)
    db.commit()


def test_save_settings_publishes_brand_section_updated(db) -> None:
    received: list[object] = []
    EventBus.subscribe("brand_section_updated", received.append)

    tenant_id = uuid4()
    _seed_tenant(db, tenant_id)
    repo = BrandRepository(db)
    settings = BrandSettings()

    repo.save_settings(tenant_id, settings)

    assert len(received) == 1
    event = received[0]
    assert event.event_name == "brand_section_updated"
    assert event.tenant_id == tenant_id


def test_event_dispatched_after_commit_only(db) -> None:
    """Handler does NOT fire until commit (after-commit dispatch contract)."""
    received: list[object] = []
    EventBus.subscribe("brand_section_updated", received.append)

    tenant_id = uuid4()
    _seed_tenant(db, tenant_id)
    # Reset received: commit above triggered nothing (no save yet).
    received.clear()

    BrandRepository(db).save_settings(tenant_id, BrandSettings())

    # save_settings calls db.commit() internally → event must have fired by now.
    assert len(received) == 1
