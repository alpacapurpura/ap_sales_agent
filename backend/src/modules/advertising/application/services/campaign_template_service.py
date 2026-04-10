"""Read-only service over ad_campaign_templates.

Base of the future Action Trigger feature: in a later iteration, a companion
service will take the template returned here and create a real Meta campaign
via the Marketing API. For now this layer only serves suggestions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.modules.advertising.application.dto.campaign_template_dto import (
    AdCampaignTemplateDTO,
)
from src.modules.advertising.domain.enums import objective_label_es
from src.modules.advertising.infrastructure.repositories.campaign_template_repository import (
    CampaignTemplateRepository,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

    from src.shared.domain.ports import OfferReadPort


class CampaignTemplateService:
    """Match an offer with the best-fit campaign template."""

    def __init__(self, db: Session, offer_read_port: OfferReadPort) -> None:
        self._db = db
        self._offer_read_port = offer_read_port
        self._template_repo = CampaignTemplateRepository(db)

    async def get_template_for_offer(
        self, tenant_id: UUID, offer_id: UUID
    ) -> AdCampaignTemplateDTO | None:
        """Return the best matching template for an offer, or None."""
        offer = await self._offer_read_port.get_offer_by_id(offer_id, tenant_id)
        if offer is None:
            return None

        template = self._template_repo.find_best_match(
            archetype=offer.offer_type or "",
            onboarding_action=offer.onboarding_action,
            is_lead_magnet=offer.is_lead_magnet,
        )
        if template is None:
            return None

        return AdCampaignTemplateDTO(
            id=template.id,
            offer_archetype=template.offer_archetype,
            offer_onboarding_action=template.offer_onboarding_action,
            offer_is_lead_magnet=template.offer_is_lead_magnet,
            name=template.name,
            description=template.description or "",
            recommended_objective=template.recommended_objective,
            recommended_objective_label_es=objective_label_es(
                template.recommended_objective
            ),
            recommended_optimization_goal=template.recommended_optimization_goal,
            recommended_destination_type=template.recommended_destination_type,
            structure_hints=template.structure_hints or {},
            priority=template.priority or 0,
        )
