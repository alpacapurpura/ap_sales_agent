"""RoutingLogRepository — insert and query copilot routing decisions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from luana_core_copilot.infrastructure.models.routing_log_model import RoutingLogModel
from sqlalchemy import select

if TYPE_CHECKING:
    from decimal import Decimal
    from uuid import UUID

    from sqlalchemy.orm import Session

logger = structlog.get_logger()


class RoutingLogRepository:
    """Persist and query copilot routing decisions per tenant."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with a database session."""
        self.db = db

    def insert(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        message_id: UUID,
        role_selected: str,
        classifier_used: str,
        reason: str,
        confidence: float | Decimal | None,
        user_msg_length: int,
        tools_available: int,
    ) -> RoutingLogModel:
        """Insert a new routing log entry and return it.

        The caller is responsible for calling db.commit() / db.flush().
        """
        row = RoutingLogModel(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            message_id=message_id,
            role_selected=role_selected,
            classifier_used=classifier_used,
            reason=reason,
            confidence=confidence,
            user_msg_length=user_msg_length,
            tools_available=tools_available,
        )
        self.db.add(row)
        self.db.flush()
        logger.debug(
            "routing_log_inserted",
            role=role_selected,
            classifier=classifier_used,
            tenant_id=str(tenant_id),
        )
        return row

    def list_by_tenant(
        self,
        *,
        tenant_id: UUID,
        limit: int = 100,
    ) -> list[RoutingLogModel]:
        """Return the most recent routing log rows for a tenant.

        Results are ordered newest-first. Always filters by tenant_id.
        """
        stmt = (
            select(RoutingLogModel)
            .where(RoutingLogModel.tenant_id == tenant_id)
            .order_by(RoutingLogModel.created_at.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_by_conversation(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        limit: int = 100,
    ) -> list[RoutingLogModel]:
        """Return routing log rows for a specific conversation.

        Filters by both tenant_id and conversation_id to prevent cross-tenant leaks.
        """
        stmt = (
            select(RoutingLogModel)
            .where(
                RoutingLogModel.tenant_id == tenant_id,
                RoutingLogModel.conversation_id == conversation_id,
            )
            .order_by(RoutingLogModel.created_at.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())
