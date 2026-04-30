"""Pydantic DTOs for Closer Studio endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

# ── List / Filters ──────────────────────────────────────────────────────────


class ConversationListItem(BaseModel):
    """Conversation List Item DTO."""

    lead_id: UUID
    customer_profile_id: UUID | None = None
    display_name: str
    channel: str | None = None
    temperature: str | None = None
    lead_score: int = 0
    handler_mode: str = "ai"
    funnel_stage: str = "rapport"
    pipeline_stage: str | None = None
    last_message_preview: str | None = None
    last_message_at: datetime | None = None
    unread_count: int = 0
    avatar_url: str | None = None
    is_frozen: bool = False
    # PR-8: enriquecimiento inbox con tag de campaña (additive optional)
    campaign_id: UUID | None = None
    campaign_name: str | None = None


class ConversationListResponse(BaseModel):
    """Conversation List Response DTO."""

    conversations: list[ConversationListItem]
    total: int


# ── Detail ──────────────────────────────────────────────────────────────────


class MessageItem(BaseModel):
    """Message Item DTO."""

    id: UUID
    role: str
    content: str
    sender_source: str = "auto"
    channel: str | None = None
    created_at: datetime | None = None
    metadata: dict | None = None


class ConversationDetail(BaseModel):
    """Conversation Detail DTO."""

    lead_id: UUID
    display_name: str
    channel: str | None = None
    temperature: str | None = None
    lead_score: int = 0
    handler_mode: str = "ai"
    funnel_stage: str = "rapport"
    pipeline_stage: str | None = None
    paused_at: datetime | None = None
    unread_count: int = 0
    qualification_answers: dict | None = None
    buying_signals: list = Field(default_factory=list)
    lead_data: dict | None = None
    customer_profile_id: UUID | None = None
    avatar_url: str | None = None
    messages: list[MessageItem] = Field(default_factory=list)
    total_messages: int = 0
    # PR-8: enriquecimiento inbox con tag de campaña (additive optional)
    campaign_id: UUID | None = None
    campaign_name: str | None = None


# ── Actions ─────────────────────────────────────────────────────────────────


class StopRequest(BaseModel):
    """Stop Request DTO."""


class StopResponse(BaseModel):
    """Stop Response DTO."""

    lead_id: UUID
    handler_mode: str
    paused_at: datetime | None = None


class ResumeRequest(BaseModel):
    """Resume Request DTO."""

    objective: str | None = None


class ResumeResponse(BaseModel):
    """Resume Response DTO."""

    lead_id: UUID
    handler_mode: str
    resume_objective: str | None = None


class SendMessageRequest(BaseModel):
    """Send Message Request DTO."""

    content: str = Field(..., min_length=1, max_length=4000)
    mode: str = Field(default="direct", pattern=r"^(direct|instruction)$")


class SendMessageResponse(BaseModel):
    """Send Message Response DTO."""

    message_id: UUID
    content: str
    mode: str
    sent_to_channel: bool = False


class NudgeRequest(BaseModel):
    """Nudge Request DTO."""

    context: str | None = None


class NudgeResponse(BaseModel):
    """Nudge Response DTO."""

    message_id: UUID | None = None
    content: str
    sent_to_channel: bool = False


class ReactivateRequest(BaseModel):
    """Reactivate Request DTO."""

    objective: str | None = None


class ReactivateResponse(BaseModel):
    """Reactivate Response DTO."""

    lead_id: UUID
    handler_mode: str
    message_sent: bool = False


class DiagnoseResponse(BaseModel):
    """Diagnose Response DTO."""

    lead_id: UUID
    diagnosis: dict
    generated_at: datetime


# ── Frozen ──────────────────────────────────────────────────────────────────


class FrozenConversation(BaseModel):
    """Frozen Conversation DTO."""

    lead_id: UUID
    display_name: str
    channel: str | None = None
    temperature: str | None = None
    lead_score: int = 0
    funnel_stage: str = "rapport"
    frozen_at: datetime | None = None
    frozen_reason: str | None = None
    frozen_diagnosis: dict | None = None
    last_message_at: datetime | None = None
    last_message_preview: str | None = None
    avatar_url: str | None = None


# ── KPIs ────────────────────────────────────────────────────────────────────


class CloserKPIs(BaseModel):
    """Closer KPIs DTO."""

    total_active: int = 0
    handled_by_ai: int = 0
    handled_by_human: int = 0
    frozen_count: int = 0
    hot_count: int = 0
    warm_count: int = 0
    cold_count: int = 0
    avg_lead_score: float = 0.0
    unread_total: int = 0
