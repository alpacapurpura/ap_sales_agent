"""Test the LaunchEdition.is_placeholder domain property."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from src.modules.offer.domain.launch_edition import (
    EditionStatus,
    EditionVisibility,
    LaunchEdition,
)
from src.modules.offer.domain.offer import PricingStructure

TENANT = uuid4()
OFFER = uuid4()


def _placeholder() -> LaunchEdition:
    return LaunchEdition(
        offer_id=OFFER,
        tenant_id=TENANT,
        edition_name="Edición #1",
        edition_number=1,
        status=EditionStatus.DRAFT,
        visibility=EditionVisibility.PRIVATE,
    )


def test_auto_created_placeholder_is_identified() -> None:
    assert _placeholder().is_placeholder is True


def test_setting_start_date_flips_placeholder_off() -> None:
    edition = _placeholder()
    edition.start_date = datetime(2026, 5, 15, tzinfo=timezone.utc)
    assert edition.is_placeholder is False


def test_pricing_override_flips_placeholder_off() -> None:
    edition = _placeholder()
    edition.pricing_override = [
        PricingStructure(label="Early", total_amount=100),
    ]
    assert edition.is_placeholder is False


def test_location_override_flips_placeholder_off() -> None:
    edition = _placeholder()
    edition.location_override = {"type": "virtual", "url": "https://zoom"}
    assert edition.is_placeholder is False


def test_upcoming_status_is_not_a_placeholder() -> None:
    edition = LaunchEdition(
        offer_id=OFFER,
        tenant_id=TENANT,
        edition_name="Edición #1",
        edition_number=1,
        status=EditionStatus.UPCOMING,
        visibility=EditionVisibility.PUBLIC,
        start_date=datetime(2026, 5, 15, tzinfo=timezone.utc),
    )
    assert edition.is_placeholder is False
