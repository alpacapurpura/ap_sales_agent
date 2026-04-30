"""Campaigns API service factories — FastAPI dependency constructors.

Builds service objects (CampaignService, SegmentService, CampaignTemplateService)
from live async repositories + shared infrastructure.
Keeps routers thin: router calls factory dep → gets service → calls service.
"""

from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.campaigns.api._async_session import get_campaigns_async_session
from src.modules.campaigns.application.services.cache import SimpleTTLCache
from src.modules.campaigns.application.services.campaign_service import CampaignService
from src.modules.campaigns.application.services.campaign_template_service import (
    CampaignTemplateService,
)
from src.modules.campaigns.application.services.segment_service import SegmentService
from src.modules.campaigns.infrastructure.repositories.campaign_repository_impl import (
    CampaignRepositoryImpl,
)
from src.modules.campaigns.infrastructure.repositories.campaign_step_repository_impl import (
    CampaignStepRepositoryImpl,
)
from src.modules.campaigns.infrastructure.repositories.campaign_template_repository_impl import (
    CampaignTemplateRepositoryImpl,
)
from src.modules.campaigns.infrastructure.repositories.segment_repository_impl import (
    SegmentRepositoryImpl,
)
from src.modules.campaigns.infrastructure.repositories.segment_snapshot_repository_impl import (
    SegmentSnapshotRepositoryImpl,
)

logger = structlog.get_logger(__name__)

# ── Module-level singletons ───────────────────────────────────────────────────
# Cache is shared per-process (mirrors PlanService PR-2 pattern).
_campaign_cache = SimpleTTLCache(max_entries=4096)
_template_cache = SimpleTTLCache(max_entries=1024)


def _get_plan_service() -> object:
    """Lazy factory for PlanService with async repos."""
    from src.core.database import redis_client
    from src.modules.campaigns.api._async_session import _AsyncSessionLocal
    from src.shared.billing.application.plan_service import PlanService
    from src.shared.billing.infrastructure.plan_repository_impl import SQLAPlanRepository
    from src.shared.billing.infrastructure.subscription_repository_impl import (
        SQLASubscriptionRepository,
    )

    async_session = _AsyncSessionLocal()

    return PlanService(
        plan_repo=SQLAPlanRepository(async_session),
        subscription_repo=SQLASubscriptionRepository(async_session),
        redis_client=redis_client,
    )


def _get_outbox_service() -> object:
    """Lazy factory for OutboxService."""
    from src.shared.domain_events.outbox.application.outbox_service import OutboxService
    from src.shared.domain_events.outbox.infrastructure.repository import (
        OutboxRepositoryImpl,
    )

    return OutboxService(repo=OutboxRepositoryImpl())


# ── Dependency factories ───────────────────────────────────────────────────────


async def get_campaign_service(
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
) -> CampaignService:
    """FastAPI dependency that builds a CampaignService for a request."""
    return CampaignService(
        repo=CampaignRepositoryImpl(),
        step_repo=CampaignStepRepositoryImpl(),
        segment_repo=SegmentRepositoryImpl(),
        plan_service=_get_plan_service(),  # type: ignore[arg-type]
        outbox_service=_get_outbox_service(),  # type: ignore[arg-type]
        cache=_campaign_cache,
    )


async def get_segment_service(
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
) -> SegmentService:
    """FastAPI dependency that builds a SegmentService for a request."""
    from src.modules.crm.infrastructure.repositories.lead_query_port_impl import (
        LeadQueryPortImpl,
    )

    from src.modules.campaigns.application.segment_filter_evaluator import (
        SegmentFilterEvaluator,
    )

    return SegmentService(
        repo=SegmentRepositoryImpl(),
        snapshot_repo=SegmentSnapshotRepositoryImpl(),
        lead_query_port=LeadQueryPortImpl(),  # type: ignore[arg-type]
        filter_evaluator=SegmentFilterEvaluator(),
        outbox_service=_get_outbox_service(),  # type: ignore[arg-type]
        cache=_campaign_cache,
    )


async def get_template_service(
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
) -> CampaignTemplateService:
    """FastAPI dependency that builds a CampaignTemplateService for a request."""
    campaign_svc = await get_campaign_service(session)
    return CampaignTemplateService(
        repo=CampaignTemplateRepositoryImpl(),
        campaign_service=campaign_svc,
        cache=_template_cache,
    )
