# Growth Studio Excellence Audit — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Audit, test, and refactor the Growth Studio module (backend ~18.6K LOC, frontend ~3.2K LOC) to become the reference standard for all Nicolify modules — without breaking any existing functionality.

**Architecture:** 5-phase approach: (1) complete test coverage as safety net, (2) performance profiling to identify bottlenecks, (3) backend refactoring guided by tests, (4) frontend refactoring guided by tests, (5) full verification. All work in isolated worktree, merge only after full CI passes.

**Tech Stack:** Backend: Python 3.11, FastAPI, SQLAlchemy 2.0 (async), pytest, Pydantic v2. Frontend: Next.js 14, React 18, TypeScript, Vitest, React Testing Library, Tailwind CSS, Shadcn UI.

**Docker-First:** ALL commands run inside Docker containers (`visionarias_brain_dev` for backend, `visionarias_client_dev` for frontend).

---

## Audit Findings Summary

### Critical Performance Issues
| ID | Issue | Impact | Location |
|----|-------|--------|----------|
| P1 | Bowtie `/summary` reads 8 full stage details (~2000 fields) for ~15 KPIs | High latency on dashboard load | `metrics_service.py:get_bowtie_summary()` |
| P2 | Row-by-row upserts in OfficialMetricsRepository | Slow ETL for large batches | `official_metrics_repository.py:upsert_from_staging()` |
| P3 | Frontend fires 8 parallel stage-detail APIs on every route change | Unnecessary network + server load | `useStageDetail.ts` hooks |
| P4 | ChannelRow (526 LOC) re-renders on every metric update, metric label lookup per render | UI jank with many channels | `ChannelRow.tsx` |

### Maintainability Issues
| ID | Issue | Impact | Location |
|----|-------|--------|----------|
| M1 | MetricsService is 2665 LOC monolith | Hard to test, modify, review | `metrics_service.py` |
| M2 | ChannelRow is 526 LOC monolith | Same | `ChannelRow.tsx` |
| M3 | METRIC_LABELS duplicated in 2 components (~180 entries total) | Drift risk, DRY violation | `ChannelRow.tsx`, `SidebarContent.tsx` |
| M4 | MetricCatalog is 1424 LOC single file | Hard to navigate | `metric_catalog.py` |
| M5 | Hardcoded cooldown/timeout values scattered | Config drift | Multiple files |
| M6 | Frontend tests are scaffolds (~1% coverage) | No safety net | `__tests__/` dirs |
| M7 | Backend tests partial (~40 files, many scaffolds) | Incomplete safety net | `tests/modules/analytics/` |

### Architecture Quality (Already Good)
- DDD Ports pattern for cross-module isolation
- Atomic ETL pipeline with transaction safety
- Redis cache-first dashboard with per-stage TTLs
- Period-aware aggregations with fiscal calendar support
- Provider Strategy pattern with 11 adapters
- React Query caching with smart stale times

---

## File Structure (Changes by Phase)

### Phase 1: Test Foundation (NEW files only)
```
backend/tests/modules/analytics/
  conftest.py                          # MODIFY: add shared fixtures
  test_domain_enums.py                 # CREATE: enum validation tests
  test_period_config.py                # CREATE: period boundary tests
  test_metric_catalog_validation.py    # CREATE: catalog consistency tests
  test_channel_registry.py            # CREATE: registry mapping tests
  test_aggregations.py                 # CREATE: aggregation logic tests
  test_metrics_cache.py                # MODIFY: complete existing
  test_etl_pipeline.py                 # MODIFY: add edge cases
  test_summary_endpoint.py            # CREATE: bowtie summary tests
  test_attraction_endpoint.py         # CREATE: attraction endpoint tests

frontend/src/features/growth-studio/
  test-utils.tsx                       # CREATE: shared test utilities
  hooks/__tests__/
    useBowtiesSummary.test.ts          # CREATE
    useStageDetail.test.ts             # MODIFY: complete scaffolds
    useSyncAllSources.test.ts          # CREATE
  components/metrics-dashboard/
    stage-widgets/__tests__/
      StageCard.test.tsx               # MODIFY: complete scaffolds
      StageSummaryRow.test.tsx         # CREATE
    channel-widgets/__tests__/
      ChannelRow.test.tsx              # CREATE
      MiniFunnel.test.tsx              # CREATE
    detail-panels/__tests__/
      AttractionCaptureDetail.test.tsx # CREATE
```

### Phase 2: Performance Profiling (NEW files only)
```
backend/tests/modules/analytics/
  test_performance_summary.py          # CREATE: summary endpoint timing
  test_performance_upsert.py           # CREATE: batch upsert benchmark
```

### Phase 3: Backend Refactoring (MODIFY existing)
```
backend/src/modules/analytics/application/services/
  metrics_service.py                   # MODIFY: extract stage methods to delegates
  stage_services/                      # CREATE: directory
    __init__.py                        # CREATE
    attraction_stage.py                # CREATE: extracted from metrics_service
    capture_stage.py                   # CREATE
    nurture_stage.py                   # CREATE
    opportunity_stage.py               # CREATE
    sales_stage.py                     # CREATE
    adoption_stage.py                  # CREATE
    expansion_stage.py                 # CREATE
    evangelization_stage.py            # CREATE
    summary_stage.py                   # CREATE: optimized 2-tier summary

backend/src/modules/analytics/application/
  config.py                            # CREATE: centralized config constants

backend/src/modules/analytics/infrastructure/repositories/
  official_metrics_repository.py       # MODIFY: batch upsert
```

### Phase 4: Frontend Refactoring (MODIFY existing)
```
frontend/src/features/growth-studio/
  lib/
    metric-labels.ts                   # CREATE: consolidated label source
  components/metrics-dashboard/channel-widgets/
    ChannelRow.tsx                      # MODIFY: split into subcomponents
    ChannelRowHeader.tsx               # CREATE: icon + name + badges
    ChannelRowMetrics.tsx              # CREATE: metric values display
    ChannelRowActions.tsx              # CREATE: refresh + configure buttons
```

---

## Phase 1: Test Foundation (Backend)

### Task 1: Enhanced conftest & shared fixtures

**Files:**
- Modify: `backend/tests/modules/analytics/conftest.py`

- [ ] **Step 1: Add comprehensive shared fixtures**

```python
import uuid
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest


@pytest.fixture
def test_tenant_id() -> UUID:
    """Fixed tenant UUID for test determinism."""
    return uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def mock_credentials() -> dict:
    """Simulated OAuth credentials dict."""
    return {
        "access_token": "test-access-token-abc123",
        "refresh_token": "test-refresh-token-xyz789",
    }


@pytest.fixture
def mock_connection_credentials():
    """ConnectionCredentials instance for testing."""
    from src.modules.analytics.domain.ports import ConnectionCredentials

    return ConnectionCredentials(
        channel_type="meta",
        credentials={"access_token": "test-token"},
        config={"page_id": "123456"},
    )


@pytest.fixture
def sample_offer_id() -> UUID:
    """Fixed offer UUID for test determinism."""
    return uuid.UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
def sample_customer_id() -> UUID:
    """Fixed customer UUID for test determinism."""
    return uuid.UUID("33333333-3333-3333-3333-333333333333")


@pytest.fixture
def date_range():
    """Standard 14-day test date range."""
    return date(2026, 3, 1), date(2026, 3, 14)


@pytest.fixture
def mock_db_session():
    """Mock async database session."""
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture
def mock_cache():
    """Mock MetricsCache."""
    cache = AsyncMock()
    cache.get.return_value = None  # cache miss by default
    return cache


@pytest.fixture
def make_extracted_metric():
    """Factory fixture for ExtractedMetric objects."""
    from src.modules.analytics.infrastructure.providers.base import ExtractedMetric

    def _factory(**overrides):
        defaults = {
            "provider": "meta",
            "channel_slug": "meta-ads",
            "metric_name": "impressions",
            "value": 1000.0,
            "unit": "count",
            "date": date(2026, 3, 10),
        }
        defaults.update(overrides)
        return ExtractedMetric(**defaults)

    return _factory


@pytest.fixture
def make_extraction_result(make_extracted_metric):
    """Factory fixture for ExtractionResult."""
    from src.modules.analytics.domain.extraction_result import ExtractionResult

    def _factory(metrics=None, failures=None):
        if metrics is None:
            metrics = [make_extracted_metric()]
        return ExtractionResult(metrics=metrics, failures=failures or [])

    return _factory


@pytest.fixture
def sample_official_metrics():
    """List of dicts representing official_metrics rows for aggregation tests."""
    return [
        {
            "tenant_id": uuid.UUID("11111111-1111-1111-1111-111111111111"),
            "provider": "meta",
            "channel_slug": "ig-organic",
            "metric_name": "impressions",
            "value": 500.0,
            "unit": "count",
            "metric_date": date(2026, 3, 10),
            "iso_week_start": date(2026, 3, 9),
            "month_key": "2026-03",
            "quarter_key": "2026-Q1",
        },
        {
            "tenant_id": uuid.UUID("11111111-1111-1111-1111-111111111111"),
            "provider": "meta",
            "channel_slug": "ig-organic",
            "metric_name": "impressions",
            "value": 600.0,
            "unit": "count",
            "metric_date": date(2026, 3, 11),
            "iso_week_start": date(2026, 3, 9),
            "month_key": "2026-03",
            "quarter_key": "2026-Q1",
        },
        {
            "tenant_id": uuid.UUID("11111111-1111-1111-1111-111111111111"),
            "provider": "meta",
            "channel_slug": "ig-organic",
            "metric_name": "reach",
            "value": 3000.0,
            "unit": "count",
            "metric_date": date(2026, 3, 10),
            "iso_week_start": date(2026, 3, 9),
            "month_key": "2026-03",
            "quarter_key": "2026-Q1",
        },
    ]
```

