"""Shared helpers for the Closer Studio split (S11B step 5).

Each method takes only the data it needs (no implicit ``self``) so the
three services (Query / Command / Kpi) can call them without instance
coupling. Keeps :func:`_get_checkpoint` as a single repo entry point —
S11B mandate "no helper duplication across services".
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from src.modules.sales_agent.infrastructure.models.agent_state_checkpoint_model import (
    AgentStateCheckpointModel,
)
from src.modules.sales_agent.infrastructure.models.message_model import MessageModel

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

    from src.shared.infrastructure.models.crm import LeadModel


def get_checkpoint(
    db: Session,
    tenant_id: UUID,
    lead_id: UUID,
) -> AgentStateCheckpointModel | None:
    """Return the active checkpoint for a lead, or ``None``."""
    return db.execute(
        select(AgentStateCheckpointModel)
        .where(
            AgentStateCheckpointModel.tenant_id == tenant_id,
            AgentStateCheckpointModel.lead_id == lead_id,
            AgentStateCheckpointModel.is_active.is_(True),
            AgentStateCheckpointModel.deleted_at.is_(None),
        )
        .order_by(AgentStateCheckpointModel.updated_at.desc()),
    ).scalar_one_or_none()


def get_last_message_preview(db: Session, lead_id: UUID, tenant_id: UUID) -> str | None:
    """Return ≤120-char preview of the last user/assistant message."""
    msg = db.execute(
        select(MessageModel.content)
        .where(
            MessageModel.user_id == lead_id,
            MessageModel.tenant_id == tenant_id,
            MessageModel.role.in_(["user", "assistant"]),
        )
        .order_by(MessageModel.created_at.desc())
        .limit(1),
    ).scalar_one_or_none()
    if msg:
        return msg[:120] + ("..." if len(msg) > 120 else "")
    return None


def resolve_display_name(lead: LeadModel) -> str:
    """Pick a human-readable display name from the lead."""
    if lead.customer and lead.customer.full_name:
        return lead.customer.full_name
    if lead.profile_data and isinstance(lead.profile_data, dict):
        first = lead.profile_data.get("first_name", "")
        last = lead.profile_data.get("last_name", "")
        name = f"{first} {last}".strip()
        if name:
            return name
    return lead.instagram_id or lead.telegram_id or lead.whatsapp_id or str(lead.id)[:8]


def resolve_avatar(lead: LeadModel) -> str | None:
    """Return the customer avatar URL when available."""
    if lead.customer and lead.customer.traits:
        return lead.customer.traits.get("profile_pic_url")
    return None


def resolve_lifecycle_stage(lead: LeadModel) -> str | None:
    """Return the customer lifecycle stage when set."""
    if lead.customer:
        return lead.customer.lifecycle_stage
    return None


__all__ = [
    "get_checkpoint",
    "get_last_message_preview",
    "resolve_avatar",
    "resolve_display_name",
    "resolve_lifecycle_stage",
]
