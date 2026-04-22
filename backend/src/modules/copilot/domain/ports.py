"""Port interfaces for the copilot domain.

All are Protocol classes — pure Python, no concrete imports from
infrastructure or api layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable
from uuid import UUID

from src.modules.copilot.domain.model_tier import ModelTier
from src.modules.copilot.domain.procedure_state import ProcedureState

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

# ── LLM provider ────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class LLMMessage:
    """A single message in an LLM conversation."""

    role: str
    content: str
    name: str | None = None
    tool_call_id: str | None = None


@dataclass(frozen=True, slots=True)
class LLMEvent:
    """One chunk of a streamed LLM response.

    ``kind`` is one of: "text" | "tool_start" | "tool_result" | "usage" |
    "done" | "error". ``data`` is kind-specific and JSON-serializable.
    """

    kind: str
    data: dict[str, Any]


@runtime_checkable
class LLMProvider(Protocol):
    """Abstraction over LLM API (OpenAI, Anthropic, etc.)."""

    async def complete(
        self,
        *,
        tier: ModelTier,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        stream: bool = True,
    ) -> AsyncIterator[LLMEvent]:
        """Stream LLM completion events for the given tier and messages."""
        ...


# ── Conversation store ───────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class ConversationPage:
    """Cursor-paginated conversation list."""

    items: list[ConversationSummaryVO]
    next_cursor: str | None


@dataclass(frozen=True, slots=True)
class ConversationSummaryVO:
    """Value object representing one row in the conversation history list."""

    id: UUID
    title: str | None
    updated_at: Any
    message_count: int
    total_tokens: int
    last_tier_used: ModelTier | None
    has_procedure: bool
    procedure_progress: float | None
    title_auto_generated: bool
    archived_at: Any | None


@runtime_checkable
class ConversationStore(Protocol):
    """Port for accessing and mutating conversations."""

    async def list(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        limit: int = 6,
        cursor: str | None = None,
        include_archived: bool = False,
    ) -> ConversationPage:
        """Return a cursor-paginated page of conversations for the user."""
        ...

    async def get(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        conversation_id: UUID,
    ) -> ConversationSummaryVO | None:
        """Fetch one conversation summary (or None if missing)."""
        ...

    async def create(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        title: str | None = None,
    ) -> ConversationSummaryVO:
        """Create a new empty conversation and return its summary."""
        ...

    async def append(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        message: LLMMessage,
        tier_used: ModelTier,
        tokens_added: int,
    ) -> None:
        """Append a message to the conversation and update aggregate counters."""
        ...

    async def update_summary(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        summary: str,
    ) -> None:
        """Persist a new rolling summary for the conversation."""
        ...

    async def update_title(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        title: str,
        auto_generated: bool,
    ) -> ConversationSummaryVO:
        """Persist a new title for the conversation."""
        ...

    async def archive(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        conversation_id: UUID,
    ) -> ConversationSummaryVO:
        """Soft-delete the conversation and return its updated summary."""
        ...

    async def update_procedure_state(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        procedure_state: ProcedureState | None,
    ) -> None:
        """Persist the procedure state attached to the conversation."""
        ...


# ── Tool registry ────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class CopilotContext:
    """Runtime context passed from the frontend to tool selection."""

    current_route: str | None
    selected_fields: list[dict[str, str]]
    form_data: dict[str, Any]
    locale: str
    procedure_state: ProcedureState | None = None


@runtime_checkable
class ToolRegistry(Protocol):
    """Port for selecting tools based on current context."""

    def get_tools_for_context(self, ctx: CopilotContext) -> list[Any]:
        """Return the ordered list of tools available for the given context."""
        ...


# ── Identity provider ────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class UserPrincipal:
    """Authenticated user identity."""

    user_id: UUID
    tenant_id: UUID


@runtime_checkable
class IdentityProvider(Protocol):
    """Port for resolving the current authenticated user."""

    async def current_user(self) -> UserPrincipal:
        """Return the authenticated user principal."""
        ...

    async def tenant_id_for(self, user_id: UUID) -> UUID:
        """Resolve the tenant id for the given user id."""
        ...
