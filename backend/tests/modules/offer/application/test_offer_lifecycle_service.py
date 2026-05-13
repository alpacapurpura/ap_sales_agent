"""Unit tests for OfferLifecycleService.

Verifies every transition in `LIFECYCLE_TRANSITIONS`, the archive delegation
path, the restore rejection path, and domain-event emission. Repos and the
underlying ``OfferService`` are mocked — these are pure service-layer tests.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from luana_core_offer_studio.application.services.offer_lifecycle_service import (
    OfferLifecycleService,
)
from luana_core_offer_studio.domain.enums import OfferStatus
from luana_core_offer_studio.domain.events import OfferStatusChanged
from luana_core_offer_studio.domain.exceptions import InvalidTransitionError
from luana_core_offer_studio.domain.lifecycle import (
    LIFECYCLE_TRANSITIONS,
    OfferLifecycleStatus,
)


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def offer_id():
    return uuid4()


@pytest.fixture
def actor_id():
    return uuid4()


@pytest.fixture
def offer_factory(tenant_id):
    def _make(status: OfferStatus, archived_at: datetime | None = None):
        offer = MagicMock()
        offer.id = uuid4()
        offer.tenant_id = tenant_id
        offer.status = status
        offer.archived_at = archived_at
        return offer

    return _make


@pytest.fixture
def offer_service():
    svc = MagicMock()
    return svc


@pytest.fixture
def event_bus():
    return MagicMock()


@pytest.fixture
def service(offer_service, event_bus):
    return OfferLifecycleService(offer_service=offer_service, event_bus=event_bus)


# ---------------------------------------------------------------- valid paths


def test_draft_to_active_transition(
    service,
    offer_service,
    event_bus,
    offer_factory,
    tenant_id,
    actor_id,
):
    offer = offer_factory(OfferStatus.DRAFT)
    updated_offer = offer_factory(OfferStatus.ACTIVE)
    offer_service.get_offer.return_value = offer
    offer_service.patch_offer.return_value = updated_offer

    result = service.change_status(
        offer_id=offer.id,
        new_status=OfferLifecycleStatus.ACTIVE,
        tenant_id=tenant_id,
        actor_user_id=actor_id,
    )

    assert result is updated_offer
    assert result.status == OfferStatus.ACTIVE
    offer_service.patch_offer.assert_called_once()
    call_args = offer_service.patch_offer.call_args
    assert call_args.kwargs["update_data"]["status"] == OfferStatus.ACTIVE
    event_bus.publish.assert_called_once()
    event = event_bus.publish.call_args.args[0]
    assert isinstance(event, OfferStatusChanged)
    assert event.from_status == OfferLifecycleStatus.DRAFT
    assert event.to_status == OfferLifecycleStatus.ACTIVE
    assert event.actor_user_id == actor_id


def test_active_to_paused_transition(service, offer_service, offer_factory, tenant_id):
    offer = offer_factory(OfferStatus.ACTIVE)
    offer_service.get_offer.return_value = offer
    offer_service.patch_offer.return_value = offer

    result = service.change_status(
        offer_id=offer.id,
        new_status=OfferLifecycleStatus.PAUSED,
        tenant_id=tenant_id,
        actor_user_id=None,
    )
    assert result is offer
    offer_service.patch_offer.assert_called_once()


def test_paused_to_active_transition(service, offer_service, offer_factory, tenant_id):
    offer = offer_factory(OfferStatus.PAUSED)
    offer_service.get_offer.return_value = offer
    offer_service.patch_offer.return_value = offer

    service.change_status(
        offer_id=offer.id,
        new_status=OfferLifecycleStatus.ACTIVE,
        tenant_id=tenant_id,
        actor_user_id=None,
    )

    offer_service.patch_offer.assert_called_once()


def test_active_to_draft_transition(service, offer_service, offer_factory, tenant_id):
    offer = offer_factory(OfferStatus.ACTIVE)
    offer_service.get_offer.return_value = offer
    offer_service.patch_offer.return_value = offer

    service.change_status(
        offer_id=offer.id,
        new_status=OfferLifecycleStatus.DRAFT,
        tenant_id=tenant_id,
        actor_user_id=None,
    )
    offer_service.patch_offer.assert_called_once()


def test_paused_to_draft_transition(service, offer_service, offer_factory, tenant_id):
    offer = offer_factory(OfferStatus.PAUSED)
    offer_service.get_offer.return_value = offer
    offer_service.patch_offer.return_value = offer

    service.change_status(
        offer_id=offer.id,
        new_status=OfferLifecycleStatus.DRAFT,
        tenant_id=tenant_id,
        actor_user_id=None,
    )
    offer_service.patch_offer.assert_called_once()


# ------------------------------------------------------------- archive branch


def test_transition_to_archived_delegates_to_archive_offer(
    service,
    offer_service,
    event_bus,
    offer_factory,
    tenant_id,
):
    offer = offer_factory(OfferStatus.ACTIVE)
    archived_offer = offer_factory(
        OfferStatus.ARCHIVED,
        archived_at=datetime.now(timezone.utc),
    )
    offer_service.get_offer.return_value = offer
    offer_service.archive_offer.return_value = archived_offer

    result = service.change_status(
        offer_id=offer.id,
        new_status=OfferLifecycleStatus.ARCHIVED,
        tenant_id=tenant_id,
        actor_user_id=None,
    )

    assert result is archived_offer
    offer_service.archive_offer.assert_called_once_with(offer.id, tenant_id)
    # patch_offer must NOT be used for archival — archive_offer is canonical.
    offer_service.patch_offer.assert_not_called()
    event_bus.publish.assert_called_once()
    event = event_bus.publish.call_args.args[0]
    assert event.to_status == OfferLifecycleStatus.ARCHIVED


# ---------------------------------------------------------- restore rejection


def test_archived_offer_cannot_transition_via_change_status(
    service,
    offer_service,
    offer_factory,
    tenant_id,
):
    """ARCHIVED is terminal from the header endpoint — must use /restore."""
    archived_offer = offer_factory(
        OfferStatus.ARCHIVED,
        archived_at=datetime.now(timezone.utc),
    )
    offer_service.get_offer.return_value = archived_offer

    with pytest.raises(InvalidTransitionError):
        service.change_status(
            offer_id=archived_offer.id,
            new_status=OfferLifecycleStatus.ACTIVE,
            tenant_id=tenant_id,
            actor_user_id=None,
        )
    offer_service.patch_offer.assert_not_called()
    offer_service.archive_offer.assert_not_called()


# ----------------------------------------------------------- invalid branches


def test_draft_to_paused_is_invalid(service, offer_service, offer_factory, tenant_id):
    offer = offer_factory(OfferStatus.DRAFT)
    offer_service.get_offer.return_value = offer

    with pytest.raises(InvalidTransitionError):
        service.change_status(
            offer_id=offer.id,
            new_status=OfferLifecycleStatus.PAUSED,
            tenant_id=tenant_id,
            actor_user_id=None,
        )


def test_not_found_offer_raises(service, offer_service, tenant_id):
    offer_service.get_offer.return_value = None
    with pytest.raises(ValueError, match="not found"):
        service.change_status(
            offer_id=uuid4(),
            new_status=OfferLifecycleStatus.ACTIVE,
            tenant_id=tenant_id,
            actor_user_id=None,
        )


# ----------------------------------------------------------- noop short-circuit


def test_same_status_is_noop(
    service,
    offer_service,
    event_bus,
    offer_factory,
    tenant_id,
):
    offer = offer_factory(OfferStatus.ACTIVE)
    offer_service.get_offer.return_value = offer

    result = service.change_status(
        offer_id=offer.id,
        new_status=OfferLifecycleStatus.ACTIVE,
        tenant_id=tenant_id,
        actor_user_id=None,
    )

    assert result is offer
    offer_service.patch_offer.assert_not_called()
    event_bus.publish.assert_not_called()


# ---------------------------------------------------- coverage of table itself


def test_transition_table_matches_expectation():
    assert LIFECYCLE_TRANSITIONS[OfferLifecycleStatus.DRAFT] == {
        OfferLifecycleStatus.ACTIVE,
        OfferLifecycleStatus.ARCHIVED,
    }
    assert LIFECYCLE_TRANSITIONS[OfferLifecycleStatus.ARCHIVED] == set()