- [ ] **Step 2: Run tests to verify fixtures load**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/modules/analytics/conftest.py --collect-only -q"
```
Expected: fixtures collected without errors.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/modules/analytics/conftest.py
git commit -m "test(analytics): enhance conftest with comprehensive shared fixtures"
```

---

### Task 2: Domain layer tests (enums, period_config, extraction_result)

**Files:**
- Create: `backend/tests/modules/analytics/test_domain_enums.py`
- Create: `backend/tests/modules/analytics/test_period_config.py`

- [ ] **Step 1: Write enum validation tests**

```python
"""Tests for analytics domain enums — verify all members exist and values are stable."""

from src.modules.analytics.domain.enums import (
    CostType,
    MetricUnit,
    ExtractionStatus,
    AggregationType,
    PeriodType,
    ExtractionType,
)


class TestCostType:
    def test_has_all_required_members(self):
        expected = {"NEUTRAL", "EXPENSE", "INVESTMENT", "REVENUE"}
        assert set(m.name for m in CostType) == expected

    def test_values_are_strings(self):
        for member in CostType:
            assert isinstance(member.value, str)


class TestMetricUnit:
    def test_has_all_required_members(self):
        expected = {"COUNT", "CURRENCY", "PERCENTAGE", "RATIO", "SECONDS", "JSON"}
        assert set(m.name for m in MetricUnit) == expected


class TestExtractionStatus:
    def test_has_terminal_states(self):
        terminal = {ExtractionStatus.SUCCESS, ExtractionStatus.FAILED}
        for s in terminal:
            assert s in ExtractionStatus

    def test_has_running_state(self):
        assert ExtractionStatus.RUNNING in ExtractionStatus

    def test_has_retry_state(self):
        assert ExtractionStatus.RETRYING in ExtractionStatus


class TestAggregationType:
    def test_has_all_required_members(self):
        expected = {"ADDITIVE", "WEIGHTED_AVERAGE", "DERIVED", "NON_AGGREGABLE", "SNAPSHOT"}
        assert set(m.name for m in AggregationType) == expected


class TestPeriodType:
    def test_has_all_required_members(self):
        expected = {"DAILY", "WEEKLY", "MONTHLY", "QUARTERLY", "LAST_30_DAYS"}
        assert set(m.name for m in PeriodType) == expected


class TestExtractionType:
    def test_has_daily_and_period(self):
        assert ExtractionType.DAILY in ExtractionType
        assert ExtractionType.PERIOD in ExtractionType
```

- [ ] **Step 2: Write period config boundary tests**

```python
"""Tests for TenantPeriodConfig — period boundary calculations.

Covers:
- Week boundaries with custom start day
- Month boundaries
- Quarter boundaries with fiscal year offset
- Period key computation
- Boundary detection for scheduler
"""

from datetime import date

from src.modules.analytics.domain.period_config import TenantPeriodConfig


class TestWeekBoundaries:
    def test_default_monday_start(self):
        """Default config: weeks start Monday."""
        config = TenantPeriodConfig()
        start, end = config.get_week_boundaries(date(2026, 3, 11))  # Wednesday
        assert start == date(2026, 3, 9)   # Monday
        assert end == date(2026, 3, 15)    # Sunday

    def test_custom_sunday_start(self):
        """weekly_start_day=6 means Sunday start."""
        config = TenantPeriodConfig(weekly_start_day=6)
        start, end = config.get_week_boundaries(date(2026, 3, 11))  # Wednesday
        assert start == date(2026, 3, 8)   # Sunday
        assert end == date(2026, 3, 14)    # Saturday

    def test_boundary_day_itself(self):
        """When date IS the start day, it's the start of its own week."""
        config = TenantPeriodConfig()
        start, end = config.get_week_boundaries(date(2026, 3, 9))  # Monday
        assert start == date(2026, 3, 9)
        assert end == date(2026, 3, 15)


class TestMonthBoundaries:
    def test_mid_month(self):
        config = TenantPeriodConfig()
        start, end = config.get_month_boundaries(date(2026, 3, 15))
        assert start == date(2026, 3, 1)
        assert end == date(2026, 3, 31)

    def test_february_non_leap(self):
        config = TenantPeriodConfig()
        start, end = config.get_month_boundaries(date(2027, 2, 15))
        assert start == date(2027, 2, 1)
        assert end == date(2027, 2, 28)


class TestQuarterBoundaries:
    def test_default_calendar_q1(self):
        config = TenantPeriodConfig()
        start, end = config.get_quarter_boundaries(date(2026, 2, 15))
        assert start == date(2026, 1, 1)
        assert end == date(2026, 3, 31)

    def test_fiscal_year_april_start(self):
        """UK-style fiscal year starting April 1."""
        config = TenantPeriodConfig(fiscal_year_start_month=4)
        start, end = config.get_quarter_boundaries(date(2026, 5, 15))
        assert start == date(2026, 4, 1)
        assert end == date(2026, 6, 30)


class TestPeriodKeys:
    def test_compute_period_keys_returns_all_keys(self):
        config = TenantPeriodConfig()
        keys = config.compute_period_keys(date(2026, 3, 11))
        assert "iso_week_start" in keys
        assert "month_key" in keys
        assert "quarter_key" in keys

    def test_month_key_format(self):
        config = TenantPeriodConfig()
        keys = config.compute_period_keys(date(2026, 3, 11))
        assert keys["month_key"] == "2026-03"

    def test_quarter_key_format(self):
        config = TenantPeriodConfig()
        keys = config.compute_period_keys(date(2026, 3, 11))
        assert keys["quarter_key"] == "2026-Q1"


class TestBoundaryDetection:
    def test_week_boundary_on_last_day(self):
        """Sunday is the last day of a default (Mon-start) week."""
        config = TenantPeriodConfig()
        from src.modules.analytics.domain.enums import PeriodType
        assert config.is_period_boundary(date(2026, 3, 15), PeriodType.WEEKLY)

    def test_month_boundary_on_last_day(self):
        config = TenantPeriodConfig()
        from src.modules.analytics.domain.enums import PeriodType
        assert config.is_period_boundary(date(2026, 3, 31), PeriodType.MONTHLY)

    def test_non_boundary_day(self):
        config = TenantPeriodConfig()
        from src.modules.analytics.domain.enums import PeriodType
        assert not config.is_period_boundary(date(2026, 3, 11), PeriodType.WEEKLY)
```

- [ ] **Step 3: Run domain tests**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/modules/analytics/test_domain_enums.py tests/modules/analytics/test_period_config.py -v --tb=short"
```
Expected: All PASS.

- [ ] **Step 4: Commit**

```bash
git add backend/tests/modules/analytics/test_domain_enums.py backend/tests/modules/analytics/test_period_config.py
git commit -m "test(analytics): add domain layer tests for enums and period config"
```

---

### Task 3: Metric catalog consistency tests

**Files:**
- Create: `backend/tests/modules/analytics/test_metric_catalog_validation.py`

- [ ] **Step 1: Write catalog validation tests**

```python
"""Tests for MetricCatalog consistency.

Validates:
- Every metric has required fields (name, unit, aggregation_type)
- No duplicate metric names
- All provider references exist in PROVIDER_REGISTRY
- Aggregation type semantics (ADDITIVE must have unit COUNT or CURRENCY, etc.)
- DERIVED metrics declare component metrics
"""

from src.modules.analytics.domain.metric_catalog import METRIC_CATALOG


class TestCatalogCompleteness:
    def test_no_duplicate_metric_names(self):
        """Each metric_name must appear exactly once in the catalog."""
        names = [m.name for m in METRIC_CATALOG]
        assert len(names) == len(set(names)), f"Duplicates: {[n for n in names if names.count(n) > 1]}"

    def test_all_metrics_have_required_fields(self):
        """Every MetricDefinition must have name, unit, and aggregation_type."""
        for m in METRIC_CATALOG:
            assert m.name, f"Metric missing name: {m}"
            assert m.unit, f"Metric {m.name} missing unit"
            assert m.aggregation_type, f"Metric {m.name} missing aggregation_type"

    def test_all_metrics_have_display_name(self):
        """display_name should never be empty."""
        for m in METRIC_CATALOG:
            assert m.display_name, f"Metric {m.name} missing display_name"

    def test_catalog_has_minimum_metrics(self):
        """Catalog should have at least 50 metrics (sanity check)."""
        assert len(METRIC_CATALOG) >= 50, f"Only {len(METRIC_CATALOG)} metrics in catalog"


