"""Architectural invariants for Meta provider.

Guarantees that period-aggregated Insights rows can NEVER pollute the
per-day metrics table. The extract_metrics() pipeline must always
request data with time_increment=1 for ads-level endpoints, and the
row parser must refuse multi-day rows outright.

Background: the Visionarias tenant's Meta Ads metrics were contaminated
(one day showed PEN 856.61 instead of PEN 31.07) because the
account/campaign/ad extractors did not pass time_increment=1, causing
Meta to return a single aggregate row that got stamped to end_date.
"""

from datetime import date

import pytest

from luana_core_analytics_engine.infrastructure.providers.meta_provider import (
    MetaProvider,
    PeriodAggregateError,
)


class TestParseAdsRowInvariants:
    """_parse_ads_row must reject any row that aggregates more than one day."""

    def test_rejects_period_row_with_date_range(self):
        """A row with date_start != date_stop is a period aggregate → reject."""
        data = {
            "date_start": "2026-03-12",
            "date_stop": "2026-04-08",
            "spend": "856.61",
            "impressions": "100000",
        }
        with pytest.raises(PeriodAggregateError) as exc_info:
            MetaProvider._parse_ads_row(data, "PEN", date(2026, 4, 8))
        assert "2026-03-12" in str(exc_info.value)
        assert "2026-04-08" in str(exc_info.value)

    def test_accepts_single_day_row(self):
        """A row with date_start == date_stop is a valid daily bucket."""
        data = {
            "date_start": "2026-04-08",
            "date_stop": "2026-04-08",
            "spend": "31.07",
            "impressions": "3468",
        }
        metrics = MetaProvider._parse_ads_row(data, "PEN", date(2026, 4, 8))

        for m in metrics:
            assert m.date == date(2026, 4, 8)

        spend_metrics = [m for m in metrics if m.metric_name == "spend"]
        assert len(spend_metrics) == 1
        assert spend_metrics[0].value == 31.07

    def test_accepts_row_without_date_metadata_using_fallback(self):
        """No date_start/date_stop → caller-provided fallback is used."""
        data = {"spend": "30.0", "impressions": "1000"}
        metrics = MetaProvider._parse_ads_row(data, "PEN", date(2026, 4, 8))

        spend_metrics = [m for m in metrics if m.metric_name == "spend"]
        assert len(spend_metrics) == 1
        assert spend_metrics[0].date == date(2026, 4, 8)
        assert spend_metrics[0].value == 30.0

    def test_accepts_row_with_only_date_start(self):
        """Row declares date_start but no date_stop → trust date_start.

        This can happen when the row was filtered from a daily response upstream;
        without a date_stop we cannot detect a range, so we honour date_start.
        """
        data = {
            "date_start": "2026-03-15",
            "spend": "30.0",
        }
        metrics = MetaProvider._parse_ads_row(data, "PEN", date(2026, 4, 8))

        spend_metrics = [m for m in metrics if m.metric_name == "spend"]
        assert len(spend_metrics) == 1
        assert spend_metrics[0].date == date(2026, 3, 15)

    def test_period_error_message_mentions_time_increment(self):
        """The error message must point developers at the correct fix."""
        data = {
            "date_start": "2026-01-01",
            "date_stop": "2026-01-31",
            "spend": "1000.0",
        }
        with pytest.raises(PeriodAggregateError) as exc_info:
            MetaProvider._parse_ads_row(data, "USD", date(2026, 1, 31))
        assert "time_increment" in str(exc_info.value)
