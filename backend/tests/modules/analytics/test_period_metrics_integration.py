"""Tests for period_metrics fallback in ChannelDashboardService.

Validates that NON_AGGREGABLE metrics (reach, frequency) use period_metrics
when available, falling back to the latest daily value from official_metrics.
"""

from collections import defaultdict
from datetime import date
from unittest.mock import MagicMock
from uuid import UUID

import pytest

from luana_core_analytics_engine.application.services.channel_dashboard_service import (
    ChannelDashboardService,
)
from luana_core_analytics_engine.domain.enums import AggregationType
from luana_core_analytics_engine.domain.metric_catalog import get_metric_def

_TENANT_ID = UUID("11111111-1111-1111-1111-111111111111")
_CHANNEL = "meta-ads"


@pytest.fixture
def mock_db():
    """Minimal mock DB session."""
    return MagicMock()


@pytest.fixture
def mock_brand_port():
    """BrandReadPort returning a generic industry."""
    port = MagicMock()
    port.get_industry = _make_coroutine_fn("general")
    return port


def _make_coroutine_fn(return_value):
    """Create a callable that returns a coroutine (for async mocks)."""

    async def _coro(*args, **kwargs):
        return return_value

    return _coro


def _aggregate_metrics(
    metrics_by_date: dict[date, dict[str, float]],
) -> dict[str, float]:
    """Simulate get_channel_metrics_for_period aggregation.

    ADDITIVE metrics: SUM across dates.
    NON_AGGREGABLE/other: latest date's value.
    """
    grouped: dict[str, list[tuple[date, float]]] = defaultdict(list)
    for d, metrics in metrics_by_date.items():
        for metric_name, value in metrics.items():
            grouped[metric_name].append((d, value))

    result: dict[str, float] = {}
    for metric_name, entries in grouped.items():
        defn = get_metric_def(metric_name)
        if defn is None or defn.aggregation == AggregationType.ADDITIVE:
            result[metric_name] = sum(v for _, v in entries)
        else:
            latest = max(entries, key=lambda x: x[0])
            result[metric_name] = latest[1]

    return result


def _make_raw_daily_rows(
    metrics_by_date: dict[date, dict[str, float]],
) -> list[tuple[date, str, float, str | None, str | None, str | None]]:
    """Simulate get_channel_raw_daily_rows output.

    Returns (date, metric_name, value, campaign_id, ad_set_id, ad_id) tuples
    with all dimension IDs set to None (account-level).
    """
    rows = []
    for d, metrics in sorted(metrics_by_date.items()):
        for metric_name, value in metrics.items():
            rows.append((d, metric_name, value, None, None, None))
    return rows


def _make_service_with_mocks(
    mock_db,
    mock_brand_port,
    current_metrics_by_date: dict[date, dict[str, float]],
    previous_metrics_by_date: dict[date, dict[str, float]],
    period_metric_fn,
):
    """Create a ChannelDashboardService with mocked repos.

    Mocks:
    - repo.get_channel_raw_daily_rows (called 3 times: current, previous, daily)
    - repo.db.execute (for currency detection query)
    - period_repo.get_best_period_metric (called for period overrides)
    """
    service = ChannelDashboardService(mock_db, brand_port=mock_brand_port)

    current_raw = _make_raw_daily_rows(current_metrics_by_date)
    previous_raw = _make_raw_daily_rows(previous_metrics_by_date)
    daily_raw = _make_raw_daily_rows(current_metrics_by_date)

    # Mock get_channel_raw_daily_rows (called 3 times via asyncio.to_thread)
    service.repo.get_channel_raw_daily_rows = MagicMock(
        side_effect=[current_raw, previous_raw, daily_raw],
    )

    # Mock currency detection query
    service.repo.db = MagicMock()
    service.repo.db.execute.return_value.fetchone.return_value = None

    # Mock period_metrics repo
    service.period_repo.get_best_period_metric = MagicMock(side_effect=period_metric_fn)

    return service