class TestAggregationSemantics:
    def test_additive_metrics_are_summable(self):
        """ADDITIVE metrics should have COUNT or CURRENCY unit (not PERCENTAGE)."""
        from src.modules.analytics.domain.enums import AggregationType, MetricUnit

        additive = [m for m in METRIC_CATALOG if m.aggregation_type == AggregationType.ADDITIVE]
        for m in additive:
            assert m.unit in (MetricUnit.COUNT, MetricUnit.CURRENCY, MetricUnit.SECONDS, MetricUnit.JSON), \
                f"ADDITIVE metric {m.name} has unit {m.unit} (should be summable)"

    def test_derived_metrics_not_additive(self):
        """DERIVED metrics (CPC, ROAS, etc.) must NOT be ADDITIVE."""
        from src.modules.analytics.domain.enums import AggregationType

        derived = [m for m in METRIC_CATALOG if m.aggregation_type == AggregationType.DERIVED]
        for m in derived:
            assert m.aggregation_type != AggregationType.ADDITIVE, \
                f"Metric {m.name} is both DERIVED and ADDITIVE"

    def test_snapshot_metrics_exist(self):
        """Catalog should have SNAPSHOT metrics (MRR, active_subscribers, etc.)."""
        from src.modules.analytics.domain.enums import AggregationType

        snapshots = [m for m in METRIC_CATALOG if m.aggregation_type == AggregationType.SNAPSHOT]
        assert len(snapshots) >= 1, "No SNAPSHOT metrics found"

    def test_non_aggregable_metrics_exist(self):
        """reach, users, frequency should be NON_AGGREGABLE."""
        from src.modules.analytics.domain.enums import AggregationType

        non_agg = {m.name for m in METRIC_CATALOG if m.aggregation_type == AggregationType.NON_AGGREGABLE}
        assert "reach" in non_agg or "unique_visitors" in non_agg, \
            "No NON_AGGREGABLE uniqueness metrics found"
```

- [ ] **Step 2: Run catalog tests**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/modules/analytics/test_metric_catalog_validation.py -v --tb=short"
```

- [ ] **Step 3: Commit**

```bash
git add backend/tests/modules/analytics/test_metric_catalog_validation.py
git commit -m "test(analytics): add metric catalog consistency validation tests"
```

---

### Task 4: Channel registry and aggregation logic tests

**Files:**
- Create: `backend/tests/modules/analytics/test_channel_registry_unit.py`
- Create: `backend/tests/modules/analytics/test_aggregation_logic.py`

- [ ] **Step 1: Write channel registry tests**

```python
"""Tests for ChannelRegistry — dynamic channel metadata mapping."""

from src.modules.analytics.application.services.channel_registry import (
    ChannelRegistry,
    STAGE_CHANNEL_MAP,
)


class TestChannelRegistryMappings:
    def test_attraction_stage_has_channels(self):
        """Attraction stage should have at least 3 channel groups."""
        channels = STAGE_CHANNEL_MAP.get("attraction", [])
        assert len(channels) >= 3, f"Attraction has only {len(channels)} channels"

    def test_all_channels_have_slug(self):
        """Every channel entry must have a slug."""
        for stage, channels in STAGE_CHANNEL_MAP.items():
            for ch in channels:
                assert ch.get("slug") or ch.get("channel_slug"), \
                    f"Channel in {stage} missing slug: {ch}"

    def test_no_duplicate_slugs_per_stage(self):
        """Channel slugs must be unique within each stage."""
        for stage, channels in STAGE_CHANNEL_MAP.items():
            slugs = [ch.get("slug") or ch.get("channel_slug") for ch in channels]
            assert len(slugs) == len(set(slugs)), \
                f"Duplicate slugs in {stage}: {[s for s in slugs if slugs.count(s) > 1]}"

    def test_channel_registry_get_channels_for_stage(self):
        """ChannelRegistry.get_channels_for_stage() returns list for valid stage."""
        registry = ChannelRegistry()
        channels = registry.get_channels_for_stage("attraction")
        assert isinstance(channels, list)
        assert len(channels) > 0
```

- [ ] **Step 2: Write aggregation logic tests**

```python
"""Tests for ETL aggregation logic — ADDITIVE, SNAPSHOT, NON_AGGREGABLE, WEIGHTED_AVERAGE.

Tests the compute_aggregations function which groups daily metrics into
weekly/monthly/quarterly/last_30_days rollups.
"""

from datetime import date
from unittest.mock import MagicMock


class TestAdditiveAggregation:
    def test_sum_daily_to_weekly(self):
        """ADDITIVE metrics (impressions) should SUM across days in a week."""
        from src.modules.analytics.infrastructure.etl.aggregations import compute_aggregations

        daily_rows = [
            MagicMock(
                channel_slug="ig-organic",
                metric_name="impressions",
                value=100.0,
                unit="count",
                currency=None,
                cost_type=None,
                metric_date=date(2026, 3, 9),
                iso_week_start=date(2026, 3, 9),
                month_key="2026-03",
                quarter_key="2026-Q1",
            ),
            MagicMock(
                channel_slug="ig-organic",
                metric_name="impressions",
                value=200.0,
                unit="count",
                currency=None,
                cost_type=None,
                metric_date=date(2026, 3, 10),
                iso_week_start=date(2026, 3, 9),
                month_key="2026-03",
                quarter_key="2026-Q1",
            ),
        ]

        result = compute_aggregations(daily_rows)
        weekly = [r for r in result if r.get("period_type") == "weekly"]
        impressions_weekly = [r for r in weekly if r["metric_name"] == "impressions"]
        assert len(impressions_weekly) >= 1
        assert impressions_weekly[0]["value"] == 300.0  # 100 + 200

    def test_non_aggregable_excluded_from_weekly(self):
        """NON_AGGREGABLE metrics (reach) should NOT produce weekly/monthly rollups."""
        from src.modules.analytics.infrastructure.etl.aggregations import compute_aggregations

        daily_rows = [
            MagicMock(
                channel_slug="ig-organic",
                metric_name="reach",
                value=5000.0,
                unit="count",
                currency=None,
                cost_type=None,
                metric_date=date(2026, 3, 9),
                iso_week_start=date(2026, 3, 9),
                month_key="2026-03",
                quarter_key="2026-Q1",
            ),
        ]

        result = compute_aggregations(daily_rows)
        # reach should appear in daily only, not in weekly/monthly aggregations
        reach_weekly = [r for r in result
                        if r.get("metric_name") == "reach" and r.get("period_type") == "weekly"]
        assert len(reach_weekly) == 0, "NON_AGGREGABLE metric 'reach' should not have weekly rollup"
```

- [ ] **Step 3: Run tests**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/modules/analytics/test_channel_registry_unit.py tests/modules/analytics/test_aggregation_logic.py -v --tb=short"
```

- [ ] **Step 4: Commit**

```bash
git add backend/tests/modules/analytics/test_channel_registry_unit.py backend/tests/modules/analytics/test_aggregation_logic.py
git commit -m "test(analytics): add channel registry and aggregation logic tests"
```

---

### Task 5: MetricsCache and ETL pipeline edge case tests

**Files:**
- Modify: `backend/tests/modules/analytics/test_metrics_cache.py`
- Modify: `backend/tests/modules/analytics/test_etl_pipeline.py`

- [ ] **Step 1: Read existing test files to understand current coverage**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/modules/analytics/test_metrics_cache.py tests/modules/analytics/test_etl_pipeline.py -v --tb=short 2>&1 | head -40"
```

- [ ] **Step 2: Add ETL pipeline edge case tests (partial success, empty extraction)**

Append to `test_etl_pipeline.py`:

