from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.landing.application.landing_service import LandingService
from src.modules.landing.domain.landing_page import LandingPage
from src.modules.landing.schemas import RegenerateBlockRequest
from uuid import UUID
from typing import List, Dict, Any

router = APIRouter()

@router.post("/", response_model=LandingPage)
async def create_landing(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = LandingService(db)
    slug = payload.get("slug")
    offer_id = payload.get("offer_id")
    if not slug:
        raise HTTPException(status_code=400, detail="Slug is required")
        
    return service.create_landing(user.tenant_id, slug, UUID(offer_id) if offer_id else None)

@router.get("/", response_model=List[LandingPage])
def list_landings(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = LandingService(db)
    return service.list_landings(user.tenant_id)

@router.get("/{landing_id}", response_model=LandingPage)
def get_landing(
    landing_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = LandingService(db)
    try:
        landing_uuid = UUID(landing_id)
    except ValueError:
        # If not a valid UUID, let it pass to next route or return 404
        raise HTTPException(status_code=404, detail="Invalid Landing ID format")
        
    landing = service.get_landing(landing_uuid)
    if not landing or str(landing.tenant_id) != str(user.tenant_id):
        raise HTTPException(status_code=404, detail="Landing not found")
    return landing

@router.get("/offer/{offer_id}", response_model=LandingPage)
def get_landing_by_offer(
    offer_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = LandingService(db)
    try:
        offer_uuid = UUID(offer_id)
    except ValueError:
         raise HTTPException(status_code=400, detail="Invalid Offer ID format")
         
    landing = service.get_landing_by_offer(user.tenant_id, offer_uuid)
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found for this offer")
    return landing

@router.patch("/offer/{offer_id}", response_model=LandingPage)
def update_landing_by_offer(
    offer_id: str,
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = LandingService(db)
    try:
        offer_uuid = UUID(offer_id)
    except ValueError:
         raise HTTPException(status_code=400, detail="Invalid Offer ID format")

    landing = service.get_landing_by_offer(user.tenant_id, offer_uuid)
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found for this offer")
        
    try:
        return service.update_landing(landing.id, payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{landing_id}", response_model=LandingPage)
def update_landing(
    landing_id: str,
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = LandingService(db)
    try:
        landing_uuid = UUID(landing_id)
    except ValueError:
         raise HTTPException(status_code=400, detail="Invalid Landing ID format")

    # Check ownership
    landing = service.get_landing(landing_uuid)
    if not landing or str(landing.tenant_id) != str(user.tenant_id):
        raise HTTPException(status_code=404, detail="Landing not found")
        
    try:
        # Payload is the full config object usually
        return service.update_landing(landing_uuid, payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- New Endpoints ---

@router.get("/{offer_id}/landing", response_model=LandingPage)
def get_offer_landing(
    offer_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = LandingService(db)
    landing = service.get_landing_by_offer(user.tenant_id, offer_id)
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found for this offer")
    return landing

@router.post("/{offer_id}/landing/generate", response_model=LandingPage)
def generate_offer_landing(
    offer_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = LandingService(db)
    try:
        return service.generate_landing_for_offer(user.tenant_id, offer_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{offer_id}/landing", response_model=LandingPage)
def update_offer_landing(
    offer_id: UUID,
    config: Dict[str, Any],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = LandingService(db)
    try:
        return service.update_landing_for_offer(user.tenant_id, offer_id, config)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{offer_id}/landing/ai/regenerate-block")
def regenerate_block(
    offer_id: UUID,
    payload: RegenerateBlockRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = LandingService(db)
    # The offer_id is part of the path, we could use it to validate ownership if needed.
    # For now, we assume the user context is enough for this stateless operation or future checks.
    
    try:
        new_content = service.regenerate_block(
            current_content=payload.current_content,
            block_type=payload.block_type,
            context=payload.context
        )
        return {"content": new_content}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
