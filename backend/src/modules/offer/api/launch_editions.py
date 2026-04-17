"""API endpoints for launch editions (sub-resource of offers)."""

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.offer.application.launch_edition_service import (
    LaunchEditionService,
)
from src.modules.offer.domain.launch_edition import (
    EditionVisibility,
    LaunchEdition,
)

router = APIRouter()


class LaunchEditionCreateDTO(BaseModel):
    """DTO for POST /offer/products/{id}/editions.

    ``start_date`` is optional to support placeholder editions: a DRAFT
    edition may be created without a date and filled in later. Domain
    validators block transitions to UPCOMING / ACTIVE / PUBLIC until
    ``start_date`` is set.
    """

    edition_name: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    registration_start: datetime | None = None
    registration_end: datetime | None = None
    timezone: str = "UTC"
    pricing_override: list[dict[str, Any]] | None = None
    capacity: int | None = None
    location_override: dict[str, Any] | None = None
    notes: str | None = None


class LaunchEditionUpdateDTO(BaseModel):
    """DTO for PATCH /offer/products/{id}/editions/{edition_id}."""

    edition_name: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    registration_start: datetime | None = None
    registration_end: datetime | None = None
    timezone: str | None = None
    pricing_override: list[dict[str, Any]] | None = None
    capacity: int | None = None
    enrollment_count: int | None = None
    status: str | None = None
    visibility: str | None = None
    location_override: dict[str, Any] | None = None
    notes: str | None = None


