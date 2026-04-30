"""LeadQueryPort — Protocol consumed by SegmentService.

DDD boundary: campaigns module does NOT import crm models or services directly.
CRM module implements this protocol. Protocol keeps DDD boundaries.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy import Boolean, ColumnElement
    from sqlalchemy.ext.asyncio import AsyncSession


class LeadQueryPort(Protocol):
    """Port consumed by SegmentService. Implementation in crm module.

    Protocol keeps DDD boundaries — campaigns module never imports
    LeadModel or CRM services directly.
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

        Total count reflects ALL matching leads (not just capped list).
        Caller detects truncation: truncated = total_count > limit.
        """
        ...

    async def count_leads_matching(
        self,
        *,
        tenant_id: UUID,
        predicate: ColumnElement[Boolean],
        session: AsyncSession,
    ) -> int:
        """Return count of leads matching the predicate for the tenant."""
        ...
