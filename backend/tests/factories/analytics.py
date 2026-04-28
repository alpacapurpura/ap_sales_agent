"""Factory-boy factories for analytics ORM models."""

import uuid
from datetime import date, datetime, timezone

import factory

from src.modules.analytics.infrastructure.models.extraction_run_model import (
    ExtractionRunModel,
)
from src.modules.analytics.infrastructure.models.metric_aggregation_model import (
    MetricAggregationModel,
)
from src.modules.analytics.infrastructure.models.official_metrics_model import (
    OfficialMetricModel,
)
from src.modules.analytics.infrastructure.models.period_metrics_model import (
    PeriodMetricModel,
)

_TENANT = uuid.UUID("11111111-1111-1111-1111-111111111111")


class OfficialMetricFactory(factory.Factory):
    class Meta:
        model = OfficialMetricModel

    id = factory.LazyFunction(uuid.uuid4)
    tenant_id = _TENANT
    provider = "meta"
    channel_slug = "meta-ads"
    metric_name = "impressions"
    value = factory.Sequence(lambda n: float(1000 + n * 100))
    unit = "count"
    currency = None
    cost_type = "investment"
    metric_date = factory.LazyFunction(lambda: date(2026, 3, 10))
    spend = None
    revenue = None
    campaign_id = None
    ad_set_id = None
    ad_id = None
    extra = {}
    source_extraction_run_id = None
    iso_week_start = None
    month_key = None
    quarter_key = None


class ExtractionRunFactory(factory.Factory):
    class Meta:
        model = ExtractionRunModel

    id = factory.LazyFunction(uuid.uuid4)
    tenant_id = _TENANT
    provider = "meta"
    status = "success"
    started_at = factory.LazyFunction(lambda: datetime(2026, 3, 10, 8, 0, 0, tzinfo=timezone.utc))
    completed_at = factory.LazyFunction(lambda: datetime(2026, 3, 10, 8, 1, 30, tzinfo=timezone.utc))
    error = None
    metrics_count = 10
    duration_seconds = 90.0
    rows_extracted = 10
    rate_limit_headroom = None
    sub_extractor_failures = []
    extraction_type = "daily"
    period_start = None
    period_end = None


class PeriodMetricFactory(factory.Factory):
    class Meta:
        model = PeriodMetricModel

    id = factory.LazyFunction(uuid.uuid4)
    tenant_id = _TENANT
    provider = "meta"
    channel_slug = "meta-ads"
    metric_name = "reach"
    value = factory.Sequence(lambda n: float(5000 + n * 500))
    unit = "count"
    currency = None
    period_type = "weekly"
    period_start = factory.LazyFunction(lambda: date(2026, 3, 3))
    period_end = factory.LazyFunction(lambda: date(2026, 3, 9))
    campaign_id = None
    ad_set_id = None
    ad_id = None
    cost_type = None
    extra = {}
    source_extraction_run_id = None


class MetricAggregationFactory(factory.Factory):
    class Meta:
        model = MetricAggregationModel

    id = factory.LazyFunction(uuid.uuid4)
    tenant_id = _TENANT
    channel_slug = "meta-ads"
    metric_name = "impressions"
    period_type = "weekly"
    period_start = factory.LazyFunction(lambda: date(2026, 3, 3))
    period_end = factory.LazyFunction(lambda: date(2026, 3, 9))
    value = factory.Sequence(lambda n: float(7000 + n * 500))
    unit = "count"
    currency = None
    cost_type = "investment"
    extraction_run_id = None
