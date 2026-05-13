"""Domain invariants for LaunchEdition — lifecycle, visibility, date rules."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from luana_core_offer_studio.domain.launch_edition import (
    EditionStatus,
    EditionVisibility,
    LaunchEdition,
)

TENANT_ID = uuid4()
OFFER_ID = uuid4()


def _minimal(**overrides) -> dict:
    base = {
        "offer_id": OFFER_ID,
        "tenant_id": TENANT_ID,
        "edition_name": "Test edition",
        "edition_number": 1,
    }
    base.update(overrides)
    return base


class TestPlaceholderEdition:
    """DRAFT + PRIVATE editions may exist without a start_date."""

    def test_draft_private_allows_null_start_date(self) -> None:
        edition = LaunchEdition(
            **_minimal(status=EditionStatus.DRAFT, visibility=EditionVisibility.PRIVATE),
        )
        assert edition.start_date is None
        assert edition.status is EditionStatus.DRAFT
        assert edition.visibility is EditionVisibility.PRIVATE


class TestPublishingInvariants:
    """Rules that gate the path to making an edition discoverable."""

    def test_public_edition_requires_start_date(self) -> None:
        with pytest.raises(ValueError, match="public edition requires start_date"):
            LaunchEdition(
                **_minimal(
                    status=EditionStatus.UPCOMING,
                    visibility=EditionVisibility.PUBLIC,
                    start_date=None,
                ),
            )

    def test_upcoming_edition_requires_start_date(self) -> None:
        with pytest.raises(ValueError, match="upcoming edition requires start_date"):
            LaunchEdition(
                **_minimal(
                    status=EditionStatus.UPCOMING,
                    visibility=EditionVisibility.PRIVATE,
                    start_date=None,
                ),
            )

    def test_active_edition_requires_start_date(self) -> None:
        with pytest.raises(ValueError, match="active edition requires start_date"):
            LaunchEdition(
                **_minimal(
                    status=EditionStatus.ACTIVE,
                    visibility=EditionVisibility.PRIVATE,
                    start_date=None,
                ),
            )

    def test_draft_cannot_be_public(self) -> None:
        """A DRAFT is work-in-progress — it must not leak to leads."""
        with pytest.raises(ValueError, match="draft edition cannot be public"):
            LaunchEdition(
                **_minimal(
                    status=EditionStatus.DRAFT,
                    visibility=EditionVisibility.PUBLIC,
                    start_date=datetime(2026, 5, 15, tzinfo=timezone.utc),
                ),
            )

    def test_upcoming_with_start_date_is_valid(self) -> None:
        edition = LaunchEdition(
            **_minimal(
                status=EditionStatus.UPCOMING,
                visibility=EditionVisibility.PUBLIC,
                start_date=datetime(2026, 5, 15, tzinfo=timezone.utc),
            ),
        )
        assert edition.visibility is EditionVisibility.PUBLIC


class TestDateOrderingInvariants:
    """Temporal consistency: dates must be monotonically increasing."""

    def test_end_date_before_start_date_is_rejected(self) -> None:
        start = datetime(2026, 5, 15, tzinfo=timezone.utc)
        with pytest.raises(ValueError, match="end_date cannot be before start_date"):
            LaunchEdition(
                **_minimal(start_date=start, end_date=start - timedelta(days=1)),
            )

    def test_registration_end_before_start_is_rejected(self) -> None:
        reg_start = datetime(2026, 4, 1, tzinfo=timezone.utc)
        with pytest.raises(ValueError, match="registration_end cannot be before"):
            LaunchEdition(
                **_minimal(
                    registration_start=reg_start,
                    registration_end=reg_start - timedelta(days=1),
                ),
            )

    def test_end_equal_to_start_is_allowed(self) -> None:
        """Zero-duration edition (same-day morning → evening) is valid."""
        same = datetime(2026, 5, 15, 19, tzinfo=timezone.utc)
        edition = LaunchEdition(**_minimal(start_date=same, end_date=same))
        assert edition.start_date == edition.end_date


class TestClonedFromProvenance:
    def test_cloned_from_edition_id_is_persisted(self) -> None:
        source_id = uuid4()
        edition = LaunchEdition(**_minimal(cloned_from_edition_id=source_id))
        assert edition.cloned_from_edition_id == source_id

    def test_cloned_from_edition_id_defaults_to_none(self) -> None:
        edition = LaunchEdition(**_minimal())
        assert edition.cloned_from_edition_id is None