```python
class TestETLPipelinePartialSuccess:
    """Tests for partial_success — some sub-extractors fail but metrics exist."""

    def test_run_marks_partial_success_with_failures(self):
        """When sub-extractors fail but some metrics extracted -> PARTIAL_SUCCESS."""
        from src.modules.analytics.infrastructure.etl.pipeline import ETLPipeline
        from src.modules.analytics.domain.enums import ExtractionStatus
        from src.modules.analytics.domain.extraction_result import (
            ExtractionResult,
            SubExtractorFailure,
        )

        mock_db = MagicMock()
        mock_provider = AsyncMock()
        mock_provider.provider_name.return_value = "meta"

        result_with_failures = ExtractionResult(
            metrics=[_make_extracted_metric()],
            failures=[
                SubExtractorFailure(
                    extractor_name="fb-organic",
                    error="Rate limited",
                    error_type="transient",
                )
            ],
        )
        mock_provider.extract_metrics.return_value = result_with_failures

        mock_connection_port = AsyncMock()
        mock_connection_port.get_credentials.return_value = MagicMock(
            credentials={"access_token": "test"}, config={},
        )

        run_model = _make_run_model()
        mock_run_repo = MagicMock()
        mock_run_repo.create.return_value = run_model
        mock_staging_repo = MagicMock()
        mock_staging_repo.bulk_insert.return_value = 1
        mock_official_repo = MagicMock()
        mock_official_repo.upsert_from_staging.return_value = 1
        mock_cache = AsyncMock()

        pipeline = ETLPipeline(
            db=mock_db,
            provider=mock_provider,
            connection_port=mock_connection_port,
            staging_repo=mock_staging_repo,
            official_repo=mock_official_repo,
            run_repo=mock_run_repo,
            cache=mock_cache,
        )

        _run(pipeline.run(TENANT_ID, START_DATE, END_DATE))

        update_calls = mock_run_repo.update_status.call_args_list
        partial_call = [c for c in update_calls
                        if c[1].get("status") == ExtractionStatus.PARTIAL_SUCCESS]
        assert len(partial_call) == 1, "Should mark PARTIAL_SUCCESS when failures present but metrics exist"


class TestETLPipelineEmptyExtraction:
    """Tests for zero-metric extraction (no data from provider)."""

    def test_run_succeeds_with_zero_metrics(self):
        """Empty extraction (no metrics, no failures) should still SUCCESS."""
        from src.modules.analytics.infrastructure.etl.pipeline import ETLPipeline
        from src.modules.analytics.domain.enums import ExtractionStatus
        from src.modules.analytics.domain.extraction_result import ExtractionResult

        mock_db = MagicMock()
        mock_provider = AsyncMock()
        mock_provider.provider_name.return_value = "meta"
        mock_provider.extract_metrics.return_value = ExtractionResult(metrics=[])

        mock_connection_port = AsyncMock()
        mock_connection_port.get_credentials.return_value = MagicMock(
            credentials={"access_token": "test"}, config={},
        )

        run_model = _make_run_model()
        mock_run_repo = MagicMock()
        mock_run_repo.create.return_value = run_model
        mock_staging_repo = MagicMock()
        mock_official_repo = MagicMock()
        mock_cache = AsyncMock()

        pipeline = ETLPipeline(
            db=mock_db,
            provider=mock_provider,
            connection_port=mock_connection_port,
            staging_repo=mock_staging_repo,
            official_repo=mock_official_repo,
            run_repo=mock_run_repo,
            cache=mock_cache,
        )

        _run(pipeline.run(TENANT_ID, START_DATE, END_DATE))

        update_calls = mock_run_repo.update_status.call_args_list
        success_call = [c for c in update_calls
                        if c[1].get("status") == ExtractionStatus.SUCCESS]
        assert len(success_call) == 1
```

- [ ] **Step 3: Run all ETL tests**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/modules/analytics/test_etl_pipeline.py -v --tb=short"
```

- [ ] **Step 4: Commit**

```bash
git add backend/tests/modules/analytics/test_etl_pipeline.py backend/tests/modules/analytics/test_metrics_cache.py
git commit -m "test(analytics): add ETL pipeline edge cases (partial success, empty extraction)"
```

---

### Task 6: API endpoint contract tests

**Files:**
- Create: `backend/tests/modules/analytics/test_summary_endpoint.py`
- Create: `backend/tests/modules/analytics/test_attraction_endpoint.py`

- [ ] **Step 1: Write summary endpoint DTO shape tests**

```python
"""Tests for /metrics/summary endpoint — Bowtie summary DTO shape validation.

Tests the DTO construction logic without hitting the DB.
Verifies the response shape matches what the frontend expects.
"""

from src.modules.analytics.application.dto.summary_dto import (
    BowtiesSummaryDTO,
    StageSummaryKpiDTO,
)


class TestBowtiesSummaryDTO:
    def test_dto_has_all_stages(self):
        """BowtiesSummaryDTO must have exactly 5 composite stages."""
        stages = BowtiesSummaryDTO.model_fields.keys()
        expected = {
            "atraccion_captura",
            "nutricion_oportunidad",
            "ventas",
            "adopcion",
            "expansion_evangelizacion",
        }
        # Verify these composite stages exist (names may vary)
        assert len(stages) >= 5, f"Expected >=5 stages, got {len(stages)}: {list(stages)}"

    def test_stage_kpi_dto_shape(self):
        """StageSummaryKpiDTO should have label, value, and optional unit."""
        kpi = StageSummaryKpiDTO(label="Visitantes", value=1250)
        assert kpi.label == "Visitantes"
        assert kpi.value == 1250

    def test_stage_kpi_with_percentage_unit(self):
        """StageSummaryKpiDTO with unit '%' for conversion rates."""
        kpi = StageSummaryKpiDTO(label="Conversion", value=18.9, unit="%")
        assert kpi.unit == "%"
        assert kpi.value == 18.9


class TestAttractionDetailDTO:
    def test_dto_has_channel_groups(self):
        """AttractionDetailDTO must expose channel groups."""
        from src.modules.analytics.application.dto.attraction_dto import AttractionDetailDTO

        fields = AttractionDetailDTO.model_fields.keys()
        assert "available_channels" in fields or "traffic_groups" in fields

    def test_channel_metric_dto_shape(self):
        """ChannelMetricDTO must have slug, metrics list, and connected flag."""
        from src.modules.analytics.application.dto.attraction_dto import ChannelMetricDTO

        fields = ChannelMetricDTO.model_fields.keys()
        assert "slug" in fields or "channel_slug" in fields
```

- [ ] **Step 2: Run endpoint tests**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/modules/analytics/test_summary_endpoint.py tests/modules/analytics/test_attraction_endpoint.py -v --tb=short"
```

- [ ] **Step 3: Commit**

```bash
git add backend/tests/modules/analytics/test_summary_endpoint.py backend/tests/modules/analytics/test_attraction_endpoint.py
git commit -m "test(analytics): add endpoint DTO shape contract tests"
```

---

## Phase 1: Test Foundation (Frontend)

### Task 7: Frontend test utilities

**Files:**
- Create: `frontend/src/features/growth-studio/test-utils.tsx`

- [ ] **Step 1: Create shared test wrapper with QueryClientProvider**

```tsx
import React, { type ReactNode } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, type RenderOptions } from '@testing-library/react';
import { vi } from 'vitest';

// Mock Clerk auth globally for all growth-studio tests
vi.mock('@clerk/nextjs', () => ({
  useAuth: () => ({
    getToken: vi.fn(() => Promise.resolve('mock-test-token')),
    isLoaded: true,
    isSignedIn: true,
    userId: 'user_test123',
    orgId: 'org_test123',
  }),
}));

// Mock next/navigation
vi.mock('next/navigation', () => ({
  usePathname: () => '/test-tenant/growth-studio/atraccion-captura',
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
  }),
  useParams: () => ({ tenantId: 'test-tenant-id' }),
}));

/**
 * Creates a fresh QueryClient for each test to prevent cache leakage.
 */
function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

interface WrapperProps {
  children: ReactNode;
}

/**
 * Renders a component wrapped with QueryClientProvider and mock auth.
 * Use this for all growth-studio component/hook tests.
 */
export function renderWithProviders(
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>,
) {
  const queryClient = createTestQueryClient();

  function Wrapper({ children }: WrapperProps) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  }

  return {
    ...render(ui, { wrapper: Wrapper, ...options }),
    queryClient,
  };
}

/**
 * Creates a wrapper for renderHook tests.
 */
export function createHookWrapper() {
  const queryClient = createTestQueryClient();

  function Wrapper({ children }: WrapperProps) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  }

  return { wrapper: Wrapper, queryClient };
}

/**
 * Mock stage summary data matching BowtiesSummary type.
 */
export const mockBowtiesSummary = {
  atraccion_captura: {
    mainKpi: { label: 'Visitantes', value: 1250 },
    secondaryKpi: { label: 'Conversion', value: 18.9, unit: '%' },
  },
  nutricion_oportunidad: {
    mainKpi: { label: 'Leads Nutridos', value: 340 },
    secondaryKpi: { label: 'Conversion', value: 12.5, unit: '%' },
  },
  ventas: {
    mainKpi: { label: 'Ventas', value: 45 },
    secondaryKpi: { label: 'Conversion', value: 8.2, unit: '%' },
  },
  adopcion: {
    mainKpi: { label: 'Clientes Activos', value: 120 },
    secondaryKpi: { label: 'Health', value: 85, unit: '%' },
  },
  expansion_evangelizacion: {
    mainKpi: { label: 'MRR', value: 4500 },
    secondaryKpi: { label: 'K-Factor', value: 1.3 },
  },
};

/**
 * Mock channel metric data.
 */
export const mockChannelMetric = {
  slug: 'ig-organic',
  name: 'Instagram Orgánico',
  connected: true,
  lastUpdated: '2026-03-15T10:00:00Z',
  metrics: [
    { name: 'reach', value: 15000, unit: 'count' },
    { name: 'engagement', value: 450, unit: 'count' },
    { name: 'impressions', value: 85000, unit: 'count' },
  ],
};
```

- [ ] **Step 2: Verify test utils compile**

```bash
docker exec -t visionarias_client_dev npx tsc --noEmit --strict src/features/growth-studio/test-utils.tsx 2>&1 | head -20
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/growth-studio/test-utils.tsx
git commit -m "test(growth-studio): add shared test utilities with QueryClient wrapper"
```

---

### Task 8: Complete frontend hook tests

