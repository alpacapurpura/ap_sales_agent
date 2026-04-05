"""DTOs for the Copilot chat endpoint and SSE event protocol."""

from typing import Any, Literal

from pydantic import BaseModel, Field

# ── Request ──────────────────────────────────────────────────────────


class ClientContextDTO(BaseModel):
    current_route: str | None = None
    selected_fields: list[dict[str, str]] = Field(default_factory=list)
    form_data: dict[str, Any] = Field(default_factory=dict)
    locale: str = "es"


class CopilotChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: str | None = None
    context: ClientContextDTO = Field(default_factory=ClientContextDTO)


# ── SSE Event Types ──────────────────────────────────────────────────

SSEEventType = Literal[
    "text_chunk",
    "tool_start",
    "tool_result",
    "ui_action",
    "proposal",
    "confirmation_required",
    "status",
    "done",
    "error",
]


class SSEEvent(BaseModel):
    """Typed SSE event for the copilot stream."""

    event: SSEEventType
    data: dict[str, Any]

    def to_sse(self) -> str:
        """Format as SSE wire protocol."""
        import json

        return f"event: {self.event}\ndata: {json.dumps(self.data, ensure_ascii=False)}\n\n"


# ── Response (for non-streaming fallback) ────────────────────────────


class CopilotChatResponse(BaseModel):
    conversation_id: str
    message: str
