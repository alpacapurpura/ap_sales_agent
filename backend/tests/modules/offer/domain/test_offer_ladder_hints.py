"""Unit tests for OFFER_LADDER_HINTS catalog.

Covers:
- helper functions (``get_ladder_hint`` / ``get_ladder_hints_for_type``)
- semantic coherence across business types (each EBT has all 5 rungs)
- universal-vs-per-type price relationship (when overridden, ranges are
  ordered the same way — more expensive rung has higher price)
"""

from __future__ import annotations

import pytest

from src.modules.offer.domain.enums import OfferValueLevel
from src.modules.offer.domain.offer_ladder_hints import (
    OFFER_LADDER_HINTS,
    LadderHint,
    get_ladder_hint,
    get_ladder_hints_for_type,
)
from src.shared.domain.expert_business_type import ExpertBusinessType


class TestHelpers:
    def test_get_ladder_hint_returns_frozen_record(self) -> None:
        hint = get_ladder_hint(
            ExpertBusinessType.PROFESIONAL_SALUD,
            OfferValueLevel.ACTIVACION,
        )
        assert isinstance(hint, LadderHint)
        assert hint.business_type is ExpertBusinessType.PROFESIONAL_SALUD
        assert hint.value_level is OfferValueLevel.ACTIVACION

    def test_get_ladder_hints_for_type_returns_five_rungs(self) -> None:
        hints = get_ladder_hints_for_type(ExpertBusinessType.COACH_MENTOR)
        assert len(hints) == len(OfferValueLevel)
        assert set(hints.keys()) == set(OfferValueLevel)

    def test_get_ladder_hints_for_type_filters_correctly(self) -> None:
        hints = get_ladder_hints_for_type(ExpertBusinessType.SOFTWARE_SAAS)
        for hint in hints.values():
            assert hint.business_type is ExpertBusinessType.SOFTWARE_SAAS


class TestMonotonicPricing:
    """When a business type overrides prices, the ordering across rungs
    must still be monotonically non-decreasing. A "premium" rung cheaper
    than "activación" would be a data-entry error."""

    @pytest.mark.parametrize("business_type", list(ExpertBusinessType))
    def test_price_min_is_monotonic_across_rungs(self, business_type: ExpertBusinessType) -> None:
        rungs_sorted = sorted(OfferValueLevel, key=lambda v: v.value)
        hints = get_ladder_hints_for_type(business_type)
        previous_min: float | None = None
        for vl in sorted(rungs_sorted, key=_rung_order):
            hint = hints[vl]
            if hint.typical_price_min_usd is None:
                continue
            if previous_min is None:
                previous_min = hint.typical_price_min_usd
                continue
            assert hint.typical_price_min_usd >= previous_min, (
                f"{business_type.value}: rung {vl.value} has min price "
                f"{hint.typical_price_min_usd} lower than previous rung's "
                f"{previous_min}"
            )
            previous_min = hint.typical_price_min_usd


def _rung_order(vl: OfferValueLevel) -> int:
    order_map = {
        OfferValueLevel.LEAD_MAGNET: 0,
        OfferValueLevel.ACTIVACION: 1,
        OfferValueLevel.TRANSFORMACION: 2,
        OfferValueLevel.MAXIMIZACION: 3,
        OfferValueLevel.CORPORATIVO: 4,
    }
    return order_map[vl]


class TestCoverage:
    def test_exactly_fortyfive_entries(self) -> None:
        expected = len(ExpertBusinessType) * len(OfferValueLevel)
        assert len(OFFER_LADDER_HINTS) == expected

    def test_every_business_type_covers_every_rung(self) -> None:
        for bt in ExpertBusinessType:
            coverage = {vl for (b, vl) in OFFER_LADDER_HINTS if b is bt}
            assert coverage == set(OfferValueLevel), f"{bt.value} missing rungs: {set(OfferValueLevel) - coverage}"
