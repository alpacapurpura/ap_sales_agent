"""ConversationQueryService — Closer Studio read-side (S11B step 5).

Handles ``list_conversations`` / ``get_conversation_detail`` / ``list_frozen``.
No mutations except resetting the unread counter when the operator opens
a thread.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from luana_core_platform.infrastructure.models.crm import CustomerProfileModel, LeadModel
from luana_core_sales_agent.application.services.closer_studio.lead_helpers import (
    get_last_message_preview,
    resolve_avatar,
    resolve_display_name,
    resolve_lifecycle_stage,
)
from luana_core_sales_agent.infrastructure.models.agent_state_checkpoint_model import (
    AgentStateCheckpointModel,
)
from luana_core_sales_agent.infrastructure.models.message_model import MessageModel
from sqlalchemy import case, func, literal_column, select
from sqlalchemy.orm import joinedload

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from sqlalchemy.orm import Session

logger = structlog.get_logger()


class ConversationQueryService:
    """Read-side service for Closer Studio conversations + frozen list."""

    def __init__(self, db: Session) -> None:
        """Bind the service to a SQLAlchemy session."""
        self.db = db

    # ── List conversations ──────────────────────────────────────────────

    def list_conversations(
        self,
        tenant_id: UUID,
        *,
        temperature: str | None = None,
        handler_mode: str | None = None,
        channel: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """Return active conversations with last-message preview."""
        last_msg_sq = (
            select(
                MessageModel.user_id.label("lead_id"),
                func.max(MessageModel.created_at).label("last_msg_at"),
            )
            .where(MessageModel.tenant_id == tenant_id)
            .group_by(MessageModel.user_id)
            .subquery("last_msg")
        )

        stmt = (
            select(
                LeadModel,
                AgentStateCheckpointModel,
                last_msg_sq.c.last_msg_at,
            )
            .outerjoin(
                AgentStateCheckpointModel,
                (AgentStateCheckpointModel.lead_id == LeadModel.id)
                & (AgentStateCheckpointModel.tenant_id == tenant_id)
                & (AgentStateCheckpointModel.is_active.is_(True))
                & (AgentStateCheckpointModel.deleted_at.is_(None)),
            )
            .outerjoin(
                last_msg_sq,
                last_msg_sq.c.lead_id == LeadModel.id,
            )
            .where(
                LeadModel.tenant_id == tenant_id,
                LeadModel.is_blacklisted.is_(False),
            )
        )

        if temperature:
            stmt = stmt.where(func.lower(LeadModel.temperature) == temperature.lower())
        if handler_mode:
            stmt = stmt.where(AgentStateCheckpointModel.handler_mode == handler_mode)
        if channel:
            stmt = stmt.where(AgentStateCheckpointModel.channel_type == channel)
        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.outerjoin(
                CustomerProfileModel,
                CustomerProfileModel.id == LeadModel.customer_id,
            ).where(
                CustomerProfileModel.full_name.ilike(search_pattern)
                | LeadModel.telegram_id.ilike(search_pattern)
                | LeadModel.whatsapp_id.ilike(search_pattern)
                | LeadModel.instagram_id.ilike(search_pattern),
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar() or 0

        stmt = (
            stmt.order_by(
                case(
                    (
                        AgentStateCheckpointModel.handler_mode == "human",
                        literal_column("0"),
                    ),
                    else_=literal_column("1"),
                ),
                last_msg_sq.c.last_msg_at.desc().nullslast(),
            )
            .offset(offset)
            .limit(limit)
        )

        rows = self.db.execute(stmt).all()

        conversations = []
        for lead, checkpoint, last_msg_at in rows:
            preview = get_last_message_preview(self.db, lead.id, tenant_id)
            conversations.append(
                {
                    "lead_id": lead.id,
                    "customer_profile_id": lead.customer_id,
                    "display_name": resolve_display_name(lead),
                    "channel": checkpoint.channel_type if checkpoint else None,
                    "temperature": lead.temperature,
                    "lead_score": checkpoint.lead_score if checkpoint else (lead.intent_score or 0),
                    "handler_mode": checkpoint.handler_mode if checkpoint else "human",
                    "funnel_stage": checkpoint.current_stage if checkpoint else "rapport",
                    "pipeline_stage": resolve_lifecycle_stage(lead),
                    "last_message_preview": preview,
                    "last_message_at": last_msg_at,
                    "unread_count": checkpoint.unread_count if checkpoint else 0,
                    "avatar_url": resolve_avatar(lead),
                    "is_frozen": bool(checkpoint and checkpoint.frozen_at),
                },
            )

        return conversations, total

    # ── Detail ──────────────────────────────────────────────────────────

    def get_conversation_detail(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        *,
        message_limit: int = 50,
        before: datetime | None = None,
    ) -> dict | None:
        """Full conversation detail with paginated messages."""
        lead = (
            self.db.execute(
                select(LeadModel)
                .options(joinedload(LeadModel.customer))
                .where(LeadModel.id == lead_id, LeadModel.tenant_id == tenant_id),
            )
            .unique()
            .scalar_one_or_none()
        )
        if not lead:
            return None

        checkpoint = self.db.execute(
            select(AgentStateCheckpointModel)
            .where(
                AgentStateCheckpointModel.lead_id == lead_id,
                AgentStateCheckpointModel.tenant_id == tenant_id,
                AgentStateCheckpointModel.is_active.is_(True),
                AgentStateCheckpointModel.deleted_at.is_(None),
            )
            .order_by(AgentStateCheckpointModel.updated_at.desc()),
        ).scalar_one_or_none()

        msg_stmt = select(MessageModel).where(
            MessageModel.user_id == lead_id,
            MessageModel.tenant_id == tenant_id,
        )
        if before:
            msg_stmt = msg_stmt.where(MessageModel.created_at < before)

        msg_stmt = msg_stmt.order_by(MessageModel.created_at.desc()).limit(message_limit)
        messages_raw = self.db.execute(msg_stmt).scalars().all()

        total_msgs = (
            self.db.execute(
                select(func.count()).where(
                    MessageModel.user_id == lead_id,
                    MessageModel.tenant_id == tenant_id,
                ),
            ).scalar()
            or 0
        )

        messages = [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "sender_source": m.sender_source,
                "channel": m.channel,
                "created_at": m.created_at,
                "metadata": m.metadata_log,
            }
            for m in reversed(messages_raw)  # chronological order
        ]

        # Reset unread when the operator opens the thread.
        if checkpoint and checkpoint.unread_count > 0:
            checkpoint.unread_count = 0
            self.db.flush()

        return {
            "lead_id": lead.id,
            "display_name": resolve_display_name(lead),
            "channel": checkpoint.channel_type if checkpoint else None,
            "temperature": lead.temperature,
            "lead_score": checkpoint.lead_score if checkpoint else 0,
            "handler_mode": checkpoint.handler_mode if checkpoint else "human",
            "funnel_stage": checkpoint.current_stage if checkpoint else "rapport",
            "pipeline_stage": resolve_lifecycle_stage(lead),
            "paused_at": checkpoint.paused_at if checkpoint else None,
            "unread_count": 0,
            "qualification_answers": checkpoint.qualification_answers if checkpoint else None,
            "buying_signals": checkpoint.buying_signals if checkpoint else [],
            "lead_data": checkpoint.lead_data if checkpoint else None,
            "customer_profile_id": lead.customer_id,
            "avatar_url": resolve_avatar(lead),
            "messages": messages,
            "total_messages": total_msgs,
        }

    # ── Frozen list ─────────────────────────────────────────────────────

    def list_frozen(self, tenant_id: UUID) -> list[dict]:
        """Return frozen conversations for the operator to triage."""
        stmt = (
            select(LeadModel, AgentStateCheckpointModel)
            .join(
                AgentStateCheckpointModel,
                (AgentStateCheckpointModel.lead_id == LeadModel.id)
                & (AgentStateCheckpointModel.tenant_id == tenant_id)
                & (AgentStateCheckpointModel.is_active.is_(True)),
            )
            .where(
                LeadModel.tenant_id == tenant_id,
                AgentStateCheckpointModel.frozen_at.isnot(None),
            )
            .order_by(AgentStateCheckpointModel.frozen_at.desc())
        )

        rows = self.db.execute(stmt).all()
        result = []
        for lead, checkpoint in rows:
            preview = get_last_message_preview(self.db, lead.id, tenant_id)
            result.append(
                {
                    "lead_id": lead.id,
                    "display_name": resolve_display_name(lead),
                    "channel": checkpoint.channel_type,
                    "temperature": lead.temperature,
                    "lead_score": checkpoint.lead_score,
                    "funnel_stage": checkpoint.current_stage,
                    "frozen_at": checkpoint.frozen_at,
                    "frozen_reason": checkpoint.frozen_reason,
                    "frozen_diagnosis": checkpoint.frozen_diagnosis,
                    "last_message_at": None,
                    "last_message_preview": preview,
                    "avatar_url": resolve_avatar(lead),
                },
            )
        return result


__all__ = ["ConversationQueryService"]
