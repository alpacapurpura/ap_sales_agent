"""Brand extraction orchestrator — wave-based LLM section coordination and merge logic.

Coordinates the multi-section extraction pipeline: schedules waves of concurrent
LLM calls, tracks progress, and merges extracted sections into BrandSettings.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import TYPE_CHECKING, Literal

import structlog
from pydantic import BaseModel, Field

from src.modules.brand.domain import (
    BrandAuthorityItem,
    BrandContact,
    BrandIdentity,
    BrandNarrative,
    BrandPositioning,
    BrandSettings,
    BrandStory,
    BrandStrategy,
    BrandTeam,
    BrandTestimonial,
    BrandVisuals,
    CommunicationAssets,
    KeyFigure,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from src.modules.brand.application.extraction_service import BrandExtractionService
    from src.modules.brand.application.extraction_trace import ExtractionTraceCollector

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Wrapper models for compound extraction results
# ---------------------------------------------------------------------------


class BrandPeopleContactExtraction(BaseModel):
    """Wrapper model for the combined people + contact extraction."""

    key_leadership: list[KeyFigure] = Field(default_factory=list)
    culture_vibe: str | None = None
    locations: str | None = None
    contact: BrandContact | None = None


class BrandTestimonialsExtraction(BaseModel):
    """Wrapper model for testimonials extraction."""

    testimonials: list[BrandTestimonial] = Field(default_factory=list)


class BrandAuthorityExtraction(BaseModel):
    """Wrapper model for authority vault extraction."""

    authority_vault: list[BrandAuthorityItem] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def summarize_settings(settings: BrandSettings) -> dict:
    """Produce a compact summary of which sections have data."""
    return {
        "identity": bool(settings.identity and settings.identity.brand_name),
        "story": bool(settings.story and settings.story.origin_story),
        "strategy": bool(settings.strategy and settings.strategy.methodology_name),
        "team_count": len(settings.team or []),
        "contact": bool(
            settings.contact
            and (settings.contact.support_email or settings.contact.phone),
        ),
        "testimonials_count": len(settings.testimonials or []),
        "authority_count": len(settings.authority_vault or []),
        "visuals": bool(settings.visuals and settings.visuals.primary_color),
        "positioning": bool(
            settings.positioning and settings.positioning.brand_essence,
        ),
        "narrative": bool(settings.narrative and settings.narrative.hero),
        "communication_assets_count": len(
            (settings.communication_assets or CommunicationAssets()).assets,
        ),
    }


# Backward-compat alias
_summarize_settings = summarize_settings


def is_empty(model: BaseModel) -> bool:
    """Check if a pydantic model has only default/empty values."""
    data = model.model_dump(exclude_unset=True, exclude_none=True)
    for value in data.values():
        if isinstance(value, list) and len(value) > 0:
            return False
        if isinstance(value, str) and value.strip():
            return False
        if isinstance(value, dict) and value:
            return False
        if value is not None and not isinstance(value, (str, list, dict)):
            return False
    return True


# ---------------------------------------------------------------------------
# Merge helpers (used by _merge_and_save)
# ---------------------------------------------------------------------------


def _merge_simple_model(current: BaseModel | None, new: BaseModel | None) -> dict:
    """Merge a new model's non-null fields into the current model's dict."""
    existing = current.model_dump() if current else {}
    if new:
        new_dict = new.model_dump(exclude_unset=True, exclude_none=True)
        existing.update(new_dict)
    return existing


def _merge_story(current: BrandStory | None, new: BrandStory) -> dict:
    """Merge story — lists replace, scalars update."""
    existing = current.model_dump() if current else {}
    new_dict = new.model_dump(exclude_unset=True, exclude_none=True)
    if new_dict.get("milestones"):
        existing["milestones"] = new_dict.pop("milestones")
    existing.update(new_dict)
    return existing


def _merge_strategy(current: BrandStrategy | None, new: BrandStrategy) -> dict:
    """Merge strategy — lists replace, scalars update."""
    existing = current.model_dump() if current else {}
    new_dict = new.model_dump(exclude_unset=True, exclude_none=True)
    for list_key in ("competitors", "methodology_pillars"):
        if new_dict.get(list_key):
            existing[list_key] = new_dict.pop(list_key)
    existing.update(new_dict)
    return existing


def _parse_locations(raw_locations) -> list[str]:
    """Normalize locations from LLM output (string, list, or other)."""
    if isinstance(raw_locations, str):
        return [loc.strip() for loc in raw_locations.split(",") if loc.strip()]
    if isinstance(raw_locations, list):
        return raw_locations
    return [str(raw_locations)]


def _merge_people(
    current_team: list | None,
    current_team_metadata: BrandTeam | None,
    people_contact: BrandPeopleContactExtraction,
) -> tuple[list | None, BrandTeam | None]:
    """Merge team + team_metadata from people_contact extraction."""
    updated_team = current_team
    if people_contact.key_leadership:
        updated_team = people_contact.key_leadership

    updated_metadata = current_team_metadata
    if people_contact.culture_vibe or people_contact.locations:
        existing_meta = updated_metadata.model_dump() if updated_metadata else {}
        if people_contact.culture_vibe:
            existing_meta["culture_vibe"] = people_contact.culture_vibe
        if people_contact.locations:
            existing_meta["locations"] = _parse_locations(people_contact.locations)
        updated_metadata = BrandTeam(**existing_meta)

    return updated_team, updated_metadata


def _merge_contact(
    current: BrandContact | None,
    new: BrandContact | None,
) -> BrandContact | None:
    """Merge contact — deep update existing or replace."""
    if not new:
        return current
    if current:
        existing_dict = current.model_dump()
        new_dict = new.model_dump(exclude_unset=True, exclude_none=True)
        existing_dict.update(new_dict)
        return BrandContact(**existing_dict)
    return new


def _deep_merge_with_nested(
    existing_dict: dict,
    new_dict: dict,
    list_fields: tuple,
    nested_fields: tuple,
) -> dict:
    """Deep merge: lists replace, nested objects merge, rest updates."""
    for list_field in list_fields:
        if new_dict.get(list_field):
            existing_dict[list_field] = new_dict.pop(list_field)
    for nested in nested_fields:
        if new_dict.get(nested):
            existing_nested = existing_dict.get(nested) or {}
            existing_nested.update(new_dict.pop(nested))
            existing_dict[nested] = existing_nested
    existing_dict.update(new_dict)
    return existing_dict


def _merge_positioning(
    current: BrandPositioning | None,
    new: BrandPositioning | None,
) -> BrandPositioning | None:
    """Merge positioning with deep merge for nested objects."""
    if not new or is_empty(new):
        return current
    if not current:
        return new
    existing = current.model_dump()
    new_dict = new.model_dump(exclude_unset=True, exclude_none=True)
    _deep_merge_with_nested(
        existing,
        new_dict,
        list_fields=("reasons_to_believe",),
        nested_fields=("competitive_environment", "insight", "benefits", "values"),
    )
    return BrandPositioning(**existing)


def _merge_narrative(
    current: BrandNarrative | None,
    new: BrandNarrative | None,
) -> BrandNarrative | None:
    """Merge narrative with deep merge for nested StoryBrand objects."""
    if not new or is_empty(new):
        return current
    if not current:
        return new
    existing = current.model_dump()
    new_dict = new.model_dump(exclude_unset=True, exclude_none=True)
    _deep_merge_with_nested(
        existing,
        new_dict,
        list_fields=("plan",),
        nested_fields=("hero", "problem", "guide", "cta", "outcome"),
    )
    return BrandNarrative(**existing)


def _merge_communication_assets(
    current: CommunicationAssets | None,
    new: CommunicationAssets | None,
) -> CommunicationAssets | None:
    """Merge communication assets — replace sub-collections if non-empty."""
    if not new or is_empty(new):
        return current
    if not current:
        return new
    existing = current.model_dump()
    new_dump = new.model_dump()
    for key in ("creative_concepts", "assets", "custom_asset_types"):
        if getattr(new, key):
            existing[key] = new_dump[key]
    return CommunicationAssets(**existing)


# ---------------------------------------------------------------------------
# ExtractionOrchestrator
# ---------------------------------------------------------------------------


class ExtractionOrchestrator:
    """Coordinates wave-based LLM extraction and merges results into BrandSettings.

    Receives a reference to the BrandExtractionService for individual section
    extraction methods. This class owns the scheduling (waves, pauses, progress)
    and the merge-and-save step.
    """

    def __init__(self, service: BrandExtractionService) -> None:
        self.service = service

    async def _crawl_content(
        self,
        url: str,
        include_visuals: bool,
        progress_callback: Callable[[int, str], None] | None,
        trace: ExtractionTraceCollector | None,
    ) -> tuple[str, str]:
        """Crawl URL content and optionally styles. Returns (content, visual_content)."""
        svc = self.service
        logger.info("starting_crawl", url=url)
        if trace:
            trace.crawl_start(url)

        t0 = time.time()

        async def safe_crawl() -> str:
            try:
                return await svc.crawler.crawl_content(url)
            except Exception as e:
                logger.error("crawl_failed", error=str(e))
                return ""

        async def safe_crawl_styles() -> str:
            try:
                return await svc.crawler.crawl_content_with_styles(url)
            except Exception as e:
                logger.error("crawl_styles_failed", error=str(e))
                return ""

        enriched_visual_content = ""
        if include_visuals:
            crawled_content, enriched_visual_content = await asyncio.gather(
                safe_crawl(),
                safe_crawl_styles(),
            )
        else:
            crawled_content = await safe_crawl()

        crawl_dur = time.time() - t0
        logger.info(
            "parallel_crawl_completed",
            duration=crawl_dur,
            crawl_length=len(crawled_content),
            enriched_length=len(enriched_visual_content),
        )
        if trace:
            trace.crawl_end(
                crawl_dur,
                content_len=len(crawled_content),
                visual_len=len(enriched_visual_content),
            )
        if progress_callback:
            progress_callback(10, "Escaneando sitio web...")

        return crawled_content, enriched_visual_content

    def _log_extraction_summary(
        self,
        positioning,
        narrative,
        communication_assets,
        extracted_visuals,
        include_assets: bool,
        total_sections: int,
    ) -> int:
        """Log extraction results and return succeeded count."""
        results = {
            "identity": not is_empty(self._last_identity),
            "story": not is_empty(self._last_story),
            "strategy": not is_empty(self._last_strategy),
            "people_contact": not is_empty(self._last_people_contact),
            "testimonials": not is_empty(self._last_testimonials),
            "authority": not is_empty(self._last_authority),
            "positioning": not is_empty(positioning),
            "narrative": not is_empty(narrative),
        }
        if include_assets:
            results["communication_assets"] = not is_empty(communication_assets)
        if extracted_visuals is not None:
            results["visuals"] = not is_empty(extracted_visuals)
        succeeded = sum(1 for v in results.values() if v)
        logger.info(
            "extraction_results_summary",
            results=results,
            succeeded=succeeded,
            total=total_sections,
        )
        return succeeded

    async def run(
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
    ) -> BrandSettings:
        """Orchestrate the full brand extraction process."""
        svc = self.service
        svc._trace = trace

        # 1. Get Content
        content = text or ""
        enriched_visual_content = ""
        has_url = bool(url)

        if url:
            crawled_content, enriched_visual_content = await self._crawl_content(
                url,
                include_visuals,
                progress_callback,
                trace,
            )
            if crawled_content:
                content = f"{content}\n\n{crawled_content}"

        if not content.strip() and not update_instructions:
            logger.warning("no_content_to_extract", tenant_id=svc.tenant_id)
            return svc.repository.get_settings(svc.tenant_id)

        logger.info("extraction_context_prepared", total_content_length=len(content))

        # 2. Prepare Context (Current Data)
        current_data_str = ""
        if mode == "update":
            current_settings = svc.repository.get_settings(svc.tenant_id)
            current_data_str = json.dumps(
                current_settings.model_dump(mode="json"),
                indent=2,
            )

        logger.info(
            "extraction_content_ready",
            content_length=len(content),
            current_data_length=len(current_data_str),
        )

        # 3. Run LLM extractions (wave strategy from profile)
        waves = svc.profile.concurrency_waves
        want_visuals = (
            include_visuals and has_url and bool(enriched_visual_content.strip())
        )
        total_sections = 8 + (1 if want_visuals else 0) + (1 if include_assets else 0)
        logger.info(
            "starting_llm_extractions",
            sections=total_sections,
            waves=waves,
            profile=svc.profile.name,
        )
        if trace:
            trace.set_content_length(len(content))
            trace.set_sections_total(total_sections)

        wave_fn = self._run_multi_wave if waves >= 2 else self._run_single_wave
        extracted_visuals, positioning, narrative, communication_assets = await wave_fn(
            svc,
            content,
            current_data_str,
            update_instructions,
            enriched_visual_content,
            want_visuals,
            include_assets,
            progress_callback,
            trace,
        )

        # Log extraction results summary
        succeeded = self._log_extraction_summary(
            positioning,
            narrative,
            communication_assets,
            extracted_visuals,
            include_assets,
            total_sections,
        )

        # 4. Merge & Save
        if trace:
            trace.merge_start()
        merge_t0 = time.time()
        result = self._merge_and_save(
            self._last_identity,
            self._last_story,
            self._last_strategy,
            self._last_people_contact,
            self._last_testimonials,
            self._last_authority,
            extracted_visuals,
            new_positioning=positioning,
            new_narrative=narrative,
            new_communication_assets=communication_assets,
            dry_run=dry_run,
        )
        if trace:
            trace.merge_end(time.time() - merge_t0)
            trace.finish(status="completed", sections_succeeded=succeeded)

        return result

    # ------------------------------------------------------------------
    # Wave execution strategies
    # ------------------------------------------------------------------

    async def _run_wave(
        self,
        wave_num: int,
        sections: list[str],
        coros: list,
        svc: BrandExtractionService,
        trace: ExtractionTraceCollector | None,
    ) -> list:
        """Execute a single wave of concurrent extractions with logging."""
        logger.info("extraction_wave_starting", wave=wave_num, sections=sections)
        if trace:
            trace.wave_start(wave_num, sections)
        return await asyncio.gather(*coros)

    async def _pause_between_waves(
        self,
        wave_num: int,
        svc: BrandExtractionService,
        trace: ExtractionTraceCollector | None,
    ) -> None:
        """Pause between waves to let TPM budget recover."""
        logger.info("extraction_wave_pause", delay=svc.profile.wave_delay_seconds)
        if trace:
            trace.wave_pause(wave_num, svc.profile.wave_delay_seconds)
        await asyncio.sleep(svc.profile.wave_delay_seconds)

    async def _extract_assets_if_requested(
        self,
        svc: BrandExtractionService,
        include_assets: bool,
        content: str,
        current_data_str: str,
        update_instructions: str | None,
        positioning,
        narrative,
        wave_num: int | None = None,
        trace: ExtractionTraceCollector | None = None,
    ) -> CommunicationAssets:
        """Extract communication assets if requested, otherwise return empty."""
        if not include_assets:
            return CommunicationAssets()

        if wave_num:
            await self._pause_between_waves(wave_num, svc, trace)

        positioning_ctx = (
            json.dumps(positioning.model_dump(exclude_none=True), indent=2)
            if not is_empty(positioning)
            else ""
        )
        narrative_ctx = (
            json.dumps(narrative.model_dump(exclude_none=True), indent=2)
            if not is_empty(narrative)
            else ""
        )

        next_wave = (wave_num or 0) + 1
        logger.info(
            "extraction_wave_starting",
            wave=next_wave,
            sections=["communication_assets"],
        )
        if trace:
            trace.wave_start(next_wave, ["communication_assets"])
        return await svc._extract_communication_assets(
            content,
            current_data_str,
            update_instructions,
            positioning_ctx,
            narrative_ctx,
        )

    def _store_section_results(
        self,
        identity,
        story,
        strategy,
        people_contact,
        testimonials_data,
        authority_data,
    ) -> None:
        """Store per-section results for summary logging."""
        self._last_identity = identity
        self._last_story = story
        self._last_strategy = strategy
        self._last_people_contact = people_contact
        self._last_testimonials = testimonials_data
        self._last_authority = authority_data

    async def _run_multi_wave(
        self,
        svc: BrandExtractionService,
        content: str,
        current_data_str: str,
        update_instructions: str | None,
        enriched_visual_content: str,
        want_visuals: bool,
        include_assets: bool,
        progress_callback: Callable[[int, str], None] | None,
        trace: ExtractionTraceCollector | None,
    ) -> tuple:
        """Execute extraction in multiple waves (for low-TPM models)."""

        # Wave 1: identity, story, testimonials + visuals (lighter extractions)
        wave1_sections = ["identity", "story", "testimonials"]
        wave1_coros = [
            svc._extract_identity(content, current_data_str, update_instructions),
            svc._extract_story(content, current_data_str, update_instructions),
            svc._extract_testimonials(content, current_data_str, update_instructions),
        ]
        if want_visuals:
            wave1_sections.append("visuals")
            wave1_coros.append(
                svc._extract_visuals(
                    enriched_visual_content,
                    current_data_str,
                    update_instructions,
                ),
            )

        wave1_results = await self._run_wave(1, wave1_sections, wave1_coros, svc, trace)
        identity, story, testimonials_data = (
            wave1_results[0],
            wave1_results[1],
            wave1_results[2],
        )
        extracted_visuals = wave1_results[3] if len(wave1_results) > 3 else None
        if progress_callback:
            progress_callback(45, "Analizando identidad y narrativa...")

        # Wave 2: strategy, people_contact, authority
        await self._pause_between_waves(1, svc, trace)
        wave2_results = await self._run_wave(
            2,
            ["strategy", "people_contact", "authority"],
            [
                svc._extract_strategy(content, current_data_str, update_instructions),
                svc._extract_people_contact(
                    content,
                    current_data_str,
                    update_instructions,
                ),
                svc._extract_authority(content, current_data_str, update_instructions),
            ],
            svc,
            trace,
        )
        strategy, people_contact, authority_data = wave2_results
        if progress_callback:
            progress_callback(65, "Extrayendo estrategia...")

        # Wave 3: positioning, narrative
        await self._pause_between_waves(2, svc, trace)
        wave3_results = await self._run_wave(
            3,
            ["positioning", "narrative"],
            [
                svc._extract_positioning(
                    content,
                    current_data_str,
                    update_instructions,
                ),
                svc._extract_narrative(content, current_data_str, update_instructions),
            ],
            svc,
            trace,
        )
        positioning, narrative = wave3_results
        if progress_callback:
            progress_callback(85, "Extrayendo posicionamiento y narrativa...")

        # Wave 4: communication_assets (depends on positioning + narrative)
        communication_assets = await self._extract_assets_if_requested(
            svc,
            include_assets,
            content,
            current_data_str,
            update_instructions,
            positioning,
            narrative,
            wave_num=3,
            trace=trace,
        )
        if progress_callback:
            progress_callback(95, "Finalizando extraccion...")

        self._store_section_results(
            identity,
            story,
            strategy,
            people_contact,
            testimonials_data,
            authority_data,
        )
        return extracted_visuals, positioning, narrative, communication_assets

    async def _run_single_wave(
        self,
        svc: BrandExtractionService,
        content: str,
        current_data_str: str,
        update_instructions: str | None,
        enriched_visual_content: str,
        want_visuals: bool,
        include_assets: bool,
        progress_callback: Callable[[int, str], None] | None,
        trace: ExtractionTraceCollector | None,
    ) -> tuple:
        """Execute all extractions concurrently (for high-TPM models)."""

        all_sections = [
            "identity",
            "story",
            "strategy",
            "people_contact",
            "testimonials",
            "authority",
            "positioning",
            "narrative",
        ]
        coros = [
            svc._extract_identity(content, current_data_str, update_instructions),
            svc._extract_story(content, current_data_str, update_instructions),
            svc._extract_strategy(content, current_data_str, update_instructions),
            svc._extract_people_contact(content, current_data_str, update_instructions),
            svc._extract_testimonials(content, current_data_str, update_instructions),
            svc._extract_authority(content, current_data_str, update_instructions),
            svc._extract_positioning(content, current_data_str, update_instructions),
            svc._extract_narrative(content, current_data_str, update_instructions),
        ]
        if want_visuals:
            all_sections.append("visuals")
            coros.append(
                svc._extract_visuals(
                    enriched_visual_content,
                    current_data_str,
                    update_instructions,
                ),
            )

        all_results = await self._run_wave(1, all_sections, coros, svc, trace)
        identity, story, strategy, people_contact, testimonials_data, authority_data = (
            all_results[:6]
        )
        positioning, narrative = all_results[6], all_results[7]
        extracted_visuals = all_results[8] if len(all_results) > 8 else None
        if progress_callback:
            progress_callback(80, "Extrayendo secciones...")

        communication_assets = await self._extract_assets_if_requested(
            svc,
            include_assets,
            content,
            current_data_str,
            update_instructions,
            positioning,
            narrative,
        )
        if progress_callback:
            progress_callback(95, "Finalizando extraccion...")

        self._store_section_results(
            identity,
            story,
            strategy,
            people_contact,
            testimonials_data,
            authority_data,
        )
        return extracted_visuals, positioning, narrative, communication_assets

    # ------------------------------------------------------------------
    # Merge & Save
    # ------------------------------------------------------------------

    def _merge_and_save(
        self,
        new_identity: BrandIdentity,
        new_story: BrandStory,
        new_strategy: BrandStrategy,
        new_people_contact: BrandPeopleContactExtraction,
        new_testimonials: BrandTestimonialsExtraction,
        new_authority: BrandAuthorityExtraction,
        new_visuals: BrandVisuals | None = None,
        new_positioning: BrandPositioning | None = None,
        new_narrative: BrandNarrative | None = None,
        new_communication_assets: CommunicationAssets | None = None,
        dry_run: bool = False,
    ) -> BrandSettings:

        svc = self.service
        current_settings = svc.repository.get_settings(svc.tenant_id)

        updated_identity = _merge_simple_model(current_settings.identity, new_identity)
        updated_story = _merge_story(current_settings.story, new_story)
        updated_strategy = _merge_strategy(current_settings.strategy, new_strategy)
        updated_team, updated_team_metadata = _merge_people(
            current_settings.team,
            current_settings.team_metadata,
            new_people_contact,
        )
        updated_contact = _merge_contact(
            current_settings.contact,
            new_people_contact.contact,
        )
        updated_testimonials = new_testimonials.testimonials or (
            current_settings.testimonials or []
        )
        updated_authority = new_authority.authority_vault or (
            current_settings.authority_vault or []
        )
        updated_visuals = _merge_simple_model(current_settings.visuals, new_visuals)
        updated_positioning = _merge_positioning(
            current_settings.positioning,
            new_positioning,
        )
        updated_narrative = _merge_narrative(current_settings.narrative, new_narrative)
        updated_comm_assets = _merge_communication_assets(
            current_settings.communication_assets,
            new_communication_assets,
        )

        final_settings = current_settings.model_copy(
            update={
                "identity": BrandIdentity(**updated_identity),
                "story": BrandStory(**updated_story),
                "strategy": BrandStrategy(**updated_strategy),
                "team": updated_team,
                "team_metadata": updated_team_metadata,
                "contact": updated_contact,
                "testimonials": updated_testimonials,
                "authority_vault": updated_authority,
                "visuals": BrandVisuals(**updated_visuals),
                "positioning": updated_positioning,
                "narrative": updated_narrative,
                "communication_assets": updated_comm_assets,
            },
        )

        logger.info(
            "merge_completed",
            tenant_id=str(svc.tenant_id),
            summary=summarize_settings(final_settings),
        )

        if dry_run:
            logger.info("dry_run_extraction_completed", tenant_id=svc.tenant_id)
            return final_settings

        saved = svc.repository.save_settings(svc.tenant_id, final_settings)
        logger.info(
            "extraction_saved_to_db",
            tenant_id=str(svc.tenant_id),
            summary=summarize_settings(saved),
        )
        return saved
