"""Tests for granularity filtering in OfficialMetricsRepository.

Bug context: `get_channel_daily_metrics` and `get_channel_metrics_for_period`
were doing `SUM(value)` across all rows without filtering by granularity
(campaign_id/ad_set_id/ad_id). When account-level + campaign-level + ad-level
rows coexisted for the same day, the totals were inflated 2x or 3x.

Fix: filter to account-level rows only (all dim IDs NULL) to prevent
double-counting. Campaign-level / ad-level data is accessed via
`get_channel_raw_daily_rows` + `MetricResolver` when needed.
"""

import uuid
from datetime import date
from uuid import UUID

import pytest

from src.modules.analytics.infrastructure.models.official_metrics_model import (
    OfficialMetricModel,
)
from src.modules.analytics.infrastructure.repositories.official_metrics_repository import (
    OfficialMetricsRepository,
)


@pytest.fixture
def tenant_id() -> UUID:
    return uuid.UUID("6347e21e-8112-4aa1-80d3-6adaa73bf6f9")


def _insert_metric(
    db,
    *,
    tenant_id: UUID,
    metric_date: date,
    value: float,
    metric_name: str = "spend",
    channel_slug: str = "meta-ads",
    provider: str = "meta",
    unit: str = "currency",
    campaign_id: str | None = None,
    ad_set_id: str | None = None,
    ad_id: str | None = None,
) -> None:
    row = OfficialMetricModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        provider=provider,
        channel_slug=channel_slug,
        metric_name=metric_name,
        value=value,
        unit=unit,
        currency="USD" if unit == "currency" else None,
        metric_date=metric_date,
        campaign_id=campaign_id,
        ad_set_id=ad_set_id,
        ad_id=ad_id,
    )
    db.add(row)
    db.flush()


class TestGetChannelDailyMetrics:
    """Tests for get_channel_daily_metrics granularity handling."""

    def test_case_a_account_plus_campaign_plus_ad_uses_account_only(
        self,
        db,
        tenant_id,
    ):
        """When account, campaign and ad rows coexist: use only account ($100)."""
        day = date(2026, 4, 8)

        # Account-level row ($100)
        _insert_metric(db, tenant_id=tenant_id, metric_date=day, value=100.0)

        # Campaign-level rows summing $100
        _insert_metric(
            db,
            tenant_id=tenant_id,
            metric_date=day,
            value=60.0,
            campaign_id="camp_1",
        )
        _insert_metric(
            db,
            tenant_id=tenant_id,
            metric_date=day,
            value=40.0,
            campaign_id="camp_2",
        )

        # Ad-level rows summing $100
        _insert_metric(
            db,
            tenant_id=tenant_id,
            metric_date=day,
            value=30.0,
            campaign_id="camp_1",
            ad_id="ad_a",
        )
        _insert_metric(
            db,
            tenant_id=tenant_id,
            metric_date=day,
            value=30.0,
            campaign_id="camp_1",
            ad_id="ad_b",
        )
        _insert_metric(
            db,
            tenant_id=tenant_id,
            metric_date=day,
            value=40.0,
            campaign_id="camp_2",
            ad_id="ad_c",
        )

        repo = OfficialMetricsRepository(db)
        result = repo.get_channel_daily_metrics(
            tenant_id=tenant_id,
            channel_slug="meta-ads",
            metric_names=["spend"],
            start_date=day,
            end_date=day,
        )

        assert result == [(day, "spend", 100.0)]

    def test_case_b_only_campaign_level_returns_empty(self, db, tenant_id):
        """When only campaign-level rows exist (no account-level), return empty.

        Account-level only filtering means campaign-level rows are invisible
        to these methods. The dashboard uses get_channel_raw_daily_rows +
        MetricResolver for full data access.
        """
        day = date(2026, 4, 1)

        _insert_metric(
            db,
            tenant_id=tenant_id,
            metric_date=day,
            value=30.0,
            campaign_id="camp_1",
        )
        _insert_metric(
            db,
            tenant_id=tenant_id,
            metric_date=day,
            value=20.0,
            campaign_id="camp_2",
        )

        repo = OfficialMetricsRepository(db)
        result = repo.get_channel_daily_metrics(
            tenant_id=tenant_id,
            channel_slug="meta-ads",
            metric_names=["spend"],
            start_date=day,
            end_date=day,
        )

        assert result == []

    def test_case_c_mixed_days_only_returns_account_level(self, db, tenant_id):
        """Day 1 has account-level; day 2 has only campaign-level.
        Only day 1 is returned since filtering is account-level only.
        """
        day1 = date(2026, 4, 5)
        day2 = date(2026, 4, 6)

        # Day 1: account + campaigns — should use account
        _insert_metric(db, tenant_id=tenant_id, metric_date=day1, value=70.0)
        _insert_metric(
            db,
            tenant_id=tenant_id,
            metric_date=day1,
            value=50.0,
            campaign_id="camp_1",
        )
        _insert_metric(
            db,
            tenant_id=tenant_id,
            metric_date=day1,
            value=20.0,
            campaign_id="camp_2",
        )

        # Day 2: only campaigns — not returned (account-level only)
        _insert_metric(
            db,
            tenant_id=tenant_id,
            metric_date=day2,
            value=15.0,
            campaign_id="camp_1",
        )
        _insert_metric(
            db,
            tenant_id=tenant_id,
            metric_date=day2,
            value=10.0,
            campaign_id="camp_2",
        )

        repo = OfficialMetricsRepository(db)
        result = repo.get_channel_daily_metrics(
            tenant_id=tenant_id,
            channel_slug="meta-ads",
            metric_names=["spend"],
            start_date=day1,
            end_date=day2,
        )

        result_dict = {(r[0], r[1]): r[2] for r in result}
        assert result_dict[(day1, "spend")] == 70.0
        assert (day2, "spend") not in result_dict

    def test_case_e_ad_set_only_rows_not_counted_as_account_level(self, db, tenant_id):
        """Rows with ad_set_id set (but ad_id NULL) are NOT account-level."""
        day = date(2026, 4, 7)

        # Ad-set level (should NOT be treated as account-level)
        _insert_metric(
            db,
            tenant_id=tenant_id,
            metric_date=day,
            value=999.0,
            campaign_id="camp_1",
            ad_set_id="adset_1",
        )

        # Actual account-level
        _insert_metric(db, tenant_id=tenant_id, metric_date=day, value=42.0)

        repo = OfficialMetricsRepository(db)
        result = repo.get_channel_daily_metrics(
            tenant_id=tenant_id,
            channel_slug="meta-ads",
            metric_names=["spend"],
            start_date=day,
            end_date=day,
        )

        assert result == [(day, "spend", 42.0)]

    def test_filters_by_tenant_and_channel(self, db, tenant_id):
        """Other tenants / channels must not leak."""
        day = date(2026, 4, 8)
        other_tenant = uuid.uuid4()

        _insert_metric(db, tenant_id=tenant_id, metric_date=day, value=100.0)
        _insert_metric(db, tenant_id=other_tenant, metric_date=day, value=500.0)
        _insert_metric(
            db,
            tenant_id=tenant_id,
            metric_date=day,
            value=999.0,
            channel_slug="google-ads",
        )

        repo = OfficialMetricsRepository(db)
        result = repo.get_channel_daily_metrics(
            tenant_id=tenant_id,
            channel_slug="meta-ads",
            metric_names=["spend"],
            start_date=day,
            end_date=day,
        )

        assert result == [(day, "spend", 100.0)]


