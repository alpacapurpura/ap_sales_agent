"""Tests for ad performance service -- aggregation logic."""

from unittest.mock import MagicMock
from uuid import uuid4

from src.modules.analytics.application.services.ad_performance_service import (
    AdPerformanceService,
)


def _make_metric_row(
    ad_id: str,
    metric_name: str,
    value: float,
    ad_name: str = "Test Ad",
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


def _make_ad_creative_row(
    external_id: str,
    creative_video_id: str | None = None,
    creative_image_url: str | None = None,
    creative_thumbnail_url: str | None = None,
    preview_shareable_link: str | None = None,
    creative_body: str | None = None,
    creative_cta: str | None = None,
    effective_status: str | None = None,
    campaign_name: str | None = None,
):
    """Create a mock DB row for ads table creative metadata."""
    row = MagicMock()
    row._mapping = {
        "external_id": external_id,
        "creative_video_id": creative_video_id,
        "creative_image_url": creative_image_url,
        "creative_thumbnail_url": creative_thumbnail_url,
        "preview_shareable_link": preview_shareable_link,
        "creative_body": creative_body,
        "creative_cta": creative_cta,
        "effective_status": effective_status,
        "campaign_name": campaign_name,
    }
    return row


def _setup_query_mocks(mock_db, metric_rows, ad_creative_rows, currency="USD"):
    """Configure mock_db.execute for the three queries in get_top_ads.

    1. official_metrics aggregation query
    2. ads table creative metadata query
    3. currency detection query
    """
    metrics_result = MagicMock()
    metrics_result.fetchall.return_value = metric_rows

    ads_result = MagicMock()
    ads_result.fetchall.return_value = ad_creative_rows

    currency_row = MagicMock()
    currency_row._mapping = {"currency": currency}
    currency_result = MagicMock()
    currency_result.fetchone.return_value = currency_row

    mock_db.execute.side_effect = [metrics_result, ads_result, currency_result]


class TestAdPerformanceService:
    def test_get_top_ads_aggregates_by_ad_id(self):
        tenant_id = uuid4()
        mock_db = MagicMock()

        metric_rows = [
            _make_metric_row("ad_001", "spend", 100.0, "Video Testimonio"),
            _make_metric_row("ad_001", "conversions", 10.0, "Video Testimonio"),
            _make_metric_row("ad_001", "roas", 3.5, "Video Testimonio"),
            _make_metric_row("ad_001", "ctr", 2.4, "Video Testimonio"),
            _make_metric_row("ad_001", "cpc", 0.42, "Video Testimonio"),
            _make_metric_row("ad_002", "spend", 200.0, "Carrusel Beneficios"),
            _make_metric_row("ad_002", "conversions", 5.0, "Carrusel Beneficios"),
            _make_metric_row("ad_002", "roas", 1.2, "Carrusel Beneficios"),
        ]
        ad_creative_rows = [
            _make_ad_creative_row("ad_001", creative_video_id="vid_123"),
            _make_ad_creative_row(
                "ad_002",
                creative_image_url="https://img.example.com/carousel.jpg",
            ),
        ]
        _setup_query_mocks(mock_db, metric_rows, ad_creative_rows)

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

        metric_rows = [
            _make_metric_row("ad_top", "spend", 100.0),
            _make_metric_row("ad_top", "roas", 5.0),
            _make_metric_row("ad_mid", "spend", 100.0),
            _make_metric_row("ad_mid", "roas", 2.0),
            _make_metric_row("ad_bad", "spend", 100.0),
            _make_metric_row("ad_bad", "roas", 0.5),
        ]
        ad_creative_rows = []  # No creative metadata — all default to "image"
        _setup_query_mocks(mock_db, metric_rows, ad_creative_rows)

        service = AdPerformanceService(mock_db)
        result = service.get_top_ads(tenant_id, "meta-ads", "30d")

        tags = {ad.ad_id: ad.performance_tag for ad in result.ads}
        assert tags["ad_top"] == "top_performer"
        assert tags["ad_bad"] == "underperformer"

    def test_get_top_ads_empty_when_no_data(self):
        tenant_id = uuid4()
        mock_db = MagicMock()

        # First call: metrics query returns empty; second: currency returns None
        empty_result = MagicMock()
        empty_result.fetchall.return_value = []
        currency_result = MagicMock()
        currency_result.fetchone.return_value = None
        mock_db.execute.side_effect = [empty_result, currency_result]

        service = AdPerformanceService(mock_db)
        result = service.get_top_ads(tenant_id, "meta-ads", "30d")

        assert result.total_ads == 0
        assert result.ads == []
        assert result.currency is None


class TestAdFormatDetection:
    """Tests for format_type detection from ads table creative metadata."""

    def test_video_format_detected_from_creative_video_id(self):
        """Ad with creative_video_id in ads table -> format_type = 'video'."""
        tenant_id = uuid4()
        mock_db = MagicMock()

        metric_rows = [
            _make_metric_row("ad_video", "spend", 150.0, "Video Ad"),
            _make_metric_row("ad_video", "impressions", 5000.0, "Video Ad"),
        ]
        ad_creative_rows = [
            _make_ad_creative_row(
                "ad_video",
                creative_video_id="vid_abc123",
                creative_thumbnail_url="https://thumb.example.com/vid.jpg",
            ),
        ]
        _setup_query_mocks(mock_db, metric_rows, ad_creative_rows)

        service = AdPerformanceService(mock_db)
        result = service.get_top_ads(tenant_id, "meta-ads", "30d")

        assert len(result.ads) == 1
        assert result.ads[0].format_type == "video"
        assert result.ads[0].thumbnail_url == "https://thumb.example.com/vid.jpg"

    def test_image_format_detected_from_creative_image_url(self):
        """Ad with creative_image_url but no video_id -> format_type = 'image'."""
        tenant_id = uuid4()
        mock_db = MagicMock()

        metric_rows = [
            _make_metric_row("ad_img", "spend", 80.0, "Image Ad"),
            _make_metric_row("ad_img", "impressions", 3000.0, "Image Ad"),
        ]
        ad_creative_rows = [
            _make_ad_creative_row(
                "ad_img",
                creative_image_url="https://img.example.com/ad.jpg",
                creative_thumbnail_url="https://thumb.example.com/ad.jpg",
            ),
        ]
        _setup_query_mocks(mock_db, metric_rows, ad_creative_rows)

        service = AdPerformanceService(mock_db)
        result = service.get_top_ads(tenant_id, "meta-ads", "30d")

        assert len(result.ads) == 1
        assert result.ads[0].format_type == "image"
        # Prefers creative_image_url (full res) over thumbnail_url
        assert result.ads[0].thumbnail_url == "https://img.example.com/ad.jpg"

    def test_fallback_to_image_when_no_creative_metadata(self):
        """Ad not found in ads table -> format_type defaults to 'image'."""
        tenant_id = uuid4()
        mock_db = MagicMock()

        metric_rows = [
            _make_metric_row("ad_unknown", "spend", 50.0, "Unknown Ad"),
        ]
        ad_creative_rows = []  # No matching ads in the ads table
        _setup_query_mocks(mock_db, metric_rows, ad_creative_rows)

        service = AdPerformanceService(mock_db)
        result = service.get_top_ads(tenant_id, "meta-ads", "30d")

        assert len(result.ads) == 1
        assert result.ads[0].format_type == "image"

    def test_mixed_formats_correctly_detected(self):
        """Multiple ads with different formats are all correctly classified."""
        tenant_id = uuid4()
        mock_db = MagicMock()

        metric_rows = [
            _make_metric_row("ad_video", "spend", 200.0, "Video Ad"),
            _make_metric_row("ad_image", "spend", 100.0, "Image Ad"),
            _make_metric_row("ad_no_data", "spend", 50.0, "No Creative Data"),
        ]
        ad_creative_rows = [
            _make_ad_creative_row("ad_video", creative_video_id="vid_001"),
            _make_ad_creative_row(
                "ad_image",
                creative_image_url="https://img.example.com/ad.jpg",
            ),
            # ad_no_data not in ads table — will fallback to "image"
        ]
        _setup_query_mocks(mock_db, metric_rows, ad_creative_rows)

        service = AdPerformanceService(mock_db)
        result = service.get_top_ads(tenant_id, "meta-ads", "30d")

        formats = {ad.ad_id: ad.format_type for ad in result.ads}
        assert formats["ad_video"] == "video"
        assert formats["ad_image"] == "image"
        assert formats["ad_no_data"] == "image"

    def test_video_id_takes_priority_over_image_url(self):
        """When both video_id and image_url exist, video takes priority."""
        tenant_id = uuid4()
        mock_db = MagicMock()

        metric_rows = [
            _make_metric_row("ad_both", "spend", 100.0, "Both Video+Image"),
        ]
        ad_creative_rows = [
            _make_ad_creative_row(
                "ad_both",
                creative_video_id="vid_priority",
                creative_image_url="https://img.example.com/also.jpg",
                creative_thumbnail_url="https://thumb.example.com/vid.jpg",
            ),
        ]
        _setup_query_mocks(mock_db, metric_rows, ad_creative_rows)

        service = AdPerformanceService(mock_db)
        result = service.get_top_ads(tenant_id, "meta-ads", "30d")

        assert result.ads[0].format_type == "video"


class TestFormatComparisonGrouping:
    """Tests for format_comparison grouping by real format types."""

    def test_format_comparison_groups_by_real_format(self):
        """Format comparison should group ads by their detected format type."""
        tenant_id = uuid4()
        mock_db = MagicMock()

        metric_rows = [
            _make_metric_row("ad_v1", "spend", 100.0, "Video 1"),
            _make_metric_row("ad_v1", "ctr", 3.0, "Video 1"),
            _make_metric_row("ad_v1", "roas", 4.0, "Video 1"),
            _make_metric_row("ad_v2", "spend", 200.0, "Video 2"),
            _make_metric_row("ad_v2", "ctr", 2.5, "Video 2"),
            _make_metric_row("ad_v2", "roas", 3.0, "Video 2"),
            _make_metric_row("ad_i1", "spend", 80.0, "Image 1"),
            _make_metric_row("ad_i1", "ctr", 1.5, "Image 1"),
            _make_metric_row("ad_i1", "roas", 2.0, "Image 1"),
        ]
        ad_creative_rows = [
            _make_ad_creative_row("ad_v1", creative_video_id="vid_1"),
            _make_ad_creative_row("ad_v2", creative_video_id="vid_2"),
            _make_ad_creative_row(
                "ad_i1",
                creative_image_url="https://img.example.com/1.jpg",
            ),
        ]

        # get_format_comparison calls get_top_ads internally (limit=500),
        # so mock needs to return data for that call
        _setup_query_mocks(mock_db, metric_rows, ad_creative_rows)

        service = AdPerformanceService(mock_db)
        result = service.get_format_comparison(tenant_id, "meta-ads", "30d")

        format_names = {f.format_type for f in result.formats}
        assert "video" in format_names
        assert "image" in format_names
        # "unknown" should NOT appear since we now detect formats
        assert "unknown" not in format_names

        video_fmt = next(f for f in result.formats if f.format_type == "video")
        assert video_fmt.ad_count == 2
        assert video_fmt.total_spend == 300.0  # 100 + 200

        image_fmt = next(f for f in result.formats if f.format_type == "image")
        assert image_fmt.ad_count == 1
        assert image_fmt.total_spend == 80.0
