"""Semantic infrastructure module."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from langchain_core.messages import HumanMessage, SystemMessage

from src.core.enums import ModelRole
from src.modules.sales_agent.infrastructure.prompts.base import prompt_loader
from src.shared.infrastructure.llm.factory import LLMFactory

if TYPE_CHECKING:
    from src.modules.iam.infrastructure.models.tenant_model import TenantModel

logger = structlog.get_logger()


async def check_is_complete(text: str, tenant: TenantModel | None = None) -> bool:
    """Use a fast LLM to check if the text is a complete thought/sentence.

    Returns True if complete (reduce buffer), False if incomplete (wait more).
    """
    if not text or len(text.strip()) < 3:
        return False  # Too short, assume incomplete

    try:
        # Use tenant-specific LLM service if available, otherwise fall back to global
        llm_service = LLMFactory.get_service_for_tenant(tenant) if tenant else LLMFactory.get_service()
        llm = llm_service.get_client(ModelRole.FAST)

        sys_prompt = prompt_loader.render("message_completeness")

        response = await llm.ainvoke(
            [
                SystemMessage(content=sys_prompt),
                HumanMessage(content=f"Mensaje: {text}"),
            ],
        )

        content = response.content.strip().upper()
        # Check strict equality or ensures it's not "INCOMPLETO"
        is_complete = content == "COMPLETO"

        logger.info(
            "semantic_check_result",
            text=text,
            result=content,
            is_complete=is_complete,
        )

    except Exception:
        logger.exception("Semantic check failed")
        # Fail safe: Default to False (wait longer) to avoid interrupting
        return False
    else:
        return is_complete
