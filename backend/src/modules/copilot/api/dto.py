"""DTOs for the Copilot chat endpoint and SSE event protocol."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ── Request ──────────────────────────────────────────────────────────

class ClientContextDTO(BaseModel):
    current_route: Optional[str] = None
    selected_fields: List[Dict[str, str]] = Field(default_factory=list)
    form_data: Dict[str, Any] = Field(default_factory=dict)
    locale: str = "es"


class CopilotChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[str] = None
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
    data: Dict[str, Any]

    def to_sse(self) -> str:
        """Format as SSE wire protocol."""
        import json
        return f"event: {self.event}\ndata: {json.dumps(self.data, ensure_ascii=False)}\n\n"


# ── Response (for non-streaming fallback) ────────────────────────────

class CopilotChatResponse(BaseModel):
    conversation_id: str
    message: str
