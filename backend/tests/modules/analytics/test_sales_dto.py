"""Tests for SalesDetailDTO structure and tier mapping.

VEN-01: Sales DTO groups offers by tier within CONVERSION/EXPANSION.
"""


class TestTierMapping:
    """VALUE_LEVEL_TO_TIER mapping tests (aligned with Value Ladder groups)."""

    def test_new_activacion_mapping(self):
        from luana_core_analytics_engine.application.dto.sales_dto import (
            get_tier_for_value_level,
        )

        assert get_tier_for_value_level("activacion") == "activacion"

    def test_new_transformacion_mapping(self):
        from luana_core_analytics_engine.application.dto.sales_dto import (
            get_tier_for_value_level,
        )

        assert get_tier_for_value_level("transformacion") == "transformacion"

    def test_new_maximizacion_mapping(self):
        from luana_core_analytics_engine.application.dto.sales_dto import (
            get_tier_for_value_level,
        )

        assert get_tier_for_value_level("maximizacion") == "maximizacion"

    def test_new_corporativo_mapping(self):
        from luana_core_analytics_engine.application.dto.sales_dto import (
            get_tier_for_value_level,
        )

        assert get_tier_for_value_level("corporativo") == "corporativo"

    def test_lead_magnet_excluded(self):
        """Lead magnets don't generate revenue (excluded from sales panel)."""
        from luana_core_analytics_engine.application.dto.sales_dto import VALUE_LEVEL_TO_TIER

        assert VALUE_LEVEL_TO_TIER.get("lead_magnet") is None

    # Legacy fallback tests (unmigrated data)
    def test_legacy_low_ticket_maps_to_activacion(self):
        from luana_core_analytics_engine.application.dto.sales_dto import (
            get_tier_for_value_level,
        )

        assert get_tier_for_value_level("level_1_low_ticket") == "activacion"

    def test_legacy_mid_ticket_maps_to_transformacion(self):
        from luana_core_analytics_engine.application.dto.sales_dto import (
            get_tier_for_value_level,
        )

        assert get_tier_for_value_level("level_2_mid_ticket") == "transformacion"

    def test_legacy_high_ticket_maps_to_transformacion(self):
        from luana_core_analytics_engine.application.dto.sales_dto import (
            get_tier_for_value_level,
        )

        assert get_tier_for_value_level("level_3_high_ticket") == "transformacion"

    def test_legacy_recurring_maps_to_transformacion(self):
        from luana_core_analytics_engine.application.dto.sales_dto import (
            get_tier_for_value_level,
        )

        assert get_tier_for_value_level("level_4_recurring") == "transformacion"

    def test_legacy_ultra_high_maps_to_maximizacion(self):
        from luana_core_analytics_engine.application.dto.sales_dto import (
            get_tier_for_value_level,
        )

        assert get_tier_for_value_level("level_5_ultra_high") == "maximizacion"

    def test_legacy_corporate_maps_to_corporativo(self):
        from luana_core_analytics_engine.application.dto.sales_dto import (
            get_tier_for_value_level,
        )

        assert get_tier_for_value_level("level_6_corporate") == "corporativo"

    def test_legacy_free_excluded(self):
        from luana_core_analytics_engine.application.dto.sales_dto import VALUE_LEVEL_TO_TIER

        assert VALUE_LEVEL_TO_TIER.get("level_0_free") is None

    def test_unknown_level_defaults_to_transformacion(self):
        from luana_core_analytics_engine.application.dto.sales_dto import (
            get_tier_for_value_level,
        )

        assert get_tier_for_value_level("level_99_unknown") == "transformacion"

    def test_none_level_defaults_to_transformacion(self):
        from luana_core_analytics_engine.application.dto.sales_dto import (
            get_tier_for_value_level,
        )

        assert get_tier_for_value_level(None) == "transformacion"


class TestSalesDetailDTOStructure:
    """SalesDetailDTO has all required fields."""

    def test_sales_detail_dto_exists(self):
        from luana_core_analytics_engine.application.dto.sales_dto import SalesDetailDTO

        assert SalesDetailDTO is not None

    def test_sales_header_kpis_dto_exists(self):
        from luana_core_analytics_engine.application.dto.sales_dto import SalesHeaderKpisDTO

        assert SalesHeaderKpisDTO is not None

    def test_revenue_group_dto_exists(self):
        from luana_core_analytics_engine.application.dto.sales_dto import RevenueGroupDTO

        assert RevenueGroupDTO is not None

    def test_tier_group_dto_exists(self):
        from luana_core_analytics_engine.application.dto.sales_dto import TierGroupDTO

        assert TierGroupDTO is not None

    def test_offer_sale_dto_exists(self):
        from luana_core_analytics_engine.application.dto.sales_dto import OfferSaleDTO

        assert OfferSaleDTO is not None


class TestCurrencyConversion:
    """Exchange rate conversion tests."""

    def test_usd_conversion_identity(self):
        from luana_core_analytics_engine.application.dto.sales_dto import convert_to_usd

        assert convert_to_usd(100.0, "USD") == 100.0

    def test_mxn_conversion(self):
        from luana_core_analytics_engine.application.dto.sales_dto import convert_to_usd

        result = convert_to_usd(1000.0, "MXN")
        assert result is not None
        assert result > 0

    def test_unknown_currency_returns_none(self):
        from luana_core_analytics_engine.application.dto.sales_dto import convert_to_usd

        assert convert_to_usd(100.0, "UNKNOWN") is None
