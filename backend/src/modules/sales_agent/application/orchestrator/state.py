from typing import TypedDict, List, Dict, Any, Optional
from uuid import UUID

class AgentState(TypedDict):
    """
    Shared state for all LangGraph agents.
    Provides context for multi-tenant isolation and session management.
    """
    # Messaging
    messages: List[Dict[str, Any]] # [{"role": "user", "content": "..."}, ...]
    
    # Routing
    next_node: Optional[str]
    
    # Context
    user_id: Optional[UUID]
    tenant_id: Optional[UUID]
    session_id: Optional[str]
    
    # Agent Memory (Short Term)
    current_state: Optional[str] # e.g. "rapport", "discovery", "closing"
    detected_intent: Optional[str]
    lead_score: Optional[int]
    
    # Lead Data (Captured Information)
    lead_data: Optional[Dict[str, Any]] # { "name": "...", "budget": "..." }

    # Configuration & History
    tenant_config: Optional[Dict[str, Any]]
    history: List[Dict[str, Any]]
    user_profile: Optional[Dict[str, Any]]
    
    # Session Status
    session_active: bool
    active_enrollment: Optional[Dict[str, Any]]
    active_product: Optional[Dict[str, Any]]
    last_intent: Optional[str]
    launch_stage: Optional[str]
    
    # Agent Knowledge System (AKS)
    agent_identity: Optional[str]  # Rendered tenant-specific identity prompt

    # Accumulated Signals (persisted via checkpoint)
    buying_signals: Optional[List[Dict[str, Any]]]
    objection_history: Optional[List[Dict[str, Any]]]
    qualification_answers: Optional[Dict[str, Any]]
    turn_count: Optional[int]
    customer_profile_id: Optional[UUID]
    channel_type: Optional[str]
    close_strategy: Optional[str]

    # Internal (graph loop control)
    internal_turn: Optional[int]

    # Errors
    error: Optional[str]

def create_initial_state(
    user_id: str,
    tenant_id: str,
    session_id: str = None,
    lead_data: Dict = None,
    tenant_config: Dict = None,
    history: List[Dict[str, Any]] = None,
    user_profile: Dict = None,
    session_active: bool = True,
    active_enrollment: Dict = None,
    active_product: Dict = None,
    last_intent: str = None,
    launch_stage: str = None,
    agent_identity: str = None,
    # Checkpoint-persisted fields
    buying_signals: List[Dict[str, Any]] = None,
    objection_history: List[Dict[str, Any]] = None,
    qualification_answers: Dict = None,
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
        "error": None,
    }
