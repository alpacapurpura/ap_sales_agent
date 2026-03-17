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
    agent_identity: str = None
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
        "current_state": "rapport",
        "detected_intent": None,
        "lead_score": 0,
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
        "error": None
    }
