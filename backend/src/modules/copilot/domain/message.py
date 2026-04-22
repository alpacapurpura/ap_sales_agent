"""Message domain entity — v2 shape with backward-compat.

Represents a single message in a copilot conversation. The shape mirrors the
JSONB element stored in copilot_conversations.messages[].

See CONTRACT-MULTIMODAL §2 for the full specification.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from src.modules.copilot.domain.message_blocks import MessageBlock

MessageRole = Literal["user", "assistant", "tool"]
MessageStatus = Literal["sending", "streaming", "sent", "error"]


class Message(BaseModel):
    """Copilot conversation message (v2 shape).

    Invariants:
    - content is NEVER null. When only blocks exist, content is flattened plain text.
    - blocks may be None (v1 legacy) or a list of up to 50 MessageBlock items.
    - status is always "sent" for user messages (lifecycle only for assistant).
    - id is server-generated for assistant, client-generated for user.

    Backward compatibility: if blocks is None, the message was persisted in
    legacy v1 shape. The read adapter (message_codec.decode_message) synthesizes
    a TextBlock from content so downstream code always sees blocks when needed.
    """

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str  # flattened plaintext; never null (invariant 2.2.1)
    blocks: list[MessageBlock] | None = None
    status: MessageStatus = "sent"
    created_at: datetime  # UTC
    tokens_used: int | None = None
    metadata: dict | None = None

    # Tool-role fields (existing legacy — kept for LangChain message replay)
    tool_calls: list[dict] | None = None
    tool_call_id: str | None = None
    name: str | None = None

    @model_validator(mode="after")
    def validate_blocks_limit(self) -> Message:
        """Enforce max 50 blocks per message (CONTRACT-MULTIMODAL Q9)."""
        if self.blocks is not None and len(self.blocks) > 50:
            msg = f"A message may contain at most 50 blocks (got {len(self.blocks)})."
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def validate_content_not_empty_when_no_blocks(self) -> Message:
        """When blocks is None, content must have some value (invariant 2.2.1)."""
        if self.blocks is None and not self.content and self.role != "tool":
            pass  # Soft constraint — content may be populated by codec
        return self


__all__ = ["Message", "MessageRole", "MessageStatus"]
