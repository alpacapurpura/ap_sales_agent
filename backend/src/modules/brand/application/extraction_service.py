"""Brand extraction service — LLM section extractors and prompt orchestration.

After decomposition, this module contains:
- ExtractionProfile dataclass and profile constants
- BrandExtractionService class with individual section extractors
- Prompt rendering and schema instruction helpers
- Delegates crawling to BrandCrawler, orchestration to ExtractionOrchestrator

Crawling utilities live in extraction_crawler.py.
Wave orchestration and merge logic live in extraction_orchestrator.py.
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import structlog

if TYPE_CHECKING:
    from collections.abc import Callable
    from uuid import UUID

    from pydantic import BaseModel
    from sqlalchemy.orm import Session

    from src.modules.brand.application.extraction_trace import ExtractionTraceCollector

import traceback

from src.core.enums import ModelRole

# Import crawler functions/class
from src.modules.brand.application.extraction_crawler import (
    _HIGH_KEYWORDS,  # noqa: F401
    _MEDIUM_KEYWORDS,  # noqa: F401
    _SKIP_EXTENSIONS,  # noqa: F401
    # Constants (re-exported for backward compat)
    _SKIP_PATTERNS,  # noqa: F401
    BrandCrawler,
    extract_css_relevant,
    extract_html_with_styles,
    extract_text_from_html,
    score_link,
    truncate_at_page_boundary,
)

# Import orchestrator models/functions
from src.modules.brand.application.extraction_orchestrator import (
    BrandAuthorityExtraction,
    BrandPeopleContactExtraction,
    BrandTestimonialsExtraction,
    ExtractionOrchestrator,
    is_empty,
    summarize_settings,
)
from src.modules.brand.domain import (
    BrandIdentity,
    BrandNarrative,
    BrandPositioning,
    BrandSettings,
    BrandStory,
    BrandStrategy,
    BrandVisuals,
    CommunicationAssets,
)
from src.modules.brand.infrastructure.repositories.brand_repository import (
    BrandRepository,
)
from src.shared.application.ai_action_service import (
    AIActionPolicy,
    AIActionService,
    AIModelPolicy,
)
from src.shared.infrastructure.prompts.base import prompt_loader

# Backward-compat alias
_summarize_settings = summarize_settings

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Extraction Profiles — both always exist, switch via BRAND_EXTRACTION_PROFILE
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExtractionProfile:
    """Immutable configuration for how brand extraction behaves."""

    name: str
    model_type: ModelRole  # Semantic role — maps to LLM factory via registry
    max_output_tokens: int  # max completion tokens (model-dependent limit)
    retries: int  # how many attempts per section
    retry_delay_seconds: float  # base delay between retries
    concurrency_waves: int  # 1 = all-6-concurrent, 2 = two-waves-of-3
    wave_delay_seconds: float  # pause between waves (only when waves > 1)


# "safe" — conservative with 3 waves and longer delays.
PROFILE_SAFE = ExtractionProfile(
    name="safe",
    model_type=ModelRole.REASONING,
    max_output_tokens=4000,
    retries=3,
    retry_delay_seconds=5.0,
    concurrency_waves=3,
    wave_delay_seconds=5.0,
)

# "fast" — all 6 concurrent, minimal delays.
PROFILE_FAST = ExtractionProfile(
    name="fast",
    model_type=ModelRole.REASONING,
    max_output_tokens=4000,
    retries=2,
    retry_delay_seconds=1.0,
    concurrency_waves=1,
    wave_delay_seconds=0,
)

_PROFILES = {
    "safe": PROFILE_SAFE,
    "fast": PROFILE_FAST,
}


def _get_active_profile() -> ExtractionProfile:
    """Resolve active profile from settings.BRAND_EXTRACTION_PROFILE (default: safe)."""
    from src.core.config import settings as app_settings

    name = app_settings.BRAND_EXTRACTION_PROFILE.lower()
    profile = _PROFILES.get(name)
    if not profile:
        logger.warning("unknown_extraction_profile", requested=name, fallback="safe")
        profile = PROFILE_SAFE
    return profile


# ---------------------------------------------------------------------------
# BrandExtractionService
# ---------------------------------------------------------------------------


class BrandExtractionService:
    """Coordinates LLM-based brand data extraction from web content.

    Individual section extractors live here (_extract_identity, _extract_story, etc.).
    Crawling is delegated to self.crawler (BrandCrawler).
    Orchestration (waves, merge, save) is delegated to self.orchestrator (ExtractionOrchestrator).
    """

    # Backward-compat static method aliases for crawler functions
    _score_link = staticmethod(score_link)
    _extract_text_from_html = staticmethod(extract_text_from_html)
    _extract_css_relevant = staticmethod(extract_css_relevant)
    _extract_html_with_styles = staticmethod(extract_html_with_styles)
    _truncate_at_page_boundary = staticmethod(truncate_at_page_boundary)
    _is_empty = staticmethod(is_empty)

    def __init__(self, db: Session, tenant_id: UUID) -> None:
        """Initialize brand extraction service."""
        self.db = db
        self.tenant_id = tenant_id
        self.repository = BrandRepository(db)
        self.ai_action_service = AIActionService()
        self._trace: ExtractionTraceCollector | None = None

        # Resolve extraction profile from env
        self.profile = _get_active_profile()
        self.default_policy = AIActionPolicy(
            retries=self.profile.retries,
            retry_delay_seconds=self.profile.retry_delay_seconds,
            model=AIModelPolicy(
                model_type=self.profile.model_type,
                temperature=0,
                max_output_tokens=self.profile.max_output_tokens,
            ),
        )

        # Composed collaborators
        self.crawler = BrandCrawler()
        self.orchestrator = ExtractionOrchestrator(self)

        logger.info(
            "extraction_profile_loaded",
            profile=self.profile.name,
            model_type=self.profile.model_type,
            max_output_tokens=self.profile.max_output_tokens,
            concurrency_waves=self.profile.concurrency_waves,
            retries=self.profile.retries,
        )

    # ------------------------------------------------------------------
    # Policy helpers
    # ------------------------------------------------------------------

    def _visuals_policy(self) -> AIActionPolicy:
        """Policy override for visuals extraction — needs more output tokens."""
        return AIActionPolicy(
            retries=self.profile.retries,
            retry_delay_seconds=self.profile.retry_delay_seconds,
            model=AIModelPolicy(
                model_type=self.profile.model_type,
                temperature=0,
                max_output_tokens=self.profile.max_output_tokens,
            ),
        )

    def _communication_assets_policy(self) -> AIActionPolicy:
        """Policy for communication assets — needs more tokens and higher temperature."""
        return AIActionPolicy(
            retries=self.profile.retries,
            retry_delay_seconds=self.profile.retry_delay_seconds,
            model=AIModelPolicy(
                model_type=self.profile.model_type,
                temperature=0.3,
                max_output_tokens=self.profile.max_output_tokens,
            ),
        )

    # ------------------------------------------------------------------
    # Prompt rendering
    # ------------------------------------------------------------------

    def _render_prompt(
        self,
        template_name: str,
        content: str,
        current_data: str,
        instructions: str,
        max_chars: int = 50000,
    ) -> str:
        """Render a brand extraction prompt using the PromptLoader (Jinja2 + DB fallback)."""
        try:
            rendered = prompt_loader.render(
                template_name,
                content=truncate_at_page_boundary(content, max_chars=max_chars),
                current_data=current_data or "None",
                instructions=instructions or "None",
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
    # Public API
    # ------------------------------------------------------------------

    async def extract_all(
        self,
        url: str | None = None,
        text: str | None = None,
        mode: Literal["initial", "update"] = "initial",
        update_instructions: str | None = None,
        dry_run: bool = False,
        include_visuals: bool = False,
        include_assets: bool = False,
        progress_callback: Callable[[int, str], None] | None = None,
        trace: ExtractionTraceCollector | None = None,
        user_id: UUID | None = None,
    ) -> BrandSettings:
        """Orchestrate the full brand extraction process. Delegates to ExtractionOrchestrator."""
        return await self.orchestrator.run(
            url=url,
            text=text,
            mode=mode,
            update_instructions=update_instructions,
            dry_run=dry_run,
            include_visuals=include_visuals,
            include_assets=include_assets,
            progress_callback=progress_callback,
            trace=trace,
            user_id=user_id,
        )

    async def extract_visuals_only(self, url: str) -> BrandVisuals:
        """Extract only visual identity (colors, fonts, style) from a URL.

        Uses CSS-enriched HTML (not stripped text) so the LLM can see actual
        colors, fonts, and class names from the website.
        """
        content = await self.crawler.crawl_content_with_styles(url)
        if not content.strip():
            msg = "Could not crawl content from URL"
            raise ValueError(msg)
        prompt = self._render_prompt(
            "brand_extract_visuals",
            content,
            "",
            "",
            max_chars=40000,
        )
        return await self._run_section(
            "visuals",
            "brand_extract_visuals",
            prompt,
            BrandVisuals,
            BrandVisuals(),
            "Extract the visual identity (colors, fonts, design style).",
            policy=self._visuals_policy(),
        )

    # Backward compat: crawl methods delegate to crawler
    async def crawl_content(self, url: str) -> str:
        """Delegate to BrandCrawler."""
        return await self.crawler.crawl_content(url)

    async def crawl_content_with_styles(self, url: str) -> str:
        """Delegate to BrandCrawler."""
        return await self.crawler.crawl_content_with_styles(url)

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
        policy: AIActionPolicy | None = None,
    ) -> BaseModel:
        """Run a single extraction section with timing and timeout."""
        effective_policy = policy or self.default_policy
        trace = self._trace
        t0 = time.time()
        try:
            logger.info(
                "extract_section_starting",
                section=section_name,
                prompt_length=len(prompt),
            )
            if trace:
                trace.section_start(section_name, prompt_length=len(prompt))
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
                    policy=effective_policy,
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
            if trace:
                trace.section_success(
                    section_name,
                    elapsed,
                    field_count=len(extracted),
                    fields=list(extracted.keys()),
                )
        except TimeoutError:
            elapsed = time.time() - t0
            logger.exception(
                "extract_section_timeout",
                section=section_name,
                timeout=per_call_timeout,
                duration_s=round(elapsed, 2),
            )
            if trace:
                trace.section_timeout(
                    section_name,
                    elapsed,
                    timeout_limit=per_call_timeout,
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
            if trace:
                trace.section_failed(
                    section_name,
                    elapsed,
                    error=str(e),
                    error_type=type(e).__name__,
                )
            return default_result

        else:
            return result

    # ------------------------------------------------------------------
    # Individual section extractors
    # ------------------------------------------------------------------

    async def _extract_identity(
        self,
        content: str,
        current_data: str,
        instructions: str | None,
    ) -> BrandIdentity:
        prompt = self._render_prompt(
            "brand_extract_identity",
            content,
            current_data,
            instructions,
        )
        return await self._run_section(
            "identity",
            "brand_extract_identity",
            prompt,
            BrandIdentity,
            BrandIdentity(),
            "Extract the Brand Identity.",
        )

    async def _extract_story(
        self,
        content: str,
        current_data: str,
        instructions: str | None,
    ) -> BrandStory:
        prompt = self._render_prompt(
            "brand_extract_story",
            content,
            current_data,
            instructions,
        )
        return await self._run_section(
            "story",
            "brand_extract_story",
            prompt,
            BrandStory,
            BrandStory(),
            "Extract the Brand Story.",
        )

    async def _extract_strategy(
        self,
        content: str,
        current_data: str,
        instructions: str | None,
    ) -> BrandStrategy:
        prompt = self._render_prompt(
            "brand_extract_strategy",
            content,
            current_data,
            instructions,
            max_chars=65000,
        )
        return await self._run_section(
            "strategy",
            "brand_extract_strategy",
            prompt,
            BrandStrategy,
            BrandStrategy(),
            "Extract the Brand Strategy.",
        )

    async def _extract_people_contact(
        self,
        content: str,
        current_data: str,
        instructions: str | None,
    ) -> BrandPeopleContactExtraction:
        prompt = self._render_prompt(
            "brand_extract_people_contact",
            content,
            current_data,
            instructions,
            max_chars=65000,
        )
        return await self._run_section(
            "people_contact",
            "brand_extract_people_contact",
            prompt,
            BrandPeopleContactExtraction,
            BrandPeopleContactExtraction(),
            "Extract People and Contact information.",
        )

    async def _extract_testimonials(
        self,
        content: str,
        current_data: str,
        instructions: str | None,
    ) -> BrandTestimonialsExtraction:
        prompt = self._render_prompt(
            "brand_extract_testimonials",
            content,
            current_data,
            instructions,
        )
        return await self._run_section(
            "testimonials",
            "brand_extract_testimonials",
            prompt,
            BrandTestimonialsExtraction,
            BrandTestimonialsExtraction(),
            "Extract Testimonials.",
        )

    async def _extract_authority(
        self,
        content: str,
        current_data: str,
        instructions: str | None,
    ) -> BrandAuthorityExtraction:
        prompt = self._render_prompt(
            "brand_extract_authority",
            content,
            current_data,
            instructions,
        )
        return await self._run_section(
            "authority",
            "brand_extract_authority",
            prompt,
            BrandAuthorityExtraction,
            BrandAuthorityExtraction(),
            "Extract Authority elements.",
        )

    async def _extract_visuals(
        self,
        content: str,
        current_data: str,
        instructions: str | None,
    ) -> BrandVisuals:
        """Extract visual identity (colors, fonts, design style) from CSS-enriched content."""
        prompt = self._render_prompt(
            "brand_extract_visuals",
            content,
            current_data,
            instructions,
            max_chars=40000,
        )
        return await self._run_section(
            "visuals",
            "brand_extract_visuals",
            prompt,
            BrandVisuals,
            BrandVisuals(),
            "Extract the visual identity (colors, fonts, design style).",
            policy=self._visuals_policy(),
        )

    async def _extract_positioning(
        self,
        content: str,
        current_data: str,
        instructions: str | None,
    ) -> BrandPositioning:
        """Extract Brand Love Key positioning from content."""
        prompt = self._render_prompt(
            "brand_extract_positioning",
            content,
            current_data,
            instructions,
            max_chars=65000,
        )
        return await self._run_section(
            "positioning",
            "brand_extract_positioning",
            prompt,
            BrandPositioning,
            BrandPositioning(),
            "Extract Brand Love Key positioning.",
        )

    async def _extract_narrative(
        self,
        content: str,
        current_data: str,
        instructions: str | None,
    ) -> BrandNarrative:
        """Extract StoryBrand narrative from content."""
        prompt = self._render_prompt(
            "brand_extract_narrative",
            content,
            current_data,
            instructions,
            max_chars=65000,
        )
        return await self._run_section(
            "narrative",
            "brand_extract_narrative",
            prompt,
            BrandNarrative,
            BrandNarrative(),
            "Extract StoryBrand narrative.",
        )

    async def _extract_communication_assets(
        self,
        content: str,
        current_data: str,
        instructions: str | None,
        positioning_ctx: str,
        narrative_ctx: str,
    ) -> CommunicationAssets:
        """Generate communication assets using positioning + narrative as context."""
        try:
            rendered = prompt_loader.render(
                "brand_extract_communication_assets",
                content=truncate_at_page_boundary(content, max_chars=30000),
                positioning_context=positioning_ctx or "No disponible",
                narrative_context=narrative_ctx or "No disponible",
                current_data=current_data or "None",
                instructions=instructions or "None",
            )
        except Exception as e:
            logger.exception(
                "prompt_render_failed",
                template="brand_extract_communication_assets",
                error=str(e),
            )
            return CommunicationAssets()

        return await self._run_section(
            "communication_assets",
            "brand_extract_communication_assets",
            rendered,
            CommunicationAssets,
            CommunicationAssets(),
            "Generate strategic communication assets for the brand.",
            policy=self._communication_assets_policy(),
        )
