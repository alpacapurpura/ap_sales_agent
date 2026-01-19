from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
import uuid
from src.services.db.repositories.product import ProductRepository
from src.services.database import SessionLocal

router = APIRouter()

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
    pricing: Optional[Dict[str, Any]] = {}
    metadata_info: Optional[Dict[str, Any]] = {}
    avatar_id: Optional[uuid.UUID] = None

    model_config = ConfigDict(from_attributes=True)

class ProductCreate(BaseModel):
    name: str
    type: str = "program"

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    pricing: Optional[Dict[str, Any]] = None
    metadata_info: Optional[Dict[str, Any]] = None
    avatar_id: Optional[uuid.UUID] = None

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
