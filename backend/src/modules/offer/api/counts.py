"""Offer tab-bar counts endpoint.

Returns aggregated counts (assets, campaigns, knowledge) used by the
header tab bar. Delegates entirely to ``OfferCountsService``.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.advertising.application.services.offer_campaigns_read_adapter import (
    OfferCampaignsReadAdapter,
)
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.offer.api.dto.counts_dtos import OfferCountsResponse
from src.modules.offer.application.services.offer_counts_service import (
    OfferCountsService,
)
from src.modules.offer.infrastructure.repositories.knowledge_source_repository import (
    KnowledgeSourceRepository,
)
from src.modules.offer.infrastructure.repositories.offer_asset_repository import (
    OfferAssetRepository,
)

router = APIRouter()


@router.get("/{offer_id}/counts", response_model=OfferCountsResponse)
async def get_offer_counts(
    offer_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
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
