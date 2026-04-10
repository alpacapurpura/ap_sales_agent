"""FastAPI router for the advertising module."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.core.database import get_db
from src.modules.advertising.application.dto.association_dto import (
    ApplySuggestionItemDTO,
    AssociationCreateDTO,
    AssociationDTO,
    AssociationSuggestionDTO,
    OfferSummaryDTO,
)
from src.modules.advertising.application.dto.campaign_template_dto import (
    AdCampaignTemplateDTO,
)
from src.modules.advertising.application.dto.health_check_dto import (
    MetaHealthCheckDTO,
)
from src.modules.advertising.application.dto.metrics_by_offer_dto import (
    MetricsByOfferDTO,
)
from src.modules.advertising.application.services import (
    CampaignTemplateService,
    HealthCheckService,
    MetricsByOfferService,
    OfferDetectionService,
)
from src.modules.advertising.domain.enums import (
    AssociationTargetType,
    AssociationType,
    expected_metric_label_es,
    resolve_expected_metric,
)
from src.modules.advertising.infrastructure.repositories.association_repository import (
    AssociationRepository,
)
from src.modules.iam.api.dependencies import get_current_user
from src.modules.offer.application.services.offer_read_port_impl import (
    OfferReadPortImpl,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from src.modules.advertising.infrastructure.models.ad_offer_association_model import (
        AdOfferAssociationModel,
    )
    from src.modules.iam.domain.user import User
    from src.shared.domain.ports import OfferReadDTO, OfferReadPort

router = APIRouter(prefix="/advertising", tags=["Advertising"])


# ── Helpers ────────────────────────────────────────────────────────────────


def _tenant_id(user: User) -> UUID:
    tenant = user.tenant_id
    if tenant is None:
        raise HTTPException(status_code=403, detail="Tenant context required")
    if isinstance(tenant, UUID):
        return tenant
    return UUID(str(tenant))


def _get_offer_port(db: Session) -> OfferReadPort:
    return OfferReadPortImpl(db)


async def _association_to_dto(
    row: AdOfferAssociationModel,
    offer_port: OfferReadPort,
    tenant_id: UUID,
) -> AssociationDTO:
    offer_name: str | None = None
    offer_archetype: str | None = None
    if row.offer_id is not None:
        offer: OfferReadDTO | None = await offer_port.get_offer_by_id(
            row.offer_id, tenant_id
        )
        if offer is not None:
            offer_name = offer.public_name
            offer_archetype = offer.offer_type
    return AssociationDTO(
        id=row.id,
        tenant_id=row.tenant_id,
        target_type=row.target_type,  # type: ignore[arg-type]
        target_external_id=row.target_external_id,
        offer_id=row.offer_id,
        offer_name=offer_name,
        offer_archetype=offer_archetype,
        association_type=row.association_type,
        confidence=row.confidence,
        notes=row.notes,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


# ── Associations endpoints ─────────────────────────────────────────────────


@router.post(
    "/associations",
    response_model=AssociationDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_association(
    payload: AssociationCreateDTO,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssociationDTO:
    """Create or replace an association between a Meta target and an offer."""
    tenant = _tenant_id(user)
    # Business rule: excluded_branding must have offer_id=None.
    if payload.association_type == "excluded_branding" and payload.offer_id is not None:
        raise HTTPException(
            status_code=422,
            detail="excluded_branding associations must not reference an offer",
        )
    if payload.association_type != "excluded_branding" and payload.offer_id is None:
        raise HTTPException(
            status_code=422,
            detail="offer_id is required for this association type",
        )

    repo = AssociationRepository(db)
    row = repo.create(
        tenant_id=tenant,
        target_type=AssociationTargetType(payload.target_type),
        target_external_id=payload.target_external_id,
        offer_id=payload.offer_id,
        association_type=AssociationType(payload.association_type),
        notes=payload.notes,
    )
    db.commit()
    db.refresh(row)
    dto = await _association_to_dto(row, _get_offer_port(db), tenant)
    return dto


@router.delete(
    "/associations/{association_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_association(
    association_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    tenant = _tenant_id(user)
    repo = AssociationRepository(db)
    deleted = repo.soft_delete(tenant, association_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Association not found")
    db.commit()


@router.get("/associations", response_model=list[AssociationDTO])
async def list_associations(
    target_type: str | None = Query(default=None),
    offer_id: UUID | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AssociationDTO]:
    tenant = _tenant_id(user)
    repo = AssociationRepository(db)
    ttype = AssociationTargetType(target_type) if target_type else None
    rows = repo.list_active(tenant, target_type=ttype, offer_id=offer_id)
    port = _get_offer_port(db)
    return [await _association_to_dto(r, port, tenant) for r in rows]


@router.get("/offers", response_model=list[OfferSummaryDTO])
async def list_offers_for_assignment(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[OfferSummaryDTO]:
    """List every active offer from the Offer Studio for the assignment drawer.

    Unlike /metrics-by-offer (which only returns offers that already have
    associations), this endpoint returns ALL active offers so users can pick
    any of them when associating a campaign.
    """
    tenant = _tenant_id(user)
    port = _get_offer_port(db)
    offers = await port.get_offers_by_tenant(tenant)
    active_offers = [
        o for o in offers if (o.status or "active") not in {"archived", "draft"}
    ]
    out: list[OfferSummaryDTO] = []
    for o in active_offers:
        expected = resolve_expected_metric(
            archetype=o.offer_type,
            onboarding_action=o.onboarding_action,
            is_lead_magnet=o.is_lead_magnet,
            has_checkout_url=bool(o.checkout_page_url),
        )
        out.append(
            OfferSummaryDTO(
                id=o.id,
                name=o.public_name,
                archetype=o.offer_type,
                expected_metric=expected.value,
                expected_metric_label_es=expected_metric_label_es(expected.value),
                is_lead_magnet=o.is_lead_magnet,
            )
        )
    return out


@router.post("/associations/auto-detect", response_model=list[AssociationSuggestionDTO])
async def auto_detect_associations(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AssociationSuggestionDTO]:
    tenant = _tenant_id(user)
    port = _get_offer_port(db)
    svc = OfferDetectionService(db, port)
    return await svc.detect(tenant)


@router.post(
    "/associations/apply-suggestions",
    response_model=list[AssociationDTO],
)
async def apply_suggestions(
    items: list[ApplySuggestionItemDTO],
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AssociationDTO]:
    tenant = _tenant_id(user)
    repo = AssociationRepository(db)
    port = _get_offer_port(db)
    saved: list[AssociationDTO] = []
    for item in items:
        row = repo.create(
            tenant_id=tenant,
            target_type=AssociationTargetType(item.target_type),
            target_external_id=item.target_external_id,
            offer_id=item.offer_id,
            association_type=AssociationType(item.association_type),
            confidence=item.confidence,
        )
        saved.append(await _association_to_dto(row, port, tenant))
    db.commit()
    return saved


# ── Health check ───────────────────────────────────────────────────────────


@router.get("/health-check", response_model=MetaHealthCheckDTO)
async def get_health_check(
    provider: str = Query(default="meta"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MetaHealthCheckDTO:
    """Diagnostic snapshot of the tenant's Meta Ads account configuration."""
    if provider != "meta":
        raise HTTPException(status_code=400, detail="Only 'meta' is supported")
    tenant = _tenant_id(user)
    port = _get_offer_port(db)
    svc = HealthCheckService(db, port)
    return await svc.run(tenant)


# ── Metrics by offer ───────────────────────────────────────────────────────


@router.get("/metrics-by-offer", response_model=MetricsByOfferDTO)
async def get_metrics_by_offer(
    period: str = Query(default="30d"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MetricsByOfferDTO:
    """Return Meta ads metrics aggregated per offer."""
    if period not in {"7d", "30d", "90d"}:
        raise HTTPException(
            status_code=400,
            detail="Invalid period — must be one of 7d, 30d, 90d",
        )
    tenant = _tenant_id(user)
    port = _get_offer_port(db)
    svc = MetricsByOfferService(db, port)
    return await svc.run(tenant, period=period)


# ── Campaign templates ─────────────────────────────────────────────────────


@router.get("/campaign-templates/suggest", response_model=AdCampaignTemplateDTO)
async def suggest_campaign_template(
    offer_id: UUID = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AdCampaignTemplateDTO:
    tenant = _tenant_id(user)
    port = _get_offer_port(db)
    svc = CampaignTemplateService(db, port)
    result = await svc.get_template_for_offer(tenant, offer_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No matching template for this offer",
        )
    return result


__all__ = ["router"]
