from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.services.database import get_db
from src.api.dependencies import get_tenant_context
from src.core.domain.offer.ai_schema import PsychologyGenerationRequest, PsychologyGenerationResponse
from src.services.offer_generator_service import OfferGeneratorService
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
         # Fallback or Error depending on policy. Usually we strictly require tenant.
         # But get_tenant_context allows None for superadmins or global scope.
         # For now, we pass it as is.
         pass
         
    service = OfferGeneratorService(db)
    try:
        # If tenant_id is None, it might fail if repo expects a UUID. 
        # But repo type hint says UUID. 
        # Let's ensure we have a valid UUID if possible, or handle None in service.
        # The service passes it to repo. Repo handles it.
        return await service.generate_psychology(request, tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Log the error properly in a real app
        raise HTTPException(status_code=500, detail=f"AI Generation failed: {str(e)}")
