"""DTOs for offer-campaign associations."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


def _to_camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


class _CamelModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=_to_camel,
    )


class AssociationDTO(_CamelModel):
    """Serialized association with resolved offer metadata."""

    id: UUID
    tenant_id: UUID
    target_type: Literal["campaign", "ad_set"]
    target_external_id: str
    offer_id: UUID | None = None
    offer_name: str | None = None
    offer_archetype: str | None = None
    association_type: str
    confidence: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class AssociationCreateDTO(_CamelModel):
    """Input DTO for creating a new association via API."""

    target_type: Literal["campaign", "ad_set"]
    target_external_id: str
    offer_id: UUID | None = None
    association_type: Literal["manual", "excluded_branding"]
    notes: str | None = None


class AssociationSuggestionDTO(_CamelModel):
    """A single auto-detected suggestion; not persisted until confirmed."""

    target_type: Literal["campaign", "ad_set"]
    target_external_id: str
    target_name: str
    suggested_offer_id: UUID
    suggested_offer_name: str
    association_type: Literal["auto_landing_url", "auto_keyword", "auto_objective"]
    confidence: Literal["high", "medium", "low"]
    reason: str


class ApplySuggestionItemDTO(_CamelModel):
    """Item used when applying one or more suggestions in bulk."""

    target_type: Literal["campaign", "ad_set"]
    target_external_id: str
    offer_id: UUID
    association_type: Literal["auto_landing_url", "auto_keyword", "auto_objective"]
    confidence: Literal["high", "medium", "low"]


class OfferSummaryDTO(_CamelModel):
    """Compact offer projection for the assignment drawer dropdown.

    Lists every active offer from the tenant's Offer Studio regardless of
    whether it already has an association — the drawer uses this to populate
    the dropdown so users can assign a campaign to ANY offer.
    """

    id: UUID
    name: str
    archetype: str
    expected_metric: str
    expected_metric_label_es: str
    is_lead_magnet: bool
