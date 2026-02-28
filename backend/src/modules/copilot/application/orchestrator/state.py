from typing import TypedDict, List, Dict, Any, Optional
from uuid import UUID

class CopilotState(TypedDict):
    """
    State for the Copilot (User Assistant).
    """
    messages: List[Dict[str, Any]]
    
    # User Context
    user_id: UUID
    tenant_id: UUID
    
    # Task Context
    current_task: Optional[str] # e.g. "extract_brand", "generate_copy"
    detected_intent: Optional[str]
    
    # Memory
    short_term_memory: Dict[str, Any]
    
    error: Optional[str]

def create_initial_copilot_state(user_id: UUID, tenant_id: UUID) -> CopilotState:
    return {
        "messages": [],
        "user_id": user_id,
        "tenant_id": tenant_id,
        "current_task": None,
        "detected_intent": None,
        "short_term_memory": {},
        "error": None
    }
