from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.copilot.application.services.offer_psychology_service import (
    CopilotOfferPsychologyService,
)
from src.modules.offer.domain.offer_ai_schemas import (
    PsychologyGenerationRequest,
    PsychologyGenerationResponse,
)

class OfferGeneratorService:
    def __init__(self, session: Session):
        self.session = session
        self.copilot_service = CopilotOfferPsychologyService(session)

    async def generate_psychology(
        self, request: PsychologyGenerationRequest, tenant_id: UUID
    ) -> PsychologyGenerationResponse:
        return await self.copilot_service.generate_psychology(request, tenant_id)
