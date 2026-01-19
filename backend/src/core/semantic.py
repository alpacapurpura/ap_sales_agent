from langchain_core.messages import HumanMessage, SystemMessage
from src.core.llm.providers.openai import OpenAIService
import structlog

logger = structlog.get_logger()

async def check_is_complete(text: str) -> bool:
    """
    Uses a fast LLM to check if the text is a complete thought/sentence.
    Returns True if complete (reduce buffer), False if incomplete (wait more).
    """
    if not text or len(text.strip()) < 3:
        return False # Too short, assume incomplete

    try:
        # Instantiate service (Adapter Pattern)
        # Note: In a cleaner DI setup, this would be injected.
        llm_service = OpenAIService()
        llm = llm_service.fast_chat_model

        sys_prompt = (
            "Eres un clasificador binario de intención de escritura. "
            "Determina si el mensaje del usuario está 'COMPLETO' (tiene sentido semántico completo, es una pregunta cerrada o una afirmación final) "
            "o 'INCOMPLETO' (parece que el usuario va a añadir más detalles en un siguiente mensaje inmediatamente). "
            "Responde SOLO con una palabra: 'COMPLETO' o 'INCOMPLETO'."
        )

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
