"""ProcedureState — serialized into copilot_conversations.procedure_state (JSONB)."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProcedureState(BaseModel):
    """Overlay stored on conversation.procedure_state (JSONB).

    Replaces the standalone InterviewSession table row-for-row for active
    procedures. See CONTRACT §2.4.
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    procedure_id: str
    current_block: str
    completed_blocks: list[str] = Field(default_factory=list)
    answers: dict[str, object] = Field(default_factory=dict)
    coverage: float = 0.0
    entity_id: UUID | None = None