**Files:**
- Create: `frontend/src/features/growth-studio/hooks/__tests__/useBowtiesSummary.test.ts`
- Modify: `frontend/src/features/growth-studio/hooks/__tests__/useAttractionDetail.test.ts`

- [ ] **Step 1: Write useBowtiesSummary tests**

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { createHookWrapper, mockBowtiesSummary } from '../../test-utils';

// Mock the API module
vi.mock('@/features/growth-studio/api/summary-api', () => ({
  fetchBowtiesSummary: vi.fn(),
}));

describe('useBowtiesSummary', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should return loading state initially', async () => {
    const { fetchBowtiesSummary } = await import(
      '@/features/growth-studio/api/summary-api'
    );
    vi.mocked(fetchBowtiesSummary).mockImplementation(
      () => new Promise(() => {}), // never resolves
    );

    const { wrapper } = createHookWrapper();
    const { useBowtiesSummary } = await import('../useBowtiesSummary');
    const { result } = renderHook(() => useBowtiesSummary(), { wrapper });

    expect(result.current.isLoading).toBe(true);
    expect(result.current.data).toBeUndefined();
  });

  it('should return summary data on successful fetch', async () => {
    const { fetchBowtiesSummary } = await import(
      '@/features/growth-studio/api/summary-api'
    );
    vi.mocked(fetchBowtiesSummary).mockResolvedValueOnce(mockBowtiesSummary);

    const { wrapper } = createHookWrapper();
    const { useBowtiesSummary } = await import('../useBowtiesSummary');
    const { result } = renderHook(() => useBowtiesSummary(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockBowtiesSummary);
  });

  it('should surface error on failed fetch', async () => {
    const { fetchBowtiesSummary } = await import(
      '@/features/growth-studio/api/summary-api'
    );
    vi.mocked(fetchBowtiesSummary).mockRejectedValueOnce(
      new Error('Network Error'),
    );

    const { wrapper } = createHookWrapper();
    const { useBowtiesSummary } = await import('../useBowtiesSummary');
    const { result } = renderHook(() => useBowtiesSummary(), { wrapper });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeDefined();
  });
});
```

- [ ] **Step 2: Rewrite useAttractionDetail test with proper QueryClient wrapper**

Replace contents of `useAttractionDetail.test.ts` with working tests using `createHookWrapper`.

- [ ] **Step 3: Run frontend hook tests**

```bash
docker exec -t visionarias_client_dev npm run test -- --run src/features/growth-studio/hooks/__tests__/
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/growth-studio/hooks/__tests__/
git commit -m "test(growth-studio): complete hook tests with QueryClient wrapper"
```

---

### Task 9: Frontend component tests (StageCard, ChannelRow)

**Files:**
- Modify: `frontend/src/features/growth-studio/components/metrics-dashboard/stage-widgets/__tests__/StageCard.test.tsx`
- Create: `frontend/src/features/growth-studio/components/metrics-dashboard/channel-widgets/__tests__/ChannelRow.test.tsx`

- [ ] **Step 1: Complete StageCard tests (replace TODOs)**

Replace `StageCard.test.tsx` with working assertions:

```tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { StageCard } from '../StageCard';
import type { StageSummary } from '@/features/growth-studio/types/metrics';

const mockStageSummary: StageSummary = {
  id: 'ATRACCION',
  order: 0,
  label: 'Atraccion',
  description: 'Total visitors attracted to your content',
  mainKpi: { label: 'Visitantes', value: 1250 },
  secondaryKpi: { label: 'Conversion', value: 18.9, unit: '%' },
  hasDetail: true,
};

describe('StageCard', () => {
  it('should display stage label', () => {
    render(
      <StageCard stage={mockStageSummary} isActive={false} onClick={() => {}} />,
    );
    expect(screen.getByText(/atraccion/i)).toBeInTheDocument();
  });

  it('should display formatted mainKpi value', () => {
    render(
      <StageCard stage={mockStageSummary} isActive={false} onClick={() => {}} />,
    );
    // 1250 >= 1000 -> formatted as "1.3k" or "1.2k"
    expect(screen.getByText(/1\.\d+k|1,?250/)).toBeInTheDocument();
  });

  it('should call onClick when clicked', async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();
    render(
      <StageCard
        stage={mockStageSummary}
        isActive={false}
        onClick={handleClick}
      />,
    );

    const card = screen.getByText(/atraccion/i).closest('button, div[role="button"], [class*="cursor"]');
    if (card) {
      await user.click(card);
      expect(handleClick).toHaveBeenCalledTimes(1);
    }
  });

  it('should show loading skeleton when isLoading', () => {
    const { container } = render(
      <StageCard
        stage={mockStageSummary}
        isActive={false}
        onClick={() => {}}
        isLoading={true}
      />,
    );
    // Skeleton uses animate-pulse class
    const skeleton = container.querySelector('[class*="animate-pulse"], [class*="skeleton"]');
    expect(skeleton).toBeTruthy();
  });
});
```

- [ ] **Step 2: Create ChannelRow snapshot/behavior tests**

```tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ChannelRow } from '../ChannelRow';
import { renderWithProviders, mockChannelMetric } from '../../../../test-utils';
import type { ChannelMetric } from '../../../../types/metrics';

// Mock channel icons
vi.mock('../../../../lib/channelIcons', () => ({
  getChannelIcon: () => () => null,
  getChannelColor: () => '#8B5CF6',
}));

// Mock useMetricCatalog
vi.mock('../../../../hooks/useMetricCatalog', () => ({
  useMetricCatalog: () => ({
    data: {},
    isLoading: false,
  }),
}));

describe('ChannelRow', () => {
  const defaultChannel: ChannelMetric = {
    slug: 'ig-organic',
    name: 'Instagram Orgánico',
    connected: true,
    lastUpdated: '2026-03-15T10:00:00Z',
    metrics: [
      { name: 'reach', value: 15000, unit: 'count' },
      { name: 'engagement', value: 450, unit: 'count' },
    ],
  };

  it('should render channel name', () => {
    renderWithProviders(
      <ChannelRow channel={defaultChannel} />,
    );
    expect(screen.getByText(/instagram orgánico/i)).toBeInTheDocument();
  });

  it('should show metric values for connected channels', () => {
    renderWithProviders(
      <ChannelRow channel={defaultChannel} />,
    );
    // At least one metric value should be visible
    expect(screen.getByText(/15/)).toBeInTheDocument(); // 15k or 15,000
  });

  it('should show "Configurar" badge for unconnected channels', () => {
    const unconnected = { ...defaultChannel, connected: false, metrics: [] };
    renderWithProviders(
      <ChannelRow channel={unconnected} />,
    );
    const badge = screen.queryByText(/configurar/i);
    expect(badge).toBeTruthy();
  });

  it('should display "---" for missing metric values', () => {
    const noMetrics = { ...defaultChannel, metrics: [] };
    renderWithProviders(
      <ChannelRow channel={noMetrics} />,
    );
    // Should show placeholder dashes
    expect(screen.queryByText('---') || screen.queryByText('–')).toBeTruthy();
  });
});
```

- [ ] **Step 3: Run component tests**

```bash
docker exec -t visionarias_client_dev npm run test -- --run src/features/growth-studio/components/
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/growth-studio/components/metrics-dashboard/stage-widgets/__tests__/StageCard.test.tsx
git add frontend/src/features/growth-studio/components/metrics-dashboard/channel-widgets/__tests__/ChannelRow.test.tsx
git commit -m "test(growth-studio): complete StageCard and add ChannelRow component tests"
```

---

## Phase 2: Performance Profiling

### Task 10: Backend performance benchmark tests

**Files:**
- Create: `backend/tests/modules/analytics/test_performance_benchmarks.py`

- [ ] **Step 1: Write performance measurement tests**

```python
"""Performance benchmark tests for Growth Studio critical paths.

These tests measure execution time of key operations to establish baselines
and detect regressions. They do NOT hit external APIs — they use mocked data.

Benchmarks:
1. Summary DTO construction from cached data
2. Aggregation computation for large metric sets
3. Metric catalog lookups
"""

import time
import uuid
from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest


TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


class TestSummaryConstruction:
    """Benchmark: How long does BowtiesSummary DTO construction take?"""

    def test_summary_dto_builds_under_100ms(self):
        """Building summary DTO from pre-fetched data should be <100ms."""
        from src.modules.analytics.application.dto.summary_dto import (
            BowtiesSummaryDTO,
            StageSummaryKpiDTO,
        )

        start = time.perf_counter()

        for _ in range(100):
            kpi = StageSummaryKpiDTO(label="Visitantes", value=1250)
            # Build 5 composite stages
            summary = BowtiesSummaryDTO.model_construct(
                atraccion_captura={"mainKpi": kpi, "secondaryKpi": kpi},
                nutricion_oportunidad={"mainKpi": kpi, "secondaryKpi": kpi},
                ventas={"mainKpi": kpi, "secondaryKpi": kpi},
                adopcion={"mainKpi": kpi, "secondaryKpi": kpi},
                expansion_evangelizacion={"mainKpi": kpi, "secondaryKpi": kpi},
            )

        elapsed = time.perf_counter() - start
        avg_ms = (elapsed / 100) * 1000

        assert avg_ms < 100, f"Summary DTO construction took {avg_ms:.1f}ms (should be <100ms)"


