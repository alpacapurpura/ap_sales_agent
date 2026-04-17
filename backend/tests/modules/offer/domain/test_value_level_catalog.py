"""Unit tests for the OfferValueLevel metadata catalog.

The ladder (LEAD_MAGNET → ACTIVACION → TRANSFORMACION → MAXIMIZACION →
CORPORATIVO) is strategic metadata reused across the Offer Studio
dashboard (grouping) and the wizard (ladder step). Living as a frozen
catalog keeps it out of frontend components and prevents drift.
"""

from __future__ import annotations

from src.modules.offer.domain.enums import OfferValueLevel
from src.modules.offer.domain.value_level_catalog import (
    VALUE_LEVEL_CATALOG,
    ValueLevelMetadata,
    get_value_level_metadata,
)


class TestValueLevelCatalog:
    def test_every_enum_value_has_a_catalog_entry(self) -> None:
        missing = [v for v in OfferValueLevel if v not in VALUE_LEVEL_CATALOG]
        assert missing == []

    def test_catalog_has_no_orphan_entries(self) -> None:
        enum_values = set(OfferValueLevel)
        catalog_values = set(VALUE_LEVEL_CATALOG.keys())
        orphans = catalog_values - enum_values
        assert orphans == set()

    def test_every_entry_has_required_localized_fields(self) -> None:
        for value_level, metadata in VALUE_LEVEL_CATALOG.items():
            assert isinstance(metadata, ValueLevelMetadata)
            assert metadata.value_level is value_level
            assert metadata.label_es.strip(), f"label_es empty for {value_level}"
            assert metadata.description_es.strip(), f"description_es empty for {value_level}"
            assert metadata.role_in_funnel_es.strip(), f"role_in_funnel_es empty for {value_level}"
            assert metadata.icon_name.strip(), f"icon_name empty for {value_level}"
            assert metadata.examples_es, f"examples_es empty for {value_level}"

    def test_ordering_is_funnel_linear_and_unique(self) -> None:
        orders = [m.order for m in VALUE_LEVEL_CATALOG.values()]
        # 5 rungs, ordered 0..4 in funnel progression
        assert sorted(orders) == [0, 1, 2, 3, 4]

    def test_lead_magnet_is_first_rung(self) -> None:
        lm = get_value_level_metadata(OfferValueLevel.LEAD_MAGNET)
        assert lm.order == 0
        assert lm.is_free is True

    def test_corporativo_is_last_rung(self) -> None:
        corp = get_value_level_metadata(OfferValueLevel.CORPORATIVO)
        assert corp.order == 4

    def test_paid_rungs_declare_typical_price_range(self) -> None:
        """Wizard uses these hints to suggest pricing to the user."""
        for value_level, metadata in VALUE_LEVEL_CATALOG.items():
            if metadata.is_free:
                assert metadata.typical_price_min_usd is None
                assert metadata.typical_price_max_usd is None
            else:
                assert metadata.typical_price_min_usd is not None
                assert metadata.typical_price_max_usd is not None
                assert metadata.typical_price_min_usd < metadata.typical_price_max_usd, (
                    f"{value_level}: min must be < max"
                )

    def test_icon_names_are_pascalcase(self) -> None:
        for metadata in VALUE_LEVEL_CATALOG.values():
            assert metadata.icon_name[0].isupper()
