"""Offer tab-bar counts endpoint.

Returns aggregated counts (assets, campaigns, knowledge) used by the
header tab bar. Delegates entirely to ``OfferCountsService``.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from luana_core_iam.api.dependencies import get_current_user
from luana_core_iam.domain.user import User
from luana_core_offer_studio.api.dto.counts_dtos import OfferCountsResponse
from luana_core_offer_studio.application.services.offer_counts_service import (
    OfferCountsService,
)
from luana_core_offer_studio.infrastructure.repositories.knowledge_source_repository import (
    KnowledgeSourceRepository,
)
from luana_core_offer_studio.infrastructure.repositories.offer_asset_repository import (
    OfferAssetRepository,
)
from luana_core_platform.core.database import get_db
from sqlalchemy.orm import Session

# DDD exception (intentional): api/ composition root — offer counts endpoint
# aggregates advertising stats alongside offer KPIs. Cross-module read at the
# API layer is correct orchestration, not accidental coupling.
from src.modules.advertising.application.services.offer_campaigns_read_adapter import (
    OfferCampaignsReadAdapter,
)

router = APIRouter()


@router.get("/{offer_id}/counts")
async def get_offer_counts(
    offer_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> OfferCountsResponse:
    """Return the tab-bar counts for the given offer."""
    service = OfferCountsService(
        asset_repo=OfferAssetRepository(db),
        knowledge_repo=KnowledgeSourceRepository(db),
        advertising_port=OfferCampaignsReadAdapter(),
    )
    counts = service.get_counts(
        tenant_id=user.tenant_id,
        offer_id=UUID(offer_id),
    )
    return OfferCountsResponse(
        assets=counts.get("assets", 0),
        campaigns=counts.get("campaigns", 0),
        knowledge=counts.get("knowledge", 0),
    )
