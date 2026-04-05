from typing import Any, TypedDict
from uuid import UUID


class AgentState(TypedDict):
    """
    Shared state for all LangGraph agents.
    Provides context for multi-tenant isolation and session management.
    """

    # Messaging
    messages: list[dict[str, Any]]  # [{"role": "user", "content": "..."}, ...]

    # Routing
    next_node: str | None

    # Context
    user_id: UUID | None
    tenant_id: UUID | None
    session_id: str | None

    # Agent Memory (Short Term)
    current_state: str | None  # e.g. "rapport", "discovery", "closing"
    detected_intent: str | None
    lead_score: int | None

    # Lead Data (Captured Information)
    lead_data: dict[str, Any] | None  # { "name": "...", "budget": "..." }

    # Configuration & History
    tenant_config: dict[str, Any] | None
    history: list[dict[str, Any]]
    user_profile: dict[str, Any] | None

    # Session Status
    session_active: bool
    active_enrollment: dict[str, Any] | None
    active_product: dict[str, Any] | None
    last_intent: str | None
    launch_stage: str | None

    # Agent Knowledge System (AKS)
    agent_identity: str | None  # Rendered tenant-specific identity prompt

    # Accumulated Signals (persisted via checkpoint)
    buying_signals: list[dict[str, Any]] | None
    objection_history: list[dict[str, Any]] | None
    qualification_answers: dict[str, Any] | None
    turn_count: int | None
    customer_profile_id: UUID | None
    channel_type: str | None
    close_strategy: str | None

    # Internal (graph loop control)
    internal_turn: int | None
    _pending_tool: dict[str, Any] | None

    # Errors
    error: str | None


def create_initial_state(
    user_id: str,
    tenant_id: str,
    session_id: str = None,
    lead_data: dict = None,
    tenant_config: dict = None,
    history: list[dict[str, Any]] = None,
    user_profile: dict = None,
    session_active: bool = True,
    active_enrollment: dict = None,
    active_product: dict = None,
    last_intent: str = None,
    launch_stage: str = None,
    agent_identity: str = None,
    # Checkpoint-persisted fields
    buying_signals: list[dict[str, Any]] = None,
    objection_history: list[dict[str, Any]] = None,
    qualification_answers: dict = None,
    turn_count: int = None,
    customer_profile_id: UUID = None,
    channel_type: str = None,
    close_strategy: str = None,
    current_state: str = None,
    lead_score: int = None,
) -> AgentState:
    """
    Factory for creating a clean AgentState.
    Handles UUID conversion and default values.
    """
    # Ensure UUIDs
    try:
        uid = UUID(user_id) if isinstance(user_id, str) else user_id
    except Exception:
        uid = None

    try:
        tid = UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
    except Exception:
        tid = None

    return {
        "messages": [],
        "next_node": None,
        "user_id": uid,
        "tenant_id": tid,
        "session_id": session_id,
        "current_state": current_state or "rapport",
        "detected_intent": None,
        "lead_score": lead_score if lead_score is not None else 0,
        "lead_data": lead_data or {},
        "tenant_config": tenant_config or {},
        "history": history or [],
        "user_profile": user_profile or {},
        "session_active": session_active,
        "active_enrollment": active_enrollment,
        "active_product": active_product,
        "last_intent": last_intent,
        "launch_stage": launch_stage,
        "agent_identity": agent_identity,
        # Checkpoint-persisted fields
        "buying_signals": buying_signals or [],
        "objection_history": objection_history or [],
        "qualification_answers": qualification_answers or {},
        "turn_count": turn_count or 0,
        "customer_profile_id": customer_profile_id,
        "channel_type": channel_type,
        "close_strategy": close_strategy,
        # Internal
        "internal_turn": 0,
        "_pending_tool": None,
        "error": None,
    }
