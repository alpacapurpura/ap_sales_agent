"""SQLAlchemy 2.0 async implementation of ChannelBlacklistRepository.

PR-2 / PI-1 S0.
"""

from __future__ import annotations

from uuid import UUID

import structlog
from luana_core_compliance.domain.blacklist_entry import ChannelBlacklistEntry
from luana_core_compliance.domain.blacklist_repository import ChannelBlacklistRepository
from luana_core_compliance.infrastructure.models.channel_blacklist_model import (
    ChannelBlacklistModel,
)
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

logger = structlog.get_logger(__name__)


def _model_to_vo(m: ChannelBlacklistModel) -> ChannelBlacklistEntry:
    """Map ORM row to immutable VO."""
    return ChannelBlacklistEntry(
        id=m.id,
        tenant_id=m.tenant_id,
        channel=m.channel,
        identifier=m.identifier,
        reason=m.reason,
        created_by_user_id=m.created_by_user_id,
        created_at=m.created_at,
        deleted_at=m.deleted_at,
    )


class SQLABlacklistRepository(ChannelBlacklistRepository):
    """SQLAlchemy 2.0 async implementation of ChannelBlacklistRepository."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind repository to async session."""
        self._session = session

    async def is_blacklisted(self, tenant_id: UUID, channel: str, identifier: str) -> bool:
        """Return True iff active blacklist entry exists. tenant_id mandatory."""
        stmt = select(ChannelBlacklistModel.id).where(
            ChannelBlacklistModel.tenant_id == tenant_id,
            ChannelBlacklistModel.channel == channel,
            ChannelBlacklistModel.identifier == identifier,
            ChannelBlacklistModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        channel: str | None = None,
    ) -> list[ChannelBlacklistEntry]:
        """Return active entries for tenant. Optionally filter by channel."""
        conditions = [
            ChannelBlacklistModel.tenant_id == tenant_id,
            ChannelBlacklistModel.deleted_at.is_(None),
        ]
        if channel is not None:
            conditions.append(ChannelBlacklistModel.channel == channel)
        stmt = select(ChannelBlacklistModel).where(*conditions)
        result = await self._session.execute(stmt)
        return [_model_to_vo(r) for r in result.scalars().all()]

    async def upsert(self, entry: ChannelBlacklistEntry) -> ChannelBlacklistEntry:
        """Create or restore blacklist entry. ON CONFLICT updates reason/deleted_at."""
        existing_result = await self._session.execute(
            select(ChannelBlacklistModel).where(
                ChannelBlacklistModel.tenant_id == entry.tenant_id,
                ChannelBlacklistModel.channel == entry.channel,
                ChannelBlacklistModel.identifier == entry.identifier,
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            await self._session.execute(
                update(ChannelBlacklistModel)
                .where(ChannelBlacklistModel.id == existing.id)
                .values(reason=entry.reason, deleted_at=None)
            )
            await self._session.flush()
            refreshed_result = await self._session.execute(
                select(ChannelBlacklistModel).where(ChannelBlacklistModel.id == existing.id)
            )
            refreshed = refreshed_result.scalar_one()
            return _model_to_vo(refreshed)
        model = ChannelBlacklistModel(
            id=entry.id,
            tenant_id=entry.tenant_id,
            channel=entry.channel,
            identifier=entry.identifier,
            reason=entry.reason,
            created_by_user_id=entry.created_by_user_id,
            created_at=entry.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return entry

    async def soft_delete(self, tenant_id: UUID, entry_id: UUID) -> None:
        """Soft-delete entry (set deleted_at = now()). tenant_id mandatory."""
        await self._session.execute(
            update(ChannelBlacklistModel)
            .where(
                ChannelBlacklistModel.id == entry_id,
                ChannelBlacklistModel.tenant_id == tenant_id,
            )
            .values(deleted_at=func.now())
        )
        await self._session.flush()
