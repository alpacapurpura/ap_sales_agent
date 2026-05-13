"""SQLAlchemy 2.0 async implementation of OptInRepository — PM Q2.

DB-backed per-channel consent tracking. tenant_id mandatory in all methods.

PR-2 / PI-1 S0.
"""

from __future__ import annotations

import datetime as dt
import uuid as uuid_mod
from uuid import UUID

import structlog
from luana_core_compliance.domain.lead_opt_in import LeadOptIn, OptInSource
from luana_core_compliance.domain.opt_in_repository import OptInRepository
from luana_core_compliance.infrastructure.models.lead_opt_in_model import LeadOptInModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

logger = structlog.get_logger(__name__)


def _model_to_vo(m: LeadOptInModel) -> LeadOptIn:
    """Map ORM row to immutable VO."""
    return LeadOptIn(
        id=m.id,
        tenant_id=m.tenant_id,
        lead_id=m.lead_id,
        channel=m.channel,
        opted_in_at=m.opted_in_at,
        opted_out_at=m.opted_out_at,
        source=m.source,  # type: ignore[arg-type]
        evidence=m.evidence or {},
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class SQLAOptInRepository(OptInRepository):
    """SQLAlchemy 2.0 async implementation of OptInRepository.

    PM Q2: reads lead_opt_ins table (not messages heuristic).
    """

    def __init__(self, session: AsyncSession) -> None:
        """Bind repository to async session."""
        self._session = session

    async def has_active_opt_in(self, tenant_id: UUID, lead_id: UUID, channel: str) -> bool:
        """Return True iff opted_in_at NOT NULL AND opted_out_at IS NULL."""
        stmt = select(LeadOptInModel.id).where(
            LeadOptInModel.tenant_id == tenant_id,
            LeadOptInModel.lead_id == lead_id,
            LeadOptInModel.channel == channel,
            LeadOptInModel.opted_in_at.is_not(None),
            LeadOptInModel.opted_out_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get(self, tenant_id: UUID, lead_id: UUID, channel: str) -> LeadOptIn | None:
        """Return opt-in record or None. tenant_id mandatory."""
        stmt = select(LeadOptInModel).where(
            LeadOptInModel.tenant_id == tenant_id,
            LeadOptInModel.lead_id == lead_id,
            LeadOptInModel.channel == channel,
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _model_to_vo(row) if row else None

    async def upsert(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        channel: str,
        opted_in_at: dt.datetime | None,
        opted_out_at: dt.datetime | None,
        source: OptInSource,
        evidence: dict,
    ) -> LeadOptIn:
        """ON CONFLICT (tenant_id, lead_id, channel) DO UPDATE — idempotent."""
        existing_result = await self._session.execute(
            select(LeadOptInModel).where(
                LeadOptInModel.tenant_id == tenant_id,
                LeadOptInModel.lead_id == lead_id,
                LeadOptInModel.channel == channel,
            )
        )
        existing = existing_result.scalar_one_or_none()
        now = dt.datetime.now(dt.timezone.utc)
        if existing:
            await self._session.execute(
                update(LeadOptInModel)
                .where(LeadOptInModel.id == existing.id)
                .values(
                    opted_in_at=opted_in_at,
                    opted_out_at=opted_out_at,
                    source=source,
                    evidence=evidence,
                    updated_at=func.now(),
                )
            )
            await self._session.flush()
            refreshed_result = await self._session.execute(
                select(LeadOptInModel).where(LeadOptInModel.id == existing.id)
            )
            return _model_to_vo(refreshed_result.scalar_one())
        model = LeadOptInModel(
            id=uuid_mod.uuid4(),
            tenant_id=tenant_id,
            lead_id=lead_id,
            channel=channel,
            opted_in_at=opted_in_at,
            opted_out_at=opted_out_at,
            source=source,
            evidence=evidence,
            created_at=now,
            updated_at=now,
        )
        self._session.add(model)
        await self._session.flush()
        return _model_to_vo(model)

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        channel: str | None = None,
        active_only: bool = True,
    ) -> list[LeadOptIn]:
        """Return opt-in records for tenant."""
        conditions = [LeadOptInModel.tenant_id == tenant_id]
        if channel is not None:
            conditions.append(LeadOptInModel.channel == channel)
        if active_only:
            conditions.append(LeadOptInModel.opted_in_at.is_not(None))
            conditions.append(LeadOptInModel.opted_out_at.is_(None))
        stmt = select(LeadOptInModel).where(*conditions)
        result = await self._session.execute(stmt)
        return [_model_to_vo(r) for r in result.scalars().all()]
