"""Advertising application services."""

from src.modules.advertising.application.services.campaign_template_service import (
    CampaignTemplateService,
)
from src.modules.advertising.application.services.health_check_service import (
    HealthCheckService,
)
from src.modules.advertising.application.services.metrics_by_offer_service import (
    MetricsByOfferService,
)
from src.modules.advertising.application.services.offer_detection_service import (
    OfferDetectionService,
)

__all__ = [
    "CampaignTemplateService",
    "HealthCheckService",
    "MetricsByOfferService",
    "OfferDetectionService",
]
