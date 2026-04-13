"""Domain entity: AdOfferAssociation.

Pure Pydantic model — no framework dependencies. Represents a single
association between a Meta campaign (or ad set) and an Offer from the
Offer Studio.
"""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.modules.advertising.domain.enums import (
    AssociationConfidence,
    AssociationTargetType,
    AssociationType,
)


class AdOfferAssociation(BaseModel):
    """Association between a Meta target (campaign or ad set) and an offer."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    provider: str = "meta"
    target_type: AssociationTargetType
    target_external_id: str
    offer_id: UUID | None = None
    association_type: AssociationType
    confidence: AssociationConfidence | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

    @model_validator(mode="after")
    def _validate_offer_rules(self) -> "AdOfferAssociation":
        """Enforce business rules around offer_id/association_type pairing."""
        if self.association_type == AssociationType.EXCLUDED_BRANDING:
            # Branding exclusions must NOT point to an offer.
            if self.offer_id is not None:
                msg = "excluded_branding associations cannot have offer_id set"
                raise ValueError(msg)
        # Every other association type requires an offer_id.
        elif self.offer_id is None:
            msg = f"association_type={self.association_type.value} requires offer_id"
            raise ValueError(msg)
        return self
