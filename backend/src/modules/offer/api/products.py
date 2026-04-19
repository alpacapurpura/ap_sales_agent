"""Products API endpoints."""

from typing import Annotated, Any
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
    PricingStructure,
)
from src.shared.domain.locale import TenantLocale

router = APIRouter()


@router.get("/metadata/hints")
async def get_offer_metadata() -> dict[str, Any]:
    """Exposes business logic hints for UI components."""
    return {}


# NOTE: empty-string route (no trailing slash) instead of "/" — avoids a
# 307 redirect-loop when called through Next.js rewrites. Next.js strips
# trailing slashes from relative fetches before forwarding, so a "/"-anchored
# route would redirect to "/x/" which the browser then tries to fetch via
# the same rewrite, which strips the slash again, causing "TypeError: Failed
# to fetch". Mounting the route at "" lets it match the stripped path directly.
@router.get("")
async def list_products(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    limit: int = 20,
    skip: int = 0,
) -> list[Offer]:
    """List products."""
    service = OfferService(db)
    # Filter by user's tenant
    return service.list_offers(user.tenant_id)


@router.post("")
async def create_product(
    product: ProductCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    locale: Annotated[TenantLocale, Depends(get_tenant_locale)],
) -> Offer:
    """Create product."""
    service = OfferService(db)
    # Resolved currency: explicit > tenant default. Used as the default
    # on both the offer AND each pricing plan that didn't specify its own.
    resolved_currency = product.currency or locale.currency
    pricing_options = _build_pricing_options(product.pricing_options, resolved_currency)
    return service.create_offer(
        name=product.name,
        tenant_id=user.tenant_id,
        archetype=product.archetype,
        format_hint=product.format_hint,
        preset_id=product.preset_id,
        is_lead_magnet=product.is_lead_magnet,
        has_editions=product.has_editions,
        headline_promise=product.headline_promise or "",
        avatar_id=product.avatar_id,
        value_level=product.value_level,
        currency=resolved_currency,
        pricing_options=pricing_options,
    )


def _build_pricing_options(
    raw: list[dict[str, Any]] | None,
    default_currency: str,
) -> list[PricingStructure]:
    """Convert the DTO pricing payload into domain ``PricingStructure`` records.

    Each plan inherits ``default_currency`` when it doesn't specify one
    — so tenants on PEN don't see their plans silently land on USD.
    """
    if not raw:
        return []
    result: list[PricingStructure] = []
    for plan in raw:
        payload = dict(plan)
        payload.setdefault("currency", default_currency)
        result.append(PricingStructure.model_validate(payload))
    return result


