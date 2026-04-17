"""API endpoints for launch editions (sub-resource of offers)."""

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.offer.application.edition_clone_service import (
    CloneStrategy,
    EditionCloneService,
)
from src.modules.offer.application.launch_edition_service import (
    LaunchEditionService,
)
from src.modules.offer.domain.launch_edition import (
    LaunchEdition,
    LaunchEditionCreate,
    PricingTier,
)
from src.modules.offer.domain.offer import PricingStructure
from src.shared.links.ports.edition_landing_clone import (
    create_edition_landing_clone_port,
)

router = APIRouter()


class PricingTierDTO(BaseModel):
    """Temporal pricing tier (Phase 4).

    Mirrors :class:`PricingTier`. Half-open ``[valid_from, valid_until)``
    semantics — the resolver selects the first tier whose window
    contains "now" ordered by ``sort_order``.
    """

    label: str
    pricing: list[dict[str, Any]]
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    sort_order: int = 0


class LaunchEditionCreateDTO(BaseModel):
    """DTO for POST /offer/products/{id}/editions.

    ``start_date`` is optional to support placeholder editions: a DRAFT
    edition may be created without a date and filled in later. Domain
    validators block transitions to UPCOMING / ACTIVE / PUBLIC until
    ``start_date`` is set.

    ``pricing_override`` is being phased out in favour of
    ``pricing_tiers`` (Phase 4). The backend refuses to accept both in
    the same request so callers migrate cleanly; each existing edition
    stays readable through the column fallback until migration 048
    drops it.
    """

    edition_name: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    registration_start: datetime | None = None
    registration_end: datetime | None = None
    timezone: str = "UTC"
    pricing_override: list[dict[str, Any]] | None = None
    pricing_tiers: list[PricingTierDTO] | None = None
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
    pricing_tiers: list[PricingTierDTO] | None = None
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
    ``pricing_tiers`` + ``active_tier`` drive the Phase 4 temporal pricing
    UI; ``pricing_override`` is kept for backward-compat readers.
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
    pricing_tiers: list[PricingTierDTO] = Field(default_factory=list)
    active_tier: PricingTierDTO | None = None
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
        active_tier: PricingTier | None = None,
    ) -> "LaunchEditionResponse":
        """Build response from a domain entity."""
        pricing_override = None
        if edition.pricing_override is not None:
            pricing_override = [p.model_dump(mode="json") for p in edition.pricing_override]

        status_value = edition.status.value if hasattr(edition.status, "value") else edition.status
        visibility_value = edition.visibility.value if hasattr(edition.visibility, "value") else edition.visibility

        tier_dtos = [_tier_to_dto(tier) for tier in edition.pricing_tiers]
        active_dto = _tier_to_dto(active_tier) if active_tier is not None else None

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
            pricing_tiers=tier_dtos,
            active_tier=active_dto,
            effective_pricing=effective_pricing,
            currency=currency,
            capacity=edition.capacity,
            enrollment_count=edition.enrollment_count,
            status=status_value,
            visibility=visibility_value,
            # Delegated to the domain entity so every consumer uses the
            # same definition — no drift between API, frontend, copilot.
            is_placeholder=edition.is_placeholder,
            location_override=edition.location_override,
            notes=edition.notes,
            cloned_from_edition_id=edition.cloned_from_edition_id,
            created_at=edition.created_at,
            updated_at=edition.updated_at,
        )


def _tier_to_dto(tier: PricingTier) -> PricingTierDTO:
    """Serialize a domain tier to its API shape."""
    return PricingTierDTO(
        label=tier.label,
        pricing=[p.model_dump(mode="json") for p in tier.pricing],
        valid_from=tier.valid_from,
        valid_until=tier.valid_until,
        sort_order=tier.sort_order,
    )


def _build_tiers_from_input(raw: list[PricingTierDTO] | None) -> list[PricingTier] | None:
    """Turn the input DTO into the domain VO, raising on malformed pricing."""
    if raw is None:
        return None
    return [
        PricingTier(
            label=t.label,
            pricing=[PricingStructure(**p) for p in t.pricing],
            valid_from=t.valid_from,
            valid_until=t.valid_until,
            sort_order=t.sort_order,
        )
        for t in raw
    ]


def _reject_dual_pricing_input(override: list[dict[str, Any]] | None, tiers: list[PricingTierDTO] | None) -> None:
    """Prevent accidental dual-write while ``pricing_override`` is phased out."""
    if override is not None and tiers is not None:
        raise HTTPException(
            status_code=422,
            detail="Provide either pricing_override (legacy) or pricing_tiers (Phase 4), not both.",
        )


