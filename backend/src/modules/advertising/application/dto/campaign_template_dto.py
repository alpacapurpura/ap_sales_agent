"""DTOs for campaign templates (base of future Action Trigger)."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


def _to_camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


class AdCampaignTemplateDTO(BaseModel):
    """Data transfer object for ad campaign template."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=_to_camel,
    )

    id: UUID
    offer_archetype: str
    offer_onboarding_action: str | None = None
    offer_is_lead_magnet: bool | None = None
    name: str
    description: str | None = None
    recommended_objective: str
    recommended_objective_label_es: str
    recommended_optimization_goal: str | None = None
    recommended_destination_type: str | None = None
    structure_hints: dict = {}
    priority: int = 0
