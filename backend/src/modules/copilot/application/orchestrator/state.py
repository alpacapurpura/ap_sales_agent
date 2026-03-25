from typing import Annotated, TypedDict, List, Dict, Any, Optional
from uuid import UUID

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class ClientContext(TypedDict, total=False):
    """Context sent from the frontend with each message."""
    current_route: str                     # e.g. "/brand-studio/positioning"
    selected_fields: List[Dict[str, str]]  # [{field_id, field_label, field_value}]
    form_data: Dict[str, Any]              # Current form snapshot (partial)
    locale: str                            # e.g. "es"


class CopilotState(TypedDict):
    """
    State for the agentic Copilot (ReAct loop with tools).
    Uses LangChain message objects for compatibility with tool-calling.
    """
    # LangChain messages (HumanMessage, AIMessage, ToolMessage, etc.)
    # add_messages reducer appends instead of replacing, preserving the full chain.
    messages: Annotated[List[BaseMessage], add_messages]

    # User / Tenant
    user_id: UUID
    tenant_id: UUID

    # Client context from the frontend
    client_context: ClientContext

    # Conversation persistence
    conversation_id: str

    # UI actions queued for the frontend
    pending_ui_actions: List[Dict[str, Any]]

    # Tool names active for this request (route-based selection)
    active_tool_names: List[str]

    # Active procedure (set by procedure tools)
    active_procedure: Optional[Dict[str, Any]]

    # Error tracking
    error: Optional[str]


def create_initial_copilot_state(
    user_id: UUID,
    tenant_id: UUID,
    conversation_id: str,
    client_context: Optional[ClientContext] = None,
) -> CopilotState:
    return {
        "messages": [],
        "user_id": user_id,
        "tenant_id": tenant_id,
        "client_context": client_context or {},
        "conversation_id": conversation_id,
        "pending_ui_actions": [],
        "active_tool_names": [],
        "active_procedure": None,
        "error": None,
    }
