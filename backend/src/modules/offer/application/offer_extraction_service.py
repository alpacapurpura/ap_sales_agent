"""Offer extraction service — LLM section extractors for offer data.

Coordinates LLM-based offer data extraction from web content and text.
Follows the same pattern as BrandExtractionService with wave-based
concurrent extraction and Redis progress tracking.
"""

from __future__ import annotations

import asyncio
import json
import time
import traceback
from typing import TYPE_CHECKING, Literal

import structlog

if TYPE_CHECKING:
    from collections.abc import Callable
    from uuid import UUID

    from pydantic import BaseModel
    from sqlalchemy.orm import Session

from luana_core_offer_studio.domain.offer import (
    OfferClosingUpdate,
    OfferDetailsUpdate,
    OfferPricingUpdate,
    OfferPromiseUpdate,
    OfferPsychologyUpdate,
    OfferStrategyUpdate,
    OfferValueStackUpdate,
)
from luana_core_platform.application.ai_action_service import (
    AIActionPolicy,
    AIActionService,
    AIModelPolicy,
)
from luana_core_platform.core.enums import ModelRole
from luana_core_platform.infrastructure.prompts.base import prompt_loader
from luana_core_platform.infrastructure.web.crawler import truncate_at_page_boundary

logger = structlog.get_logger()


