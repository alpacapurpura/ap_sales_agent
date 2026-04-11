"""Lifecycle transitions for the offer header status switcher.

Exposes ``POST /{offer_id}/status`` which the Draft/Active/Paused/Archived
switcher calls. Maps domain exceptions to HTTP status codes; all business
rules live in ``OfferLifecycleService``.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.offer.api.dto.lifecycle_dtos import (
    OfferStatusChangeRequest,
    OfferStatusChangeResponse,
)
from src.modules.offer.application.offer_service import OfferService
from src.modules.offer.application.services.offer_lifecycle_service import (
    OfferLifecycleService,
)
from src.modules.offer.domain.exceptions import InvalidTransitionError

router = APIRouter()


@router.post("/{offer_id}/status", response_model=OfferStatusChangeResponse)
async def change_offer_status(
    offer_id: str,
    body: OfferStatusChangeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OfferStatusChangeResponse:
    """Transition an offer through the writable lifecycle states."""
    offer_service = OfferService(db)
    lifecycle_service = OfferLifecycleService(offer_service=offer_service)
    try:
        updated = lifecycle_service.change_status(
            offer_id=UUID(offer_id),
            new_status=body.new_status,
            tenant_id=user.tenant_id,
            actor_user_id=body.actor_user_id,
        )
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return OfferStatusChangeResponse(
        offer_id=updated.id,
        status=body.new_status,
    )
