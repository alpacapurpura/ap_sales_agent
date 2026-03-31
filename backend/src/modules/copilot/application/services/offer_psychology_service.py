from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.brand.infrastructure.repositories.avatar_repository import AvatarRepository
from src.modules.copilot.infrastructure.prompts.base import prompt_loader
from src.modules.offer.domain.offer_ai_schemas import (
    PsychologyGenerationRequest,
    PsychologyGenerationResponse,
)
from src.core.enums import ModelRole
from src.shared.application.ai_action_service import AIActionService, AIActionPolicy, AIModelPolicy


class CopilotOfferPsychologyService:
    def __init__(self, session: Session):
        self.session = session
        self.avatar_repo = AvatarRepository(session)
        self.ai_action_service = AIActionService()

    async def generate_psychology(
        self, request: PsychologyGenerationRequest, tenant_id: UUID
    ) -> PsychologyGenerationResponse:
        avatar = self.avatar_repo.get_by_id(request.avatar_id)
        if not avatar:
            raise ValueError(f"Avatar with ID {request.avatar_id} not found")

        if avatar.tenant_id and str(avatar.tenant_id) != str(tenant_id):
            raise ValueError("Avatar not found in this tenant")

        system_prompt_content = prompt_loader.render(
            template_name="offer_psychology_generator.j2",
            offer_name=request.offer_name,
            offer_description=request.offer_description or "",
            current_pains=", ".join(request.current_pains),
            current_desires=", ".join(request.current_desires),
            avatar_name=avatar.name,
            avatar_description=avatar.icp_description or "No description provided",
            avatar_pains="See Description",
            avatar_desires="See Description",
        )

        return self.ai_action_service.run_structured_action(
            action_name="offer_psychology_generation",
            tenant_id=tenant_id,
            system_prompt=system_prompt_content,
            user_prompt="Analiza el avatar y la oferta, y genera los puntos de dolor y deseos según las instrucciones. Recuerda devolver JSON válido.",
            response_model=PsychologyGenerationResponse,
            policy=AIActionPolicy(
                retries=2,
                retry_delay_seconds=0.4,
                model=AIModelPolicy(
                    model_type=ModelRole.REASONING,
                    temperature=0.7,
                    max_output_tokens=800,
                ),
            ),
            metadata={"prompt_template": "offer_psychology_generator"},
        )
