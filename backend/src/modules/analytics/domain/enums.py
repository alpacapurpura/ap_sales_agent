"""Domain enums for the analytics ETL infrastructure."""

from enum import StrEnum


class CostType(StrEnum):
    """Classifies the financial nature of a metric's associated channel/stage."""

    NEUTRAL = "neutral"
    EXPENSE = "expense"
    INVESTMENT = "investment"
    REVENUE = "revenue"


class MetricUnit(StrEnum):
    """Unit of measurement for a metric value."""

    COUNT = "count"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    RATIO = "ratio"
    SECONDS = "seconds"
    JSON = "json"


class ExtractionStatus(StrEnum):
    """Lifecycle status of an ETL extraction run."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL_SUCCESS = "partial_success"
    RETRYING = "retrying"


class AggregationType(StrEnum):
    """Defines how a metric should be aggregated across time periods."""

    ADDITIVE = "additive"  # SUM seguro (clicks, spend, sessions)
    WEIGHTED_AVERAGE = "weighted_avg"  # Requiere denominador (bounceRate/sessions)
    DERIVED = "derived"  # Recalcular de componentes (CPC = spend/clicks)
    NON_AGGREGABLE = "non_aggregable"  # Solo diario; personas únicas, no summable cross-day
    SNAPSHOT = "snapshot"  # Último valor del período (active_subscribers)


class PeriodType(StrEnum):
    """Time period granularity for metric aggregation and extraction."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    LAST_30_DAYS = "last_30_days"


class ExtractionType(StrEnum):
    """Whether an extraction run covers daily or period-level data."""

    DAILY = "daily"
    PERIOD = "period"
