from uuid import UUID

from src.modules.offer.application.ports import PsychologyGeneratorPort
from src.modules.offer.domain.offer_ai_schemas import (
    PsychologyGenerationRequest,
    PsychologyGenerationResponse,
)


class OfferGeneratorService:
    def __init__(self, psychology_port: PsychologyGeneratorPort):
        self.psychology_port = psychology_port

    async def generate_psychology(
        self, request: PsychologyGenerationRequest, tenant_id: UUID
    ) -> PsychologyGenerationResponse:
        return await self.psychology_port.generate_psychology(request, tenant_id)
