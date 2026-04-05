"""Pydantic DTOs for Closer Studio endpoints."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from uuid import UUID  # noqa: TC003

from pydantic import BaseModel, Field

# ── List / Filters ──────────────────────────────────────────────────────────


class ConversationListItem(BaseModel):
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


class ConversationListResponse(BaseModel):
    conversations: list[ConversationListItem]
    total: int


# ── Detail ──────────────────────────────────────────────────────────────────


class MessageItem(BaseModel):
    id: UUID
    role: str
    content: str
    sender_source: str = "auto"
    channel: str | None = None
    created_at: datetime | None = None
    metadata: dict | None = None


class ConversationDetail(BaseModel):
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


# ── Actions ─────────────────────────────────────────────────────────────────


class StopRequest(BaseModel):
    pass


class StopResponse(BaseModel):
    lead_id: UUID
    handler_mode: str
    paused_at: datetime | None = None


class ResumeRequest(BaseModel):
    objective: str | None = None


class ResumeResponse(BaseModel):
    lead_id: UUID
    handler_mode: str
    resume_objective: str | None = None


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)
    mode: str = Field(default="direct", pattern=r"^(direct|instruction)$")


class SendMessageResponse(BaseModel):
    message_id: UUID
    content: str
    mode: str
    sent_to_channel: bool = False


class NudgeRequest(BaseModel):
    context: str | None = None


class NudgeResponse(BaseModel):
    message_id: UUID | None = None
    content: str
    sent_to_channel: bool = False


class ReactivateRequest(BaseModel):
    objective: str | None = None


class ReactivateResponse(BaseModel):
    lead_id: UUID
    handler_mode: str
    message_sent: bool = False


class DiagnoseResponse(BaseModel):
    lead_id: UUID
    diagnosis: dict
    generated_at: datetime


# ── Frozen ──────────────────────────────────────────────────────────────────


class FrozenConversation(BaseModel):
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
    total_active: int = 0
    handled_by_ai: int = 0
    handled_by_human: int = 0
    frozen_count: int = 0
    hot_count: int = 0
    warm_count: int = 0
    cold_count: int = 0
    avg_lead_score: float = 0.0
    unread_total: int = 0