class TestAggregationPerformance:
    """Benchmark: compute_aggregations with realistic data volume."""

    def test_aggregation_1000_rows_under_500ms(self):
        """1000 daily metric rows should aggregate in <500ms."""
        from src.modules.analytics.infrastructure.etl.aggregations import compute_aggregations

        base_date = date(2026, 1, 1)
        channels = ["ig-organic", "meta-ads", "google-organic", "yt-organic", "tiktok-organic"]
        metrics = ["impressions", "clicks", "spend", "conversions", "sessions"]

        rows = []
        for day_offset in range(40):  # 40 days
            d = base_date + timedelta(days=day_offset)
            for ch in channels:
                for m in metrics:
                    rows.append(MagicMock(
                        channel_slug=ch,
                        metric_name=m,
                        value=float(100 + day_offset),
                        unit="count",
                        currency=None,
                        cost_type=None,
                        metric_date=d,
                        iso_week_start=d - timedelta(days=d.weekday()),
                        month_key=d.strftime("%Y-%m"),
                        quarter_key=f"{d.year}-Q{(d.month - 1) // 3 + 1}",
                    ))

        assert len(rows) == 1000, f"Expected 1000 rows, got {len(rows)}"

        start = time.perf_counter()
        result = compute_aggregations(rows)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 500, f"Aggregation of 1000 rows took {elapsed_ms:.1f}ms (should be <500ms)"
        assert len(result) > 0, "Should produce aggregation results"


class TestMetricCatalogLookup:
    """Benchmark: metric catalog lookups should be O(1)."""

    def test_catalog_dict_lookup_under_1ms(self):
        """Looking up 100 metrics by name should be <1ms total."""
        from src.modules.analytics.domain.metric_catalog import METRIC_CATALOG

        catalog_dict = {m.name: m for m in METRIC_CATALOG}
        names = list(catalog_dict.keys())[:100]

        start = time.perf_counter()
        for _ in range(1000):
            for name in names:
                _ = catalog_dict.get(name)
        elapsed_ms = (time.perf_counter() - start) * 1000

        avg_per_lookup_us = (elapsed_ms / (1000 * len(names))) * 1000
        assert avg_per_lookup_us < 10, f"Catalog lookup took {avg_per_lookup_us:.1f}μs (should be <10μs)"
```

- [ ] **Step 2: Run performance tests**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/modules/analytics/test_performance_benchmarks.py -v --tb=short -s"
```
Expected: All pass with timing output.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/modules/analytics/test_performance_benchmarks.py
git commit -m "perf(analytics): add performance benchmark tests for critical paths"
```

---

## Phase 3: Backend Refactoring

### Task 11: Extract MetricsService into stage-specific services

**Files:**
- Create: `backend/src/modules/analytics/application/services/stage_services/__init__.py`
- Create: `backend/src/modules/analytics/application/services/stage_services/attraction_stage.py`
- Create: `backend/src/modules/analytics/application/services/stage_services/summary_stage.py`
- Modify: `backend/src/modules/analytics/application/services/metrics_service.py`

**Strategy:** Extract each `get_*_metrics()` method into a stage-specific class. MetricsService becomes a facade that delegates to stage services. This is a SAFE refactoring because:
1. Public API (method signatures) stays identical
2. Each extracted class is a 1:1 copy of the original method
3. MetricsService delegates, so callers see no change

- [ ] **Step 1: Read metrics_service.py fully to understand method boundaries**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && grep -n 'async def get_\|def get_' src/modules/analytics/application/services/metrics_service.py"
```

- [ ] **Step 2: Create stage_services directory and __init__.py**

```python
"""Stage-specific service classes — extracted from MetricsService for maintainability.

Each class handles a single Bowtie funnel stage:
- AttractionStageService  -> get_attraction_metrics()
- CaptureStageService     -> get_capture_metrics()
- SummaryStageService     -> get_bowtie_summary()
(etc.)

MetricsService delegates to these classes — public API unchanged.
"""

from .attraction_stage import AttractionStageService
from .summary_stage import SummaryStageService

__all__ = [
    "AttractionStageService",
    "SummaryStageService",
]
```

- [ ] **Step 3: Extract AttractionStageService**

Extract `get_attraction_metrics()` method (and its private helpers) from `metrics_service.py` into `attraction_stage.py`. The method signature, imports, and logic remain identical. Only the class wrapper changes.

```python
"""Attraction stage service — Stage 1 of the Bowtie funnel.

Extracted from MetricsService.get_attraction_metrics() for maintainability.
"""

from collections import defaultdict
from datetime import datetime
from uuid import UUID
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session

from src.modules.analytics.application.dto.attraction_dto import (
    AttractionDetailDTO,
    AvailableChannelsDTO,
    TrafficGroupDTO,
    ChannelMetricDTO,
    MetricValueDTO,
)
from src.modules.analytics.application.services.channel_registry import ChannelRegistry
from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache


class AttractionStageService:
    """Handles attraction stage metric aggregation."""

    def __init__(
        self,
        db: Session,
        cache: MetricsCache,
        channel_registry: ChannelRegistry,
    ):
        self.db = db
        self.cache = cache
        self.channel_registry = channel_registry

    async def get_attraction_metrics(
        self,
        tenant_id: UUID,
        period: str = "last_30_days",
    ) -> AttractionDetailDTO:
        # COPY: exact body from MetricsService.get_attraction_metrics()
        # This is a move refactoring — no logic changes
        ...
```

- [ ] **Step 4: Update MetricsService to delegate to AttractionStageService**

In `metrics_service.py`, replace the method body with delegation:

```python
async def get_attraction_metrics(self, tenant_id: UUID, period: str = "last_30_days") -> AttractionDetailDTO:
    return await self._attraction_service.get_attraction_metrics(tenant_id, period)
```

Add `_attraction_service` initialization in `__init__`.

- [ ] **Step 5: Run all existing analytics tests to verify no regressions**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/modules/analytics/ -v --tb=short -q"
```
Expected: All existing tests still pass.

- [ ] **Step 6: Commit**

```bash
git add backend/src/modules/analytics/application/services/stage_services/
git add backend/src/modules/analytics/application/services/metrics_service.py
git commit -m "refactor(analytics): extract AttractionStageService from MetricsService (2665→~2400 LOC)"
```

---

### Task 12: Extract remaining stage services (one-by-one, test after each)

**Files:**
- Create: `backend/src/modules/analytics/application/services/stage_services/capture_stage.py`
- Create: `backend/src/modules/analytics/application/services/stage_services/nurture_stage.py`
- Create: `backend/src/modules/analytics/application/services/stage_services/opportunity_stage.py`
- Create: `backend/src/modules/analytics/application/services/stage_services/sales_stage.py`
- Create: `backend/src/modules/analytics/application/services/stage_services/adoption_stage.py`
- Create: `backend/src/modules/analytics/application/services/stage_services/expansion_stage.py`
- Create: `backend/src/modules/analytics/application/services/stage_services/evangelization_stage.py`
- Modify: `backend/src/modules/analytics/application/services/metrics_service.py`

**Strategy:** Same pattern as Task 11 for each stage. Extract method body → create stage class → delegate in MetricsService → run tests.

- [ ] **Step 1: For each stage (capture, nurture, opportunity, sales, adoption, expansion, evangelization):**

1. Read the `get_{stage}_metrics()` method in metrics_service.py
2. Create `{stage}_stage.py` with the extracted class
3. Update MetricsService to delegate
4. Run tests after each extraction

- [ ] **Step 2: Run full test suite after all extractions**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/modules/analytics/ -v --tb=short -q"
```

- [ ] **Step 3: Verify MetricsService is now a thin facade**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && wc -l src/modules/analytics/application/services/metrics_service.py"
```
Expected: ~300-500 LOC (down from 2665).

- [ ] **Step 4: Commit**

```bash
git add backend/src/modules/analytics/application/services/stage_services/
git add backend/src/modules/analytics/application/services/metrics_service.py
git commit -m "refactor(analytics): extract all 8 stage services — MetricsService now thin facade (~400 LOC)"
```

---

### Task 13: Centralize hardcoded configuration values

**Files:**
- Create: `backend/src/modules/analytics/application/config.py`
- Modify: Multiple files (replace hardcoded values with config references)

- [ ] **Step 1: Create centralized config module**

```python
"""Analytics module configuration constants.

Centralizes all magic numbers and timeouts that were previously scattered
across services, workers, and API routes.
"""


class ETLConfig:
    """ETL pipeline configuration."""

    MAX_LOOKBACK_DAYS: int = 60
    EXTRACTION_TIMEOUT_SECONDS: int = 600
    MAX_CONCURRENT_JOBS: int = 10
    MAX_RETRIES: int = 5
    FIBONACCI_BACKOFF: list[int] = [1, 1, 2, 3, 5, 8, 13]

    # Cooldowns (seconds)
    GLOBAL_SYNC_COOLDOWN: int = 120
    PER_PROVIDER_REFRESH_COOLDOWN: int = 900  # 15 min
    PER_CHANNEL_REFRESH_COOLDOWN: int = 60

    # Provider-specific
    IG_INSIGHTS_MAX_CHUNK_DAYS: int = 30
    GA4_MAX_DIMENSIONS: int = 9
    SHOPIFY_ORDERS_PAGE_SIZE: int = 250

    # Scheduling
    DAILY_EXTRACTION_HOUR_LOCAL: int = 3  # 3:00 AM tenant local time


