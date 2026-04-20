"""Architecture fitness: OFFER_LADDER_HINTS invariants.

Every ``(ExpertBusinessType, OfferValueLevel)`` pair must have a hint
(9 x 5 = 45 entries). Missing entries, orphans, empty fields, or
out-of-range prices fail CI.

Also enforces the "universal fallback still applies" invariant: per-type
prices must stay within ±10x of the universal ``VALUE_LEVEL_CATALOG``
range — a 10x deviation signals a mis-classified rung, not a valid
tenant-specific adjustment.
"""

from __future__ import annotations

import pytest

from src.modules.offer.domain.enums import OfferValueLevel
from src.modules.offer.domain.offer_ladder_hints import (
    OFFER_LADDER_HINTS,
    LadderHint,
)
from src.modules.offer.domain.value_level_catalog import VALUE_LEVEL_CATALOG
from src.shared.domain.expert_business_type import ExpertBusinessType

_EXPECTED_KEYS = frozenset((bt, vl) for bt in ExpertBusinessType for vl in OfferValueLevel)


def test_every_expected_pair_has_a_hint() -> None:
    missing = _EXPECTED_KEYS - set(OFFER_LADDER_HINTS.keys())
    assert missing == set(), (
        f"Missing hints for {len(missing)} (EBT, VL) pair(s). "
        f"Sample: {sorted(missing)[:5]}. Add entries to offer_ladder_hints.py."
    )


def test_catalog_has_no_orphan_entries() -> None:
    orphans = set(OFFER_LADDER_HINTS.keys()) - _EXPECTED_KEYS
    assert orphans == set(), f"Hints reference unknown (EBT, VL) pairs: {orphans}. Enum drifted from catalog."


def test_hints_self_reference_their_keys() -> None:
    for (bt, vl), hint in OFFER_LADDER_HINTS.items():
        assert isinstance(hint, LadderHint)
        assert hint.business_type is bt, f"hint at ({bt}, {vl}) has wrong business_type"
        assert hint.value_level is vl, f"hint at ({bt}, {vl}) has wrong value_level"


def test_examples_and_offer_type_non_empty() -> None:
    for (bt, vl), hint in OFFER_LADDER_HINTS.items():
        assert hint.examples_es, f"examples_es empty for ({bt}, {vl})"
        assert hint.typical_offer_type_es.strip(), f"typical_offer_type_es empty for ({bt}, {vl})"


def test_lead_magnet_hints_have_no_prices() -> None:
    """LEAD_MAGNET is free in the universal catalog — per-type overrides
    must not introduce a paid price for it."""
    for (bt, vl), hint in OFFER_LADDER_HINTS.items():
        if vl is OfferValueLevel.LEAD_MAGNET:
            assert hint.typical_price_min_usd is None, f"({bt}, LEAD_MAGNET) has min price — LM must stay free"
            assert hint.typical_price_max_usd is None, f"({bt}, LEAD_MAGNET) has max price — LM must stay free"


def test_paid_rungs_declare_both_prices() -> None:
    """Paid rungs must declare both min and max (or both None to fall back
    to the universal VL range). Mixed partial overrides are a bug."""
    for (bt, vl), hint in OFFER_LADDER_HINTS.items():
        if vl is OfferValueLevel.LEAD_MAGNET:
            continue
        min_p = hint.typical_price_min_usd
        max_p = hint.typical_price_max_usd
        if min_p is None and max_p is None:
            continue  # fallback to universal — valid
        assert min_p is not None and max_p is not None, (
            f"({bt}, {vl}) declares only one bound — must declare both or neither"
        )
        assert min_p < max_p, f"({bt}, {vl}) min={min_p} must be < max={max_p}"


@pytest.mark.parametrize("pair,hint", list(OFFER_LADDER_HINTS.items()))
def test_per_type_prices_stay_within_universal_band(
    pair: tuple[ExpertBusinessType, OfferValueLevel],
    hint: LadderHint,
) -> None:
    """Per-type prices should stay within ±10x of the universal VL range.

    Wider deviation almost always signals a mis-classified rung (the
    tenant's "premium" offer actually belongs in a different rung). The
    band is intentionally loose: Latam currency swings + pricing variance
    already cover 3-4x; 10x is the sanity boundary.
    """
    _, vl = pair
    if vl is OfferValueLevel.LEAD_MAGNET:
        return
    if hint.typical_price_min_usd is None:
        return  # fallback to universal — by definition within band
    universal = VALUE_LEVEL_CATALOG[vl]
    assert universal.typical_price_min_usd is not None
    assert universal.typical_price_max_usd is not None

    min_band = universal.typical_price_min_usd / 10.0
    max_band = universal.typical_price_max_usd * 10.0
    assert hint.typical_price_min_usd >= min_band, (
        f"{pair} min={hint.typical_price_min_usd} below 1/10 of universal min "
        f"({universal.typical_price_min_usd}) — possible rung misclassification"
    )
    # hint.typical_price_max_usd narrowed to float above via the None guard.
    assert hint.typical_price_max_usd is not None
    assert hint.typical_price_max_usd <= max_band, (
        f"{pair} max={hint.typical_price_max_usd} exceeds 10x universal max "
        f"({universal.typical_price_max_usd}) — possible rung misclassification"
    )
