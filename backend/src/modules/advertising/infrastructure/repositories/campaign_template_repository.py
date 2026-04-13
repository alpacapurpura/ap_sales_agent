"""Repository for AdCampaignTemplateModel — read-only."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.advertising.infrastructure.models.ad_campaign_template_model import (
    AdCampaignTemplateModel,
)


class CampaignTemplateRepository:
    """Data-access layer for ad_campaign_templates (tenant-agnostic)."""

    def __init__(self, db: Session) -> None:
        """Initialize CampaignTemplateRepository."""
        self._db = db

    def list_all(self) -> list[AdCampaignTemplateModel]:
        """List all."""
        stmt = select(AdCampaignTemplateModel).order_by(
            AdCampaignTemplateModel.priority.desc(),
        )
        result = self._db.execute(stmt)
        return list(result.scalars().all())

    def find_best_match(
        self,
        *,
        archetype: str,
        onboarding_action: str | None,
        is_lead_magnet: bool,
    ) -> AdCampaignTemplateModel | None:
        """Return the highest-priority template matching the offer traits.

        Matching rules, in order of strictness:
        1. (archetype, onboarding_action, is_lead_magnet) exact triple.
        2. (archetype, is_lead_magnet) with NULL onboarding_action.
        3. (archetype, onboarding_action) with NULL is_lead_magnet.
        4. (archetype) with NULL onboarding_action AND NULL is_lead_magnet.
        """
        templates = self.list_all()
        archetype_upper = (archetype or "").upper()
        matches = [t for t in templates if (t.offer_archetype or "").upper() == archetype_upper]
        if not matches:
            return None

        def score(t: AdCampaignTemplateModel) -> int:
            s = 0
            if t.offer_onboarding_action is None or (
                onboarding_action and t.offer_onboarding_action == onboarding_action
            ):
                if onboarding_action and t.offer_onboarding_action == onboarding_action:
                    s += 20
                elif t.offer_onboarding_action is None and not onboarding_action:
                    s += 10
            else:
                # Mismatch on onboarding action — disqualify unless NULL.
                return -1

            if t.offer_is_lead_magnet is None:
                s += 5
            elif t.offer_is_lead_magnet == is_lead_magnet:
                s += 15
            else:
                return -1

            s += t.priority or 0
            return s

        scored = [(score(t), t) for t in matches]
        scored = [(sc, t) for sc, t in scored if sc >= 0]
        if not scored:
            return None
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return scored[0][1]
