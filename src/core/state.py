from typing import TypedDict, List, Optional, Literal, Dict, Any

class AgentState(TypedDict):
    user_id: str
    messages: List[Dict[str, str]]  # History of messages [{"role": "user", "content": "..."}, ...]
    current_state: Literal["S1_Rapport", "S2_Discovery", "S3_Gap", "S4_Pitch", "S5_Anchoring", "S6_Closing", "DOWNSELL_EXIT"]
    user_profile: dict   # Extracted info: {occupation, pain_point, budget_tier, etc.}
    last_intent: Optional[str]
    disqualification_reason: Optional[str] # Nuevo campo para tracking de rechazos
    downsell_path: Optional[str] # 'masterclass', 'community', 'none'
    financial_flag: bool # True if price was mentioned
    session_active: bool # True if within 6h window
    
    # --- ROUTING FIELDS (Hybrid Architecture) ---
    router_outcome: Literal["critical_objection", "rag_query", "sales_flow"]
    objection_type: Optional[str] # 'medical', 'price', 'ai', 'tech'
