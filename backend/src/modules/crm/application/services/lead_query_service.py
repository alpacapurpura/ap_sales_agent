"""LeadQueryServiceImpl — async SQL-side filtering for segment resolution.

Implements the LeadQueryPort protocol consumed by campaigns.SegmentService.
Uses AsyncSession + SQLA 2.0. Never loads lead objects in Python (SQL-side only).

Note: existing LeadService uses sync Session (legacy). This service is
new async path for campaigns module. CRM full sync→async migration is post-PI-1.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from sqlalchemy import func, select

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy import Boolean, ColumnElement
    from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.models.crm import LeadModel

logger = structlog.get_logger(__name__)


class LeadQueryServiceImpl:
    """Async lead query service for segment resolution.

    Implements LeadQueryPort protocol.
    SQL-side filtering — NEVER iterates leads in Python.
    """

    async def list_lead_ids_matching(
        self,
        *,
        tenant_id: UUID,
        predicate: ColumnElement[Boolean],
        limit: int,
        session: AsyncSession,
    ) -> tuple[list[UUID], int]:
        """Return (lead_ids ordered by id, total_count).

        Uses two queries: count (total) + select (capped list).
        total_count reflects ALL matching leads (truncation signal for caller).
        """
        base_filter = (
            LeadModel.tenant_id == tenant_id,
            LeadModel.deleted_at.is_(None),
            predicate,
        )

        # Count total matching
        count_stmt = select(func.count(LeadModel.id)).where(*base_filter)
        count_result = await session.execute(count_stmt)
        total = count_result.scalar_one()

        # Fetch capped list
        select_stmt = select(LeadModel.id).where(*base_filter).order_by(LeadModel.id.asc()).limit(limit)
        select_result = await session.execute(select_stmt)
        lead_ids = list(select_result.scalars().all())

        logger.info(
            "lead_query_service_list_matching",
            tenant_id=str(tenant_id),
            total=total,
            returned=len(lead_ids),
            capped=(total > limit),
        )
        return lead_ids, total

    async def count_leads_matching(
        self,
        *,
        tenant_id: UUID,
        predicate: ColumnElement[Boolean],
        session: AsyncSession,
    ) -> int:
        """Return count of leads matching the predicate for the tenant."""
        stmt = select(func.count(LeadModel.id)).where(
            LeadModel.tenant_id == tenant_id,
            LeadModel.deleted_at.is_(None),
            predicate,
        )
        result = await session.execute(stmt)
        count: int = result.scalar_one()
        return count
