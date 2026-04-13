"""Copilot orchestrator state definitions."""

from typing import Annotated, Any, TypedDict
from uuid import UUID

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class FocusContext(TypedDict, total=False):
    """Focus context sent when the user activates Focus or Interview mode."""

    domain: str  # "offer", "brand", "buyer_persona"
    entity_id: str  # UUID of the focused entity (omit for brand singleton)


class ClientContext(TypedDict, total=False):
    """Context sent from the frontend with each message."""

    current_route: str  # e.g. "/brand-studio/positioning"
    selected_fields: list[dict[str, str]]  # [{field_id, field_label, field_value}]
    form_data: dict[str, Any]  # Current form snapshot (partial)
    locale: str  # e.g. "es"
    focus: FocusContext  # Active when Focus or Interview mode is on
    interview_session_id: str  # Active interview session UUID


class CopilotState(TypedDict):
    """Define state for the agentic Copilot (ReAct loop with tools).

    Use LangChain message objects for compatibility with tool-calling.
    """

    # LangChain messages (HumanMessage, AIMessage, ToolMessage, etc.)
    # add_messages reducer appends instead of replacing, preserving the full chain.
    messages: Annotated[list[BaseMessage], add_messages]

    # User / Tenant
    user_id: UUID
    tenant_id: UUID

    # Client context from the frontend
    client_context: ClientContext

    # Conversation persistence
    conversation_id: str

    # UI actions queued for the frontend
    pending_ui_actions: list[dict[str, Any]]

    # Tool names active for this request (route-based selection)
    active_tool_names: list[str]

    # Active procedure (set by procedure tools)
    active_procedure: dict[str, Any] | None

    # Entity data loaded when Focus Mode is active (None when no focus is set)
    focus_entity_data: dict[str, Any] | None

    # Error tracking
    error: str | None


def create_initial_copilot_state(
    user_id: UUID,
    tenant_id: UUID,
    conversation_id: str,
    client_context: ClientContext | None = None,
) -> CopilotState:
    """Create initial copilot state."""
    return {
        "messages": [],
        "user_id": user_id,
        "tenant_id": tenant_id,
        "client_context": client_context or {},
        "conversation_id": conversation_id,
        "pending_ui_actions": [],
        "active_tool_names": [],
        "active_procedure": None,
        "focus_entity_data": None,
        "error": None,
    }
