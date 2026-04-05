"""Pydantic DTOs for Sales Agent Audit endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

# ── Lead List ────────────────────────────────────────────────────────────────


class AuditLeadSummary(BaseModel):
    id: str
    full_name: str
    telegram_id: str | None = None
    whatsapp_id: str | None = None
    created_at: str | None = None


class AuditLeadListItem(BaseModel):
    lead: AuditLeadSummary
    last_activity: str | None = None


# ── Lead Detail ──────────────────────────────────────────────────────────────


class AuditLeadDetail(BaseModel):
    id: str
    full_name: str
    # email and phone are intentionally None — PII not exposed via this endpoint
    email: None = None
    phone: None = None
    telegram_id: str | None = None
    whatsapp_id: str | None = None
    instagram_id: str | None = None
    tiktok_id: str | None = None
    profile_data: dict[str, Any] = {}
    created_at: str | None = None
    updated_at: str | None = None


# ── Timeline ─────────────────────────────────────────────────────────────────


class LLMLogSummary(BaseModel):
    model: str | None = None
    total_tokens: int = 0
    prompt_template: str | None = None


class TimelineEvent(BaseModel):
    type: str  # "message" | "trace"
    id: str
    created_at: str | None = None
    timestamp: float = 0
    # message fields
    role: str | None = None
    content: str | None = None
    # trace fields
    node_name: str | None = None
    execution_time_ms: int | None = None
    llm_summary: LLMLogSummary | None = None


# ── Trace Detail ─────────────────────────────────────────────────────────────


class LLMLogDetail(BaseModel):
    id: str
    model: str | None = None
    prompt_template: str
    prompt_rendered: str | None = None
    response_text: str | None = None
    tokens_input: int | None = None
    tokens_output: int | None = None
    metadata: dict[str, Any] | None = None


class TraceDetail(BaseModel):
    id: str
    node_name: str | None = None
    input_state: dict[str, Any] | None = None
    output_state: dict[str, Any] | None = None
    execution_time_ms: int | None = None
    created_at: str | None = None
    llm_logs: list[LLMLogDetail] = []


# ── Clear History ────────────────────────────────────────────────────────────


class ClearHistoryResponse(BaseModel):
    status: str
