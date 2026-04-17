"""Architecture fitness: OfferValueLevel enum <-> catalog invariants.

Mirrors ``test_archetype_catalog_completeness``. Adding a new rung to
``OfferValueLevel`` without a matching catalog entry (or leaving an
orphan entry) fails CI.
"""

from __future__ import annotations

from src.modules.offer.domain.enums import OfferValueLevel
from src.modules.offer.domain.value_level_catalog import VALUE_LEVEL_CATALOG


def test_every_value_level_has_a_catalog_entry() -> None:
    missing = [v for v in OfferValueLevel if v not in VALUE_LEVEL_CATALOG]
    assert missing == [], (
        "Every OfferValueLevel must have a VALUE_LEVEL_CATALOG entry. "
        f"Missing: {missing}. Add a record to offer/domain/value_level_catalog.py."
    )


def test_catalog_has_no_orphan_entries() -> None:
    enum_values = set(OfferValueLevel)
    catalog_values = set(VALUE_LEVEL_CATALOG.keys())
    orphans = catalog_values - enum_values
    assert orphans == set(), f"Catalog has entries for value levels that no longer exist in the enum: {orphans}"


def test_catalog_records_self_reference_their_level() -> None:
    for value_level, metadata in VALUE_LEVEL_CATALOG.items():
        assert metadata.value_level is value_level, (
            f"Catalog entry for {value_level} declares value_level={metadata.value_level}"
        )


def test_orders_form_contiguous_funnel() -> None:
    """Rungs must form a contiguous 0..N-1 sequence so UI can sort them."""
    orders = sorted(m.order for m in VALUE_LEVEL_CATALOG.values())
    assert orders == list(range(len(orders))), (
        "value-level orders must be a contiguous 0..N-1 sequence for funnel sorting."
    )
