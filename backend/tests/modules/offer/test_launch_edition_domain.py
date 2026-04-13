"""Tests for LaunchEdition domain entity."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from src.modules.offer.domain.launch_edition import (
    EditionStatus,
    LaunchEdition,
    LaunchEditionCreate,
    LaunchEditionUpdate,
)
from src.modules.offer.domain.offer import PricingStructure


class TestEditionStatus:
    def test_all_values_exist(self):
        assert EditionStatus.DRAFT == "draft"
        assert EditionStatus.UPCOMING == "upcoming"
        assert EditionStatus.ACTIVE == "active"
        assert EditionStatus.COMPLETED == "completed"
        assert EditionStatus.CANCELLED == "cancelled"


class TestLaunchEdition:
    def test_create_minimal(self):
        edition = LaunchEdition(
            offer_id=uuid4(),
            tenant_id=uuid4(),
            edition_name="Cohorte #1",
            edition_number=1,
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        assert edition.status == EditionStatus.DRAFT
        assert edition.pricing_override is None
        assert edition.capacity is None
        assert edition.enrollment_count == 0

    def test_create_with_pricing_override(self):
        pricing = [
            PricingStructure(label="Early Bird", total_amount=397.0),
        ]
        edition = LaunchEdition(
            offer_id=uuid4(),
            tenant_id=uuid4(),
            edition_name="Cohorte #2",
            edition_number=2,
            start_date=datetime(2026, 10, 7, tzinfo=timezone.utc),
            end_date=datetime(2026, 11, 18, tzinfo=timezone.utc),
            pricing_override=pricing,
            capacity=30,
        )
        assert edition.pricing_override is not None
        assert len(edition.pricing_override) == 1
        assert edition.pricing_override[0].total_amount == 397.0
        assert edition.capacity == 30

    def test_end_date_before_start_raises(self):
        with pytest.raises(ValueError, match=r"end_date.*before.*start_date"):
            LaunchEdition(
                offer_id=uuid4(),
                tenant_id=uuid4(),
                edition_name="Bad",
                edition_number=1,
                start_date=datetime(2026, 10, 1, tzinfo=timezone.utc),
                end_date=datetime(2026, 9, 1, tzinfo=timezone.utc),
            )

    def test_registration_end_before_start_raises(self):
        with pytest.raises(
            ValueError,
            match=r"registration_end.*before.*registration_start",
        ):
            LaunchEdition(
                offer_id=uuid4(),
                tenant_id=uuid4(),
                edition_name="Bad",
                edition_number=1,
                start_date=datetime(2026, 10, 1, tzinfo=timezone.utc),
                registration_start=datetime(2026, 9, 15, tzinfo=timezone.utc),
                registration_end=datetime(2026, 9, 1, tzinfo=timezone.utc),
            )


class TestLaunchEditionCreate:
    def test_minimal(self):
        dto = LaunchEditionCreate(
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        assert dto.edition_name is None
        assert dto.pricing_override is None

    def test_with_all_fields(self):
        dto = LaunchEditionCreate(
            edition_name="Cohorte Especial",
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
            end_date=datetime(2026, 8, 26, tzinfo=timezone.utc),
            registration_start=datetime(2026, 6, 1, tzinfo=timezone.utc),
            registration_end=datetime(2026, 7, 1, tzinfo=timezone.utc),
            timezone="America/Lima",
            capacity=30,
            notes="Early bird pricing",
        )
        assert dto.edition_name == "Cohorte Especial"
        assert dto.timezone == "America/Lima"


class TestLaunchEditionUpdate:
    def test_all_optional(self):
        dto = LaunchEditionUpdate()
        assert dto.edition_name is None
        assert dto.status is None
