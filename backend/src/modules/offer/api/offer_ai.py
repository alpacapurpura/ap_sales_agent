from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.copilot.application.services.offer_psychology_service import (
    CopilotOfferPsychologyService,
)
from src.modules.iam.api.dependencies import get_tenant_context
from src.modules.offer.application.offer_generator import OfferGeneratorService
from src.modules.offer.domain.offer_ai_schemas import (
    PsychologyGenerationRequest,
    PsychologyGenerationResponse,
)

router = APIRouter()


@router.post("/psychology", response_model=PsychologyGenerationResponse)
async def generate_offer_psychology(
    request: PsychologyGenerationRequest,
    db: Session = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_context),
):
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID required")

    psychology_port = CopilotOfferPsychologyService(db)
    service = OfferGeneratorService(psychology_port)
    try:
        return await service.generate_psychology(request, tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Generation failed: {e!s}")
