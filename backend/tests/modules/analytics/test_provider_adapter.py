"""Tests for BaseMetricsProvider ABC and ExtractedMetric model."""

import pytest
from datetime import date
from uuid import UUID


class TestBaseMetricsProvider:
    def test_cannot_instantiate_abc(self):
        from src.modules.analytics.infrastructure.providers.base import (
            BaseMetricsProvider,
        )

        with pytest.raises(TypeError):
            BaseMetricsProvider()

    def test_concrete_provider_works(self):
        """A concrete DummyProvider implementing all abstract methods can be instantiated."""
        from src.modules.analytics.infrastructure.providers.base import (
            BaseMetricsProvider,
            ExtractedMetric,
        )
        from typing import List

        class DummyProvider(BaseMetricsProvider):
            async def extract_metrics(
                self,
                tenant_id: UUID,
                credentials: dict,
                start_date: date,
                end_date: date,
            ) -> List[ExtractedMetric]:
                return [
                    ExtractedMetric(
                        provider="dummy",
                        channel_slug="dummy-channel",
                        metric_name="impressions",
                        value=100.0,
                        unit="count",
                        date=start_date,
                    )
                ]

            def provider_name(self) -> str:
                return "dummy"

            def rate_limit_config(self) -> dict:
                return {"requests_per_minute": 60}

        provider = DummyProvider()
        assert provider.provider_name() == "dummy"
        assert provider.rate_limit_config()["requests_per_minute"] == 60

    @pytest.mark.asyncio
    async def test_concrete_provider_extract_returns_list(self):
        """DummyProvider.extract_metrics returns List[ExtractedMetric]."""
        from src.modules.analytics.infrastructure.providers.base import (
            BaseMetricsProvider,
            ExtractedMetric,
        )
        from typing import List
        import uuid

        class DummyProvider(BaseMetricsProvider):
            async def extract_metrics(
                self,
                tenant_id: UUID,
                credentials: dict,
                start_date: date,
                end_date: date,
            ) -> List[ExtractedMetric]:
                return [
                    ExtractedMetric(
                        provider="dummy",
                        channel_slug="test",
                        metric_name="clicks",
                        value=42.0,
                        unit="count",
                        date=start_date,
                    )
                ]

            def provider_name(self) -> str:
                return "dummy"

            def rate_limit_config(self) -> dict:
                return {}

        provider = DummyProvider()
        result = await provider.extract_metrics(
            tenant_id=uuid.uuid4(),
            credentials={"token": "test"},
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
        )
        assert len(result) == 1
        assert isinstance(result[0], ExtractedMetric)
        assert result[0].value == 42.0


class TestExtractedMetric:
    def test_validates_required_fields(self):
        from src.modules.analytics.infrastructure.providers.base import ExtractedMetric

        metric = ExtractedMetric(
            provider="meta",
            channel_slug="meta-ads",
            metric_name="impressions",
            value=1500.0,
            unit="count",
            date=date(2026, 3, 1),
        )
        assert metric.provider == "meta"
        assert metric.value == 1500.0

    def test_optional_fields_default_correctly(self):
        from src.modules.analytics.infrastructure.providers.base import ExtractedMetric

        metric = ExtractedMetric(
            provider="google",
            channel_slug="google-ads",
            metric_name="spend",
            value=250.50,
            unit="currency",
            date=date(2026, 3, 1),
        )
        assert metric.currency is None
        assert metric.campaign_id is None
        assert metric.ad_set_id is None
        assert metric.ad_id is None
        assert metric.extra == {}

    def test_rejects_missing_required(self):
        from src.modules.analytics.infrastructure.providers.base import ExtractedMetric

        with pytest.raises(Exception):
            ExtractedMetric(
                provider="meta",
                # missing channel_slug, metric_name, value, unit, date
            )
