"""Repository for ``copilot_llm_call``.

All queries are tenant-scoped per ``.claude/rules/tenant-isolation.md``.
The callback handler (Phase 1, Task T1.7) is the sole writer; reporting
services (Phase 3) are the readers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog
from sqlalchemy import func, select

from src.modules.copilot.observability.persistence.models.llm_call_model import (
    CopilotLlmCallModel,
)

if TYPE_CHECKING:
    import datetime as dt
    from uuid import UUID

    from sqlalchemy.orm import Session

logger = structlog.get_logger()


class LlmCallRepository:
    """Persist and query LLM call rows. Caller controls commit."""

    def __init__(self, db: Session) -> None:
        """Bind the repository to a session."""
        self.db = db

    def add(self, **kwargs: Any) -> CopilotLlmCallModel:  # noqa: ANN401 — column kwargs vary
        """Insert one row. Returns the persisted model.

        ``flush`` is left to the caller (callback handler batches several
        adds per turn before committing).
        """
        row = CopilotLlmCallModel(**kwargs)
        self.db.add(row)
        return row

    def find_by_turn(self, *, tenant_id: UUID, turn_id: UUID) -> list[CopilotLlmCallModel]:
        """Return every LLM call recorded for a turn under one tenant."""
        stmt = (
            select(CopilotLlmCallModel)
            .where(
                CopilotLlmCallModel.tenant_id == tenant_id,
                CopilotLlmCallModel.turn_id == turn_id,
            )
            .order_by(CopilotLlmCallModel.started_at.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def find_by_tenant_range(
        self,
        *,
        tenant_id: UUID,
        start: dt.datetime,
        end: dt.datetime,
    ) -> list[CopilotLlmCallModel]:
        """Return rows for ``tenant_id`` whose ``started_at`` falls in ``[start, end)``."""
        stmt = (
            select(CopilotLlmCallModel)
            .where(
                CopilotLlmCallModel.tenant_id == tenant_id,
                CopilotLlmCallModel.started_at >= start,
                CopilotLlmCallModel.started_at < end,
            )
            .order_by(CopilotLlmCallModel.started_at.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def count_errors_today(self, *, tenant_id: UUID) -> int:
        """Return the count of error rows for ``tenant_id`` since 00:00 UTC today.

        Drives the per-tenant alert in Phase 3.
        """
        # Use UTC midnight as the lower bound. Phase 3 will replace this
        # with the tenant's local midnight when ``TenantLocale`` integration
        # lands; for now the system-clock UTC day is fine.
        import datetime as dt

        today_start = dt.datetime.now(tz=dt.UTC).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        stmt = (
            select(func.count())
            .select_from(CopilotLlmCallModel)
            .where(
                CopilotLlmCallModel.tenant_id == tenant_id,
                CopilotLlmCallModel.status == "error",
                CopilotLlmCallModel.started_at >= today_start,
            )
        )
        return int(self.db.execute(stmt).scalar_one())
