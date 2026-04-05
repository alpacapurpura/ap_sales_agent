"""Pydantic DTOs for Closer Studio endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── List / Filters ──────────────────────────────────────────────────────────


class ConversationListItem(BaseModel):
    lead_id: UUID
    customer_profile_id: Optional[UUID] = None
    display_name: str
    channel: Optional[str] = None
    temperature: Optional[str] = None
    lead_score: int = 0
    handler_mode: str = "ai"
    funnel_stage: str = "rapport"
    pipeline_stage: Optional[str] = None
    last_message_preview: Optional[str] = None
    last_message_at: Optional[datetime] = None
    unread_count: int = 0
    avatar_url: Optional[str] = None
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
    channel: Optional[str] = None
    created_at: Optional[datetime] = None
    metadata: Optional[dict] = None


class ConversationDetail(BaseModel):
    lead_id: UUID
    display_name: str
    channel: Optional[str] = None
    temperature: Optional[str] = None
    lead_score: int = 0
    handler_mode: str = "ai"
    funnel_stage: str = "rapport"
    pipeline_stage: Optional[str] = None
    paused_at: Optional[datetime] = None
    unread_count: int = 0
    qualification_answers: Optional[dict] = None
    buying_signals: list = Field(default_factory=list)
    lead_data: Optional[dict] = None
    customer_profile_id: Optional[UUID] = None
    avatar_url: Optional[str] = None
    messages: list[MessageItem] = Field(default_factory=list)
    total_messages: int = 0


# ── Actions ─────────────────────────────────────────────────────────────────


class StopRequest(BaseModel):
    pass


class StopResponse(BaseModel):
    lead_id: UUID
    handler_mode: str
    paused_at: Optional[datetime] = None


class ResumeRequest(BaseModel):
    objective: Optional[str] = None


class ResumeResponse(BaseModel):
    lead_id: UUID
    handler_mode: str
    resume_objective: Optional[str] = None


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)
    mode: str = Field(default="direct", pattern=r"^(direct|instruction)$")


class SendMessageResponse(BaseModel):
    message_id: UUID
    content: str
    mode: str
    sent_to_channel: bool = False


class NudgeRequest(BaseModel):
    context: Optional[str] = None


class NudgeResponse(BaseModel):
    message_id: Optional[UUID] = None
    content: str
    sent_to_channel: bool = False


class ReactivateRequest(BaseModel):
    objective: Optional[str] = None


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
    channel: Optional[str] = None
    temperature: Optional[str] = None
    lead_score: int = 0
    funnel_stage: str = "rapport"
    frozen_at: Optional[datetime] = None
    frozen_reason: Optional[str] = None
    frozen_diagnosis: Optional[dict] = None
    last_message_at: Optional[datetime] = None
    last_message_preview: Optional[str] = None
    avatar_url: Optional[str] = None


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