class OfferExtractionService:
    """Coordinates LLM-based offer data extraction from web content.

    Individual section extractors (_extract_promise, _extract_psychology, etc.)
    are run in two concurrent waves and persisted via OfferService.patch_offer.
    """

    def __init__(self, db: Session, tenant_id: UUID, offer_id: UUID) -> None:
        """Initialize service with dependencies."""
        self.db = db
        self.tenant_id = tenant_id
        self.offer_id = offer_id
        self.ai_action_service = AIActionService()

        self.default_policy = AIActionPolicy(
            retries=3,
            retry_delay_seconds=5.0,
            model=AIModelPolicy(
                model_type=ModelRole.REASONING,
                temperature=0,
                max_output_tokens=4000,
            ),
        )

        logger.info(
            "offer_extraction_service_init",
            tenant_id=str(tenant_id),
            offer_id=str(offer_id),
        )

    # ------------------------------------------------------------------
    # Prompt rendering
    # ------------------------------------------------------------------

    def _render_prompt(
        self,
        template_name: str,
        content: str,
        current_data: str,
        instructions: str | None,
        archetype: str | None,
        max_chars: int = 50000,
    ) -> str:
        """Render an offer extraction prompt using PromptLoader (Jinja2 + DB fallback)."""
        try:
            rendered = prompt_loader.render(
                template_name,
                content=truncate_at_page_boundary(content, max_chars=max_chars),
                current_data=current_data or "None",
                instructions=instructions or "None",
                archetype=archetype or "general",
            )
            logger.info(
                "prompt_rendered",
                template=template_name,
                prompt_length=len(rendered),
                content_input_length=len(content),
                current_data_length=len(current_data or ""),
            )
        except Exception as e:
            logger.exception(
                "prompt_render_failed",
                template=template_name,
                error=str(e),
                error_type=type(e).__name__,
                traceback=traceback.format_exc(),
            )
            raise

        else:
            return rendered

    def _append_schema_instruction(
        self,
        prompt: str,
        schema_model: type[BaseModel],
    ) -> str:
        schema_json = json.dumps(schema_model.model_json_schema(), indent=2)
        return f"{prompt}\n\nSCHEMA:\n{schema_json}\n\nReturn a valid JSON object matching this schema."

    # ------------------------------------------------------------------
    # Generic section runner
    # ------------------------------------------------------------------

    async def _run_section(
        self,
        section_name: str,
        action_name: str,
        prompt: str,
        response_model: type[BaseModel],
        default_result: BaseModel,
        user_prompt: str,
        per_call_timeout: float = 120.0,
    ) -> BaseModel:
        """Run a single extraction section with timing and timeout."""
        t0 = time.time()
        try:
            logger.info(
                "extract_section_starting",
                section=section_name,
                prompt_length=len(prompt),
            )
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    self.ai_action_service.run_structured_action,
                    action_name=action_name,
                    tenant_id=self.tenant_id,
                    system_prompt=self._append_schema_instruction(
                        prompt,
                        response_model,
                    ),
                    user_prompt=user_prompt,
                    response_model=response_model,
                    policy=self.default_policy,
                    metadata={"prompt_template": action_name},
                ),
                timeout=per_call_timeout,
            )
            elapsed = time.time() - t0
            extracted = result.model_dump(exclude_unset=True, exclude_none=True)
            logger.info(
                "extract_section_success",
                section=section_name,
                fields_extracted=list(extracted.keys()),
                field_count=len(extracted),
                duration_s=round(elapsed, 2),
            )
        except TimeoutError:
            elapsed = time.time() - t0
            logger.exception(
                "extract_section_timeout",
                section=section_name,
                timeout=per_call_timeout,
                duration_s=round(elapsed, 2),
            )
            return default_result
        except Exception as e:
            elapsed = time.time() - t0
            logger.exception(
                "extract_section_failed",
                section=section_name,
                error=str(e),
                error_type=type(e).__name__,
                duration_s=round(elapsed, 2),
                traceback=traceback.format_exc(),
            )
            return default_result

        else:
            return result

    # ------------------------------------------------------------------
    # Individual section extractors
    # ------------------------------------------------------------------

    async def _extract_promise(
        self,
        content: str,
        current_data: str,
        instructions: str | None,
        archetype: str | None,
    ) -> OfferPromiseUpdate:
        prompt = self._render_prompt(
            "offer_extract_promise",
            content,
            current_data,
            instructions,
            archetype,
        )
        return await self._run_section(
            "promise",
            "offer_extract_promise",
            prompt,
            OfferPromiseUpdate,
            OfferPromiseUpdate(),
            "Extract the Offer Promise (headline, primary outcome, time to value).",
        )

    async def _extract_psychology(
        self,
        content: str,
        current_data: str,
        instructions: str | None,
        archetype: str | None,
    ) -> OfferPsychologyUpdate:
        prompt = self._render_prompt(
            "offer_extract_psychology",
            content,
            current_data,
            instructions,
            archetype,
        )
        return await self._run_section(
            "psychology",
            "offer_extract_psychology",
            prompt,
            OfferPsychologyUpdate,
            OfferPsychologyUpdate(),
            "Extract the Offer Psychology (avatars, pain points, desires, objections).",
        )

    async def _extract_strategy(
        self,
        content: str,
        current_data: str,
        instructions: str | None,
        archetype: str | None,
    ) -> OfferStrategyUpdate:
        prompt = self._render_prompt(
            "offer_extract_strategy",
            content,
            current_data,
            instructions,
            archetype,
        )
        return await self._run_section(
            "strategy",
            "offer_extract_strategy",
            prompt,
            OfferStrategyUpdate,
            OfferStrategyUpdate(),
            "Extract the Offer Strategy (value level, delivery model).",
        )

    async def _extract_value_stack(
        self,
        content: str,
        current_data: str,
        instructions: str | None,
        archetype: str | None,
    ) -> OfferValueStackUpdate:
        prompt = self._render_prompt(
            "offer_extract_value_stack",
            content,
            current_data,
            instructions,
            archetype,
        )
        return await self._run_section(
            "value_stack",
            "offer_extract_value_stack",
            prompt,
            OfferValueStackUpdate,
            OfferValueStackUpdate(),
            "Extract the Offer Value Stack (deliverables, included offers).",
        )

    async def _extract_pricing(
        self,
        content: str,
        current_data: str,
        instructions: str | None,
        archetype: str | None,
    ) -> OfferPricingUpdate:
        prompt = self._render_prompt(
            "offer_extract_pricing",
            content,
            current_data,
            instructions,
            archetype,
        )
        return await self._run_section(
            "pricing",
            "offer_extract_pricing",
            prompt,
            OfferPricingUpdate,
            OfferPricingUpdate(),
            "Extract the Offer Pricing LATAM (tax inclusion, installments).",
        )

    async def _extract_closing(
        self,
        content: str,
        current_data: str,
        instructions: str | None,
        archetype: str | None,
    ) -> OfferClosingUpdate:
        prompt = self._render_prompt(
            "offer_extract_closing",
            content,
            current_data,
            instructions,
            archetype,
        )
        return await self._run_section(
            "closing",
            "offer_extract_closing",
            prompt,
            OfferClosingUpdate,
            OfferClosingUpdate(),
            "Extract the Offer Closing (guarantee, checkout, onboarding, upsell/downsell).",
        )

    async def _extract_details(
        self,
        content: str,
        current_data: str,
        instructions: str | None,
        archetype: str | None,
    ) -> OfferDetailsUpdate:
        prompt = self._render_prompt(
            "offer_extract_details",
            content,
            current_data,
            instructions,
            archetype,
        )
        return await self._run_section(
            "details",
            "offer_extract_details",
            prompt,
            OfferDetailsUpdate,
            OfferDetailsUpdate(),
            "Extract the Offer Details (specific details, access duration, support).",
        )

    # ------------------------------------------------------------------
    # Main orchestration
    # ------------------------------------------------------------------

    async def extract_all(
        self,
        url: str | None = None,
        text: str | None = None,
        mode: Literal["initial", "update"] = "initial",
        update_instructions: str | None = None,
        progress_callback: Callable[..., None] | None = None,
        user_id: UUID | None = None,
        trace: object | None = None,
    ) -> None:
        """Orchestrate full offer extraction via OfferExtractionOrchestrator.

        Delegates to the orchestrator which handles wave management, per-wave
        persistence, trace collection, and progress emission. Signature is
        maintained for backward compatibility with existing callers.
        """
        from luana_core_offer_studio.application.offer_extraction_orchestrator import (
            OfferExtractionOrchestrator,
        )

        orchestrator = OfferExtractionOrchestrator(self)
        await orchestrator.run(
            url=url,
            text=text,
            mode=mode,
            update_instructions=update_instructions,
            progress_callback=progress_callback,
            user_id=user_id,
            trace=trace,  # type: ignore[arg-type]
        )
