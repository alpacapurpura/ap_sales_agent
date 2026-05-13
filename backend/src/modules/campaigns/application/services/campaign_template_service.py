"""CampaignTemplateService — globals + tenant-scoped templates + clone_to_campaign.

PR-4: seeds 5 global templates via migration 112.
Service: list_available + get + clone_to_campaign (atomic TX).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

import structlog
from luana_core_campaigns.domain.enums import StepType
from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from luana_core_campaigns.application.dtos.campaign_template_dtos import (
        CampaignCreateFromTemplate,
    )
    from luana_core_campaigns.application.services.cache import CacheBackend
    from luana_core_campaigns.application.services.campaign_service import CampaignService
    from luana_core_campaigns.domain.campaign import Campaign
    from luana_core_campaigns.domain.campaign_template import CampaignTemplate
    from luana_core_campaigns.domain.repositories import CampaignTemplateRepository
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


class CampaignTemplateNotFoundError(Exception):
    """Raised when template not found (→ 404)."""


# ── Internal Pydantic validators for template_body JSONB ──────────────────────


class CampaignTemplateStepBody(BaseModel):
    """Validated step inside template_body.steps. Indexes resolved to UUIDs on clone."""

    model_config = ConfigDict(extra="forbid")

    step_type: StepType
    step_index: int = Field(..., ge=0)
    label: str | None = Field(default=None, max_length=128)
    next_step_indexes: list[int] = Field(
        default_factory=list,
        description="Índices ref a otros steps (no UUIDs — instanciados en clone).",
    )
    step_config: dict[str, Any] = Field(default_factory=dict)


class CampaignTemplateBody(BaseModel):
    """Validator for template_body JSONB. NOT exposed in response (only dict[str, Any])."""

    model_config = ConfigDict(extra="forbid")

    description_internal: str | None = None
    suggested_channel_priority: list[str] = Field(default_factory=list)
    config_defaults: dict[str, Any] = Field(default_factory=dict)
    steps: list[CampaignTemplateStepBody] = Field(default_factory=list)


# ── Service ────────────────────────────────────────────────────────────────────


class CampaignTemplateService:
    """CRUD globals (cross-tenant read) + tenant-scoped + clone_to_campaign transactional."""

    LIST_CACHE_TTL = 300  # 5min

    def __init__(
        self,
        *,
        repo: CampaignTemplateRepository,
        campaign_service: CampaignService,
        cache: CacheBackend,
    ) -> None:
        """Initialize with repos and collaborators."""
        self._repo = repo
        self._campaign_service = campaign_service
        self._cache = cache

    async def list_available(
        self,
        tenant_id: UUID,
        *,
        session: AsyncSession,
    ) -> list[CampaignTemplate]:
        """Return globals UNION tenant-scoped templates. Cached 5min."""
        cache_key = f"templates:available:{tenant_id}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            logger.info(
                "campaign_template_service_list_cache_hit",
                tenant_id=str(tenant_id),
            )
            return cached  # type: ignore[no-any-return]  # cache stores list[CampaignTemplate]; Any from cache.get()
        templates = list(await self._repo.list_for_tenant(tenant_id, session=session))
        await self._cache.set(cache_key, templates, ttl=self.LIST_CACHE_TTL)
        return templates

    async def get(
        self,
        tenant_id: UUID,
        template_id: UUID,
        *,
        session: AsyncSession,
    ) -> CampaignTemplate:
        """Lookup tenant-scoped first; falls back to global. Raises 404 if not found."""
        tpl = await self._repo.get_by_id(template_id, tenant_id, session=session)
        if tpl is None or tpl.deleted_at is not None:
            raise CampaignTemplateNotFoundError(str(template_id))
        return tpl

    async def clone_to_campaign(
        self,
        tenant_id: UUID,
        template_id: UUID,
        dto: CampaignCreateFromTemplate,
        *,
        session: AsyncSession,
        user_id: UUID | None = None,
    ) -> Campaign:
        """Atomic clone: instantiate Campaign + N CampaignSteps in single TX.

        Body validation:
        - Parses template.template_body → CampaignTemplateBody (Pydantic strict)
        - Resolves next_step_indexes → next_step_ids: list[UUID]
        - Applies dto.config_overrides on top of template body config_defaults

        If dto.scheduled_for provided → calls schedule() inline post-create.
        """
        from uuid import uuid4

        from luana_core_campaigns.application.dtos.campaign_dtos import CampaignCreate
        from luana_core_campaigns.application.dtos.campaign_step_dtos import CampaignStepCreate

        # 1. Load template (raises 404 if not found)
        tpl = await self.get(tenant_id, template_id, session=session)

        # 2. Parse + validate template body
        body = CampaignTemplateBody.model_validate(tpl.template_body)

        # 3. Build Campaign
        merged_config = {**body.config_defaults, **dto.config_overrides}
        campaign = await self._campaign_service.create(
            tenant_id,
            CampaignCreate(
                name=dto.name,
                description=dto.description,
                campaign_type=tpl.campaign_type,
                segment_id=dto.segment_id,
                channel_priority=body.suggested_channel_priority,
                offer_id=dto.offer_id,
                config=merged_config,
                created_by_source="api",
            ),
            session=session,
            user_id=user_id,
        )

        # 4. Build steps with index→UUID mapping
        index_to_id: dict[int, UUID] = {step_body.step_index: uuid4() for step_body in body.steps}
        for step_body in body.steps:
            next_ids = [index_to_id[idx] for idx in step_body.next_step_indexes if idx in index_to_id]
            await self._campaign_service.add_step(
                tenant_id,
                campaign.id,
                CampaignStepCreate(
                    step_type=step_body.step_type,
                    step_index=step_body.step_index,
                    label=step_body.label,
                    next_step_ids=next_ids,
                    step_config=step_body.step_config,
                ),
                session=session,
            )

        # 5. Optional schedule
        if dto.scheduled_for is not None:
            campaign = await self._campaign_service.schedule(
                tenant_id,
                campaign.id,
                dto.scheduled_for,
                session=session,
            )

        logger.info(
            "campaign_template_service_clone",
            tenant_id=str(tenant_id),
            template_id=str(template_id),
            campaign_id=str(campaign.id),
            steps_count=len(body.steps),
        )
        return campaign
