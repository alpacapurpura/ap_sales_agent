from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from uuid import UUID
from src.core.database import get_db
from sqlalchemy.orm import Session
from src.modules.iam.domain.user import User
from src.modules.iam.api.dependencies import get_current_user
from src.modules.offer.domain.offer import Offer
from src.modules.offer.domain.enums import OFFER_METADATA
from src.modules.offer.api.dto.products import ProductCreate, ProductUpdate
from src.modules.offer.application.offer_service import OfferService
from src.modules.offer.domain.offer import (
    OfferIdentityUpdate, OfferStrategyUpdate, OfferPricingUpdate, 
    OfferDetailsUpdate, OfferVisualsUpdate, OfferClosingUpdate, 
    OfferResourcesUpdate, OfferInstructorsUpdate,
    OfferPromiseUpdate, OfferPsychologyUpdate, OfferValueStackUpdate
)

router = APIRouter()

@router.get("/metadata/hints", response_model=Dict[str, Any])
async def get_offer_metadata():
    """Exposes business logic hints for UI components."""
    return OFFER_METADATA

@router.get("/", response_model=List[Offer])
async def list_products(
    limit: int = 20, 
    skip: int = 0, 
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = OfferService(db)
    # Filter by user's tenant
    return service.list_offers(user.tenant_id)

@router.post("/", response_model=Offer)
async def create_product(
    product: ProductCreate, 
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = OfferService(db)
    return service.create_offer(name=product.name, offer_type=product.type, tenant_id=user.tenant_id)

@router.get("/{product_id}", response_model=Offer)
async def get_product(
    product_id: str, 
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = OfferService(db)
    product = service.get_offer(UUID(product_id))
    if not product or str(product.tenant_id) != str(user.tenant_id):
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.patch("/{product_id}", response_model=Offer)
async def update_product(
    product_id: str, 
    update: ProductUpdate, 
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = OfferService(db)
    try:
        return service.patch_offer(UUID(product_id), user.tenant_id, update.model_dump(exclude_unset=True))
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found")

@router.patch("/{product_id}/identity", response_model=Offer)
async def update_identity(product_id: str, update: OfferIdentityUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = OfferService(db)
    try:
        return service.patch_offer(UUID(product_id), user.tenant_id, update.model_dump(exclude_unset=True))
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found")

@router.patch("/{product_id}/strategy", response_model=Offer)
async def update_strategy(product_id: str, update: OfferStrategyUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = OfferService(db)
    try:
        return service.patch_offer(UUID(product_id), user.tenant_id, update.model_dump(exclude_unset=True))
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found")

@router.patch("/{product_id}/promise", response_model=Offer)
async def update_promise(product_id: str, update: OfferPromiseUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = OfferService(db)
    try:
        return service.patch_offer(UUID(product_id), user.tenant_id, update.model_dump(exclude_unset=True))
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found")

@router.patch("/{product_id}/psychology", response_model=Offer)
async def update_psychology(product_id: str, update: OfferPsychologyUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = OfferService(db)
    try:
        return service.patch_offer(UUID(product_id), user.tenant_id, update.model_dump(exclude_unset=True))
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found")

@router.patch("/{product_id}/value_stack", response_model=Offer)
async def update_value_stack(product_id: str, update: OfferValueStackUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = OfferService(db)
    try:
        return service.patch_offer(UUID(product_id), user.tenant_id, update.model_dump(exclude_unset=True))
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found")

@router.patch("/{product_id}/pricing", response_model=Offer)
async def update_pricing(product_id: str, update: OfferPricingUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = OfferService(db)
    try:
        return service.patch_offer(UUID(product_id), user.tenant_id, update.model_dump(exclude_unset=True))
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found")

@router.patch("/{product_id}/details", response_model=Offer)
async def update_details(product_id: str, update: OfferDetailsUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = OfferService(db)
    try:
        return service.patch_offer(UUID(product_id), user.tenant_id, update.model_dump(exclude_unset=True))
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found")

@router.patch("/{product_id}/visuals", response_model=Offer)
async def update_visuals(product_id: str, update: OfferVisualsUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = OfferService(db)
    try:
        return service.patch_offer(UUID(product_id), user.tenant_id, update.model_dump(exclude_unset=True))
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found")

@router.patch("/{product_id}/closing", response_model=Offer)
async def update_closing(product_id: str, update: OfferClosingUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = OfferService(db)
    try:
        return service.patch_offer(UUID(product_id), user.tenant_id, update.model_dump(exclude_unset=True))
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found")

@router.patch("/{product_id}/resources", response_model=Offer)
async def update_resources(product_id: str, update: OfferResourcesUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = OfferService(db)
    try:
        return service.patch_offer(UUID(product_id), user.tenant_id, update.model_dump(exclude_unset=True))
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found")

@router.patch("/{product_id}/instructors", response_model=Offer)
async def update_instructors(product_id: str, update: OfferInstructorsUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = OfferService(db)
    try:
        return service.patch_offer(UUID(product_id), user.tenant_id, update.model_dump(exclude_unset=True))
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found")
