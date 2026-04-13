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
