"""Tests for ad performance service -- aggregation logic."""

from unittest.mock import MagicMock
from uuid import uuid4

from src.modules.analytics.application.services.ad_performance_service import (
    AdPerformanceService,
)


def _make_metric_row(
    ad_id: str, metric_name: str, value: float, ad_name: str = "Test Ad"
):
    """Create a mock DB row for official_metrics."""
    row = MagicMock()
    row._mapping = {
        "ad_id": ad_id,
        "metric_name": metric_name,
        "total_value": value,
        "ad_name": ad_name,
    }
    return row


class TestAdPerformanceService:
    def test_get_top_ads_aggregates_by_ad_id(self):
        tenant_id = uuid4()
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchall.return_value = [
            _make_metric_row("ad_001", "spend", 100.0, "Video Testimonio"),
            _make_metric_row("ad_001", "conversions", 10.0, "Video Testimonio"),
            _make_metric_row("ad_001", "roas", 3.5, "Video Testimonio"),
            _make_metric_row("ad_001", "ctr", 2.4, "Video Testimonio"),
            _make_metric_row("ad_001", "cpc", 0.42, "Video Testimonio"),
            _make_metric_row("ad_002", "spend", 200.0, "Carrusel Beneficios"),
            _make_metric_row("ad_002", "conversions", 5.0, "Carrusel Beneficios"),
            _make_metric_row("ad_002", "roas", 1.2, "Carrusel Beneficios"),
        ]

        service = AdPerformanceService(mock_db)
        result = service.get_top_ads(tenant_id, "meta-ads", "30d", limit=10)

        assert result.total_ads == 2
        assert result.period == "30d"
        assert len(result.ads) == 2

        # Should be sorted by spend descending
        assert result.ads[0].ad_id == "ad_002"
        assert result.ads[0].spend == 200.0
        assert result.ads[1].ad_id == "ad_001"
        assert result.ads[1].spend == 100.0
        assert result.ads[1].conversions == 10.0
        assert result.ads[1].roas == 3.5

    def test_get_top_ads_assigns_performance_tags(self):
        tenant_id = uuid4()
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchall.return_value = [
            _make_metric_row("ad_top", "spend", 100.0),
            _make_metric_row("ad_top", "roas", 5.0),
            _make_metric_row("ad_mid", "spend", 100.0),
            _make_metric_row("ad_mid", "roas", 2.0),
            _make_metric_row("ad_bad", "spend", 100.0),
            _make_metric_row("ad_bad", "roas", 0.5),
        ]

        service = AdPerformanceService(mock_db)
        result = service.get_top_ads(tenant_id, "meta-ads", "30d")

        tags = {ad.ad_id: ad.performance_tag for ad in result.ads}
        assert tags["ad_top"] == "top_performer"
        assert tags["ad_bad"] == "underperformer"

    def test_get_top_ads_empty_when_no_data(self):
        tenant_id = uuid4()
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchall.return_value = []

        service = AdPerformanceService(mock_db)
        result = service.get_top_ads(tenant_id, "meta-ads", "30d")

        assert result.total_ads == 0
        assert result.ads == []
