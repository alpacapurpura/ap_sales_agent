"""Style analyzer agent state definitions."""

from typing import Any, TypedDict


class StyleProfile(TypedDict):
    """Define style profile typed dictionary."""

    tone: str
    signature_phrases: list[str]
    emoji_density: str
    response_structure: str
    key_characteristics: list[str]


class OnboardingState(TypedDict):
    """Define onboarding state typed dictionary."""

    # Input
    user_id: str
    raw_input: str
    target_url: str | None  # URL to research

    # Processing Stages
    cleaned_input: str | None
    style_profile: StyleProfile | None
    research_summary: str | None  # Results from Research Agent
    offer_context: dict[str, Any] | None  # Serialized HighTicketOffer

    system_instruction: str | None

    # Validation
    simulation_examples: list[str]

    # Error Handling
    error: str | None

    # ---------------------------------------------------------------
    # Personality Engine fields (6-node pipeline)
    # ---------------------------------------------------------------

    # Output of node_parser — parsed messages from chat export
    parsed_messages: list[dict]

    # Output of node_psychologist (new pipeline)
    personality_dimensions: dict  # {energy: 0.7, warmth: 0.8, ...}
    personality_linguistic_patterns: dict  # emoji_style, greeting, etc.
    personality_sample_exchanges: list[dict]  # best exchanges selected
    personality_confidence: float  # extraction confidence 0.0-1.0

    # Post-persist fields
    personality_profile_id: str  # UUID of created PersonalityProfileModel

    # Qdrant
    anchor_count: int  # number of style anchors upserted
