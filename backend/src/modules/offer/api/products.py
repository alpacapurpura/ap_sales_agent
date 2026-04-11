from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user, get_tenant_locale
from src.modules.iam.domain.user import User
from src.modules.offer.api.dto.products import ProductCreate, ProductUpdate
from src.modules.offer.application.offer_service import OfferService
from src.modules.offer.domain.offer import (
    Offer,
    OfferClosingUpdate,
    OfferDetailsUpdate,
    OfferIdentityUpdate,
    OfferInstructorsUpdate,
    OfferPricingUpdate,
    OfferPromiseUpdate,
    OfferPsychologyUpdate,
    OfferResourcesUpdate,
    OfferStrategyUpdate,
    OfferValueStackUpdate,
    OfferVisualsUpdate,
)
from src.shared.domain.locale import TenantLocale

router = APIRouter()


@router.get("/metadata/hints", response_model=dict[str, Any])
async def get_offer_metadata():
    """Exposes business logic hints for UI components."""
    return {}


# NOTE: empty-string route (no trailing slash) instead of "/" — avoids a
# 307 redirect-loop when called through Next.js rewrites. Next.js strips
# trailing slashes from relative fetches before forwarding, so a "/"-anchored
# route would redirect to "/x/" which the browser then tries to fetch via
# the same rewrite, which strips the slash again, causing "TypeError: Failed
# to fetch". Mounting the route at "" lets it match the stripped path directly.
@router.get("", response_model=list[Offer])
async def list_products(
    limit: int = 20,
    skip: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = OfferService(db)
    # Filter by user's tenant
    return service.list_offers(user.tenant_id)


@router.post("", response_model=Offer)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    locale: TenantLocale = Depends(get_tenant_locale),
):
    service = OfferService(db)
    return service.create_offer(
        name=product.name,
        tenant_id=user.tenant_id,
        archetype=product.archetype,
        format_hint=product.format_hint,
        is_lead_magnet=product.is_lead_magnet,
        headline_promise=product.headline_promise or "",
        avatar_id=product.avatar_id,
        value_level=product.value_level,
        # Fall back to tenant default so new offers inherit the tenant's
        # configured currency (e.g. PEN) instead of a hardcoded USD.
        currency=product.currency or locale.currency,
    )


# NOTE: /archived must be registered BEFORE /{product_id} so FastAPI does
# not interpret "archived" as a UUID path parameter.
@router.get("/archived", response_model=list[Offer])
async def list_archived_products(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return offers that have been archived (reversible) but not deleted."""
    service = OfferService(db)
    return service.list_archived_offers(user.tenant_id)


@router.get("/{product_id}", response_model=Offer)
async def get_product(
    product_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = OfferService(db)
    product = service.get_offer(UUID(product_id), user.tenant_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/{product_id}/archive", response_model=Offer)
async def archive_product(
    product_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Archive an offer. Reversible via /restore.

    Also unpublishes the embedded landing page config as a side-effect.
    """
    service = OfferService(db)
    return service.archive_offer(UUID(product_id), user.tenant_id)


@router.post("/{product_id}/restore", response_model=Offer)
async def restore_product(
    product_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Restore a previously archived offer (clears archived_at).

    Landing pages are not auto-republished — user must republish manually.
    """
    service = OfferService(db)
    return service.restore_offer(UUID(product_id), user.tenant_id)


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Soft-delete an offer. Requires the offer to be archived first (409 otherwise).

    The offer is hidden from both the active and archived lists. Data is
    preserved in the DB (deleted_at timestamp) to keep foreign-key
    references intact (journey_events, sales, ads).
    """
    service = OfferService(db)
    service.delete_offer(UUID(product_id), user.tenant_id)


@router.patch("/{product_id}", response_model=Offer)
async def update_product(
    product_id: str,
    update: ProductUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = OfferService(db)
    try:
        return service.patch_offer(
            UUID(product_id), user.tenant_id, update.model_dump(exclude_unset=True)
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found")


@router.patch("/{product_id}/identity", response_model=Offer)
async def update_identity(
    product_id: str,
    update: OfferIdentityUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = OfferService(db)
    try:
        return service.patch_offer(
            UUID(product_id), user.tenant_id, update.model_dump(exclude_unset=True)
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found")


@router.patch("/{product_id}/strategy", response_model=Offer)
async def update_strategy(
    product_id: str,
    update: OfferStrategyUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = OfferService(db)
    try:
        return service.patch_offer(
            UUID(product_id), user.tenant_id, update.model_dump(exclude_unset=True)
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found")


@router.patch("/{product_id}/promise", response_model=Offer)
async def update_promise(
    product_id: str,
    update: OfferPromiseUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = OfferService(db)
    try:
        return service.patch_offer(
            UUID(product_id), user.tenant_id, update.model_dump(exclude_unset=True)
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found")


@router.patch("/{product_id}/psychology", response_model=Offer)
async def update_psychology(
    product_id: str,
    update: OfferPsychologyUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = OfferService(db)
    try:
        return service.patch_offer(
            UUID(product_id), user.tenant_id, update.model_dump(exclude_unset=True)
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found")


@router.patch("/{product_id}/value_stack", response_model=Offer)
async def update_value_stack(
    product_id: str,
    update: OfferValueStackUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = OfferService(db)
    try:
        return service.patch_offer(
            UUID(product_id), user.tenant_id, update.model_dump(exclude_unset=True)
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found")


@router.patch("/{product_id}/pricing", response_model=Offer)
async def update_pricing(
    product_id: str,
    update: OfferPricingUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = OfferService(db)
    try:
        return service.patch_offer(
            UUID(product_id), user.tenant_id, update.model_dump(exclude_unset=True)
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found")


@router.patch("/{product_id}/details", response_model=Offer)
async def update_details(
    product_id: str,
    update: OfferDetailsUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = OfferService(db)
    try:
        return service.patch_offer(
            UUID(product_id), user.tenant_id, update.model_dump(exclude_unset=True)
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found")


@router.patch("/{product_id}/visuals", response_model=Offer)
async def update_visuals(
    product_id: str,
    update: OfferVisualsUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = OfferService(db)
    try:
        return service.patch_offer(
            UUID(product_id), user.tenant_id, update.model_dump(exclude_unset=True)
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found")


@router.patch("/{product_id}/closing", response_model=Offer)
async def update_closing(
    product_id: str,
    update: OfferClosingUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = OfferService(db)
    try:
        return service.patch_offer(
            UUID(product_id), user.tenant_id, update.model_dump(exclude_unset=True)
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found")


@router.patch("/{product_id}/resources", response_model=Offer)
async def update_resources(
    product_id: str,
    update: OfferResourcesUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = OfferService(db)
    try:
        return service.patch_offer(
            UUID(product_id), user.tenant_id, update.model_dump(exclude_unset=True)
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found")


@router.patch("/{product_id}/instructors", response_model=Offer)
async def update_instructors(
    product_id: str,
    update: OfferInstructorsUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = OfferService(db)
    try:
        return service.patch_offer(
            UUID(product_id), user.tenant_id, update.model_dump(exclude_unset=True)
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found")
