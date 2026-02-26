from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.shared.infrastructure.db.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.landing.application.landing_service import LandingService
from src.modules.landing.domain.landing_page import LandingPage
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
    landing = service.get_landing(UUID(landing_id))
    if not landing or str(landing.tenant_id) != str(user.tenant_id):
        raise HTTPException(status_code=404, detail="Landing not found")
    return landing

@router.patch("/{landing_id}", response_model=LandingPage)
def update_landing(
    landing_id: str,
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = LandingService(db)
    # Check ownership
    landing = service.get_landing(UUID(landing_id))
    if not landing or str(landing.tenant_id) != str(user.tenant_id):
        raise HTTPException(status_code=404, detail="Landing not found")
        
    try:
        # Payload is the full config object usually
        return service.update_landing(UUID(landing_id), payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
