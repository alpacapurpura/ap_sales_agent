"""Performance benchmark tests for analytics module critical paths.

Measures execution time of hot paths to catch performance regressions:
- BowtiesSummaryDTO construction
- compute_aggregations with realistic data volume
- METRIC_CATALOG lookup speed
- TenantPeriodConfig.compute_period_keys() throughput
"""

import time
import uuid
from datetime import date, timedelta

from luana_core_analytics_engine.application.dto.summary_dto import (
    BowtiesSummaryDTO,
    StageSummaryKpiDTO,
)
from luana_core_analytics_engine.domain.metric_catalog import METRIC_CATALOG
from luana_core_analytics_engine.domain.period_config import TenantPeriodConfig
from luana_core_analytics_engine.infrastructure.etl.aggregations import compute_aggregations

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CHANNELS = ["meta", "google_analytics", "tiktok", "youtube", "shopify"]
_METRICS = ["impressions", "clicks", "spend", "sessions", "views"]
_STAGES = [
    "awareness",
    "acquisition",
    "activation",
    "revenue",
    "retention",
    "referral",
    "expansion",
    "advocacy",
]


def _build_stage_summaries() -> list[StageSummaryKpiDTO]:
    """Pre-build a list of 8 stage summaries for DTO construction tests."""
    return [
        StageSummaryKpiDTO(
            stage=stage,
            main_kpi=1234.56,
            main_label="Impressions",
            main_unit="count",
            secondary_kpi=78.9,
            secondary_label="CTR",
            secondary_unit="percentage",
        )
        for stage in _STAGES
    ]


def _build_official_rows(
    num_days: int = 40,
    channels: list[str] | None = None,
    metrics: list[str] | None = None,
) -> list[dict]:
    """Build mock official_rows dicts matching compute_aggregations input format.

    Default: 40 days x 5 channels x 5 metrics = 1000 rows.
    """
    channels = channels or _CHANNELS
    metrics = metrics or _METRICS
    base_date = date(2026, 1, 1)
    rows: list[dict] = [
        {
            "channel_slug": ch,
            "metric_name": metric,
            "value": 100.0 + day_offset,
            "unit": "count",
            "currency": None,
            "cost_type": None,
            "metric_date": (d := base_date + timedelta(days=day_offset)),
            "iso_week_start": d - timedelta(days=d.weekday()),
            "month_key": d.strftime("%Y-%m"),
            "quarter_key": f"{d.year}-Q{(d.month - 1) // 3 + 1}",
        }
        for day_offset in range(num_days)
        for ch in channels
        for metric in metrics
    ]
    return rows


# ---------------------------------------------------------------------------
# Benchmark 1: Summary DTO Construction
# ---------------------------------------------------------------------------


class TestBowtiesSummaryDTOPerformance:
    """BowtiesSummaryDTO construction should be fast for dashboard rendering."""

    def test_dto_construction_under_100ms(self) -> None:
        """Building BowtiesSummaryDTO 100 times from pre-constructed data
        should complete under 100ms average."""
        stages = _build_stage_summaries()
        iterations = 100

        start = time.perf_counter()
        for _ in range(iterations):
            dto = BowtiesSummaryDTO(
                stages=stages,
                period="last_30_days",
                last_updated="2026-04-01T00:00:00Z",
            )
            # Force attribute access to ensure no lazy evaluation
            assert len(dto.stages) == 8
        elapsed_ms = (time.perf_counter() - start) * 1000

        avg_ms = elapsed_ms / iterations
        assert avg_ms < 100, (
            f"BowtiesSummaryDTO construction averaged {avg_ms:.2f}ms "
            f"(limit: 100ms). Total for {iterations} iterations: {elapsed_ms:.2f}ms"
        )

    def test_dto_serialization_performance(self) -> None:
        """model_dump() should also be fast since it feeds JSON responses."""
        stages = _build_stage_summaries()
        dto = BowtiesSummaryDTO(
            stages=stages,
            period="last_30_days",
            last_updated="2026-04-01T00:00:00Z",
        )
        iterations = 100

        start = time.perf_counter()
        for _ in range(iterations):
            data = dto.model_dump()
            assert "stages" in data
        elapsed_ms = (time.perf_counter() - start) * 1000

        avg_ms = elapsed_ms / iterations
        assert avg_ms < 100, (
            f"BowtiesSummaryDTO.model_dump() averaged {avg_ms:.2f}ms "
            f"(limit: 100ms). Total for {iterations} iterations: {elapsed_ms:.2f}ms"
        )


# ---------------------------------------------------------------------------
# Benchmark 2: Aggregation Performance
# ---------------------------------------------------------------------------


