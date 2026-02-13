from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from src.services.database import get_db
from src.api.dependencies import get_tenant_context, get_optional_tenant_context
from src.services.landing_generator_service import LandingGeneratorService
from src.core.domain.landing_page.schema import LandingPageConfig
from src.services.db.models.business import Product
from uuid import UUID
from typing import Optional

import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/{offer_id}/landing/generate", response_model=LandingPageConfig)
async def generate_landing_page(
    offer_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: Optional[UUID] = Depends(get_tenant_context)
):
    service = LandingGeneratorService(db)
    try:
        return await service.generate_landing_page(offer_id, tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from pydantic import BaseModel

class RegenerateBlockRequest(BaseModel):
    block_type: str
    current_content: dict
    instruction: Optional[str] = None

@router.post("/{offer_id}/landing/ai/regenerate-block", response_model=dict)
async def regenerate_block(
    offer_id: UUID,
    request: RegenerateBlockRequest,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_context)
):
    """
    Regenerates content for a specific block using AI.
    """
    service = LandingGeneratorService(db)
    try:
        return await service.regenerate_section_content(
            offer_id=offer_id,
            tenant_id=tenant_id,
            block_type=request.block_type,
            current_content=request.current_content,
            instruction=request.instruction
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error regenerating block: {e}")
        raise HTTPException(status_code=500, detail="Failed to regenerate content")

@router.get("/{offer_id}/landing", response_model=LandingPageConfig)
def get_landing_page_config(
    offer_id: UUID,
    db: Session = Depends(get_db),
    # Allow optional auth for Dev Preview (when token might not be passed by Next.js server)
    # In production, this should be stricter or use a shared secret for preview mode
    tenant_id: Optional[UUID] = Depends(get_optional_tenant_context) 
):
    """
    Get current Landing Page Configuration for an offer.
    """
    # If tenant_id is None (no auth), we can still fetch if we are just previewing by ID
    # But we should ensure we don't leak data across tenants if multi-tenant strictness is required.
    # For this MVP/Dev stage, fetching by ID is acceptable as IDs are UUIDs (hard to guess).
    
    product = db.query(Product).filter(Product.id == offer_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    # Optional: Verify tenant ownership if tenant_id is present
    if tenant_id and product.tenant_id and product.tenant_id != tenant_id:
         raise HTTPException(status_code=403, detail="Not authorized to access this offer")
        
    if not product.landing_page_config:
        # Return 404 so frontend knows to trigger generation or show empty state
        # Alternatively, could return a default empty config, but 404 is cleaner for "not exists yet"
        raise HTTPException(status_code=404, detail="Landing page not configured")
        
    return LandingPageConfig(**product.landing_page_config)

@router.put("/{offer_id}/landing", response_model=LandingPageConfig)
def update_landing_page_config(
    offer_id: UUID,
    config: LandingPageConfig,
    db: Session = Depends(get_db),
    tenant_id: Optional[UUID] = Depends(get_tenant_context)
):
    """
    Updates the Landing Page Configuration manually (from the Editor).
    """
    # 1. Fetch Product
    product = db.query(Product).filter(Product.id == offer_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Offer not found")
        
    # 2. Update Config
    # Pydantic model dump to JSON-compatible dict
    # Ensure we use model_dump(mode='json') to handle Enums/DateTimes correctly
    product.landing_page_config = config.model_dump(mode='json')
    
    # 3. Save
    db.commit()
    db.refresh(product)
    
    return config

@router.get("/public/{slug}", response_model=LandingPageConfig)
def get_public_landing_page(
    slug: str,
    db: Session = Depends(get_db)
):
    """
    Public Endpoint for ISR/SSG pages.
    Finds the offer by the slug inside the landing_page_config JSON.
    This query might be slow on large datasets without a dedicated index on JSONB.
    For MVP it is fine. For scale, we should extract slug to a column or GIN index.
    """
    # Query using Postgres JSONB operator ->> to extract text
    # product.landing_page_config ->> 'slug' == slug
    product = db.query(Product).filter(
        Product.landing_page_config['slug'].astext == f"/p/{slug}" 
        # Note: Frontend sends "lead-magnet", stored as "/p/lead-magnet" in generator service
        # We need to be careful with the slash. 
        # Let's assume the slug param comes without /p/ prefix from Next.js params.
    ).first()

    if not product:
        # Fallback check without /p/ prefix if data inconsistency exists
        product = db.query(Product).filter(
            Product.landing_page_config['slug'].astext == slug
        ).first()

    if not product or not product.landing_page_config:
        raise HTTPException(status_code=404, detail="Landing page not found")
        
    return LandingPageConfig(**product.landing_page_config)
