"""Copilot pinned memory repository.

CRUD over ``copilot_pinned_memory`` (StoreBackend, per-user opt-in).
Tenant-scoped on every query. F2 ships the repo; the ``pin_to_memory``
tool that uses it lands in F4 (URL contextual scratchpad).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from luana_core_copilot.infrastructure.models.pinned_memory_model import (
    CopilotPinnedMemoryModel,
)
from luana_core_platform.domain.datetime_utils import utc_now
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

logger = structlog.get_logger()


class CopilotPinnedMemoryRepository:
    """Repository for copilot pinned memory."""

    def __init__(self, db: Session) -> None:
        """Bind a SQLAlchemy session."""
        self.db = db

    def upsert(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        path: str,
        content: str,
        pinned_from_conversation_id: UUID | None = None,
    ) -> CopilotPinnedMemoryModel:
        """Insert or update by ``(tenant_id, user_id, path)``."""
        now = utc_now()
        stmt = (
            pg_insert(CopilotPinnedMemoryModel)
            .values(
                tenant_id=tenant_id,
                user_id=user_id,
                path=path,
                content=content,
                pinned_from_conversation_id=pinned_from_conversation_id,
                updated_at=now,
            )
            .on_conflict_do_update(
                index_elements=["tenant_id", "user_id", "path"],
                set_={"content": content, "updated_at": now},
            )
            .returning(CopilotPinnedMemoryModel)
        )
        row = self.db.execute(stmt).scalar_one()
        self.db.flush()
        return row

    def get(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        path: str,
    ) -> CopilotPinnedMemoryModel | None:
        """Fetch a single pinned entry by path."""
        stmt = select(CopilotPinnedMemoryModel).where(
            CopilotPinnedMemoryModel.tenant_id == tenant_id,
            CopilotPinnedMemoryModel.user_id == user_id,
            CopilotPinnedMemoryModel.path == path,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_user(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        path_prefix: str | None = None,
    ) -> list[CopilotPinnedMemoryModel]:
        """List entries for a user, optionally filtered by path prefix."""
        stmt = select(CopilotPinnedMemoryModel).where(
            CopilotPinnedMemoryModel.tenant_id == tenant_id,
            CopilotPinnedMemoryModel.user_id == user_id,
        )
        if path_prefix:
            stmt = stmt.where(CopilotPinnedMemoryModel.path.like(f"{path_prefix}%"))
        stmt = stmt.order_by(CopilotPinnedMemoryModel.updated_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    def delete(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        path: str,
    ) -> bool:
        """Hard-delete by path. Returns True when a row was removed."""
        stmt = delete(CopilotPinnedMemoryModel).where(
            CopilotPinnedMemoryModel.tenant_id == tenant_id,
            CopilotPinnedMemoryModel.user_id == user_id,
            CopilotPinnedMemoryModel.path == path,
        )
        result = self.db.execute(stmt)
        self.db.flush()
        return bool(result.rowcount)
