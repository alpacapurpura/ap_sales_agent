"""Tests for ad-level metric extraction in MetaProvider."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.analytics.infrastructure.providers.meta_provider import MetaProvider


def _ok_response(data: list) -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"data": data}
    return resp


def _ad_insight_row(
    ad_id: str,
    ad_name: str,
    spend: str = "50.00",
    campaign_id: str | None = None,
    date_start: str | None = None,
) -> dict:
    row = {
        "ad_id": ad_id,
        "ad_name": ad_name,
        "impressions": "1000",
        "clicks": "50",
        "spend": spend,
        "ctr": "5.0",
        "cpc": "1.00",
        "reach": "800",
        "frequency": "1.25",
        "actions": [
            {"action_type": "purchase", "value": "5"},
            {"action_type": "link_click", "value": "45"},
        ],
        "cost_per_action_type": [
            {"action_type": "purchase", "value": "10.00"},
        ],
        "purchase_roas": [{"action_type": "omni_purchase", "value": "3.5"}],
    }
    if campaign_id is not None:
        row["campaign_id"] = campaign_id
    if date_start is not None:
        row["date_start"] = date_start
    return row


class TestExtractMetaAdsByAd:
    """Test _extract_meta_ads_by_ad method."""

    @pytest.mark.asyncio
    async def test_extracts_metrics_with_ad_id(self):
        provider = MetaProvider()
        credentials = {
            "access_token": "tok_test",
            "ad_account_id": "123456",
            "currency": "USD",
        }
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            return_value=_ok_response(
                [
                    _ad_insight_row("ad_001", "Video Testimonio"),
                    _ad_insight_row("ad_002", "Carrusel Beneficios"),
                ],
            ),
        )

        metrics = await provider._extract_meta_ads_by_ad(
            mock_client,
            credentials,
            date(2026, 3, 1),
            date(2026, 3, 31),
        )

        # Should have metrics for both ads
        ad_ids = {m.ad_id for m in metrics if m.ad_id}
        assert "ad_001" in ad_ids
        assert "ad_002" in ad_ids

        # Each ad should have spend metric
        spend_metrics = [m for m in metrics if m.metric_name == "spend"]
        assert len(spend_metrics) >= 2

        # All metrics should have ad_id set
        for m in metrics:
            assert m.ad_id is not None

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_ad_account(self):
        provider = MetaProvider()
        credentials = {"access_token": "tok_test", "currency": "USD"}
        mock_client = AsyncMock()

        metrics = await provider._extract_meta_ads_by_ad(
            mock_client,
            credentials,
            date(2026, 3, 1),
            date(2026, 3, 31),
        )
        assert metrics == []

    @pytest.mark.asyncio
    async def test_api_called_with_level_ad(self):
        provider = MetaProvider()
        credentials = {
            "access_token": "tok_test",
            "ad_account_id": "123456",
            "currency": "USD",
        }
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=_ok_response([]))

        await provider._extract_meta_ads_by_ad(
            mock_client,
            credentials,
            date(2026, 3, 1),
            date(2026, 3, 31),
        )

        call_args = mock_client.get.call_args
        params = call_args.kwargs.get("params") or call_args[1].get("params")
        assert params["level"] == "ad"
        assert "ad_id" in params["fields"]
        assert "ad_name" in params["fields"]

    @pytest.mark.asyncio
    async def test_campaign_id_is_requested_and_stored(self):
        """Regression: ad-level rows must carry campaign_id to avoid being
        mistaken for account-level rows at query time (bug #1).
        """
        provider = MetaProvider()
        credentials = {
            "access_token": "tok_test",
            "ad_account_id": "123456",
            "currency": "USD",
        }
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            return_value=_ok_response(
                [
                    _ad_insight_row(
                        "ad_001",
                        "Video Testimonio",
                        campaign_id="camp_777",
                    ),
                ],
            ),
        )

        metrics = await provider._extract_meta_ads_by_ad(
            mock_client,
            credentials,
            date(2026, 3, 1),
            date(2026, 3, 31),
        )

        # All returned metrics must carry both ad_id and campaign_id
        assert len(metrics) > 0
        for m in metrics:
            assert m.ad_id == "ad_001"
            assert m.campaign_id == "camp_777"

        # API params must request campaign_id
        call_args = mock_client.get.call_args
        params = call_args.kwargs.get("params") or call_args[1].get("params")
        assert "campaign_id" in params["fields"]


class TestParseAdsRowDate:
    """Regression tests for _parse_ads_row date handling (bug #3)."""

    def test_uses_date_start_from_row_when_present(self):
        """If the row has date_start, it must override the metric_date param.

        Backfills over multi-day ranges were concentrating totals on the last
        day because callers were passing end_date blindly.
        """
        row = {
            "spend": "123.45",
            "impressions": "1000",
            "date_start": "2026-03-15",
        }

        metrics = MetaProvider._parse_ads_row(
            row,
            currency="USD",
            metric_date=date(2026, 4, 8),
        )

        assert len(metrics) > 0
        for m in metrics:
            assert m.date == date(2026, 3, 15)

    def test_falls_back_to_metric_date_when_no_date_start(self):
        """If row has no date_start, use the provided metric_date."""
        row = {
            "spend": "10.00",
            "impressions": "500",
        }

        metrics = MetaProvider._parse_ads_row(
            row,
            currency="USD",
            metric_date=date(2026, 4, 8),
        )

        assert len(metrics) > 0
        for m in metrics:
            assert m.date == date(2026, 4, 8)

    def test_falls_back_on_invalid_date_start(self):
        """Malformed date_start should fall back to metric_date, not crash."""
        row = {
            "spend": "10.00",
            "date_start": "not-a-date",
        }

        metrics = MetaProvider._parse_ads_row(
            row,
            currency="USD",
            metric_date=date(2026, 4, 8),
        )

        assert len(metrics) > 0
        for m in metrics:
            assert m.date == date(2026, 4, 8)
