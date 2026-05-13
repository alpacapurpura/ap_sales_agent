"""Unit tests for OfferCountsService.

Verifies tab-bar badge counts aggregate across the three sources (assets,
campaigns, knowledge) with all dependencies mocked.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from luana_core_offer_studio.application.services.offer_counts_service import (
    OfferCountsService,
)


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def offer_id():
    return uuid4()


@pytest.fixture
def asset_repo():
    repo = MagicMock()
    repo.count_by_offer.return_value = 5
    return repo


@pytest.fixture
def knowledge_repo():
    repo = MagicMock()
    repo.count_by_offer.return_value = 3
    return repo


@pytest.fixture
def advertising_port():
    port = MagicMock()
    kpis = MagicMock()
    kpis.active_count = 7
    view = MagicMock()
    view.kpis = kpis
    view.campaigns = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
    port.get_campaigns_for_offer.return_value = view
    return port


@pytest.fixture
def service(asset_repo, knowledge_repo, advertising_port):
    return OfferCountsService(
        asset_repo=asset_repo,
        knowledge_repo=knowledge_repo,
        advertising_port=advertising_port,
    )


def test_get_counts_aggregates_all_three_sources(
    service,
    asset_repo,
    knowledge_repo,
    advertising_port,
    tenant_id,
    offer_id,
):
    counts = service.get_counts(tenant_id=tenant_id, offer_id=offer_id)

    assert counts["assets"] == 5
    assert counts["knowledge"] == 3
    # campaigns count uses number of campaign rows, not active_count
    assert counts["campaigns"] == 4

    asset_repo.count_by_offer.assert_called_once_with(tenant_id, offer_id)
    knowledge_repo.count_by_offer.assert_called_once_with(tenant_id, offer_id)
    advertising_port.get_campaigns_for_offer.assert_called_once()
    call = advertising_port.get_campaigns_for_offer.call_args
    assert call.kwargs["tenant_id"] == tenant_id or call.args[0] == tenant_id


def test_get_counts_returns_zeros_when_nothing(
    asset_repo,
    knowledge_repo,
    advertising_port,
    tenant_id,
    offer_id,
):
    asset_repo.count_by_offer.return_value = 0
    knowledge_repo.count_by_offer.return_value = 0
    empty_view = MagicMock()
    empty_view.kpis = MagicMock(active_count=0)
    empty_view.campaigns = []
    advertising_port.get_campaigns_for_offer.return_value = empty_view

    svc = OfferCountsService(
        asset_repo=asset_repo,
        knowledge_repo=knowledge_repo,
        advertising_port=advertising_port,
    )
    counts = svc.get_counts(tenant_id=tenant_id, offer_id=offer_id)
    assert counts == {"assets": 0, "campaigns": 0, "knowledge": 0}


def test_get_counts_swallows_advertising_port_errors(
    asset_repo,
    knowledge_repo,
    tenant_id,
    offer_id,
):
    """If advertising port fails, fall back to 0 campaigns — the badge is
    non-critical and must never break the offer page."""
    broken_port = MagicMock()
    broken_port.get_campaigns_for_offer.side_effect = RuntimeError("boom")

    svc = OfferCountsService(
        asset_repo=asset_repo,
        knowledge_repo=knowledge_repo,
        advertising_port=broken_port,
    )
    counts = svc.get_counts(tenant_id=tenant_id, offer_id=offer_id)
    assert counts["campaigns"] == 0
    assert counts["assets"] == 5
    assert counts["knowledge"] == 3


def test_advertising_port_is_called_with_date_range(
    service,
    advertising_port,
    tenant_id,
    offer_id,
):
    service.get_counts(tenant_id=tenant_id, offer_id=offer_id)
    call = advertising_port.get_campaigns_for_offer.call_args
    # must pass period_start / period_end kwargs
    assert isinstance(call.kwargs.get("period_start"), date)
    assert isinstance(call.kwargs.get("period_end"), date)
