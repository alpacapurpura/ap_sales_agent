from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Dict, Any, List, Union
import uuid
from src.services.db.repositories.product import ProductRepository
from src.services.database import SessionLocal
from src.core.domain.offer_enums import OFFER_METADATA

router = APIRouter()

@router.get("/metadata/hints", response_model=Dict[str, Any])
async def get_offer_metadata():
    """Exposes business logic hints for UI components."""
    return OFFER_METADATA

def get_product_repo():
    db = SessionLocal()
    repo = ProductRepository(db)
    try:
        yield repo
    finally:
        repo.close()

class ProductResponse(BaseModel):
    id: uuid.UUID
    name: str
    type: str
    status: str
    
    # Polymorphic fields
    delivery_model: Optional[str] = None
    headline_promise: Optional[str] = None
    primary_outcome: Optional[str] = None
    time_to_value: Optional[str] = None
    access_duration: Optional[str] = None
    access_duration_text: Optional[str] = None
    support_duration_days: Optional[int] = None
    target_avatar_match: Optional[List[str]] = []
    
    marketing_pain_points: Optional[List[str]] = []
    marketing_desires: Optional[List[str]] = []

    requires_application: Optional[bool] = False
    min_financial_capacity: Optional[str] = None
    prerequisites: Optional[List[str]] = []
    
    pricing: Optional[List[Dict[str, Any]]] = [] # Changed from Dict to List to match DB
    currency: Optional[str] = "USD"
    
    @field_validator('pricing', mode='before')
    @classmethod
    def normalize_pricing(cls, v):
        if isinstance(v, dict):
            return [v]
        return v

    guarantee_type: Optional[str] = None
    guarantee_terms: Optional[str] = None
    
    downsell_product_id: Optional[uuid.UUID] = None
    upsell_product_id: Optional[uuid.UUID] = None
    includes_offers: Optional[List[uuid.UUID]] = []
    deliverables: Optional[List[Dict[str, Any]]] = []
    specific_details: Optional[Dict[str, Any]] = {}
    
    metadata_info: Optional[Dict[str, Any]] = {}
    avatar_id: Optional[uuid.UUID] = None
    
    # New fields for response
    onboarding_action: Optional[str] = None
    onboarding_url: Optional[str] = None
    calendar_type_id: Optional[str] = None
    checkout_page_url: Optional[str] = None
    vsl_link: Optional[str] = None
    
    landing_page_config: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class ProductCreate(BaseModel):
    name: str
    type: str = "program"
    status: str = "DRAFT"

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    internal_sku: Optional[str] = None
    type: Optional[str] = None
    delivery_model: Optional[str] = None
    status: Optional[str] = None
    
    headline_promise: Optional[str] = None
    primary_outcome: Optional[str] = None
    time_to_value: Optional[str] = None
    access_duration: Optional[str] = None
    access_duration_text: Optional[str] = None
    support_duration_days: Optional[int] = None
    target_avatar_match: Optional[List[str]] = None
    
    marketing_pain_points: Optional[List[str]] = None
    marketing_desires: Optional[List[str]] = None
    
    requires_application: Optional[bool] = None
    min_financial_capacity: Optional[str] = None
    prerequisites: Optional[List[str]] = None
    
    pricing: Optional[List[Dict[str, Any]]] = None
    currency: Optional[str] = None
    
    guarantee_type: Optional[str] = None
    guarantee_terms: Optional[str] = None
    
    downsell_product_id: Optional[uuid.UUID] = None
    upsell_product_id: Optional[uuid.UUID] = None
    includes_offers: Optional[List[uuid.UUID]] = None
    deliverables: Optional[List[Dict[str, Any]]] = None
    specific_details: Optional[Dict[str, Any]] = None
    
    metadata_info: Optional[Dict[str, Any]] = None
    avatar_id: Optional[uuid.UUID] = None
    
    # New fields for onboarding logic
    onboarding_action: Optional[str] = None
    onboarding_url: Optional[str] = None
    calendar_type_id: Optional[str] = None
    checkout_page_url: Optional[str] = None
    vsl_link: Optional[str] = None

@router.get("/", response_model=List[ProductResponse])
async def list_products(limit: int = 20, skip: int = 0, repo: ProductRepository = Depends(get_product_repo)):
    return repo.list_products(limit=limit, skip=skip)

@router.post("/", response_model=ProductResponse)
async def create_product(product: ProductCreate, repo: ProductRepository = Depends(get_product_repo)):
    return repo.create_product(name=product.name, type=product.type)

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, repo: ProductRepository = Depends(get_product_repo)):
    product = repo.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(product_id: str, update: ProductUpdate, repo: ProductRepository = Depends(get_product_repo)):
    updated = repo.update_product(product_id, update.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Product not found")
    return updated
