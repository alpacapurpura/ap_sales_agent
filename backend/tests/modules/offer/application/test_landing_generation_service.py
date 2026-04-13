"""Unit tests for LandingGenerationService — status/generate/publish flows."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from src.modules.offer.application.services.landing_generation_service import (
    LandingGenerationService,
)
from src.modules.offer.domain.exceptions import LandingNotReadyError


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def offer_id():
    return uuid4()


@pytest.fixture
def completion_service():
    svc = MagicMock()
    svc.compute.return_value = {
        "percentage": 95.0,
        "completed_sections": 9,
        "total_sections": 10,
        "next_milestone": None,
    }
    return svc


@pytest.fixture
def landing_repo():
    repo = MagicMock()
    repo.get_by_offer_id.return_value = None
    return repo


@pytest.fixture
def offer_service():
    svc = MagicMock()
    return svc


@pytest.fixture
def event_bus():
    return MagicMock()


@pytest.fixture
def service(completion_service, landing_repo, offer_service, event_bus):
    return LandingGenerationService(
        completion_service=completion_service,
        landing_repo=landing_repo,
        offer_service=offer_service,
        event_bus=event_bus,
    )


# --------------------------------------------------------------------- status


def test_status_no_landing_returns_idle(service, landing_repo, tenant_id, offer_id):
    landing_repo.get_by_offer_id.return_value = None

    status = service.get_status(tenant_id=tenant_id, offer_id=offer_id)
    assert status["is_published"] is False
    assert status["generated_at"] is None
    assert status["is_outdated"] is False
    assert status["job_id"] is None
    assert status["job_status"] in ("idle", None)


def test_status_in_sync_landing(
    service,
    landing_repo,
    offer_service,
    tenant_id,
    offer_id,
):
    now = datetime.now(timezone.utc)
    landing = MagicMock()
    landing.generated_at = now
    landing.is_published = True
    landing.offer_snapshot_version = "v1"
    landing.generation_job_id = uuid4()
    landing.generation_job_status = "success"
    landing_repo.get_by_offer_id.return_value = landing

    offer = MagicMock()
    offer.updated_at = now - timedelta(hours=1)
    offer_service.get_offer.return_value = offer

    status = service.get_status(tenant_id=tenant_id, offer_id=offer_id)
    assert status["is_published"] is True
    assert status["is_outdated"] is False


def test_status_outdated_when_offer_updated_after_landing(
    service,
    landing_repo,
    offer_service,
    tenant_id,
    offer_id,
):
    generated = datetime.now(timezone.utc) - timedelta(hours=2)
    landing = MagicMock()
    landing.generated_at = generated
    landing.is_published = True
    landing.offer_snapshot_version = "v1"
    landing.generation_job_id = None
    landing.generation_job_status = None
    landing_repo.get_by_offer_id.return_value = landing

    offer = MagicMock()
    offer.updated_at = datetime.now(timezone.utc)
    offer_service.get_offer.return_value = offer

    status = service.get_status(tenant_id=tenant_id, offer_id=offer_id)
    assert status["is_outdated"] is True


# ------------------------------------------------------------------ generate


def test_generate_rejects_incomplete_offer(
    service,
    completion_service,
    tenant_id,
    offer_id,
):
    completion_service.compute.return_value = {
        "percentage": 40.0,
        "completed_sections": 4,
        "total_sections": 10,
        "next_milestone": "promise",
    }
    with pytest.raises(LandingNotReadyError):
        service.generate(tenant_id=tenant_id, offer_id=offer_id)


def test_generate_queues_job_and_emits_event(
    service,
    landing_repo,
    event_bus,
    tenant_id,
    offer_id,
):
    created = MagicMock()
    created.id = uuid4()
    created.generation_job_id = uuid4()
    created.generation_job_status = "queued"
    landing_repo.upsert_for_generation.return_value = created

    result = service.generate(tenant_id=tenant_id, offer_id=offer_id)
    assert result["job_status"] == "queued"
    assert result["job_id"] is not None
    landing_repo.upsert_for_generation.assert_called_once()
    event_bus.publish.assert_called_once()


# ------------------------------------------------------------------- publish


def test_publish_sets_flag_and_emits_event(
    service,
    landing_repo,
    event_bus,
    tenant_id,
    offer_id,
):
    landing = MagicMock()
    landing.id = uuid4()
    landing.is_published = False
    landing_repo.get_by_offer_id.return_value = landing

    service.publish(tenant_id=tenant_id, offer_id=offer_id)
    assert landing.is_published is True
    landing_repo.save.assert_called_once_with(landing)
    event_bus.publish.assert_called_once()


def test_unpublish_clears_flag(service, landing_repo, event_bus, tenant_id, offer_id):
    landing = MagicMock()
    landing.id = uuid4()
    landing.is_published = True
    landing_repo.get_by_offer_id.return_value = landing

    service.unpublish(tenant_id=tenant_id, offer_id=offer_id)
    assert landing.is_published is False
    event_bus.publish.assert_called_once()


# ---------------------------------------------------------------- regenerate


def test_regenerate_bumps_snapshot_and_queues(
    service,
    landing_repo,
    event_bus,
    tenant_id,
    offer_id,
):
    landing = MagicMock()
    landing.id = uuid4()
    landing.offer_snapshot_version = "v1"
    landing.generation_job_id = uuid4()
    landing.generation_job_status = "queued"
    landing_repo.get_by_offer_id.return_value = landing
    landing_repo.upsert_for_generation.return_value = landing

    result = service.regenerate(tenant_id=tenant_id, offer_id=offer_id)
    assert result["job_status"] == "queued"
    event_bus.publish.assert_called_once()