class TestAggregationPerformance:
    """compute_aggregations must handle realistic data volumes efficiently."""

    def test_1000_rows_under_500ms(self) -> None:
        """compute_aggregations with 1000 mock daily metric rows (40 days x
        5 channels x 5 metrics) should complete under 500ms."""
        tenant_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        rows = _build_official_rows(num_days=40, channels=_CHANNELS, metrics=_METRICS)
        assert len(rows) == 1000, f"Expected 1000 rows, got {len(rows)}"

        start = time.perf_counter()
        result = compute_aggregations(
            official_rows=rows,
            tenant_id=tenant_id,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Sanity: should produce aggregation records
        assert len(result) > 0, "compute_aggregations returned empty list"
        assert elapsed_ms < 500, (
            f"compute_aggregations took {elapsed_ms:.2f}ms for 1000 rows "
            f"(limit: 500ms). Produced {len(result)} aggregation records."
        )

    def test_aggregation_output_structure(self) -> None:
        """Verify aggregation output contains expected period types."""
        tenant_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        rows = _build_official_rows(num_days=40)
        result = compute_aggregations(official_rows=rows, tenant_id=tenant_id)

        period_types = {r["period_type"] for r in result}
        assert "daily" in period_types, "Missing daily aggregations"
        # ADDITIVE metrics should produce multi-period aggregations
        assert "weekly" in period_types, "Missing weekly aggregations"
        assert "monthly" in period_types, "Missing monthly aggregations"


# ---------------------------------------------------------------------------
# Benchmark 3: Metric Catalog Lookup
# ---------------------------------------------------------------------------


class TestMetricCatalogLookupPerformance:
    """METRIC_CATALOG dict lookups should be near-instantaneous."""

    def test_lookup_under_10us_average(self) -> None:
        """Building a lookup dict and performing 100 lookups x 1000 iterations
        should average under 10 microseconds per lookup."""
        catalog_names = list(METRIC_CATALOG.keys())
        assert len(catalog_names) > 0, "METRIC_CATALOG is empty"

        # Pick up to 100 names to look up (cycle if catalog is smaller)
        lookup_names = [catalog_names[i % len(catalog_names)] for i in range(100)]

        iterations = 1000
        total_lookups = len(lookup_names) * iterations

        # Build the lookup dict (simulating what code does at import time)
        lookup_dict = dict(METRIC_CATALOG.items())

        start = time.perf_counter()
        for _ in range(iterations):
            for name in lookup_names:
                defn = lookup_dict[name]
                # Access a field to prevent dead-code elimination
                _ = defn.aggregation
        elapsed_s = time.perf_counter() - start
        elapsed_us = elapsed_s * 1_000_000

        avg_us = elapsed_us / total_lookups
        assert avg_us < 10, (
            f"Metric catalog lookup averaged {avg_us:.4f}us per lookup "
            f"(limit: 10us). Total: {total_lookups} lookups in {elapsed_us:.2f}us."
        )

    def test_catalog_has_expected_entries(self) -> None:
        """Sanity check: catalog should have a meaningful number of metrics."""
        assert len(METRIC_CATALOG) >= 10, (
            f"METRIC_CATALOG only has {len(METRIC_CATALOG)} entries — expected at least 10 defined metrics."
        )


# ---------------------------------------------------------------------------
# Benchmark 4: Period Config Computation
# ---------------------------------------------------------------------------


class TestPeriodConfigPerformance:
    """TenantPeriodConfig.compute_period_keys() must be fast for ETL pipelines."""

    def test_365_dates_under_50ms(self) -> None:
        """Calling compute_period_keys() for 365 consecutive dates should
        complete under 50ms."""
        config = TenantPeriodConfig(
            weekly_start_day=0,
            fiscal_year_start_month=1,
            fiscal_year_start_day=1,
        )
        base_date = date(2026, 1, 1)
        dates = [base_date + timedelta(days=i) for i in range(365)]

        start = time.perf_counter()
        for d in dates:
            keys = config.compute_period_keys(d)
            # Verify structure to prevent dead-code elimination
            assert "iso_week_start" in keys
            assert "month_key" in keys
            assert "quarter_key" in keys
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 50, f"compute_period_keys() for 365 dates took {elapsed_ms:.2f}ms (limit: 50ms)."

    def test_period_keys_correctness(self) -> None:
        """Verify compute_period_keys returns correct values for known dates."""
        config = TenantPeriodConfig(weekly_start_day=0)

        # Wednesday 2026-01-07
        keys = config.compute_period_keys(date(2026, 1, 7))
        assert keys["month_key"] == "2026-01"
        assert keys["quarter_key"] == "2026-Q1"
        # Week containing Jan 7 (Wednesday) starts Monday Jan 5
        assert keys["iso_week_start"] == date(2026, 1, 5)

    def test_fiscal_year_custom_start(self) -> None:
        """compute_period_keys with non-January fiscal year should still be fast."""
        config = TenantPeriodConfig(
            weekly_start_day=0,
            fiscal_year_start_month=4,  # April fiscal year (common in UK)
            fiscal_year_start_day=1,
        )
        base_date = date(2026, 1, 1)
        dates = [base_date + timedelta(days=i) for i in range(365)]

        start = time.perf_counter()
        for d in dates:
            keys = config.compute_period_keys(d)
            assert "quarter_key" in keys
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 50, (
            f"compute_period_keys() with custom fiscal year for 365 dates took {elapsed_ms:.2f}ms (limit: 50ms)."
        )
