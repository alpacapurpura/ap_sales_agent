"""Repository for ``sales_agent_llm_call``.

Satisfies :class:`~src.shared.agent_observability.persistence.base_llm_call_repo.BaseLLMCallRepoProtocol`
via structural typing — sync ``Session`` (matches sales_agent
``ChatOrchestrator`` which uses ``SessionLocal()`` per turn). Tenant-
scoped reads. Caller controls commit.

The callback handler (S1) is the sole writer; reporting services (S2)
are the readers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog
from sqlalchemy import select

from src.modules.sales_agent.observability.persistence.models.llm_call_model import (
    SalesAgentLlmCallModel,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

logger = structlog.get_logger()


class SalesAgentLlmCallRepository:
    """Persist and query LLM call rows for sales_agent. Caller controls commit."""

    def __init__(self, db: Session) -> None:
        """Bind the repository to a session."""
        self.db = db

    def add(self, **kwargs: Any) -> SalesAgentLlmCallModel:  # noqa: ANN401 — column kwargs vary
        """Insert one row. Returns the persisted model.

        ``flush`` and ``commit`` are left to the caller (the callback
        handler batches several adds per turn before committing).
        """
        row = SalesAgentLlmCallModel(**kwargs)
        self.db.add(row)
        return row

    def find_by_turn(
        self,
        *,
        tenant_id: UUID,
        turn_id: UUID,
    ) -> list[SalesAgentLlmCallModel]:
        """Return every LLM call recorded for a turn under one tenant."""
        stmt = (
            select(SalesAgentLlmCallModel)
            .where(
                SalesAgentLlmCallModel.tenant_id == tenant_id,
                SalesAgentLlmCallModel.turn_id == turn_id,
            )
            .order_by(SalesAgentLlmCallModel.started_at.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def find_by_lead(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        limit: int = 200,
    ) -> list[SalesAgentLlmCallModel]:
        """Return rows for a single lead under one tenant, newest first.

        Drives the dual-read window in admin ``sales_audit.py`` —
        replaces the legacy ``LLMLog`` join over ``agent_traces``.
        """
        stmt = (
            select(SalesAgentLlmCallModel)
            .where(
                SalesAgentLlmCallModel.tenant_id == tenant_id,
                SalesAgentLlmCallModel.lead_id == lead_id,
            )
            .order_by(SalesAgentLlmCallModel.started_at.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())