class LaunchEditionResponse(BaseModel):
    """Launch Edition Response DTO.

    ``start_date`` is optional so placeholder editions serialize cleanly.
    ``visibility`` exposes private/public to the frontend for status chips.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    offer_id: UUID
    edition_name: str
    edition_number: int
    start_date: datetime | None = None
    end_date: datetime | None = None
    registration_start: datetime | None = None
    registration_end: datetime | None = None
    timezone: str
    pricing_override: list[dict[str, Any]] | None = None
    effective_pricing: list[dict[str, Any]]
    currency: str
    capacity: int | None = None
    enrollment_count: int
    status: str
    visibility: str
    is_placeholder: bool
    location_override: dict[str, Any] | None = None
    notes: str | None = None
    cloned_from_edition_id: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_domain(
        cls,
        edition: LaunchEdition,
        effective_pricing: list[dict[str, Any]],
        currency: str,
    ) -> "LaunchEditionResponse":
        """Build response from a domain entity."""
        pricing_override = None
        if edition.pricing_override is not None:
            pricing_override = [p.model_dump(mode="json") for p in edition.pricing_override]

        status_value = edition.status.value if hasattr(edition.status, "value") else edition.status
        visibility_value = edition.visibility.value if hasattr(edition.visibility, "value") else edition.visibility

        # An edition is considered a placeholder when it has neither a
        # start_date nor a pricing override nor notes — i.e. it's the
        # default row auto-created by OfferService on offer birth.
        is_placeholder = (
            edition.start_date is None
            and edition.pricing_override is None
            and edition.visibility == EditionVisibility.PRIVATE
            and edition.status.value == "draft"
        )

        return cls(
            id=edition.id,
            offer_id=edition.offer_id,
            edition_name=edition.edition_name,
            edition_number=edition.edition_number,
            start_date=edition.start_date,
            end_date=edition.end_date,
            registration_start=edition.registration_start,
            registration_end=edition.registration_end,
            timezone=edition.timezone,
            pricing_override=pricing_override,
            effective_pricing=effective_pricing,
            currency=currency,
            capacity=edition.capacity,
            enrollment_count=edition.enrollment_count,
            status=status_value,
            visibility=visibility_value,
            is_placeholder=is_placeholder,
            location_override=edition.location_override,
            notes=edition.notes,
            cloned_from_edition_id=edition.cloned_from_edition_id,
            created_at=edition.created_at,
            updated_at=edition.updated_at,
        )


def _build_response(
    svc: LaunchEditionService,
    edition: LaunchEdition,
    tenant_id: UUID,
) -> LaunchEditionResponse:
    effective_pricing, currency = svc.resolve_effective_pricing(edition, tenant_id)
    return LaunchEditionResponse.from_domain(edition, effective_pricing, currency)


@router.get(
    "/{offer_id}/editions",
)
async def list_editions(
    offer_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[LaunchEditionResponse]:
    """List editions."""
    svc = LaunchEditionService(db)
    editions = svc.list_editions(UUID(offer_id), user.tenant_id)
    return [_build_response(svc, e, user.tenant_id) for e in editions]


@router.post(
    "/{offer_id}/editions",
    status_code=201,
)
async def create_edition(
    offer_id: str,
    body: LaunchEditionCreateDTO,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> LaunchEditionResponse:
    """Create edition."""
    svc = LaunchEditionService(db)
    from src.modules.offer.domain.offer import PricingStructure

    pricing = None
    if body.pricing_override is not None:
        pricing = [PricingStructure(**p) for p in body.pricing_override]

    try:
        edition = svc.create_edition(
            offer_id=UUID(offer_id),
            tenant_id=user.tenant_id,
            edition_name=body.edition_name,
            start_date=body.start_date,
            end_date=body.end_date,
            registration_start=body.registration_start,
            registration_end=body.registration_end,
            timezone=body.timezone,
            pricing_override=pricing,
            capacity=body.capacity,
            location_override=body.location_override,
            notes=body.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return _build_response(svc, edition, user.tenant_id)


@router.get(
    "/{offer_id}/editions/public",
)
async def list_public_editions(
    offer_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[LaunchEditionResponse]:
    """List editions discoverable by sales agent & public URLs.

    Filters: ``visibility=PUBLIC`` and ``status IN (UPCOMING, ACTIVE)``.
    Ordered ascending by ``start_date`` — caller picks ``[0]`` for the next
    edition to propose.

    Declared BEFORE the parametrized ``/{edition_id}`` route so FastAPI
    matches ``public`` as a literal segment instead of a UUID param.
    """
    svc = LaunchEditionService(db)
    editions = svc.list_public_editions(UUID(offer_id), user.tenant_id)
    return [_build_response(svc, e, user.tenant_id) for e in editions]


@router.get(
    "/{offer_id}/editions/{edition_id}",
)
async def get_edition(
    offer_id: str,
    edition_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> LaunchEditionResponse:
    """Retrieve edition."""
    svc = LaunchEditionService(db)
    edition = svc.get_edition(UUID(edition_id), user.tenant_id)
    if not edition or str(edition.offer_id) != offer_id:
        raise HTTPException(status_code=404, detail="Edition not found")
    return _build_response(svc, edition, user.tenant_id)


@router.patch(
    "/{offer_id}/editions/{edition_id}",
)
async def update_edition(
    offer_id: str,
    edition_id: str,
    body: LaunchEditionUpdateDTO,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> LaunchEditionResponse:
    """Patch fields on an edition.

    Returns 404 when the edition doesn't exist in this tenant, 422 when
    the patched state violates a domain invariant (e.g. publishing an
    edition without ``start_date``).
    """
    svc = LaunchEditionService(db)
    # Distinguish not-found vs validation error by checking existence first.
    if svc.get_edition(UUID(edition_id), user.tenant_id) is None:
        raise HTTPException(status_code=404, detail="Edition not found")
    try:
        edition = svc.update_edition(
            UUID(edition_id),
            user.tenant_id,
            body.model_dump(exclude_unset=True),
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return _build_response(svc, edition, user.tenant_id)


@router.post(
    "/{offer_id}/editions/{edition_id}/publish",
    status_code=200,
)
async def publish_edition(
    offer_id: str,
    edition_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> LaunchEditionResponse:
    """Promote an edition to UPCOMING + PUBLIC.

    Returns 422 if the edition is missing required fields (start_date,
    and archetype-specific fields enforced by the domain validator).
    """
    svc = LaunchEditionService(db)
    if svc.get_edition(UUID(edition_id), user.tenant_id) is None:
        raise HTTPException(status_code=404, detail="Edition not found")
    try:
        edition = svc.publish_edition(UUID(edition_id), user.tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return _build_response(svc, edition, user.tenant_id)


@router.post(
    "/{offer_id}/editions/{edition_id}/unpublish",
    status_code=200,
)
async def unpublish_edition(
    offer_id: str,
    edition_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> LaunchEditionResponse:
    """Flip an edition back to PRIVATE (does not change status)."""
    svc = LaunchEditionService(db)
    if svc.get_edition(UUID(edition_id), user.tenant_id) is None:
        raise HTTPException(status_code=404, detail="Edition not found")
    edition = svc.unpublish_edition(UUID(edition_id), user.tenant_id)
    return _build_response(svc, edition, user.tenant_id)


@router.delete(
    "/{offer_id}/editions/{edition_id}",
    status_code=204,
)
async def delete_edition(
    offer_id: str,
    edition_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete edition."""
    svc = LaunchEditionService(db)
    svc.delete_edition(UUID(edition_id), user.tenant_id)


@router.post(
    "/{offer_id}/editions/{edition_id}/duplicate",
    status_code=201,
)
async def duplicate_edition(
    offer_id: str,
    edition_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> LaunchEditionResponse:
    """Duplicate edition."""
    svc = LaunchEditionService(db)
    try:
        edition = svc.duplicate_edition(UUID(edition_id), user.tenant_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Edition not found") from None
    return _build_response(svc, edition, user.tenant_id)
