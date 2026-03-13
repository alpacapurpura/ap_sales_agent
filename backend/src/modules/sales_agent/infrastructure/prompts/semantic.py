from langchain_core.messages import HumanMessage, SystemMessage
from src.shared.infrastructure.llm.factory import LLMFactory
from src.modules.sales_agent.infrastructure.prompts.base import prompt_loader
import structlog

logger = structlog.get_logger()

async def check_is_complete(text: str, tenant=None) -> bool:
    """
    Uses a fast LLM to check if the text is a complete thought/sentence.
    Returns True if complete (reduce buffer), False if incomplete (wait more).
    """
    if not text or len(text.strip()) < 3:
        return False # Too short, assume incomplete

    try:
        # Use tenant-specific LLM service if available, otherwise fall back to global
        if tenant:
            llm_service = LLMFactory.get_service_for_tenant(tenant)
        else:
            llm_service = LLMFactory.get_service()
        llm = llm_service.fast_chat_model

        sys_prompt = prompt_loader.render("message_completeness")

        response = await llm.ainvoke([
            SystemMessage(content=sys_prompt),
            HumanMessage(content=f"Mensaje: {text}")
        ])

        content = response.content.strip().upper()
        # Check strict equality or ensures it's not "INCOMPLETO"
        is_complete = content == "COMPLETO"
        
        logger.info("semantic_check_result", text=text, result=content, is_complete=is_complete)
        return is_complete

    except Exception as e:
        logger.error(f"Semantic check failed: {e}")
        # Fail safe: Default to False (wait longer) to avoid interrupting
        return False