# NOTE: /archived must be registered BEFORE /{product_id} so FastAPI does
# not interpret "archived" as a UUID path parameter.
@router.get("/archived")
async def list_archived_products(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[Offer]:
    """Return offers that have been archived (reversible) but not deleted."""
    service = OfferService(db)
    return service.list_archived_offers(user.tenant_id)


@router.get("/{product_id}")
async def get_product(
    product_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Offer:
    """Retrieve product."""
    service = OfferService(db)
    product = service.get_offer(UUID(product_id), user.tenant_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/{product_id}/archive")
async def archive_product(
    product_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Offer:
    """Archive an offer. Reversible via /restore.

    Also unpublishes the embedded landing page config as a side-effect.
    """
    service = OfferService(db)
    return service.archive_offer(UUID(product_id), user.tenant_id)


@router.post("/{product_id}/restore")
async def restore_product(
    product_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Offer:
    """Restore a previously archived offer (clears archived_at).

    Landing pages are not auto-republished — user must republish manually.
    """
    service = OfferService(db)
    return service.restore_offer(UUID(product_id), user.tenant_id)


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Soft-delete an offer. Requires the offer to be archived first (409 otherwise).

    The offer is hidden from both the active and archived lists. Data is
    preserved in the DB (deleted_at timestamp) to keep foreign-key
    references intact (journey_events, sales, ads).
    """
    service = OfferService(db)
    service.delete_offer(UUID(product_id), user.tenant_id)


@router.patch("/{product_id}")
async def update_product(
    product_id: str,
    update: ProductUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Offer:
    """Update product."""
    service = OfferService(db)
    try:
        return service.patch_offer(
            UUID(product_id),
            user.tenant_id,
            update.model_dump(exclude_unset=True),
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found") from None


@router.patch("/{product_id}/identity")
async def update_identity(
    product_id: str,
    update: OfferIdentityUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Offer:
    """Update identity."""
    service = OfferService(db)
    try:
        return service.patch_offer(
            UUID(product_id),
            user.tenant_id,
            update.model_dump(exclude_unset=True),
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found") from None


@router.patch("/{product_id}/strategy")
async def update_strategy(
    product_id: str,
    update: OfferStrategyUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Offer:
    """Update strategy."""
    service = OfferService(db)
    try:
        return service.patch_offer(
            UUID(product_id),
            user.tenant_id,
            update.model_dump(exclude_unset=True),
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found") from None


@router.patch("/{product_id}/promise")
async def update_promise(
    product_id: str,
    update: OfferPromiseUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Offer:
    """Update promise."""
    service = OfferService(db)
    try:
        return service.patch_offer(
            UUID(product_id),
            user.tenant_id,
            update.model_dump(exclude_unset=True),
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found") from None


@router.patch("/{product_id}/psychology")
async def update_psychology(
    product_id: str,
    update: OfferPsychologyUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Offer:
    """Update psychology."""
    service = OfferService(db)
    try:
        return service.patch_offer(
            UUID(product_id),
            user.tenant_id,
            update.model_dump(exclude_unset=True),
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found") from None


@router.patch("/{product_id}/value_stack")
async def update_value_stack(
    product_id: str,
    update: OfferValueStackUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Offer:
    """Update value stack."""
    service = OfferService(db)
    try:
        return service.patch_offer(
            UUID(product_id),
            user.tenant_id,
            update.model_dump(exclude_unset=True),
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found") from None


@router.patch("/{product_id}/pricing")
async def update_pricing(
    product_id: str,
    update: OfferPricingUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Offer:
    """Update pricing."""
    service = OfferService(db)
    try:
        return service.patch_offer(
            UUID(product_id),
            user.tenant_id,
            update.model_dump(exclude_unset=True),
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found") from None


@router.patch("/{product_id}/details")
async def update_details(
    product_id: str,
    update: OfferDetailsUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Offer:
    """Update details."""
    service = OfferService(db)
    try:
        return service.patch_offer(
            UUID(product_id),
            user.tenant_id,
            update.model_dump(exclude_unset=True),
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found") from None


@router.patch("/{product_id}/visuals")
async def update_visuals(
    product_id: str,
    update: OfferVisualsUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Offer:
    """Update visuals."""
    service = OfferService(db)
    try:
        return service.patch_offer(
            UUID(product_id),
            user.tenant_id,
            update.model_dump(exclude_unset=True),
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found") from None


@router.patch("/{product_id}/closing")
async def update_closing(
    product_id: str,
    update: OfferClosingUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Offer:
    """Update closing."""
    service = OfferService(db)
    try:
        return service.patch_offer(
            UUID(product_id),
            user.tenant_id,
            update.model_dump(exclude_unset=True),
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found") from None


@router.patch("/{product_id}/resources")
async def update_resources(
    product_id: str,
    update: OfferResourcesUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Offer:
    """Update resources."""
    service = OfferService(db)
    try:
        return service.patch_offer(
            UUID(product_id),
            user.tenant_id,
            update.model_dump(exclude_unset=True),
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found") from None


@router.patch("/{product_id}/instructors")
async def update_instructors(
    product_id: str,
    update: OfferInstructorsUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Offer:
    """Update instructors."""
    service = OfferService(db)
    try:
        return service.patch_offer(
            UUID(product_id),
            user.tenant_id,
            update.model_dump(exclude_unset=True),
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found") from None
