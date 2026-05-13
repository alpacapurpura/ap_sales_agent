"""Analytics ETL infrastructure models.

All models are imported here so Alembic autogenerate can detect them.
"""

from luana_core_analytics_engine.infrastructure.models.ad_campaign_model import (
    AdCampaignModel,
)
from luana_core_analytics_engine.infrastructure.models.ad_model import (
    AdModel,
)
from luana_core_analytics_engine.infrastructure.models.ad_recommendation_model import (
    AdRecommendationModel,
)
from luana_core_analytics_engine.infrastructure.models.ad_set_model import (
    AdSetModel,
)
from luana_core_analytics_engine.infrastructure.models.channel_cost_model import (
    ChannelCostSettingModel,
)
from luana_core_analytics_engine.infrastructure.models.extraction_run_model import (
    ExtractionRunModel,
)
from luana_core_analytics_engine.infrastructure.models.metric_aggregation_model import (
    MetricAggregationModel,
)
from luana_core_analytics_engine.infrastructure.models.official_metrics_model import (
    OfficialMetricModel,
)
from luana_core_analytics_engine.infrastructure.models.period_metrics_model import (
    PeriodMetricModel,
)
from luana_core_analytics_engine.infrastructure.models.staging_metrics_model import (
    StagingMetricModel,
)

__all__ = [
    "AdCampaignModel",
    "AdModel",
    "AdRecommendationModel",
    "AdSetModel",
    "ChannelCostSettingModel",
    "ExtractionRunModel",
    "MetricAggregationModel",
    "OfficialMetricModel",
    "PeriodMetricModel",
    "StagingMetricModel",
]