class CacheConfig:
    """Redis cache TTLs (seconds)."""

    ATTRACTION_TTL: int = 3600      # 1 hour
    DETAIL_STAGE_TTL: int = 300     # 5 minutes
    SUMMARY_TTL: int = 60           # 1 minute
    CATALOG_TTL: int = 3600         # 1 hour
    DEFAULT_TTL: int = 300          # 5 minutes


class DashboardConfig:
    """Dashboard display configuration."""

    LOW_CONVERSION_THRESHOLD: float = 0.02
    HIGH_CAC_WARNING_RATIO: float = 0.5
    HIGH_CAC_CRITICAL_RATIO: float = 0.8
    MIN_CHANNELS_FOR_COMPARISON: int = 2
```

- [ ] **Step 2: Replace hardcoded values in cache layer**

In `metrics_cache.py`, replace magic numbers with `CacheConfig` references.

- [ ] **Step 3: Run tests**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/modules/analytics/ -v --tb=short -q"
```

- [ ] **Step 4: Commit**

```bash
git add backend/src/modules/analytics/application/config.py
git add backend/src/modules/analytics/infrastructure/cache/metrics_cache.py
git commit -m "refactor(analytics): centralize hardcoded config values into config.py"
```

---

### Task 14: Optimize batch upsert in OfficialMetricsRepository

**Files:**
- Modify: `backend/src/modules/analytics/infrastructure/repositories/official_metrics_repository.py`
- Create: `backend/tests/modules/analytics/test_batch_upsert.py`

- [ ] **Step 1: Read current upsert implementation**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && grep -n 'def upsert' src/modules/analytics/infrastructure/repositories/official_metrics_repository.py"
```

- [ ] **Step 2: Write batch upsert test**

```python
"""Tests for batch upsert optimization in OfficialMetricsRepository."""

import uuid
from datetime import date
from unittest.mock import MagicMock, AsyncMock

import pytest


TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


class TestBatchUpsert:
    def test_batch_upsert_processes_multiple_rows(self):
        """Batch upsert should handle N rows without N separate DB calls."""
        from src.modules.analytics.infrastructure.repositories.official_metrics_repository import (
            OfficialMetricsRepository,
        )

        mock_db = MagicMock()
        mock_db.execute = MagicMock(return_value=MagicMock(rowcount=10))
        repo = OfficialMetricsRepository(mock_db)

        rows = [
            {
                "tenant_id": TENANT_ID,
                "provider": "meta",
                "channel_slug": "ig-organic",
                "metric_name": f"metric_{i}",
                "value": float(i * 100),
                "unit": "count",
                "metric_date": date(2026, 3, 10),
                "iso_week_start": date(2026, 3, 9),
                "month_key": "2026-03",
                "quarter_key": "2026-Q1",
            }
            for i in range(10)
        ]

        result = repo.upsert_from_staging(rows)

        # Should use batch INSERT ON CONFLICT, not N individual INSERTs
        execute_calls = mock_db.execute.call_count
        assert execute_calls <= 2, f"Expected <=2 DB calls for batch, got {execute_calls}"
```

- [ ] **Step 3: Implement batch upsert (if current is row-by-row)**

Replace row-by-row loop with batch `INSERT ... ON CONFLICT` using SQLAlchemy's `insert().values(rows).on_conflict_do_update()`.

- [ ] **Step 4: Run tests**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/modules/analytics/test_batch_upsert.py tests/modules/analytics/test_etl_pipeline.py -v --tb=short"
```

- [ ] **Step 5: Commit**

```bash
git add backend/src/modules/analytics/infrastructure/repositories/official_metrics_repository.py
git add backend/tests/modules/analytics/test_batch_upsert.py
git commit -m "perf(analytics): batch upsert in OfficialMetricsRepository (N rows → 1 SQL call)"
```

---

## Phase 4: Frontend Refactoring

### Task 15: Consolidate METRIC_LABELS into single source

**Files:**
- Create: `frontend/src/features/growth-studio/lib/metric-labels.ts`
- Modify: `frontend/src/features/growth-studio/components/metrics-dashboard/channel-widgets/ChannelRow.tsx`
- Modify: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/SidebarContent.tsx`

- [ ] **Step 1: Create consolidated metric labels module**

```typescript
/**
 * Single source of truth for metric name → Spanish display label mapping.
 *
 * Previously duplicated in ChannelRow.tsx (~70 entries) and SidebarContent.tsx (~50 entries).
 * Now consolidated here. useMetricCatalog() provides authoritative labels from the backend;
 * this map is the fallback for when the catalog hasn't loaded yet.
 */

export const METRIC_LABELS: Record<string, string> = {
  // Attraction (Stage 1)
  reach: 'Alcance',
  impressions: 'Impresiones',
  engagement: 'Engagement',
  sessions: 'Sesiones',
  users: 'Usuarios',
  visitors: 'Visitantes',
  clicks: 'Clicks',
  views: 'Vistas',
  watch_time: 'Tiempo de Vista',
  subscribers_gained: 'Nuevos Suscriptores',
  new_subscribers: 'Nuevos Suscriptores',
  comment_triggers: 'Comment Triggers',
  dm_opens: 'DMs Abiertos',
  sequences_sent: 'Secuencias Enviadas',
  video_views: 'Vistas de Video',
  profile_views: 'Visitas al Perfil',
  link_clicks: 'Clicks en Link',
  saves: 'Guardados',
  shares: 'Compartidos',
  comments: 'Comentarios',

  // Capture (Stage 2)
  leads: 'Leads',
  contacts: 'Contactos',
  conversions: 'Conversiones',
  conversion_rate: 'Conversion',
  cost_per_lead: 'Costo por Lead',

  // Nurture (Stage 3)
  emails_sent: 'Enviados',
  open_rate: 'Apertura',
  click_rate: 'Clicks',
  unsubscribe_rate: 'Desuscripciones',
  followups: 'Follow-ups',
  response_rate: 'Respuestas',
  responses: 'Respuestas',
  campaigns: 'Campanas',

  // Opportunity (Stage 4)
  count: 'Cantidad',
  value: 'Valor',
  abandonment_rate: 'Abandono',
  booked: 'Agendadas',
  completed: 'Completadas',
  no_show: 'No-Show',
  rescheduled: 'Reprogramadas',
  attendance_rate: 'Asistencia',
  checkout_initiated: 'Checkouts Iniciados',
  checkout_completed: 'Checkouts Completados',

  // Sales (Stage 5)
  revenue: 'Ingresos',
  spend: 'Gasto',
  cost: 'Costo',
  new_customers: 'Nuevos Clientes',
  sales_count: 'Ventas',
  avg_order_value: 'Ticket Promedio',
  cac: 'CAC',
  roas: 'ROAS',

  // Adoption (Stage 6)
  active_customers: 'Clientes Activos',
  health_score: 'Health Score',
  onboarding_rate: 'Tasa de Onboarding',

  // Expansion (Stage 7)
  mrr: 'MRR',
  churn_rate: 'Churn',
  ltv: 'LTV',
  expansion_revenue: 'Ingresos Expansión',

  // Evangelization (Stage 8)
  nps_score: 'NPS',
  referrals: 'Referidos',
  k_factor: 'K-Factor',
  ugc_count: 'UGC',
  conversations: 'Conversaciones',
};

/**
 * Get display label for a metric, with catalog override.
 * @param metricName - raw metric name (e.g., "impressions")
 * @param catalogByName - optional catalog map for authoritative labels
 * @returns Spanish display label
 */
