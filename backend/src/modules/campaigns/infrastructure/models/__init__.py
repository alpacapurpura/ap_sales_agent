"""Campaign SQLAlchemy models — registers all models with Base metadata."""

from src.modules.campaigns.infrastructure.models.campaign_model import CampaignModel
from src.modules.campaigns.infrastructure.models.campaign_step_model import CampaignStepModel
from src.modules.campaigns.infrastructure.models.campaign_task_model import CampaignTaskModel
from src.modules.campaigns.infrastructure.models.campaign_template_model import CampaignTemplateModel
from src.modules.campaigns.infrastructure.models.segment_model import SegmentModel
from src.modules.campaigns.infrastructure.models.segment_snapshot_model import SegmentSnapshotModel

__all__ = [
    "CampaignModel",
    "CampaignStepModel",
    "CampaignTaskModel",
    "CampaignTemplateModel",
    "SegmentModel",
    "SegmentSnapshotModel",
]
