"""Lifecycle transitions for the offer header status switcher.

Exposes ``POST /{offer_id}/status`` which the Draft/Active/Paused/Archived
switcher calls. Maps domain exceptions to HTTP status codes; all business
rules live in ``OfferLifecycleService``.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from luana_core_iam.api.dependencies import get_current_user
from luana_core_iam.domain.user import User
from luana_core_offer_studio.api.dto.lifecycle_dtos import (
    OfferStatusChangeRequest,
    OfferStatusChangeResponse,
)
from luana_core_offer_studio.application.offer_service import OfferService
from luana_core_offer_studio.application.services.offer_lifecycle_service import (
    OfferLifecycleService,
)
from luana_core_offer_studio.domain.exceptions import InvalidTransitionError
from luana_core_platform.core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/{offer_id}/status")
async def change_offer_status(
    offer_id: str,
    body: OfferStatusChangeRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
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