class TestGetChannelMetricsForPeriod:
    """Tests for get_channel_metrics_for_period granularity handling."""

    def test_case_d_period_uses_account_level_only(self, db, tenant_id):
        """Aggregate period: only account-level rows are summed.
        Days with only campaign-level data are excluded.
        """
        day1 = date(2026, 4, 5)  # account-level exists ($70)
        day2 = date(2026, 4, 6)  # only campaign-level (excluded)
        day3 = date(2026, 4, 7)  # both — account wins ($100)

        # Day 1
        _insert_metric(db, tenant_id=tenant_id, metric_date=day1, value=70.0)
        _insert_metric(
            db,
            tenant_id=tenant_id,
            metric_date=day1,
            value=60.0,
            campaign_id="c1",
        )

        # Day 2 (campaign-only — excluded from account-level filter)
        _insert_metric(
            db,
            tenant_id=tenant_id,
            metric_date=day2,
            value=15.0,
            campaign_id="c1",
        )
        _insert_metric(
            db,
            tenant_id=tenant_id,
            metric_date=day2,
            value=10.0,
            campaign_id="c2",
        )

        # Day 3 — account + campaigns + ads (3x bug scenario)
        _insert_metric(db, tenant_id=tenant_id, metric_date=day3, value=100.0)
        _insert_metric(
            db,
            tenant_id=tenant_id,
            metric_date=day3,
            value=100.0,
            campaign_id="c1",
        )
        _insert_metric(
            db,
            tenant_id=tenant_id,
            metric_date=day3,
            value=100.0,
            campaign_id="c1",
            ad_id="ad_x",
        )

        repo = OfficialMetricsRepository(db)
        totals = repo.get_channel_metrics_for_period(
            tenant_id=tenant_id,
            channel_slug="meta-ads",
            start_date=day1,
            end_date=day3,
        )

        # 70 (account day1) + 100 (account day3) = 170
        # Day 2 has no account-level rows, so excluded
        assert totals["spend"] == 170.0

    def test_period_ignores_ad_and_adset_rows(self, db, tenant_id):
        """Only account-level or campaign-level rows should participate."""
        day = date(2026, 4, 8)

        # Account-level
        _insert_metric(db, tenant_id=tenant_id, metric_date=day, value=80.0)

        # Ad-level noise
        _insert_metric(
            db,
            tenant_id=tenant_id,
            metric_date=day,
            value=9999.0,
            campaign_id="c1",
            ad_id="ad_1",
        )
        # Ad-set level noise
        _insert_metric(
            db,
            tenant_id=tenant_id,
            metric_date=day,
            value=9999.0,
            campaign_id="c1",
            ad_set_id="adset_1",
        )

        repo = OfficialMetricsRepository(db)
        totals = repo.get_channel_metrics_for_period(
            tenant_id=tenant_id,
            channel_slug="meta-ads",
            start_date=day,
            end_date=day,
        )

        assert totals["spend"] == 80.0
