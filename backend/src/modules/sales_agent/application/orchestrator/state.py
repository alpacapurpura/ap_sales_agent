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
    
    # Errors
    error: Optional[str]

def create_initial_state(user_id: str, tenant_id: str, session_id: str, lead_data: Dict = None) -> AgentState:
    """
    Factory for creating a clean AgentState.
    Handles UUID conversion and default values.
    """
    # Ensure UUIDs
    try:
        uid = UUID(user_id) if isinstance(user_id, str) else user_id
    except:
        uid = None
        
    try:
        tid = UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
    except:
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
        "error": None
    }
