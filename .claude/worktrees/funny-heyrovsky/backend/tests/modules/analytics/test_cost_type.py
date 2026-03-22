"""Tests for domain enums: CostType, MetricUnit, ExtractionStatus."""

import pytest


class TestCostType:
    def test_has_exactly_four_members(self):
        from src.modules.analytics.domain.enums import CostType

        assert len(CostType) == 4

    def test_values(self):
        from src.modules.analytics.domain.enums import CostType

        assert CostType.NEUTRAL == "neutral"
        assert CostType.EXPENSE == "expense"
        assert CostType.INVESTMENT == "investment"
        assert CostType.REVENUE == "revenue"

    def test_is_str_enum(self):
        from src.modules.analytics.domain.enums import CostType

        for member in CostType:
            assert isinstance(member, str)
            assert isinstance(member.value, str)


class TestMetricUnit:
    def test_has_exactly_four_members(self):
        from src.modules.analytics.domain.enums import MetricUnit

        assert len(MetricUnit) == 4

    def test_values(self):
        from src.modules.analytics.domain.enums import MetricUnit

        assert MetricUnit.COUNT == "count"
        assert MetricUnit.CURRENCY == "currency"
        assert MetricUnit.PERCENTAGE == "percentage"
        assert MetricUnit.RATIO == "ratio"

    def test_is_str_enum(self):
        from src.modules.analytics.domain.enums import MetricUnit

        for member in MetricUnit:
            assert isinstance(member, str)


class TestExtractionStatus:
    def test_has_exactly_five_members(self):
        from src.modules.analytics.domain.enums import ExtractionStatus

        assert len(ExtractionStatus) == 5

    def test_values(self):
        from src.modules.analytics.domain.enums import ExtractionStatus

        expected = {"pending", "running", "success", "failed", "retrying"}
        actual = {member.value for member in ExtractionStatus}
        assert actual == expected

    def test_is_str_enum(self):
        from src.modules.analytics.domain.enums import ExtractionStatus

        for member in ExtractionStatus:
            assert isinstance(member, str)
