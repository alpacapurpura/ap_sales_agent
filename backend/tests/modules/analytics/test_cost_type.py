"""Tests for domain enums: CostType, MetricUnit, ExtractionStatus."""


class TestCostType:
    def test_has_exactly_four_members(self):
        from luana_core_analytics_engine.domain.enums import CostType

        assert len(CostType) == 4

    def test_values(self):
        from luana_core_analytics_engine.domain.enums import CostType

        assert CostType.NEUTRAL == "neutral"
        assert CostType.EXPENSE == "expense"
        assert CostType.INVESTMENT == "investment"
        assert CostType.REVENUE == "revenue"

    def test_is_str_enum(self):
        from luana_core_analytics_engine.domain.enums import CostType

        for member in CostType:
            assert isinstance(member, str)
            assert isinstance(member.value, str)


class TestMetricUnit:
    def test_has_exactly_six_members(self):
        from luana_core_analytics_engine.domain.enums import MetricUnit

        assert len(MetricUnit) == 6

    def test_values(self):
        from luana_core_analytics_engine.domain.enums import MetricUnit

        assert MetricUnit.COUNT == "count"
        assert MetricUnit.CURRENCY == "currency"
        assert MetricUnit.PERCENTAGE == "percentage"
        assert MetricUnit.RATIO == "ratio"
        assert MetricUnit.SECONDS == "seconds"
        assert MetricUnit.JSON == "json"

    def test_is_str_enum(self):
        from luana_core_analytics_engine.domain.enums import MetricUnit

        for member in MetricUnit:
            assert isinstance(member, str)


class TestExtractionStatus:
    def test_has_exactly_six_members(self):
        from luana_core_analytics_engine.domain.enums import ExtractionStatus

        assert len(ExtractionStatus) == 6

    def test_values(self):
        from luana_core_analytics_engine.domain.enums import ExtractionStatus

        expected = {
            "pending",
            "running",
            "success",
            "failed",
            "partial_success",
            "retrying",
        }
        actual = {member.value for member in ExtractionStatus}
        assert actual == expected

    def test_is_str_enum(self):
        from luana_core_analytics_engine.domain.enums import ExtractionStatus

        for member in ExtractionStatus:
            assert isinstance(member, str)
