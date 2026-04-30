"""SQLAlchemy 2.0 async implementation of MVRefreshLogRepository — PM Q4.

PR-2 / PI-1 S0.
"""

from __future__ import annotations

import datetime as dt
import uuid as uuid_mod

import structlog
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.billing.domain.mv_refresh_log import MVRefreshLog, RefreshStatus
from src.shared.billing.domain.mv_refresh_log_repository import MVRefreshLogRepository
from src.shared.billing.infrastructure.models.mv_refresh_log_model import MVRefreshLogModel

logger = structlog.get_logger(__name__)


def _model_to_vo(m: MVRefreshLogModel) -> MVRefreshLog:
    """Map ORM row to immutable VO."""
    return MVRefreshLog(
        id=m.id,
        mv_name=m.mv_name,
        refreshed_at=m.refreshed_at,
        refresh_duration_ms=m.refresh_duration_ms,
        rows_affected=m.rows_affected,
        status=m.status,  # type: ignore[arg-type]
    )


class SQLAMVRefreshLogRepository(MVRefreshLogRepository):
    """SQLAlchemy 2.0 async implementation of MVRefreshLogRepository."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind repository to async session."""
        self._session = session

    async def record_refresh(
        self,
        mv_name: str,
        refresh_duration_ms: int | None,
        rows_affected: int | None,
        status: RefreshStatus,
    ) -> MVRefreshLog:
        """Insert a new refresh log row."""
        now = dt.datetime.now(dt.timezone.utc)
        model = MVRefreshLogModel(
            id=uuid_mod.uuid4(),
            mv_name=mv_name,
            refreshed_at=now,
            refresh_duration_ms=refresh_duration_ms,
            rows_affected=rows_affected,
            status=status,
        )
        self._session.add(model)
        await self._session.flush()
        return _model_to_vo(model)

    async def get_last_refresh(self, mv_name: str) -> MVRefreshLog | None:
        """Return most recent row for mv_name (ORDER BY refreshed_at DESC LIMIT 1)."""
        stmt = (
            select(MVRefreshLogModel)
            .where(MVRefreshLogModel.mv_name == mv_name)
            .order_by(MVRefreshLogModel.refreshed_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _model_to_vo(row) if row else None

    async def delete_older_than(self, cutoff: dt.datetime) -> int:
        """Delete rows older than cutoff. Returns count deleted."""
        stmt = delete(MVRefreshLogModel).where(MVRefreshLogModel.refreshed_at < cutoff)
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount  # type: ignore[return-value]