def _build_response(
    svc: LaunchEditionService,
    edition: LaunchEdition,
    tenant_id: UUID,
) -> LaunchEditionResponse:
    effective_pricing, currency, active_tier = svc.resolve_effective_pricing_full(edition, tenant_id)
    return LaunchEditionResponse.from_domain(edition, effective_pricing, currency, active_tier)


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
    _reject_dual_pricing_input(body.pricing_override, body.pricing_tiers)
    svc = LaunchEditionService(db)

    pricing = None
    if body.pricing_override is not None:
        pricing = [PricingStructure(**p) for p in body.pricing_override]

    try:
        tiers = _build_tiers_from_input(body.pricing_tiers)
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
            pricing_tiers=tiers,
            capacity=body.capacity,
            location_override=body.location_override,
            notes=body.notes,
        )
    except ValueError as e:
        # Archetype/offer-not-found vs pricing-tier validation — the
        # former is a 404, the latter a 422.
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e)) from e
        raise HTTPException(status_code=422, detail=str(e)) from e
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
    _reject_dual_pricing_input(body.pricing_override, body.pricing_tiers)
    svc = LaunchEditionService(db)
    # Distinguish not-found vs validation error by checking existence first.
    if svc.get_edition(UUID(edition_id), user.tenant_id) is None:
        raise HTTPException(status_code=404, detail="Edition not found")

    patch = body.model_dump(exclude_unset=True)
    # Replace the DTO list with domain VOs so repo-level serialization
    # can `.model_dump()` each tier consistently with other writes.
    if "pricing_tiers" in patch and body.pricing_tiers is not None:
        patch["pricing_tiers"] = _build_tiers_from_input(body.pricing_tiers)

    try:
        edition = svc.update_edition(
            UUID(edition_id),
            user.tenant_id,
            patch,
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
    """Duplicate edition — light-weight copy of dates/pricing/capacity only.

    Heavier clone flows (landing + assets + IA regen) live behind
    :class:`EditionCloneService` and the ``/clone`` endpoint below.
    """
    svc = LaunchEditionService(db)
    try:
        edition = svc.duplicate_edition(UUID(edition_id), user.tenant_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Edition not found") from None
    return _build_response(svc, edition, user.tenant_id)


class EditionCloneInputDTO(BaseModel):
    """New-edition values forwarded into :class:`LaunchEditionCreate`."""

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


class CloneEditionRequestDTO(BaseModel):
    """Body for the ``/clone`` endpoint.

    ``strategy`` is the canonical :class:`CloneStrategy` enum. The DTO
    narrows the type to the three supported string values so the OpenAPI
    schema is self-documenting.
    """

    strategy: CloneStrategy = Field(
        default=CloneStrategy.LITERAL,
        description="Controls how the source landing is transformed.",
    )
    new_edition_input: EditionCloneInputDTO
    changes_brief: str | None = None
    attachment_ids: list[UUID] | None = None


class CloneEditionResponseDTO(BaseModel):
    """Response for the ``/clone`` endpoint."""

    edition: LaunchEditionResponse
    landing_id: UUID | None = None
    landing_slug: str | None = None
    asset_ids: list[UUID] = Field(default_factory=list)


@router.post(
    "/{offer_id}/editions/{edition_id}/clone",
    status_code=201,
)
async def clone_edition(
    offer_id: str,
    edition_id: str,
    body: CloneEditionRequestDTO,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> CloneEditionResponseDTO:
    """Clone an edition, its landing, and its edition-scoped assets.

    Returns 404 when the source edition is missing or belongs to
    another tenant; 422 when the new-edition input violates a domain
    invariant (e.g. ``start_date``/``end_date`` inversion).
    """
    pricing = None
    if body.new_edition_input.pricing_override is not None:
        pricing = [PricingStructure(**p) for p in body.new_edition_input.pricing_override]

    create_input = LaunchEditionCreate(
        edition_name=body.new_edition_input.edition_name,
        start_date=body.new_edition_input.start_date,
        end_date=body.new_edition_input.end_date,
        registration_start=body.new_edition_input.registration_start,
        registration_end=body.new_edition_input.registration_end,
        timezone=body.new_edition_input.timezone,
        pricing_override=pricing,
        capacity=body.new_edition_input.capacity,
        location_override=body.new_edition_input.location_override,
        notes=body.new_edition_input.notes,
    )

    clone_service = EditionCloneService(
        db,
        landing_clone=create_edition_landing_clone_port(db),
    )

    try:
        result = clone_service.clone_edition(
            source_edition_id=UUID(edition_id),
            tenant_id=user.tenant_id,
            strategy=body.strategy,
            new_edition_input=create_input,
            changes_brief=body.changes_brief,
            attachment_ids=list(body.attachment_ids) if body.attachment_ids else None,
        )
    except ValueError as exc:
        # ``not found`` vs invariant violation — distinguish by message.
        if "not found" in str(exc):
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    edition_response = _build_response(
        LaunchEditionService(db),
        result.edition,
        user.tenant_id,
    )
    return CloneEditionResponseDTO(
        edition=edition_response,
        landing_id=result.landing.id if result.landing else None,
        landing_slug=result.landing.slug if result.landing else None,
        asset_ids=list(result.asset_ids),
    )


class EditionLandingResponseDTO(BaseModel):
    """Minimal edition-scoped landing lookup response."""

    landing_id: UUID | None = None
    slug: str | None = None
    is_published: bool = False


@router.get(
    "/{offer_id}/editions/{edition_id}/landing",
)
async def get_edition_landing(
    offer_id: str,
    edition_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> EditionLandingResponseDTO:
    """Return the landing bound to ``(offer, edition)`` if any.

    Falls back to an empty response (``landing_id=None``) so the frontend
    can render a "no landing yet — generate one?" CTA without a second
    existence check. Goes through the cross-module port rather than
    importing the landing repository directly.
    """
    # Validate edition ownership first so we don't expose other tenants' data.
    svc = LaunchEditionService(db)
    edition = svc.get_edition(UUID(edition_id), user.tenant_id)
    if edition is None or str(edition.offer_id) != offer_id:
        raise HTTPException(status_code=404, detail="Edition not found")

    port = create_edition_landing_clone_port(db)
    ref = port.get_for_edition(
        tenant_id=user.tenant_id,
        offer_id=UUID(offer_id),
        edition_id=UUID(edition_id),
    )
    if ref is None:
        return EditionLandingResponseDTO()
    return EditionLandingResponseDTO(
        landing_id=ref.id,
        slug=ref.slug,
        is_published=ref.is_published,
    )
