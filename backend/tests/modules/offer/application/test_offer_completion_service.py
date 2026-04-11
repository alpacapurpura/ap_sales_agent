"""Unit tests for OfferCompletionService.

Ports the frontend `getOfferHealth()` logic to backend. Verifies percentages
for empty/partial/complete offers across archetypes.
"""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from src.modules.offer.application.services.offer_completion_service import (
    OfferCompletionService,
)
from src.modules.offer.domain.enums import (
    GuaranteeType,
    OfferArchetype,
    OfferValueLevel,
)


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def offer_id():
    return uuid4()


def _make_offer(
    *,
    archetype: OfferArchetype = OfferArchetype.PRODUCTO,
    name: str = "Test",
    value_level: OfferValueLevel | None = OfferValueLevel.ACTIVACION,
    headline_promise: str = "",
    target_avatar_match: list | None = None,
    marketing_pain_points: list | None = None,
    marketing_desires: list | None = None,
    pricing_options: list | None = None,
    guarantee_type: GuaranteeType | None = None,
    specific_details: dict | None = None,
    instructors: list | None = None,
):
    offer = MagicMock()
    offer.archetype = archetype
    offer.public_name = name
    offer.value_level = value_level
    offer.headline_promise = headline_promise
    offer.target_avatar_match = target_avatar_match or []
    offer.marketing_pain_points = marketing_pain_points or []
    offer.marketing_desires = marketing_desires or []
    offer.pricing_options = pricing_options or []
    offer.guarantee_type = guarantee_type
    offer.specific_details = specific_details
    offer.instructors = instructors or []
    return offer


@pytest.fixture
def offer_service():
    return MagicMock()


@pytest.fixture
def service(offer_service):
    return OfferCompletionService(offer_service=offer_service)


def test_empty_producto_is_low_completion(service, offer_service, tenant_id, offer_id):
    empty = _make_offer(
        name="",
        value_level=None,
        headline_promise="",
        guarantee_type=None,
    )
    offer_service.get_offer.return_value = empty

    result = service.compute(offer_id=offer_id, tenant_id=tenant_id)
    assert result["percentage"] == 0.0
    assert result["completed_sections"] == 0
    assert result["total_sections"] > 0
    assert result["next_milestone"] is not None


def test_fully_complete_producto_is_100(service, offer_service, tenant_id, offer_id):
    complete = _make_offer(
        name="Complete Offer",
        value_level=OfferValueLevel.ACTIVACION,
        headline_promise="Gran promesa",
        target_avatar_match=["avatar-1"],
        marketing_pain_points=["pain-1"],
        marketing_desires=["desire-1"],
        pricing_options=[{"plan_type": "one_time"}],
        guarantee_type=GuaranteeType.UNCONDITIONAL_30_DAY,
        specific_details={"category": "ebook"},
    )
    offer_service.get_offer.return_value = complete

    result = service.compute(offer_id=offer_id, tenant_id=tenant_id)
    assert result["percentage"] == 100.0
    assert result["completed_sections"] == result["total_sections"]
    assert result["next_milestone"] is None


def test_partial_producto_is_between(service, offer_service, tenant_id, offer_id):
    partial = _make_offer(
        name="Partial",
        value_level=OfferValueLevel.ACTIVACION,
        headline_promise="Promesa",
        target_avatar_match=["avatar"],
        marketing_pain_points=["pain"],
        marketing_desires=["desire"],
        pricing_options=[],  # missing
        guarantee_type=None,  # missing
        specific_details=None,  # missing
    )
    offer_service.get_offer.return_value = partial

    result = service.compute(offer_id=offer_id, tenant_id=tenant_id)
    assert 0 < result["percentage"] < 100


def test_programa_archetype_uses_program_details(
    service, offer_service, tenant_id, offer_id
):
    offer = _make_offer(
        archetype=OfferArchetype.PROGRAMA,
        name="Prog",
        value_level=OfferValueLevel.TRANSFORMACION,
        headline_promise="Promise",
        target_avatar_match=["a"],
        marketing_pain_points=["p"],
        marketing_desires=["d"],
        pricing_options=[{"plan_type": "payment_plan"}],
        guarantee_type=GuaranteeType.UNCONDITIONAL_30_DAY,
        specific_details={"duration_weeks": 12},
    )
    offer_service.get_offer.return_value = offer

    result = service.compute(offer_id=offer_id, tenant_id=tenant_id)
    assert result["percentage"] == 100.0


def test_compute_not_found_raises(service, offer_service, tenant_id):
    offer_service.get_offer.return_value = None
    with pytest.raises(ValueError, match="not found"):
        service.compute(offer_id=uuid4(), tenant_id=tenant_id)
