"""API endpoints for external product → offer mappings."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.offer.infrastructure.models.external_product_mapping_model import (
    ExternalProductMappingModel,
)
from src.modules.offer.infrastructure.repositories.external_product_mapping_repository import (
    ExternalProductMappingRepository,
)

router = APIRouter(tags=["Offer - Product Mappings"])


class ProductMappingOut(BaseModel):
    id: UUID
    tenant_id: UUID
    offer_id: UUID
    source: str
    external_id: str
    external_name: str | None = None
    metadata_info: dict = {}

    class Config:
        from_attributes = True


class CreateProductMappingIn(BaseModel):
    offer_id: UUID
    source: str
    external_id: str
    external_name: str | None = None
    metadata_info: dict = {}


class UnmatchedProductOut(BaseModel):
    external_id: str
    external_name: str | None = None
    total_price: float | None = None
    currency: str | None = None
    event_count: int = 0


@router.get("/product-mappings", response_model=list[ProductMappingOut])
async def list_product_mappings(
    source: str = Query(default="shopify"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all external product mappings for the tenant."""
    repo = ExternalProductMappingRepository(db)
    mappings = repo.list_by_source(user.tenant_id, source)
    return mappings


@router.get("/product-mappings/unmatched", response_model=list[UnmatchedProductOut])
async def list_unmatched_products(
    source: str = Query(default="shopify"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List external products seen in journey_events that have no mapping."""
    from sqlalchemy import func as sa_func

    from src.modules.crm.infrastructure.models.customer_model import JourneyEventModel

    # Get all mapped external_ids for this source
    mapped_stmt = select(ExternalProductMappingModel.external_id).where(
        ExternalProductMappingModel.tenant_id == user.tenant_id,
        ExternalProductMappingModel.source == source,
    )
    mapped_ids = {row[0] for row in db.execute(mapped_stmt).all()}

    # Scan journey_events for product_ids from this source
    stmt = select(
        JourneyEventModel.properties,
    ).where(
        JourneyEventModel.tenant_id == user.tenant_id,
        JourneyEventModel.event_name.in_(
            ["checkout_initiated", "checkout_completed"]
        ),
        sa_func.jsonb_extract_path_text(
            JourneyEventModel.properties, "source"
        ) == source,
    )
    events = db.execute(stmt).all()

    # Aggregate products seen in events
    product_map: dict[str, dict] = {}
    for (props,) in events:
        if not props:
            continue
        # line_items stored in properties
        line_items = props.get("line_items", [])
        if not line_items:
            # Legacy format: single product_id at top level
            continue
        for item in line_items:
            pid = str(item.get("product_id", ""))
            if not pid or pid in mapped_ids:
                continue
            if pid not in product_map:
                product_map[pid] = {
                    "external_id": pid,
                    "external_name": item.get("title"),
                    "total_price": 0,
                    "currency": props.get("currency", "USD"),
                    "event_count": 0,
                }
            product_map[pid]["total_price"] += float(item.get("price", 0))
            product_map[pid]["event_count"] += 1

    return list(product_map.values())


@router.post("/product-mappings", response_model=ProductMappingOut, status_code=201)
async def create_product_mapping(
    payload: CreateProductMappingIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new external product → offer mapping."""
    repo = ExternalProductMappingRepository(db)

    # Check for duplicates
    existing = repo.get_by_external_id(
        user.tenant_id, payload.source, payload.external_id
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Mapping already exists for {payload.source}:{payload.external_id}",
        )

    mapping = repo.create_mapping(
        tenant_id=user.tenant_id,
        offer_id=payload.offer_id,
        source=payload.source,
        external_id=payload.external_id,
        external_name=payload.external_name,
        metadata_info=payload.metadata_info,
    )
    db.commit()
    return mapping


@router.delete("/product-mappings/{mapping_id}", status_code=204)
async def delete_product_mapping(
    mapping_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a product mapping."""
    repo = ExternalProductMappingRepository(db)
    deleted = repo.delete_mapping(mapping_id, user.tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Mapping not found")
    db.commit()
