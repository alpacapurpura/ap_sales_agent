"""Campaign SQLAlchemy models — registers all models with Base metadata."""

from luana_core_campaigns.infrastructure.models.campaign_model import CampaignModel
from luana_core_campaigns.infrastructure.models.campaign_step_model import CampaignStepModel
from luana_core_campaigns.infrastructure.models.campaign_task_model import CampaignTaskModel
from luana_core_campaigns.infrastructure.models.campaign_template_model import CampaignTemplateModel
from luana_core_campaigns.infrastructure.models.segment_model import SegmentModel
from luana_core_campaigns.infrastructure.models.segment_snapshot_model import SegmentSnapshotModel

__all__ = [
    "CampaignModel",
    "CampaignStepModel",
    "CampaignTaskModel",
    "CampaignTemplateModel",
    "SegmentModel",
    "SegmentSnapshotModel",
]
