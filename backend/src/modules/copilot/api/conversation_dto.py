"""DTOs for the Copilot conversations endpoints (CONTRACT §4.1)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ModelTierLiteral = Literal["nano", "mini", "reasoning", "heavy"]


class ConversationSummary(BaseModel):
    """Summary DTO returned for every conversation list and CRUD operation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str | None
    title_auto_generated: bool
    updated_at: datetime
    message_count: int
    total_tokens: int
    last_tier_used: ModelTierLiteral | None
    has_procedure: bool
    procedure_progress: Annotated[float | None, Field(default=None, ge=0.0, le=1.0)]
    archived_at: datetime | None = None


class ConversationListResponse(BaseModel):
    """Paginated list of conversation summaries."""

    model_config = ConfigDict(from_attributes=True)

    items: list[ConversationSummary]
    next_cursor: str | None = None


class ConversationMessageDTO(BaseModel):
    """Single decoded message in a conversation detail response.

    Mirrors the canonical v2 envelope (CONTRACT-MULTIMODAL §3) while
    keeping `blocks` as an untyped list — block validation happens via
    `decode_message`, and every client renderer is block-schema aware.
    """

    model_config = ConfigDict(extra="ignore")

    id: UUID
    role: Literal["user", "assistant", "tool"]
    content: str
    blocks: list[dict] | None = None
    status: Literal["sending", "streaming", "sent", "error"] = "sent"
    created_at: datetime
    tokens_used: int | None = None
    metadata: dict | None = None


class ConversationDetail(ConversationSummary):
    """Full conversation: summary + decoded messages list.

    Used when the client opens a historical conversation and needs to
    hydrate the chat panel in one round-trip.
    """

    messages: list[ConversationMessageDTO]


class PatchConversationRequest(BaseModel):
    """Request body for PATCH /conversations/{id}."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=120)
    archived: bool | None = None


class RevertRequest(BaseModel):
    """Request body for POST /conversations/{id}/revert.

    When mutation_ids is omitted, all active mutations are reverted.
    """

    model_config = ConfigDict(extra="forbid")

    mutation_ids: list[UUID] | None = None


class RevertFailure(BaseModel):
    """A single revert failure entry."""

    id: UUID
    error: str


class RevertResponse(BaseModel):
    """Response from POST /conversations/{id}/revert."""

    model_config = ConfigDict(from_attributes=True)

    reverted_count: int
    failed: list[RevertFailure] = Field(default_factory=list)


class ActiveJobProgressDTO(BaseModel):
    """Progress snapshot for a single in-flight extraction job.

    Fields sourced from procedure_state (persisted) + Redis key (live progress).
    When Redis has expired (job finished long ago or TTL hit), status/progress/
    stage fields are None — FE treats that as "job likely done, reload sections".
    """

    model_config = ConfigDict(from_attributes=True)

    job_id: str
    module: str
    entity_id: str | None
    source_kind: str
    source_ref: str
    scope: str
    mode: str
    started_at: str
    # Live progress from Redis (None if Redis key expired):
    status: str | None  # "queued" | "processing" | "completed" | "failed" | None
    progress: int | None
    stage: str | None
    filled_fields: list[str]
    filled_fields_by_section: dict[str, list[str]]
    sections_touched: list[str]
    sections_completed: list[str]
    finished_at: str | None
    poll_endpoint: str  # relative URL for FE to continue polling


class ActiveJobsResponse(BaseModel):
    """Response for GET /conversations/{id}/active-jobs."""

    model_config = ConfigDict(from_attributes=True)

    jobs: list[ActiveJobProgressDTO]
