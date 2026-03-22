"""Domain enums for the analytics ETL infrastructure."""

from enum import Enum


class CostType(str, Enum):
    """Classifies the financial nature of a metric's associated channel/stage."""

    NEUTRAL = "neutral"
    EXPENSE = "expense"
    INVESTMENT = "investment"
    REVENUE = "revenue"


class MetricUnit(str, Enum):
    """Unit of measurement for a metric value."""

    COUNT = "count"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    RATIO = "ratio"


class ExtractionStatus(str, Enum):
    """Lifecycle status of an ETL extraction run."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
