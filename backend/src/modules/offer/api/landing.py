"""Landing generation endpoints exposed on the offer header.

Drives the ``/landing/status``, ``/landing/generate``, ``/landing/publish``,
``/landing/unpublish`` and ``/landing/regenerate`` buttons. All business
rules live in ``LandingGenerationService``; this layer only wires
dependencies and maps domain exceptions onto HTTP codes.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.offer.api.dto.landing_dtos import (
    LandingGenerateResponse,
    LandingPublishResponse,
    LandingStatusResponse,
    LandingUnpublishResponse,
)
from src.modules.offer.application.offer_service import OfferService
from src.modules.offer.application.services.landing_generation_service import (
    LandingGenerationService,
)
from src.modules.offer.application.services.offer_completion_service import (
    OfferCompletionService,
)
from src.modules.offer.domain.exceptions import LandingNotReadyError
from src.modules.offer.infrastructure.repositories.stub_landing_generation_repository import (
    StubLandingGenerationRepository,
)

router = APIRouter()


def _build_service(db: Session) -> LandingGenerationService:
    offer_service = OfferService(db)
    completion_service = OfferCompletionService(offer_service=offer_service)
    return LandingGenerationService(
        completion_service=completion_service,
        landing_repo=StubLandingGenerationRepository(),
        offer_service=offer_service,
    )


def _map_landing_not_ready(exc: LandingNotReadyError) -> HTTPException:
    return HTTPException(
        status_code=422,
        detail={
            "error": "landing_not_ready",
            "completion_percentage": exc.completion_percentage,
            "required": 90.0,
        },
    )


@router.get("/{offer_id}/landing/status", response_model=LandingStatusResponse)
async def get_landing_status(
    offer_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LandingStatusResponse:
    """Return the current landing generation/publish state."""
    service = _build_service(db)
    status = service.get_status(
        tenant_id=user.tenant_id,
        offer_id=UUID(offer_id),
    )
    return LandingStatusResponse(
        generated_at=status.get("generated_at"),
        is_published=bool(status.get("is_published", False)),
        offer_snapshot_version=status.get("offer_snapshot_version"),
        is_outdated=bool(status.get("is_outdated", False)),
        job_id=status.get("job_id"),
        job_status=status.get("job_status") or "idle",
    )


@router.post(
    "/{offer_id}/landing/generate",
    response_model=LandingGenerateResponse,
)
async def generate_landing(
    offer_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LandingGenerateResponse:
    """Queue an initial landing generation job."""
    service = _build_service(db)
    try:
        result = service.generate(
            tenant_id=user.tenant_id,
            offer_id=UUID(offer_id),
        )
    except LandingNotReadyError as exc:
        raise _map_landing_not_ready(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return LandingGenerateResponse(
        job_id=result["job_id"],
        job_status=result["job_status"],
        snapshot_version=result["snapshot_version"],
    )


@router.post(
    "/{offer_id}/landing/regenerate",
    response_model=LandingGenerateResponse,
)
async def regenerate_landing(
    offer_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LandingGenerateResponse:
    """Queue a regeneration of the landing."""
    service = _build_service(db)
    try:
        result = service.regenerate(
            tenant_id=user.tenant_id,
            offer_id=UUID(offer_id),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return LandingGenerateResponse(
        job_id=result["job_id"],
        job_status=result["job_status"],
        snapshot_version=result["snapshot_version"],
    )


@router.post(
    "/{offer_id}/landing/publish",
    response_model=LandingPublishResponse,
)
async def publish_landing(
    offer_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LandingPublishResponse:
    """Publish the landing (sets ``is_published=True``)."""
    service = _build_service(db)
    try:
        service.publish(
            tenant_id=user.tenant_id,
            offer_id=UUID(offer_id),
        )
    except LandingNotReadyError as exc:
        raise _map_landing_not_ready(exc) from exc
    return LandingPublishResponse(is_published=True)


@router.post(
    "/{offer_id}/landing/unpublish",
    response_model=LandingUnpublishResponse,
)
async def unpublish_landing(
    offer_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LandingUnpublishResponse:
    """Unpublish the landing (sets ``is_published=False``)."""
    service = _build_service(db)
    try:
        service.unpublish(
            tenant_id=user.tenant_id,
            offer_id=UUID(offer_id),
        )
    except LandingNotReadyError as exc:
        raise _map_landing_not_ready(exc) from exc
    return LandingUnpublishResponse(is_published=False)