class TestPeriodMetricsFallback:
    """Test that reach/frequency use period_metrics when available."""

    @pytest.mark.asyncio
    async def test_reach_from_period_metrics_when_available(
        self,
        mock_db,
        mock_brand_port,
    ):
        """If period_metrics has reach for the period, use it instead of daily."""
        current = {
            date(2026, 3, 10): {
                "spend": 200.0,
                "impressions": 5000.0,
                "clicks": 100.0,
                "reach": 1200.0,
                "conversions": 3.0,
            },
            date(2026, 3, 11): {
                "spend": 150.0,
                "impressions": 5000.0,
                "clicks": 100.0,
                "reach": 1100.0,
                "conversions": 3.0,
            },
            date(2026, 3, 12): {
                "spend": 150.0,
                "impressions": 5000.0,
                "clicks": 100.0,
                "reach": 1000.0,
                "conversions": 4.0,
            },
        }
        previous = {
            date(2026, 2, 10): {
                "spend": 400.0,
                "impressions": 12000.0,
                "clicks": 250.0,
                "reach": 900.0,
                "conversions": 8.0,
            },
        }

        def period_fn(tenant_id, channel_slug, metric_name, start_date, end_date):
            if metric_name == "reach":
                return 5000.0
            return None

        service = _make_service_with_mocks(
            mock_db,
            mock_brand_port,
            current,
            previous,
            period_fn,
        )
        result = await service.get_dashboard(_TENANT_ID, _CHANNEL, "30d")

        # frequency = SUM(impressions) / period_reach = 15000 / 5000 = 3.0
        # 3.0 >= FREQUENCY_FATIGUE_THRESHOLD (3.0) -> warning
        assert result.frequency_alert is not None
        assert result.frequency_alert.current_value == 3.0
        assert result.frequency_alert.severity == "warning"

    @pytest.mark.asyncio
    async def test_reach_falls_back_to_latest_daily(self, mock_db, mock_brand_port):
        """If no period_metrics, use latest daily value from official_metrics."""
        current = {
            date(2026, 3, 10): {
                "spend": 500.0,
                "impressions": 15000.0,
                "clicks": 300.0,
                "reach": 1200.0,
                "conversions": 10.0,
            },
        }
        previous = {
            date(2026, 2, 10): {
                "spend": 400.0,
                "impressions": 12000.0,
                "clicks": 250.0,
                "reach": 900.0,
                "conversions": 8.0,
            },
        }

        def period_fn(tenant_id, channel_slug, metric_name, start_date, end_date):
            return None

        service = _make_service_with_mocks(
            mock_db,
            mock_brand_port,
            current,
            previous,
            period_fn,
        )
        result = await service.get_dashboard(_TENANT_ID, _CHANNEL, "30d")

        # reach stays 1200 from daily (NON_AGGREGABLE -> latest value)
        # frequency = 15000 / 1200 = 12.5
        assert result.frequency_alert is not None
        assert result.frequency_alert.current_value == 12.5
        assert result.frequency_alert.severity == "critical"

    @pytest.mark.asyncio
    async def test_frequency_derived_from_impressions_and_period_reach(
        self,
        mock_db,
        mock_brand_port,
    ):
        """frequency = SUM(impressions) / period_reach when period data exists."""
        current = {
            date(2026, 3, 10): {
                "spend": 250.0,
                "impressions": 7500.0,
                "clicks": 150.0,
                "reach": 600.0,
                "conversions": 5.0,
            },
            date(2026, 3, 11): {
                "spend": 250.0,
                "impressions": 7500.0,
                "clicks": 150.0,
                "reach": 600.0,
                "conversions": 5.0,
            },
        }
        previous = {
            date(2026, 2, 10): {
                "spend": 400.0,
                "impressions": 12000.0,
                "clicks": 250.0,
                "reach": 900.0,
                "conversions": 8.0,
            },
        }

        def period_fn(tenant_id, channel_slug, metric_name, start_date, end_date):
            if metric_name == "reach":
                return 5000.0
            return None

        service = _make_service_with_mocks(
            mock_db,
            mock_brand_port,
            current,
            previous,
            period_fn,
        )
        result = await service.get_dashboard(_TENANT_ID, _CHANNEL, "30d")

        # frequency = SUM(impressions) / period_reach = 15000 / 5000 = 3.0
        assert result.frequency_alert is not None
        assert result.frequency_alert.current_value == 3.0

    @pytest.mark.asyncio
    async def test_period_override_does_not_affect_additive_metrics(
        self,
        mock_db,
        mock_brand_port,
    ):
        """Additive metrics like spend are NOT overridden by period_metrics."""
        current = {
            date(2026, 3, 10): {
                "spend": 500.0,
                "impressions": 15000.0,
                "clicks": 300.0,
                "reach": 1200.0,
                "conversions": 10.0,
            },
        }
        previous = {
            date(2026, 2, 10): {"spend": 400.0},
        }

        def period_fn(tenant_id, channel_slug, metric_name, start_date, end_date):
            if metric_name == "reach":
                return 5000.0
            return None

        service = _make_service_with_mocks(
            mock_db,
            mock_brand_port,
            current,
            previous,
            period_fn,
        )
        result = await service.get_dashboard(_TENANT_ID, _CHANNEL, "30d")

        spend_kpi = next((k for k in result.kpis if k.metric_name == "spend"), None)
        assert spend_kpi is not None
        assert spend_kpi.current_value == 500.0

    @pytest.mark.asyncio
    async def test_period_repo_called_with_correct_args(self, mock_db, mock_brand_port):
        """Verify period_repo receives correct tenant, channel, and metric args."""
        current = {
            date(2026, 3, 10): {
                "spend": 500.0,
                "impressions": 15000.0,
                "reach": 1200.0,
            },
        }
        previous = {
            date(2026, 2, 10): {
                "spend": 400.0,
                "impressions": 12000.0,
                "reach": 900.0,
            },
        }

        calls: list[tuple] = []

        def period_fn(tenant_id, channel_slug, metric_name, start_date, end_date):
            calls.append(
                (str(tenant_id), channel_slug, metric_name, start_date, end_date),
            )

        service = _make_service_with_mocks(
            mock_db,
            mock_brand_port,
            current,
            previous,
            period_fn,
        )
        await service.get_dashboard(_TENANT_ID, _CHANNEL, "30d")

        # Called for both current and previous periods
        assert len(calls) >= 2
        metric_names = [c[2] for c in calls]
        assert all(m == "reach" for m in metric_names)
        tenant_ids = [c[0] for c in calls]
        assert all(t == str(_TENANT_ID) for t in tenant_ids)
        channel_slugs = [c[1] for c in calls]
        assert all(c == _CHANNEL for c in channel_slugs)


