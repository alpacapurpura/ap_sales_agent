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
