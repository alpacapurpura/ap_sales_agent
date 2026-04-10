"""DTOs for Meta Ads account health check."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.modules.advertising.application.dto.association_dto import AssociationDTO


def _to_camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


class _CamelModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=_to_camel,
    )


class CampaignHealthDTO(_CamelModel):
    external_id: str
    name: str
    objective: str | None = None
    objective_label_es: str
    status: str | None = None
    offer_association: AssociationDTO | None = None
    expected_outcome_es: str
    has_issue: bool = False
    issue_text: str | None = None


class OfferCoverageDTO(_CamelModel):
    offer_id: UUID
    offer_name: str
    archetype: str
    expected_metric: str
    expected_metric_label_es: str
    has_active_campaign: bool
    associated_targets: list[AssociationDTO]


class UnassignedTargetDTO(_CamelModel):
    target_type: Literal["campaign", "ad_set"]
    external_id: str
    name: str
    objective: str | None = None
    status: str | None = None


class RecommendationDTO(_CamelModel):
    type: str
    severity: Literal["info", "warning", "critical"]
    title: str
    body: str
    action_label: str
    action_url: str | None = None
    related_offer_id: UUID | None = None
    related_target_id: str | None = None


class MetaHealthCheckDTO(_CamelModel):
    overall_status: Literal["healthy", "needs_attention", "critical"]
    active_campaigns: list[CampaignHealthDTO]
    offers_coverage: list[OfferCoverageDTO]
    unassigned_targets: list[UnassignedTargetDTO]
    recommendations: list[RecommendationDTO]
    summary_text: str
