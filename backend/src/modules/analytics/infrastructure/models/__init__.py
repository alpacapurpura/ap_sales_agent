"""Analytics ETL infrastructure models.

All models are imported here so Alembic autogenerate can detect them.
"""

from src.modules.analytics.infrastructure.models.staging_metrics_model import (
    StagingMetricModel,
)
from src.modules.analytics.infrastructure.models.official_metrics_model import (
    OfficialMetricModel,
)
from src.modules.analytics.infrastructure.models.extraction_run_model import (
    ExtractionRunModel,
)
from src.modules.analytics.infrastructure.models.metric_aggregation_model import (
    MetricAggregationModel,
)

__all__ = [
    "StagingMetricModel",
    "OfficialMetricModel",
    "ExtractionRunModel",
    "MetricAggregationModel",
]
