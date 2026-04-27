"""Repository for ``copilot_trace_event``.

Replaces the legacy ``application/observability/trace_recorder.py`` write
path during Phase 2 (the recorder file is removed in the atomic switch).
For now the new repo coexists with the recorder — both write to the same
table with the same shape. Tenant-scoped reads.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import uuid4

import structlog
from sqlalchemy import select

from src.modules.copilot.infrastructure.models.trace_event_model import (
    CopilotTraceEventModel,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

logger = structlog.get_logger()


class TraceEventRepository:
    """Persist and query ``copilot_trace_event`` rows."""

    def __init__(self, db: Session) -> None:
        """Bind the repository to a session."""
        self.db = db

    def add(
        self,
        *,
        tenant_id: UUID,
        turn_id: UUID,
        span_id: UUID,
        event_type: str,
        name: str | None = None,
        data: dict[str, Any] | None = None,
        duration_ms: int | None = None,
        status: str = "ok",
        user_id: UUID | None = None,
        conversation_id: UUID | None = None,
        message_id: UUID | None = None,
        parent_span_id: UUID | None = None,
    ) -> CopilotTraceEventModel:
        """Insert one trace-event row. Returns the persisted model."""
        row = CopilotTraceEventModel(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            turn_id=turn_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            event_type=event_type,
            name=name,
            data=data or {},
            duration_ms=duration_ms,
            status=status,
        )
        self.db.add(row)
        return row

    def list_by_turn(
        self,
        *,
        tenant_id: UUID,
        turn_id: UUID,
    ) -> list[CopilotTraceEventModel]:
        """Return every trace event of ``turn_id`` for ``tenant_id``."""
        stmt = (
            select(CopilotTraceEventModel)
            .where(
                CopilotTraceEventModel.tenant_id == tenant_id,
                CopilotTraceEventModel.turn_id == turn_id,
            )
            .order_by(CopilotTraceEventModel.created_at.asc())
        )
        return list(self.db.execute(stmt).scalars().all())
