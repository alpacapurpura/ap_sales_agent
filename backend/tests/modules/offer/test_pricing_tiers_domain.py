"""Domain tests for ``PricingTier`` + ``resolve_active_tier`` (Phase 4).

The tier VO + resolver model ``early bird → regular → last call`` windows
that a single edition cycles through. Windows are **half-open** —
``[valid_from, valid_until)`` — so the boundary instant belongs to the
next tier, eliminating the ambiguous "both active at T" edge case.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from luana_core_offer_studio.domain.launch_edition import (
    LaunchEdition,
    PricingTier,
    resolve_active_tier,
)
from luana_core_offer_studio.domain.offer import PricingStructure


def _tier(
    label: str,
    *,
    valid_from: datetime | None = None,
    valid_until: datetime | None = None,
    amount: float = 100.0,
    sort_order: int = 0,
) -> PricingTier:
    return PricingTier(
        label=label,
        pricing=[PricingStructure(label=label, total_amount=amount)],
        valid_from=valid_from,
        valid_until=valid_until,
        sort_order=sort_order,
    )


class TestPricingTierVO:
    def test_requires_non_empty_pricing(self) -> None:
        with pytest.raises(ValueError, match="pricing"):
            PricingTier(
                label="broken",
                pricing=[],
            )

    def test_valid_until_before_valid_from_raises(self) -> None:
        with pytest.raises(ValueError, match="valid_until"):
            PricingTier(
                label="bad",
                pricing=[PricingStructure(label="x", total_amount=1.0)],
                valid_from=datetime(2026, 6, 10, tzinfo=timezone.utc),
                valid_until=datetime(2026, 6, 5, tzinfo=timezone.utc),
            )

    def test_open_ended_both_sides_is_allowed(self) -> None:
        tier = _tier("regular")
        assert tier.valid_from is None
        assert tier.valid_until is None


class TestResolveActiveTier:
    def test_returns_none_when_no_tiers(self) -> None:
        assert resolve_active_tier([], datetime(2026, 6, 1, tzinfo=timezone.utc)) is None

    def test_returns_tier_whose_window_contains_now(self) -> None:
        early = _tier(
            "early",
            valid_until=datetime(2026, 5, 1, tzinfo=timezone.utc),
            sort_order=0,
        )
        regular = _tier(
            "regular",
            valid_from=datetime(2026, 5, 1, tzinfo=timezone.utc),
            valid_until=datetime(2026, 5, 14, tzinfo=timezone.utc),
            sort_order=1,
        )
        last_call = _tier(
            "last_call",
            valid_from=datetime(2026, 5, 14, tzinfo=timezone.utc),
            sort_order=2,
        )
        tiers = [early, regular, last_call]

        now = datetime(2026, 4, 15, tzinfo=timezone.utc)
        assert resolve_active_tier(tiers, now).label == "early"

        now = datetime(2026, 5, 7, tzinfo=timezone.utc)
        assert resolve_active_tier(tiers, now).label == "regular"

        now = datetime(2026, 5, 30, tzinfo=timezone.utc)
        assert resolve_active_tier(tiers, now).label == "last_call"

    def test_half_open_boundary_picks_next_tier(self) -> None:
        """At exactly ``valid_until`` the tier has already expired."""
        early = _tier(
            "early",
            valid_until=datetime(2026, 5, 1, tzinfo=timezone.utc),
            sort_order=0,
        )
        regular = _tier(
            "regular",
            valid_from=datetime(2026, 5, 1, tzinfo=timezone.utc),
            sort_order=1,
        )

        at_boundary = datetime(2026, 5, 1, tzinfo=timezone.utc)
        assert resolve_active_tier([early, regular], at_boundary).label == "regular"

    def test_sort_order_breaks_ties_deterministically(self) -> None:
        tier_a = _tier("a", sort_order=5)
        tier_b = _tier("b", sort_order=1)
        assert resolve_active_tier([tier_a, tier_b], datetime(2030, 1, 1, tzinfo=timezone.utc)).label == "b"

    def test_returns_none_when_all_windows_closed(self) -> None:
        past = _tier(
            "past",
            valid_until=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        future = _tier(
            "future",
            valid_from=datetime(2099, 1, 1, tzinfo=timezone.utc),
        )
        now = datetime(2026, 6, 1, tzinfo=timezone.utc)
        assert resolve_active_tier([past, future], now) is None


class TestLaunchEditionNonOverlapping:
    def test_overlapping_windows_raise(self) -> None:
        overlapping_a = _tier(
            "a",
            valid_from=datetime(2026, 5, 1, tzinfo=timezone.utc),
            valid_until=datetime(2026, 5, 10, tzinfo=timezone.utc),
        )
        overlapping_b = _tier(
            "b",
            valid_from=datetime(2026, 5, 5, tzinfo=timezone.utc),
            valid_until=datetime(2026, 5, 15, tzinfo=timezone.utc),
        )
        with pytest.raises(ValueError, match="overlap"):
            LaunchEdition(
                offer_id=uuid4(),
                tenant_id=uuid4(),
                edition_name="Cohort",
                edition_number=1,
                start_date=datetime(2026, 5, 1, tzinfo=timezone.utc),
                pricing_tiers=[overlapping_a, overlapping_b],
            )

    def test_adjacent_windows_are_allowed(self) -> None:
        """Half-open intervals mean touching boundaries do NOT overlap."""
        a = _tier(
            "a",
            valid_until=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )
        b = _tier(
            "b",
            valid_from=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )
        ed = LaunchEdition(
            offer_id=uuid4(),
            tenant_id=uuid4(),
            edition_name="Cohort",
            edition_number=1,
            start_date=datetime(2026, 5, 1, tzinfo=timezone.utc),
            pricing_tiers=[a, b],
        )
        assert len(ed.pricing_tiers) == 2

    def test_multiple_open_ended_tiers_raise(self) -> None:
        a = _tier("a")  # open both sides
        b = _tier("b")  # open both sides — overlap by definition
        with pytest.raises(ValueError, match="overlap"):
            LaunchEdition(
                offer_id=uuid4(),
                tenant_id=uuid4(),
                edition_name="Cohort",
                edition_number=1,
                start_date=datetime(2026, 5, 1, tzinfo=timezone.utc),
                pricing_tiers=[a, b],
            )
