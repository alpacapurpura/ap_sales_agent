"""Campaigns domain — public exports.

Domain layer: pure Python, no framework dependencies.
All entities, enums, events, and repository interfaces.
"""

from luana_core_campaigns.domain.campaign import Campaign
from luana_core_campaigns.domain.campaign_step import CampaignStep
from luana_core_campaigns.domain.campaign_task import CampaignTask
from luana_core_campaigns.domain.campaign_template import CampaignTemplate
from luana_core_campaigns.domain.channel_router import ChannelRouter, ChannelSendResult
from luana_core_campaigns.domain.enums import (
    CampaignStatus,
    CampaignType,
    SegmentFilterCombinator,
    SegmentType,
    StepType,
    TaskStatus,
)
from luana_core_campaigns.domain.events import (
    CampaignCanceled,
    CampaignCompleted,
    CampaignCreated,
    CampaignLaunched,
    CampaignPaused,
    CampaignScheduled,
    CampaignStepAdded,
    CampaignStepUpdated,
    CampaignTaskDispatched,
    CampaignTaskFailed,
    CampaignTaskQueued,
    CampaignTaskSent,
    SegmentCreated,
    SegmentSnapshotted,
)
from luana_core_campaigns.domain.repositories import (
    CampaignRepository,
    CampaignStepRepository,
    CampaignTaskRepository,
    CampaignTemplateRepository,
    SegmentRepository,
    SegmentSnapshotRepository,
)
from luana_core_campaigns.domain.segment import Segment, SegmentSnapshot
from luana_core_campaigns.domain.segment_filter import (
    DateRange,
    PredefinedSegmentFilter,
    ScoreRange,
    SegmentFilter,
    TagsFilter,
)

__all__ = [
    "Campaign",
    "CampaignCanceled",
    "CampaignCompleted",
    "CampaignCreated",
    "CampaignLaunched",
    "CampaignPaused",
    "CampaignRepository",
    "CampaignScheduled",
    "CampaignStatus",
    "CampaignStep",
    "CampaignStepAdded",
    "CampaignStepRepository",
    "CampaignStepUpdated",
    "CampaignTask",
    "CampaignTaskDispatched",
    "CampaignTaskFailed",
    "CampaignTaskQueued",
    "CampaignTaskRepository",
    "CampaignTaskSent",
    "CampaignTemplate",
    "CampaignTemplateRepository",
    "CampaignType",
    "ChannelRouter",
    "ChannelSendResult",
    "DateRange",
    "PredefinedSegmentFilter",
    "ScoreRange",
    "Segment",
    "SegmentCreated",
    "SegmentFilter",
    "SegmentFilterCombinator",
    "SegmentRepository",
    "SegmentSnapshot",
    "SegmentSnapshotRepository",
    "SegmentSnapshotted",
    "SegmentType",
    "StepType",
    "TagsFilter",
    "TaskStatus",
]
