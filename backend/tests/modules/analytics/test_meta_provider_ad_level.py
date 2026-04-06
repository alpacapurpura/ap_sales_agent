"""Tests for ad-level metric extraction in MetaProvider."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.analytics.infrastructure.providers.meta_provider import MetaProvider


def _ok_response(data: list) -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"data": data}
    return resp


def _ad_insight_row(ad_id: str, ad_name: str, spend: str = "50.00") -> dict:
    return {
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
            return_value=_ok_response([
                _ad_insight_row("ad_001", "Video Testimonio"),
                _ad_insight_row("ad_002", "Carrusel Beneficios"),
            ])
        )

        metrics = await provider._extract_meta_ads_by_ad(
            mock_client, credentials, date(2026, 3, 1), date(2026, 3, 31)
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
            mock_client, credentials, date(2026, 3, 1), date(2026, 3, 31)
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
            mock_client, credentials, date(2026, 3, 1), date(2026, 3, 31)
        )

        call_args = mock_client.get.call_args
        params = call_args.kwargs.get("params") or call_args[1].get("params")
        assert params["level"] == "ad"
        assert "ad_id" in params["fields"]
        assert "ad_name" in params["fields"]
