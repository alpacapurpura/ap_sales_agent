"""Read-only repository over analytics' Meta catalog tables.

This module is the documented exception where advertising reads directly
from analytics infrastructure models (ad_campaigns, ad_sets, ads). We
intentionally do NOT touch analytics services/repositories — only the
SQLAlchemy models. See tests/architecture/conftest.py for the allowlist
rationale.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from sqlalchemy import select

from src.modules.analytics.infrastructure.models.ad_campaign_model import (
    AdCampaignModel,
)
from src.modules.analytics.infrastructure.models.ad_model import AdModel
from src.modules.analytics.infrastructure.models.ad_set_model import AdSetModel

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session


@dataclass
class CampaignSnapshot:
    external_id: str
    name: str
    objective: str | None
    status: str | None
    effective_status: str | None


@dataclass
class AdSetSnapshot:
    external_id: str
    campaign_external_id: str
    name: str
    status: str | None
    effective_status: str | None
    optimization_goal: str | None
    destination_type: str | None


@dataclass
class AdSnapshot:
    external_id: str
    campaign_external_id: str
    ad_set_external_id: str
    name: str
    creative_link_url: str | None
    status: str | None


@dataclass
class MetaCatalog:
    """Full snapshot of the Meta catalog for a tenant."""

    campaigns: list[CampaignSnapshot] = field(default_factory=list)
    ad_sets: list[AdSetSnapshot] = field(default_factory=list)
    ads: list[AdSnapshot] = field(default_factory=list)

    def ad_sets_by_campaign(self, external_id: str) -> list[AdSetSnapshot]:
        return [s for s in self.ad_sets if s.campaign_external_id == external_id]

    def ads_for_ad_set(self, external_id: str) -> list[AdSnapshot]:
        return [a for a in self.ads if a.ad_set_external_id == external_id]


class MetaCatalogRepository:
    """Loader for the Meta catalog tables filtered by tenant."""

    def __init__(self, db: Session):
        self._db = db

    def load(self, tenant_id: UUID) -> MetaCatalog:
        """Return a consolidated snapshot of campaigns+ad_sets+ads."""
        campaigns_stmt = select(AdCampaignModel).where(
            AdCampaignModel.tenant_id == tenant_id,
            AdCampaignModel.deleted_at.is_(None),
        )
        campaigns = [
            CampaignSnapshot(
                external_id=c.external_id,
                name=c.name,
                objective=c.objective,
                status=c.status,
                effective_status=c.effective_status,
            )
            for c in self._db.execute(campaigns_stmt).scalars().all()
        ]

        ad_sets_stmt = select(AdSetModel).where(
            AdSetModel.tenant_id == tenant_id,
            AdSetModel.deleted_at.is_(None),
        )
        ad_sets = [
            AdSetSnapshot(
                external_id=s.external_id,
                campaign_external_id=s.campaign_external_id,
                name=s.name,
                status=s.status,
                effective_status=s.effective_status,
                optimization_goal=s.optimization_goal,
                destination_type=s.destination_type,
            )
            for s in self._db.execute(ad_sets_stmt).scalars().all()
        ]

        ads_stmt = select(AdModel).where(
            AdModel.tenant_id == tenant_id,
            AdModel.deleted_at.is_(None),
        )
        ads = [
            AdSnapshot(
                external_id=a.external_id,
                campaign_external_id=a.campaign_external_id,
                ad_set_external_id=a.ad_set_external_id,
                name=a.name,
                creative_link_url=a.creative_link_url,
                status=a.status,
            )
            for a in self._db.execute(ads_stmt).scalars().all()
        ]

        return MetaCatalog(campaigns=campaigns, ad_sets=ad_sets, ads=ads)
