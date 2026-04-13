"""API endpoints for launch editions (sub-resource of offers)."""

from datetime import datetime
from typing import Any
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
from src.modules.offer.domain.launch_edition import LaunchEdition

router = APIRouter()


class LaunchEditionCreateDTO(BaseModel):
    edition_name: str | None = None
    start_date: datetime
    end_date: datetime | None = None
    registration_start: datetime | None = None
    registration_end: datetime | None = None
    timezone: str = "UTC"
    pricing_override: list[dict[str, Any]] | None = None
    capacity: int | None = None
    location_override: dict[str, Any] | None = None
    notes: str | None = None


class LaunchEditionUpdateDTO(BaseModel):
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
    location_override: dict[str, Any] | None = None
    notes: str | None = None


class LaunchEditionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    offer_id: UUID
    edition_name: str
    edition_number: int
    start_date: datetime
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
    location_override: dict[str, Any] | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_domain(
        cls,
        edition: LaunchEdition,
        effective_pricing: list[dict[str, Any]],
        currency: str,
    ) -> "LaunchEditionResponse":
        pricing_override = None
        if edition.pricing_override is not None:
            pricing_override = [
                p.model_dump(mode="json") for p in edition.pricing_override
            ]
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
            status=edition.status.value
            if hasattr(edition.status, "value")
            else edition.status,
            location_override=edition.location_override,
            notes=edition.notes,
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
    response_model=list[LaunchEditionResponse],
)
async def list_editions(
    offer_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = LaunchEditionService(db)
    editions = svc.list_editions(UUID(offer_id), user.tenant_id)
    return [_build_response(svc, e, user.tenant_id) for e in editions]


@router.post(
    "/{offer_id}/editions",
    response_model=LaunchEditionResponse,
    status_code=201,
)
async def create_edition(
    offer_id: str,
    body: LaunchEditionCreateDTO,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
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
    "/{offer_id}/editions/{edition_id}",
    response_model=LaunchEditionResponse,
)
async def get_edition(
    offer_id: str,
    edition_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = LaunchEditionService(db)
    edition = svc.get_edition(UUID(edition_id), user.tenant_id)
    if not edition or str(edition.offer_id) != offer_id:
        raise HTTPException(status_code=404, detail="Edition not found")
    return _build_response(svc, edition, user.tenant_id)


@router.patch(
    "/{offer_id}/editions/{edition_id}",
    response_model=LaunchEditionResponse,
)
async def update_edition(
    offer_id: str,
    edition_id: str,
    body: LaunchEditionUpdateDTO,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = LaunchEditionService(db)
    try:
        edition = svc.update_edition(
            UUID(edition_id),
            user.tenant_id,
            body.model_dump(exclude_unset=True),
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Edition not found") from None
    return _build_response(svc, edition, user.tenant_id)


@router.delete(
    "/{offer_id}/editions/{edition_id}",
    status_code=204,
)
async def delete_edition(
    offer_id: str,
    edition_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = LaunchEditionService(db)
    svc.delete_edition(UUID(edition_id), user.tenant_id)


@router.post(
    "/{offer_id}/editions/{edition_id}/duplicate",
    response_model=LaunchEditionResponse,
    status_code=201,
)
async def duplicate_edition(
    offer_id: str,
    edition_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = LaunchEditionService(db)
    try:
        edition = svc.duplicate_edition(UUID(edition_id), user.tenant_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Edition not found") from None
    return _build_response(svc, edition, user.tenant_id)
