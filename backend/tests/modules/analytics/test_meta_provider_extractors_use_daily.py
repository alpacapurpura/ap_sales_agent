"""Architectural invariants for the Meta ads extraction pipeline.

Guarantee that ``MetaProvider.extract_metrics()`` (the cron entry point)
ALWAYS asks Meta for daily buckets for account / campaign / ad level
insights. Without ``time_increment=1``, Meta returns a single aggregated
row for the whole period and the parser used to stamp it to ``end_date``,
polluting the per-day metrics table (Visionarias contamination bug).
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.modules.analytics.infrastructure.providers.meta_provider import MetaProvider

TENANT_ID = uuid4()
CREDS = {
    "access_token": "tok_test",
    "instagram_account_id": "12345",
    "page_id": "67890",
    "page_access_token": "page_tok",
    "ad_account_id": "111222",
    "currency": "PEN",
}


def _ok_response(json_data: dict) -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


def _daily_row(
    metric_date: date,
    spend: str = "31.07",
    impressions: str = "3468",
    campaign_id: str | None = None,
    ad_id: str | None = None,
) -> dict:
    row: dict = {
        "date_start": metric_date.isoformat(),
        "date_stop": metric_date.isoformat(),
        "reach": "1000",
        "impressions": impressions,
        "clicks": "50",
        "spend": spend,
        "ctr": "1.4",
        "cpm": "9.0",
        "cpc": "0.62",
        "frequency": "2.1",
        "actions": [],
    }
    if campaign_id is not None:
        row["campaign_id"] = campaign_id
        row["campaign_name"] = "Test Campaign"
    if ad_id is not None:
        row["ad_id"] = ad_id
        row["ad_name"] = "Test Ad"
    return row


def _insights_calls_by_level(captured_params: list[dict]) -> dict[str, list[dict]]:
    """Group captured insights calls by ``level`` param."""
    by_level: dict[str, list[dict]] = {"account": [], "campaign": [], "ad": []}
    for p in captured_params:
        level = p.get("level")
        if level in by_level:
            by_level[level].append(p)
    return by_level


class TestExtractMetricsAlwaysUsesDaily:
    """extract_metrics() must always request daily ad data with time_increment=1."""

    @pytest.mark.asyncio
    async def test_account_insights_uses_time_increment(self):
        captured_params: list[dict] = []

        async def mock_get(url, **kwargs):
            captured_params.append(kwargs.get("params", {}))
            return _ok_response({"data": []})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 4, 1),
                date(2026, 4, 8),
            )

        by_level = _insights_calls_by_level(captured_params)
        assert by_level["account"], "Expected at least one account-level insights call"
        for params in by_level["account"]:
            # The breakdowns extractor is intentionally period-aggregated and
            # uses `breakdowns=` instead of `time_increment=1`. Skip it.
            if params.get("breakdowns"):
                continue
            assert params.get("time_increment") == "1", (
                f"Account-level insights must use time_increment=1, got {params}"
            )

    @pytest.mark.asyncio
    async def test_campaign_insights_uses_time_increment(self):
        captured_params: list[dict] = []

        async def mock_get(url, **kwargs):
            captured_params.append(kwargs.get("params", {}))
            return _ok_response({"data": []})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 4, 1),
                date(2026, 4, 8),
            )

        by_level = _insights_calls_by_level(captured_params)
        assert by_level["campaign"], "Expected at least one campaign-level insights call"
        for params in by_level["campaign"]:
            assert params.get("time_increment") == "1", (
                f"Campaign-level insights must use time_increment=1, got {params}"
            )

    @pytest.mark.asyncio
    async def test_ad_insights_uses_time_increment(self):
        captured_params: list[dict] = []

        async def mock_get(url, **kwargs):
            captured_params.append(kwargs.get("params", {}))
            return _ok_response({"data": []})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 4, 1),
                date(2026, 4, 8),
            )

        by_level = _insights_calls_by_level(captured_params)
        assert by_level["ad"], "Expected at least one ad-level insights call"
        for params in by_level["ad"]:
            assert params.get("time_increment") == "1", f"Ad-level insights must use time_increment=1, got {params}"


class TestExtractMetricsPeriodAggregateDoesNotPollute:
    """Defensive: even if Meta answers with a period aggregate, the parser rejects it."""

    @pytest.mark.asyncio
    async def test_multi_day_response_does_not_leak_into_metrics(self):
        """A period-aggregated response must be rejected, not stamped to end_date.

        This is the exact pattern that corrupted Visionarias' data: Meta
        returned ``{"date_start": "2026-03-12", "date_stop": "2026-04-08",
        "spend": "856.61"}`` and the old parser stamped PEN 856.61 to
        2026-04-08 (the end of the period) instead of rejecting it.
        """
        polluted_row = {
            "date_start": "2026-03-12",
            "date_stop": "2026-04-08",
            "spend": "856.61",
            "impressions": "100000",
        }

        async def mock_get(url, **kwargs):
            params = kwargs.get("params", {})
            if "/act_" in url and "/insights" in url:
                level = params.get("level", "")
                if level in ("account", "campaign", "ad"):
                    return _ok_response({"data": [polluted_row]})
            return _ok_response({"data": []})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            result = await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 3, 12),
                date(2026, 4, 8),
            )

        # The spend metric from the polluted row must NOT appear anywhere
        spend_metrics = [m for m in result.metrics if m.metric_name == "spend" and m.channel_slug == "meta-ads"]
        for m in spend_metrics:
            assert m.value != 856.61, f"Period aggregate leaked into per-day metric: {m}"

    @pytest.mark.asyncio
    async def test_daily_response_produces_per_day_metrics(self):
        """With well-formed daily rows, each metric lands on its own day."""
        daily_rows = [
            _daily_row(date(2026, 4, 6), spend="10.00"),
            _daily_row(date(2026, 4, 7), spend="20.00"),
            _daily_row(date(2026, 4, 8), spend="31.07"),
        ]

        async def mock_get(url, **kwargs):
            params = kwargs.get("params", {})
            if "/act_" in url and "/insights" in url:
                level = params.get("level", "")
                if level == "account" and not params.get("breakdowns"):
                    return _ok_response({"data": daily_rows})
            return _ok_response({"data": []})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            result = await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 4, 6),
                date(2026, 4, 8),
            )

        account_spend = [
            m
            for m in result.metrics
            if m.metric_name == "spend" and m.channel_slug == "meta-ads" and m.campaign_id is None and m.ad_id is None
        ]
        assert len(account_spend) == 3
        by_date = {m.date: m.value for m in account_spend}
        assert by_date[date(2026, 4, 6)] == 10.00
        assert by_date[date(2026, 4, 7)] == 20.00
        assert by_date[date(2026, 4, 8)] == 31.07
