"""Tests for SalesDetailDTO structure and tier mapping.

VEN-01: Sales DTO groups offers by tier within CONVERSION/EXPANSION.
Wave 0 stubs -- will fail until 08-01 creates production code.
"""
import pytest


class TestTierMapping:
    """VALUE_LEVEL_TO_TIER mapping tests."""

    def test_low_ticket_mapping(self):
        from src.modules.analytics.application.dto.sales_dto import get_tier_for_value_level
        assert get_tier_for_value_level("level_1_low_ticket") == "low_ticket"

    def test_mid_ticket_mapping(self):
        from src.modules.analytics.application.dto.sales_dto import get_tier_for_value_level
        assert get_tier_for_value_level("level_2_mid_ticket") == "mid_ticket"

    def test_high_ticket_mapping(self):
        from src.modules.analytics.application.dto.sales_dto import get_tier_for_value_level
        assert get_tier_for_value_level("level_3_high_ticket") == "high_ticket"

    def test_recurring_mapping(self):
        from src.modules.analytics.application.dto.sales_dto import get_tier_for_value_level
        assert get_tier_for_value_level("level_4_recurring") == "recurrente"

    def test_ultra_high_maps_to_high_ticket(self):
        from src.modules.analytics.application.dto.sales_dto import get_tier_for_value_level
        assert get_tier_for_value_level("level_5_ultra_high") == "high_ticket"

    def test_corporate_maps_to_high_ticket(self):
        from src.modules.analytics.application.dto.sales_dto import get_tier_for_value_level
        assert get_tier_for_value_level("level_6_corporate") == "high_ticket"

    def test_unknown_level_defaults_to_high_ticket(self):
        from src.modules.analytics.application.dto.sales_dto import get_tier_for_value_level
        assert get_tier_for_value_level("level_99_unknown") == "high_ticket"

    def test_none_level_defaults_to_high_ticket(self):
        from src.modules.analytics.application.dto.sales_dto import get_tier_for_value_level
        assert get_tier_for_value_level(None) == "high_ticket"

    def test_free_level_excluded(self):
        """FREE tier (level_0) should map to None (excluded from sales panel)."""
        from src.modules.analytics.application.dto.sales_dto import VALUE_LEVEL_TO_TIER
        assert VALUE_LEVEL_TO_TIER.get("level_0_free") is None


class TestSalesDetailDTOStructure:
    """SalesDetailDTO has all required fields."""

    def test_sales_detail_dto_exists(self):
        from src.modules.analytics.application.dto.sales_dto import SalesDetailDTO
        assert SalesDetailDTO is not None

    def test_sales_header_kpis_dto_exists(self):
        from src.modules.analytics.application.dto.sales_dto import SalesHeaderKpisDTO
        assert SalesHeaderKpisDTO is not None

    def test_revenue_group_dto_exists(self):
        from src.modules.analytics.application.dto.sales_dto import RevenueGroupDTO
        assert RevenueGroupDTO is not None

    def test_tier_group_dto_exists(self):
        from src.modules.analytics.application.dto.sales_dto import TierGroupDTO
        assert TierGroupDTO is not None

    def test_offer_sale_dto_exists(self):
        from src.modules.analytics.application.dto.sales_dto import OfferSaleDTO
        assert OfferSaleDTO is not None


class TestCurrencyConversion:
    """Exchange rate conversion tests."""

    def test_usd_conversion_identity(self):
        from src.modules.analytics.application.dto.sales_dto import convert_to_usd
        assert convert_to_usd(100.0, "USD") == 100.0

    def test_mxn_conversion(self):
        from src.modules.analytics.application.dto.sales_dto import convert_to_usd
        result = convert_to_usd(1000.0, "MXN")
        assert result is not None
        assert result > 0

    def test_unknown_currency_returns_none(self):
        from src.modules.analytics.application.dto.sales_dto import convert_to_usd
        assert convert_to_usd(100.0, "UNKNOWN") is None
