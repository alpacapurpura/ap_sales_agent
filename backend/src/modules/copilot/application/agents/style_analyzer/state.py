from typing import TypedDict, List, Optional, Dict, Any

class StyleProfile(TypedDict):
    tone: str
    signature_phrases: List[str]
    emoji_density: str
    response_structure: str
    key_characteristics: List[str]

class OnboardingState(TypedDict):
    # Input
    user_id: str
    raw_input: str
    target_url: Optional[str] # URL to research
    
    # Processing Stages
    cleaned_input: Optional[str]
    style_profile: Optional[StyleProfile]
    research_summary: Optional[str] # Results from Research Agent
    offer_context: Optional[Dict[str, Any]] # Serialized HighTicketOffer
    
    system_instruction: Optional[str]
    
    # Validation
    simulation_examples: List[str]
    
    # Error Handling
    error: Optional[str]
