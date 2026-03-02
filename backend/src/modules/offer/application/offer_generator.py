from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.modules.sales_agent.infrastructure.prompts.base import prompt_loader
from src.modules.brand.infrastructure.repositories.avatar_repository import AvatarRepository
from src.modules.offer.domain.offer_ai_schemas import PsychologyGenerationRequest, PsychologyGenerationResponse
from src.core.config import settings
from uuid import UUID
import json
import logging

logger = logging.getLogger(__name__)

class OfferGeneratorService:
    def __init__(self, session: Session):
        self.session = session
        self.avatar_repo = AvatarRepository(session)
        # Use Standard ChatOpenAI with JSON Mode
        self.llm = ChatOpenAI(
            model="gpt-4o", 
            temperature=0.7,
            openai_api_key=settings.OPENAI_API_KEY,
            model_kwargs={"response_format": {"type": "json_object"}}
        )

    async def generate_psychology(self, request: PsychologyGenerationRequest, tenant_id: UUID) -> PsychologyGenerationResponse:
        """
        Generates psychological hooks (Pains & Desires) based on Avatar and Offer context.
        """
        # 1. Fetch Avatar Details (Sync Call)
        avatar = self.avatar_repo.get_by_id(request.avatar_id)
        # Note: AvatarRepository.get_by_id takes only ID now, scope filtering is usually higher level or repo handles it if tenant_id provided.
        # The new repo signature is get_by_id(uuid). We should verify tenant access in Application Service if critical.
        
        if not avatar:
            raise ValueError(f"Avatar with ID {request.avatar_id} not found")
            
        if avatar.tenant_id and str(avatar.tenant_id) != str(tenant_id):
             # Simple security check if tenant_id is provided
             raise ValueError("Avatar not found in this tenant")

        # 2. Prepare Context for Prompt
        avatar_context = {
            "avatar_name": avatar.name,
            "avatar_description": avatar.icp_description or "No description provided",
            "avatar_pains": "See Description", 
            "avatar_desires": "See Description"
        }
        
        # 3. Render Prompt Template
        try:
            system_prompt_content = prompt_loader.render(
                template_name="offer_psychology_generator.j2",
                offer_name=request.offer_name,
                offer_description=request.offer_description or "",
                current_pains=", ".join(request.current_pains),
                current_desires=", ".join(request.current_desires),
                **avatar_context
            )
        except Exception as e:
            logger.error(f"Error rendering prompt: {e}")
            raise e

        # 4. Call LLM (Standard Mode)
        messages = [
            SystemMessage(content=system_prompt_content),
            HumanMessage(content="Analiza el avatar y la oferta, y genera los puntos de dolor y deseos según las instrucciones. Recuerda devolver JSON válido.")
        ]
        
        logger.info(f"Invoking LLM for psychology generation (JSON Mode). Avatar: {avatar.name}")
        
        try:
            response_msg = await self.llm.ainvoke(messages)
            content = response_msg.content
            
            logger.info(f"LLM Raw Content: {content[:100]}...") # Log start of content
            
            # Parse JSON
            data = json.loads(content)
            
            # Validate with Pydantic
            result = PsychologyGenerationResponse(**data)
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON: {e}")
            raise ValueError("La IA generó una respuesta inválida (No es JSON).")
        except Exception as e:
            logger.error(f"LLM Invocation failed: {e}")
            raise e