class TestGetBestPeriodMetric:
    """Test the repository method for finding best matching period metric."""

    def test_exact_match_returns_value(self, mock_db):
        """When period_metrics covers the exact date range, return its value."""
        from luana_core_analytics_engine.infrastructure.repositories.period_metrics_repository import (
            PeriodMetricsRepository,
        )

        repo = PeriodMetricsRepository(mock_db)

        mock_row = MagicMock()
        mock_row.value = 5000.0
        mock_result = MagicMock()
        mock_result.first.return_value = mock_row
        mock_db.execute.return_value = mock_result

        result = repo.get_best_period_metric(
            tenant_id=_TENANT_ID,
            channel_slug=_CHANNEL,
            metric_name="reach",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )

        assert result == 5000.0
        mock_db.execute.assert_called_once()

    def test_no_match_returns_none(self, mock_db):
        """When no period_metrics match, return None."""
        from luana_core_analytics_engine.infrastructure.repositories.period_metrics_repository import (
            PeriodMetricsRepository,
        )

        repo = PeriodMetricsRepository(mock_db)

        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_db.execute.return_value = mock_result

        result = repo.get_best_period_metric(
            tenant_id=_TENANT_ID,
            channel_slug=_CHANNEL,
            metric_name="reach",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )

        assert result is None

    def test_filters_by_tenant_id(self, mock_db):
        """Query must always include tenant_id filter."""
        from luana_core_analytics_engine.infrastructure.repositories.period_metrics_repository import (
            PeriodMetricsRepository,
        )

        repo = PeriodMetricsRepository(mock_db)

        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_db.execute.return_value = mock_result

        repo.get_best_period_metric(
            tenant_id=_TENANT_ID,
            channel_slug=_CHANNEL,
            metric_name="reach",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )

        call_args = mock_db.execute.call_args
        assert call_args is not None
        stmt = call_args[0][0]
        # Extract column names from WHERE clause by traversing BinaryExpressions
        # (avoids stmt.compile() which can fail from mapper contamination)
        where_clause = stmt.whereclause
        assert where_clause is not None
        col_names: set[str] = set()
        for clause in where_clause.clauses:
            if hasattr(clause, "left") and hasattr(clause.left, "key"):
                col_names.add(clause.left.key)
        assert "tenant_id" in col_names
        assert "channel_slug" in col_names
        assert "metric_name" in col_names
