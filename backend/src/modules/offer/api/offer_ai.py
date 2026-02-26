from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.shared.infrastructure.db.database import get_db
from src.modules.iam.api.dependencies import get_tenant_context
from src.modules.offer.domain.offer_ai_schemas import PsychologyGenerationRequest, PsychologyGenerationResponse
from src.modules.offer.application.offer_generator import OfferGeneratorService
from uuid import UUID
from typing import Optional

router = APIRouter()

@router.post("/psychology", response_model=PsychologyGenerationResponse)
async def generate_offer_psychology(
    request: PsychologyGenerationRequest,
    db: Session = Depends(get_db),
    tenant_id: Optional[UUID] = Depends(get_tenant_context)
):
    """
    Generates AI-powered psychology insights (pains & desires) for an offer.
    Requires an Avatar ID and Offer Context.
    """
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID required")
         
    service = OfferGeneratorService(db)
    try:
        return await service.generate_psychology(request, tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Log the error properly in a real app
        raise HTTPException(status_code=500, detail=f"AI Generation failed: {str(e)}")
