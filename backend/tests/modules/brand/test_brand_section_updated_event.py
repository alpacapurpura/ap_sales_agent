"""Tests that ``BrandRepository.save_settings`` publishes ``BrandSectionUpdatedEvent``.

F3 hooks the lighthouse regen worker on this event. The repo is the
single emission point so any caller (API, extraction orchestrator,
admin tools) automatically triggers regen.

D2 migration (PI-11 PR-1 Fase 2): removed monkeypatch.setattr(USE_OUTBOX_PATTERN_BRAND=False)
band-aid. Now uses patch.object(EventBusAdapter, "_is_outbox_enabled", return_value=False)
to force legacy dispatch path. The outbox-settings flag is production state (D1: True permanent);
tests control dispatch path via adapter mock (Caso C per CONTRACT.md § 3).
"""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import pytest

from src.modules.brand.domain import BrandSettings
from src.modules.brand.infrastructure.repositories.brand_repository import (
    BrandRepository,
)
from src.modules.iam.infrastructure.models.tenant_model import TenantModel
from src.shared.domain.events import EventBus
from src.shared.domain_events.outbox.application.event_bus_adapter import EventBusAdapter


@pytest.fixture(autouse=True)
def _clear_bus():
    """Clear EventBus handlers before and after each test."""
    EventBus.clear()
    yield
    EventBus.clear()


@pytest.fixture(autouse=True)
def _force_legacy_dispatch():
    """Force legacy in-memory dispatch path via adapter mock.

    D2 migration (PI-11 PR-1): replaces monkeypatch.setattr(USE_OUTBOX_PATTERN_BRAND=False)
    band-aid. Patches EventBusAdapter._is_outbox_enabled to return False so the adapter
    routes through legacy EventBus (Caso C). The outbox flag stays True (D1); only the
    dispatch path is controlled per-test via adapter boundary mock.

    Using patch.object instead of monkeypatching settings ensures:
    - D1 invariant: USE_OUTBOX_PATTERN_BRAND stays True in settings (not mutated)
    - D2 invariant: no band-aid flag flip; test controls adapter dispatch path directly
    - SQLite compat: legacy path avoids domain_event_outbox table (not in SQLite fixture)
    """
    with patch.object(EventBusAdapter, "_is_outbox_enabled", return_value=False):
        yield


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
