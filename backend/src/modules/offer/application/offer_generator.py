"""Offer Generator application module."""

from uuid import UUID

from src.modules.offer.application.ports import PsychologyGeneratorPort
from src.modules.offer.domain.offer_ai_schemas import (
    PsychologyGenerationRequest,
    PsychologyGenerationResponse,
)


class OfferGeneratorService:
    """Service for offer generator operations."""

    def __init__(self, psychology_port: PsychologyGeneratorPort) -> None:
        """Initialize service with dependencies."""
        self.psychology_port = psychology_port

    async def generate_psychology(
        self,
        request: PsychologyGenerationRequest,
        tenant_id: UUID,
    ) -> PsychologyGenerationResponse:
        """Generate psychology."""
        return await self.psychology_port.generate_psychology(request, tenant_id)
