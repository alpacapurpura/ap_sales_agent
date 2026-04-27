"""Copilot orchestrator state definitions."""

from typing import Annotated, Any, TypedDict
from uuid import UUID

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class ClientContext(TypedDict, total=False):
    """Context sent from the frontend with each message.

    Focus mode was retired on 2026-04-21; the standalone interview engine was
    consolidated into the main chat on 2026-04-22. Guided setup is now a flag
    (``guided_mode``) — the actual state lives in
    ``CopilotConversationModel.procedure_state["guided"]`` and is rehydrated
    server-side.
    """

    current_route: str  # e.g. "/brand-studio/positioning"
    selected_fields: list[dict[str, str]]  # [{field_id, field_label, field_value}]
    form_data: dict[str, Any]  # Current form snapshot (partial)
    locale: str  # e.g. "es"
    guided_mode: bool  # True when a GuidedState is loaded for this conversation


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

    # Active guided setup — rehydrated from procedure_state["guided"] per turn
    # so tools can introspect it without an extra DB hit inside the graph.
    guided_state: dict[str, Any] | None

    # FP2 (B24) — channel intent detected in the user message. When present,
    # the deep-agent prompt builder injects an instruction forcing
    # ``format_for_channel`` invocation before the AGENT finalises the turn.
    # Shape: ``{"channel": "whatsapp", "label": "WhatsApp", "matched_span": [start, end]}``
    # or ``None`` when no channel keyword was detected.
    channel_intent: dict[str, Any] | None

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
        "guided_state": None,
        "channel_intent": None,
        "error": None,
    }
