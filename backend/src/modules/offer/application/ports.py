"""Application ports for the offer module.

Defines abstract interfaces that external modules must implement
to provide services to the offer bounded context.
"""
from abc import ABC, abstractmethod
from uuid import UUID

from src.modules.offer.domain.offer_ai_schemas import (
    PsychologyGenerationRequest,
    PsychologyGenerationResponse,
)


class PsychologyGeneratorPort(ABC):
    @abstractmethod
    async def generate_psychology(
        self, request: PsychologyGenerationRequest, tenant_id: UUID
    ) -> PsychologyGenerationResponse: ...
