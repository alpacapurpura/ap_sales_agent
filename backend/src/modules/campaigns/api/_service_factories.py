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
    from src.modules.campaigns.application.segment_filter_evaluator import (
        SegmentFilterEvaluator,
    )
    from src.modules.crm.application.services.lead_query_service import (
        LeadQueryServiceImpl,
    )

    return SegmentService(
        repo=SegmentRepositoryImpl(),
        snapshot_repo=SegmentSnapshotRepositoryImpl(),
        lead_query_port=LeadQueryServiceImpl(),  # type: ignore[arg-type]
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


async def get_campaign_stats_service(
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
) -> object:
    """FastAPI dependency que construye CampaignStatsService para una request."""
    from src.modules.campaigns.application.services.campaign_stats_service import (
        CampaignStatsService,
    )
    from src.modules.campaigns.infrastructure.repositories.campaign_task_repository_impl import (
        CampaignTaskRepositoryImpl,
    )
    from src.shared.domain.locale import TenantLocale

    async def _get_locale(tenant_id: object) -> TenantLocale:
        """Resuelve TenantLocale de forma async (Lee config_json del TenantModel)."""
        from sqlalchemy import select

        try:
            from src.modules.iam.infrastructure.models.tenant_model import TenantModel

            row = (await session.execute(select(TenantModel).where(TenantModel.id == tenant_id))).scalar_one_or_none()
            if row is not None:
                raw = (row.config_json or {}).get("tenant_locale")
                if isinstance(raw, dict):
                    return TenantLocale(
                        currency=raw.get("currency") or TenantLocale.default().currency,
                        timezone=raw.get("timezone") or TenantLocale.default().timezone,
                    )
        except Exception:  # noqa: BLE001 — graceful degradation
            pass
        return TenantLocale.default()

    return CampaignStatsService(
        campaign_repo=CampaignRepositoryImpl(),
        task_repo=CampaignTaskRepositoryImpl(),
        get_locale=_get_locale,
    )


def _get_audit_log_service() -> object:
    """Lazy factory for AuditLogService."""
    from src.modules.campaigns.application.services.audit_log_service import AuditLogService
    from src.modules.campaigns.infrastructure.repositories.audit_log_repo_impl import (
        AuditLogRepositoryImpl,
    )

    return AuditLogService(repo=AuditLogRepositoryImpl())


async def _arq_pool_provider() -> object:
    """Lazy async factory for ARQ Redis pool.

    Uses app-level REDIS_URL (same pattern as scheduler_tick._arq_pool_provider_fn)
    to create an ARQ-compatible pool. Fallback: None → scheduler_tick picks up tasks.
    """
    try:
        from arq import create_pool
        from arq.connections import RedisSettings

        from src.core.config import settings as app_settings

        return await create_pool(RedisSettings.from_dsn(app_settings.REDIS_URL))
    except Exception:  # noqa: BLE001
        # Best-effort: if arq pool unavailable, scheduler_tick picks up pending tasks.
        logger.warning("arq_pool_provider_unavailable_in_api_factory")
        return None


async def get_campaign_orchestrator(
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
) -> object:
    """FastAPI dependency that builds a CampaignOrchestrator for a request."""
    from src.modules.campaigns.application.segment_filter_evaluator import (
        SegmentFilterEvaluator,
    )
    from src.modules.campaigns.application.services.orchestrator import CampaignOrchestrator
    from src.modules.campaigns.infrastructure.repositories.campaign_task_repository_impl import (
        CampaignTaskRepositoryImpl,
    )
    from src.modules.crm.application.services.lead_query_service import (
        LeadQueryServiceImpl,
    )

    return CampaignOrchestrator(
        campaign_repo=CampaignRepositoryImpl(),
        step_repo=CampaignStepRepositoryImpl(),
        task_repo=CampaignTaskRepositoryImpl(),
        segment_service=SegmentService(
            repo=SegmentRepositoryImpl(),
            snapshot_repo=SegmentSnapshotRepositoryImpl(),
            lead_query_port=LeadQueryServiceImpl(),  # type: ignore[arg-type]
            filter_evaluator=SegmentFilterEvaluator(),
            outbox_service=_get_outbox_service(),  # type: ignore[arg-type]
            cache=_campaign_cache,
        ),
        outbox_service=_get_outbox_service(),  # type: ignore[arg-type]
        audit_log_service=_get_audit_log_service(),  # type: ignore[arg-type]
        arq_pool_provider=_arq_pool_provider,
    )
