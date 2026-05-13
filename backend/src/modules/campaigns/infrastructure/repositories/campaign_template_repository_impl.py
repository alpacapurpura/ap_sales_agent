"""CampaignTemplateRepository SQLAlchemy implementation.

Handles both global templates (tenant_id=NULL) and per-tenant templates.
list_for_tenant returns globals UNION tenant-scoped (UNION semantics in Python,
not SQL, to stay compatible with async session and domain mapping).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from sqlalchemy import or_, select

if TYPE_CHECKING:
    from collections.abc import Sequence
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

from luana_core_campaigns.domain.campaign_template import CampaignTemplate
from luana_core_campaigns.domain.repositories import CampaignTemplateRepository
from luana_core_campaigns.infrastructure.models.campaign_template_model import (
    CampaignTemplateModel,
)

logger = structlog.get_logger()


class CampaignTemplateRepositoryImpl(CampaignTemplateRepository):
    """Async SQLAlchemy 2.0 implementation of CampaignTemplateRepository."""

    async def append(self, tpl: CampaignTemplate, *, session: AsyncSession) -> None:
        """Persist a new CampaignTemplate."""
        row = CampaignTemplateModel(
            id=tpl.id,
            tenant_id=tpl.tenant_id,
            slug=tpl.slug,
            name=tpl.name,
            description=tpl.description,
            campaign_type=tpl.campaign_type.value,
            template_body=tpl.template_body,
            recommended_segment_slugs=tpl.recommended_segment_slugs,
            tags=tpl.tags,
            version=tpl.version,
            created_at=tpl.created_at,
            updated_at=tpl.updated_at,
            deleted_at=tpl.deleted_at,
        )
        session.add(row)
        logger.info(
            "campaign_template_repository_append",
            tenant_id=str(tpl.tenant_id) if tpl.tenant_id else "global",
            template_id=str(tpl.id),
            slug=tpl.slug,
        )

    async def get_by_id(
        self,
        tpl_id: UUID,
        tenant_id: UUID | None,
        *,
        session: AsyncSession,
    ) -> CampaignTemplate | None:
        """Fetch by primary key.

        If tenant_id provided: returns tenant-scoped OR global.
        If tenant_id None: returns global templates only.
        """
        if tenant_id is not None:
            stmt = select(CampaignTemplateModel).where(
                CampaignTemplateModel.id == tpl_id,
                or_(
                    CampaignTemplateModel.tenant_id == tenant_id,
                    CampaignTemplateModel.tenant_id.is_(None),
                ),
                CampaignTemplateModel.deleted_at.is_(None),
            )
        else:
            stmt = select(CampaignTemplateModel).where(
                CampaignTemplateModel.id == tpl_id,
                CampaignTemplateModel.tenant_id.is_(None),
                CampaignTemplateModel.deleted_at.is_(None),
            )
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return CampaignTemplate.model_validate(row)

    async def get_by_slug(
        self,
        slug: str,
        tenant_id: UUID | None,
        *,
        session: AsyncSession,
    ) -> CampaignTemplate | None:
        """Fetch by natural key (slug).

        If tenant_id provided: checks tenant-scoped first, then global.
        If tenant_id None: returns global templates only.
        """
        if tenant_id is not None:
            stmt = (
                select(CampaignTemplateModel)
                .where(
                    CampaignTemplateModel.slug == slug,
                    or_(
                        CampaignTemplateModel.tenant_id == tenant_id,
                        CampaignTemplateModel.tenant_id.is_(None),
                    ),
                    CampaignTemplateModel.deleted_at.is_(None),
                )
                .order_by(CampaignTemplateModel.tenant_id.nulls_last())
                .limit(1)
            )
        else:
            stmt = select(CampaignTemplateModel).where(
                CampaignTemplateModel.slug == slug,
                CampaignTemplateModel.tenant_id.is_(None),
                CampaignTemplateModel.deleted_at.is_(None),
            )
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return CampaignTemplate.model_validate(row)

    async def list_globals(self, *, session: AsyncSession) -> Sequence[CampaignTemplate]:
        """List all global (tenant_id=NULL) templates.

        Cross-tenant: tenant_id=None is semantically correct for global lookup.
        Documented exception — same pattern as CampaignTaskRepository.claim_pending_for_worker.
        """
        stmt = (
            select(CampaignTemplateModel)
            .where(
                CampaignTemplateModel.tenant_id.is_(None),
                CampaignTemplateModel.deleted_at.is_(None),
            )
            .order_by(CampaignTemplateModel.name.asc())
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()
        return [CampaignTemplate.model_validate(row) for row in rows]

    async def list_for_tenant(
        self,
        tenant_id: UUID,
        *,
        session: AsyncSession,
    ) -> Sequence[CampaignTemplate]:
        """Return globals UNION tenant-scoped templates.

        Single query with OR to avoid two round-trips.
        Service PR-4 uses this for 'available templates' view.
        """
        stmt = (
            select(CampaignTemplateModel)
            .where(
                or_(
                    CampaignTemplateModel.tenant_id == tenant_id,
                    CampaignTemplateModel.tenant_id.is_(None),
                ),
                CampaignTemplateModel.deleted_at.is_(None),
            )
            .order_by(
                CampaignTemplateModel.tenant_id.nulls_first(),
                CampaignTemplateModel.name.asc(),
            )
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()
        return [CampaignTemplate.model_validate(row) for row in rows]
