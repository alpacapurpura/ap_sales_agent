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
from src.modules.analytics.infrastructure.models.channel_cost_model import (
    ChannelCostSettingModel,
)
from src.modules.analytics.infrastructure.models.ad_campaign_model import (
    AdCampaignModel,
)
from src.modules.analytics.infrastructure.models.ad_set_model import (
    AdSetModel,
)
from src.modules.analytics.infrastructure.models.ad_model import (
    AdModel,
)
from src.modules.analytics.infrastructure.models.ad_recommendation_model import (
    AdRecommendationModel,
)

__all__ = [
    "StagingMetricModel",
    "OfficialMetricModel",
    "ExtractionRunModel",
    "MetricAggregationModel",
    "ChannelCostSettingModel",
    "AdCampaignModel",
    "AdSetModel",
    "AdModel",
    "AdRecommendationModel",
]
