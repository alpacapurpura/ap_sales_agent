from typing import TypedDict, List, Optional, Literal, Dict, Any
from src.core.schema import FunnelStage, ProductLaunchStage, UserProfile

class AgentState(TypedDict):
    user_id: str
    messages: List[Dict[str, str]]  # History of messages [{"role": "user", "content": "..."}, ...]
    # current_state usa los valores del Enum FunnelStage
    current_state: FunnelStage
    user_profile: Dict[str, Any]   # Serialized UserProfile Pydantic model
    last_intent: Optional[str]
    disqualification_reason: Optional[str] # Nuevo campo para tracking de rechazos
    downsell_path: Optional[str] # 'masterclass', 'community', 'none'
    financial_flag: bool # True if price was mentioned
    session_active: bool # True if within 6h window
    lead_score: int # 0-100
    
    # --- PRODUCT CONTEXT (Multi-product support) ---
    product_id: Optional[str] # UUID of the active product being discussed
    launch_stage: ProductLaunchStage

    # --- ROUTING FIELDS (Hybrid Architecture) ---
    router_outcome: Literal["critical_objection", "rag_query", "sales_flow", "handled_safety", "direct_response"]
    objection_type: Optional[str] # 'medical', 'price', 'ai', 'tech'
    
    # --- COGNITIVE FIELDS ---
    latest_reasoning: Optional[str] # Chain of Thought trace from Manager
    active_strategy: Optional[str] # Strategy decided by Manager for the current turn

    # --- EXTRA CONTEXT FIELDS ---
    detected_intent: Optional[str]
    security_flag: Optional[str]
    priority_level: Optional[str]

def create_initial_state(
    user_id: str,
    history: List[Dict[str, str]],
    user_profile: Dict[str, Any],
    session_active: bool,
    # Optional Business Context
    active_enrollment: Optional[Any] = None,
    active_product: Optional[Any] = None,
    last_intent: Optional[str] = None
) -> AgentState:
    """
    Factory Method to ensure a valid, type-safe AgentState structure.
    Centralizes default values and business logic for state initialization.
    """
    
    # 1. Determine Funnel Stage
    initial_stage = FunnelStage.RAPPORT.value
    lead_score = 0
    
    if active_enrollment:
        if active_enrollment.stage:
            initial_stage = active_enrollment.stage
        if active_enrollment.lead_score:
            lead_score = active_enrollment.lead_score

    # 2. Determine Product Context
    # launch_stage_val = "evergreen"
    product_id_val = None
    
    if active_product:
        product_id_val = str(active_product.id)
        # Note: We assume launch_stage comes from caller logic or product attributes
        # For now, defaulting to evergreen or passed logic if we extend this factory
        # To keep signature simple, we might want to accept launch_stage as arg if it's complex calculation
    
    # Construct State
    return {
        # Mandatory Inputs
        "user_id": user_id,
        "messages": history,
        "user_profile": user_profile,
        "session_active": session_active,
        
        # Calculated / Business Logic
        "current_state": initial_stage,
        "lead_score": lead_score,
        "product_id": product_id_val,
        "launch_stage": ProductLaunchStage.EVERGREEN, # Default safe
        "last_intent": last_intent,

        # Default Safe Values (Avoid KeyErrors)
        "financial_flag": False,
        "disqualification_reason": None,
        "downsell_path": None,
        "detected_intent": None,
        "security_flag": "safe",
        "priority_level": "normal",
        "latest_reasoning": None,
        "active_strategy": None
    }