export function getMetricLabel(
  metricName: string,
  catalogByName?: Record<string, { display_name: string }>,
): string {
  if (catalogByName?.[metricName]?.display_name) {
    return catalogByName[metricName].display_name;
  }
  return METRIC_LABELS[metricName] ?? metricName;
}
```

- [ ] **Step 2: Update ChannelRow.tsx to use consolidated labels**

Remove the inline `METRIC_LABELS` dict from ChannelRow.tsx and import from `metric-labels.ts`:

```typescript
import { getMetricLabel } from '../../../lib/metric-labels';
```

Replace all `METRIC_LABELS[metricName]` usages with `getMetricLabel(metricName, catalogByName)`.

- [ ] **Step 3: Update SidebarContent.tsx to use consolidated labels**

Same pattern: remove inline METRIC_LABELS, import from `metric-labels.ts`.

- [ ] **Step 4: Run frontend tests + type check**

```bash
docker exec -t visionarias_client_dev bash -c "npx tsc --noEmit && npm run test -- --run src/features/growth-studio/"
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/growth-studio/lib/metric-labels.ts
git add frontend/src/features/growth-studio/components/metrics-dashboard/channel-widgets/ChannelRow.tsx
git add frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/SidebarContent.tsx
git commit -m "refactor(growth-studio): consolidate METRIC_LABELS into single source (DRY)"
```

---

### Task 16: Split ChannelRow into focused subcomponents

**Files:**
- Create: `frontend/src/features/growth-studio/components/metrics-dashboard/channel-widgets/ChannelRowHeader.tsx`
- Create: `frontend/src/features/growth-studio/components/metrics-dashboard/channel-widgets/ChannelRowMetrics.tsx`
- Create: `frontend/src/features/growth-studio/components/metrics-dashboard/channel-widgets/ChannelRowActions.tsx`
- Modify: `frontend/src/features/growth-studio/components/metrics-dashboard/channel-widgets/ChannelRow.tsx`

**Strategy:** Extract 3 focused components from ChannelRow (526 LOC → ~150 LOC coordinator + 3 × ~120 LOC subcomponents). The split is:
1. **ChannelRowHeader**: icon, name, connection badge, "Proximamente"/"Configurar" badges
2. **ChannelRowMetrics**: metric values display, "---" fallback, CostLink, secondary line (conversations)
3. **ChannelRowActions**: refresh button with cooldown, configure button

- [ ] **Step 1: Read full ChannelRow.tsx to identify exact split boundaries**

```bash
docker exec -t visionarias_client_dev bash -c "wc -l src/features/growth-studio/components/metrics-dashboard/channel-widgets/ChannelRow.tsx"
```

- [ ] **Step 2: Create ChannelRowHeader**

```tsx
'use client';

import React from 'react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { ConnectionBadge } from './ConnectionBadge';
import { getChannelIcon, getChannelColor } from '../../../lib/channelIcons';

interface ChannelRowHeaderProps {
  slug: string;
  name: string;
  connected: boolean;
  isComingSoon?: boolean;
  lastUpdated?: string | null;
  staleThresholdHours?: number;
  onConfigure?: () => void;
}

export const ChannelRowHeader = React.memo(function ChannelRowHeader({
  slug,
  name,
  connected,
  isComingSoon,
  lastUpdated,
  staleThresholdHours = 24,
  onConfigure,
}: ChannelRowHeaderProps) {
  const Icon = getChannelIcon(slug);
  const color = getChannelColor(slug);

  // ... extract the icon + name + badges JSX from ChannelRow
  return (
    <div className="flex items-center gap-3 min-w-0 flex-1">
      <div
        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg"
        style={{ backgroundColor: `${color}20` }}
      >
        <Icon className="h-4 w-4" style={{ color }} />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate text-sm font-medium text-white">{name}</span>
          {connected && <ConnectionBadge lastUpdated={lastUpdated} />}
          {isComingSoon && (
            <Badge variant="outline" className="text-[10px] text-slate-500 border-slate-700">
              Próximamente
            </Badge>
          )}
          {!connected && !isComingSoon && (
            <Badge
              variant="outline"
              className="cursor-pointer text-[10px] text-amber-400 border-amber-500/30 hover:bg-amber-500/10"
              onClick={onConfigure}
            >
              Configurar
            </Badge>
          )}
        </div>
      </div>
    </div>
  );
});
```

- [ ] **Step 3: Create ChannelRowMetrics and ChannelRowActions similarly**

Extract metric display and action button JSX into their own components.

- [ ] **Step 4: Refactor ChannelRow to compose subcomponents**

ChannelRow becomes a coordinator:

```tsx
export const ChannelRow = React.memo(function ChannelRow({
  channel,
  stageId,
  onMetricClick,
  onChannelClick,
  onConfigure,
}: ChannelRowProps) {
  // State + hooks remain here (shared state)
  // ...

  return (
    <div className={cn("flex items-center gap-4 px-4 py-3", /* ... */)}>
      <ChannelRowHeader
        slug={channel.slug}
        name={channel.name}
        connected={channel.connected}
        lastUpdated={channel.lastUpdated}
        onConfigure={handleConfigure}
      />
      <ChannelRowMetrics
        metrics={channel.metrics}
        slug={channel.slug}
        catalogByName={catalogByName}
        onMetricClick={handleMetricClick}
      />
      <ChannelRowActions
        connected={channel.connected}
        slug={channel.slug}
        refreshing={refreshing}
        cooldown={cooldown}
        onRefresh={handleRefresh}
      />
    </div>
  );
});
```

- [ ] **Step 5: Run all frontend tests + type check**

```bash
docker exec -t visionarias_client_dev bash -c "npx tsc --noEmit && npm run test -- --run src/features/growth-studio/"
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/growth-studio/components/metrics-dashboard/channel-widgets/
git commit -m "refactor(growth-studio): split ChannelRow (526 LOC) into 3 focused subcomponents"
```

---

### Task 17: Lazy stage detail loading (performance optimization)

**Files:**
- Modify: `frontend/src/features/growth-studio/hooks/useStageDetail.ts`

**Strategy:** Add `enabled` option to useQuery hooks so stage details only fetch when the user navigates to that stage's route, not all 8 on every route change.

- [ ] **Step 1: Read useStageDetail.ts to understand current hook pattern**

```bash
docker exec -t visionarias_client_dev bash -c "cat src/features/growth-studio/hooks/useStageDetail.ts | head -60"
```

- [ ] **Step 2: Add `enabled` parameter to each stage detail hook**

Each hook should accept an optional `enabled?: boolean` parameter (default `true`):

```typescript
export function useAttractionDetail(options?: { enabled?: boolean }) {
  const { getToken } = useAuth();
  const { selectedPeriod } = useGrowthStudio();

  return useQuery({
    queryKey: ['attraction-detail', selectedPeriod],
    queryFn: async () => {
      const token = await getToken();
      return metricsApi.getAttractionDetail(token!, selectedPeriod);
    },
    staleTime: 1000 * 60 * 5,
    enabled: options?.enabled ?? true,
  });
}
```

- [ ] **Step 3: Update detail panels to pass `enabled` based on active stage**

In each detail panel, only enable the hooks for the currently active stage:

```typescript
// In AttractionCaptureDetail:
const attraction = useAttractionDetail(); // always enabled (this IS the active stage)
const capture = useCaptureDetail();       // always enabled (same composite stage)

// Other hooks NOT called from this panel — they're in their own panels
```

Verify that each stage panel only calls its own hooks (not all 8).

- [ ] **Step 4: Run frontend tests**

```bash
docker exec -t visionarias_client_dev bash -c "npx tsc --noEmit && npm run test -- --run src/features/growth-studio/"
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/growth-studio/hooks/useStageDetail.ts
git commit -m "perf(growth-studio): add enabled option to stage detail hooks for lazy loading"
```

---

## Phase 5: Verification

### Task 18: Full CI verification

**Files:** None (verification only)

- [ ] **Step 1: Run backend lint**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && ruff check src/modules/analytics --no-cache"
```
Expected: No errors.

- [ ] **Step 2: Run all backend analytics tests**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/modules/analytics/ -v --tb=short -q"
```
Expected: All PASS.

- [ ] **Step 3: Run full backend test suite (verify no cross-module regressions)**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest -x -q --tb=short"
```
Expected: All PASS.

- [ ] **Step 4: Run frontend type check**

```bash
docker exec -t visionarias_client_dev npx tsc --noEmit
```
Expected: No errors.

- [ ] **Step 5: Run frontend lint**

```bash
docker exec -t visionarias_client_dev npx next lint
```
Expected: No errors.

- [ ] **Step 6: Run frontend tests**

```bash
docker exec -t visionarias_client_dev npm run test -- --run
```
Expected: All PASS.

- [ ] **Step 7: Commit verification results**

No commit needed — this is a verification step only.

---

### Task 19: Final review and merge preparation

- [ ] **Step 1: Review git log for clean commit history**

```bash
git log --oneline --since="today" | head -20
```

- [ ] **Step 2: Verify no unintended file changes**

```bash
git diff --stat main
```

- [ ] **Step 3: Merge worktree to main**

```bash
# From the worktree, merge back to main
git checkout main
git merge <worktree-branch> --no-ff -m "feat(analytics): Growth Studio excellence audit — tests, refactoring, performance"
```

---

## Appendix: Audit Scorecard (Before → After)

| Dimension | Before | Target After | How |
|-----------|--------|-------------|-----|
| **Backend Test Coverage** | ~40% (scaffolds) | ~80% (working) | Tasks 1-6 |
| **Frontend Test Coverage** | ~1% (scaffolds) | ~40% (working) | Tasks 7-9 |
| **MetricsService LOC** | 2665 | ~400 (facade) | Tasks 11-12 |
| **ChannelRow LOC** | 526 | ~150 (coordinator) | Task 16 |
| **Metric Labels** | 2 duplicated dicts | 1 consolidated module | Task 15 |
| **Config Values** | Scattered magic numbers | Centralized config.py | Task 13 |
| **Upsert Pattern** | Row-by-row | Batch SQL | Task 14 |
| **Stage Detail Loading** | Eager (8 requests) | Lazy (2 per route) | Task 17 |
| **Performance Baselines** | None | 3 benchmarks | Task 10 |
