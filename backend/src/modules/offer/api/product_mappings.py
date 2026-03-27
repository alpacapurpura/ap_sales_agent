"""API endpoints for external product → offer mappings."""

import uuid as uuid_mod
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


class CreateProductMappingOut(BaseModel):
    """Extended response with backfill stats."""
    id: UUID
    tenant_id: UUID
    offer_id: UUID
    source: str
    external_id: str
    external_name: str | None = None
    metadata_info: dict = {}
    sales_created: int = 0

    class Config:
        from_attributes = True


class UnmatchedProductOut(BaseModel):
    external_id: str
    external_name: str | None = None
    total_price: float | None = None
    currency: str | None = None
    event_count: int = 0


class SourceProductOut(BaseModel):
    external_id: str
    external_name: str | None = None
    source: str
    total_price: float = 0.0
    currency: str | None = None
    event_count: int = 0
    is_mapped: bool = False
    offer_id: UUID | None = None
    offer_name: str | None = None
    mapping_id: UUID | None = None


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


@router.get("/product-mappings/source-products", response_model=list[SourceProductOut])
async def list_source_products(
    source: str = Query(default="shopify"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List ALL products from a source (mapped + unmapped) with metrics."""
    from sqlalchemy import func as sa_func

    from src.modules.crm.infrastructure.models.customer_model import JourneyEventModel
    from src.modules.offer.infrastructure.models.product_model import ProductModel

    # 1. Fetch all mappings for tenant+source
    mapping_stmt = select(
        ExternalProductMappingModel.external_id,
        ExternalProductMappingModel.id,
        ExternalProductMappingModel.offer_id,
        ExternalProductMappingModel.external_name,
    ).where(
        ExternalProductMappingModel.tenant_id == user.tenant_id,
        ExternalProductMappingModel.source == source,
    )
    mapping_rows = db.execute(mapping_stmt).all()
    mapping_dict: dict[str, dict] = {}
    offer_ids: set[UUID] = set()
    for ext_id, map_id, offer_id, ext_name in mapping_rows:
        mapping_dict[ext_id] = {
            "mapping_id": map_id,
            "offer_id": offer_id,
            "external_name": ext_name,
        }
        if offer_id:
            offer_ids.add(offer_id)

    # 2. Batch query offer names
    offer_names: dict[UUID, str] = {}
    if offer_ids:
        offer_stmt = select(ProductModel.id, ProductModel.name).where(
            ProductModel.id.in_(offer_ids),
        )
        for oid, oname in db.execute(offer_stmt).all():
            offer_names[oid] = oname

    # 3. Scan journey_events (checkout_initiated + checkout_completed)
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

    # 4. Aggregate by external_id
    product_map: dict[str, dict] = {}
    for (props,) in events:
        if not props:
            continue
        line_items = props.get("line_items", [])
        if not line_items:
            continue
        for item in line_items:
            pid = str(item.get("product_id", ""))
            if not pid:
                continue
            if pid not in product_map:
                product_map[pid] = {
                    "external_id": pid,
                    "external_name": item.get("title"),
                    "source": source,
                    "total_price": 0.0,
                    "currency": props.get("currency", "USD"),
                    "event_count": 0,
                }
            product_map[pid]["total_price"] += float(item.get("price", 0))
            product_map[pid]["event_count"] += 1

    # 5. Merge: enrich with mapping info; add mappings without events
    for ext_id, minfo in mapping_dict.items():
        if ext_id not in product_map:
            product_map[ext_id] = {
                "external_id": ext_id,
                "external_name": minfo["external_name"],
                "source": source,
                "total_price": 0.0,
                "currency": None,
                "event_count": 0,
            }
        product_map[ext_id]["is_mapped"] = True
        product_map[ext_id]["offer_id"] = minfo["offer_id"]
        product_map[ext_id]["offer_name"] = offer_names.get(minfo["offer_id"])
        product_map[ext_id]["mapping_id"] = minfo["mapping_id"]

    # Fill is_mapped=False for products without mapping
    for pid, pdata in product_map.items():
        if "is_mapped" not in pdata:
            pdata["is_mapped"] = False

    # 6. Sort by total_price DESC
    result = sorted(product_map.values(), key=lambda x: x["total_price"], reverse=True)
    return result


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


@router.post("/product-mappings", response_model=CreateProductMappingOut, status_code=201)
async def create_product_mapping(
    payload: CreateProductMappingIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new external product → offer mapping with retroactive backfill."""
    from sqlalchemy import func as sa_func

    from src.modules.crm.domain.enums import SaleStage, SaleStatus
    from src.modules.crm.infrastructure.models.customer_model import JourneyEventModel
    from src.modules.crm.infrastructure.models.sale_model import SaleModel

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

    # --- Retroactive backfill: create SaleModel for past checkout_completed events ---
    sales_created = 0

    checkout_stmt = select(
        JourneyEventModel.properties,
        JourneyEventModel.profile_id,
        JourneyEventModel.occurred_at,
    ).where(
        JourneyEventModel.tenant_id == user.tenant_id,
        JourneyEventModel.event_name == "checkout_completed",
        sa_func.jsonb_extract_path_text(
            JourneyEventModel.properties, "source"
        ) == payload.source,
    )
    checkout_events = db.execute(checkout_stmt).all()

    for props, profile_id, occurred_at in checkout_events:
        if not props or not profile_id:
            continue
        order_id = props.get("order_id", "")
        currency = props.get("currency", "USD")
        line_items = props.get("line_items", [])
        if not line_items:
            continue

        for item in line_items:
            product_id = str(item.get("product_id", ""))
            if product_id != payload.external_id:
                continue

            txn_id = f"{payload.source}-{order_id}-{product_id}"

            # Dedup by transaction_id
            existing_sale = db.execute(
                select(SaleModel.id).where(
                    SaleModel.tenant_id == user.tenant_id,
                    SaleModel.transaction_id == txn_id,
                ).limit(1)
            ).scalar_one_or_none()
            if existing_sale:
                continue

            line_amount = float(item.get("price", 0)) * int(item.get("quantity", 1))
            sale = SaleModel(
                id=uuid_mod.uuid4(),
                tenant_id=user.tenant_id,
                customer_id=profile_id,
                offer_id=payload.offer_id,
                transaction_id=txn_id,
                amount=line_amount,
                currency=currency,
                status=SaleStatus.COMPLETED,
                stage=SaleStage.CONVERSION,
                source=payload.source.upper(),
                metadata_info={
                    "retroactive_backfill": True,
                    f"{payload.source}_order_id": str(order_id),
                },
                occurred_at=occurred_at,
            )
            db.add(sale)
            sales_created += 1

    if sales_created > 0:
        db.commit()

    return CreateProductMappingOut(
        id=mapping.id,
        tenant_id=mapping.tenant_id,
        offer_id=mapping.offer_id,
        source=mapping.source,
        external_id=mapping.external_id,
        external_name=mapping.external_name,
        metadata_info=mapping.metadata_info or {},
        sales_created=sales_created,
    )


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
