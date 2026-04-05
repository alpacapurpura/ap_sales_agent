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
            and (settings.contact.support_email or settings.contact.phone)
        ),
        "testimonials_count": len(settings.testimonials or []),
        "authority_count": len(settings.authority_vault or []),
        "visuals": bool(settings.visuals and settings.visuals.primary_color),
        "positioning": bool(
            settings.positioning and settings.positioning.brand_essence
        ),
        "narrative": bool(settings.narrative and settings.narrative.hero),
        "communication_assets_count": len(
            (settings.communication_assets or CommunicationAssets()).assets
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
        """Orchestrate the full brand extraction process.

        include_visuals=True adds visual identity extraction (colors, fonts, design).
        include_assets=True adds communication assets extraction (taglines, CTAs).
        """
        svc = self.service
        # Store trace on service so _run_section can access it
        svc._trace = trace

        # 1. Get Content
        content = text or ""
        enriched_visual_content = ""
        has_url = bool(url)

        if url:
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

            # Parallel: regular crawl (for text sections) + CSS-enriched crawl (only when visuals requested)
            if include_visuals:
                crawled_content, enriched_visual_content = await asyncio.gather(
                    safe_crawl(), safe_crawl_styles()
                )
            else:
                crawled_content = await safe_crawl()

            t1 = time.time()
            crawl_dur = t1 - t0
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

            if crawled_content:
                content = f"{content}\n\n{crawled_content}"

        if not content.strip() and not update_instructions:
            logger.warning("no_content_to_extract", tenant_id=svc.tenant_id)
            return svc.repository.get_settings(svc.tenant_id)

        logger.info("extraction_context_prepared", total_content_length=len(content))

        # 2. Prepare Context (Current Data)
        current_settings = svc.repository.get_settings(svc.tenant_id)
        current_data_str = ""
        if mode == "update":
            current_data_str = json.dumps(
                current_settings.model_dump(mode="json"), indent=2
            )

        logger.info(
            "extraction_content_ready",
            content_length=len(content),
            current_data_length=len(current_data_str),
        )

        # 3. Run LLM extractions (wave strategy from profile)
        waves = svc.profile.concurrency_waves
        base_sections = (
            6  # identity, story, strategy, people_contact, testimonials, authority
        )
        want_visuals = include_visuals and has_url and enriched_visual_content.strip()
        total_sections = (
            base_sections
            + 2
            + (1 if want_visuals else 0)
            + (1 if include_assets else 0)
        )
        logger.info(
            "starting_llm_extractions",
            sections=total_sections,
            waves=waves,
            profile=svc.profile.name,
        )
        if trace:
            trace.set_content_length(len(content))
            trace.set_sections_total(total_sections)

        extracted_visuals = None
        positioning = BrandPositioning()
        narrative = BrandNarrative()
        communication_assets = CommunicationAssets()

        if waves >= 2:
            (
                extracted_visuals,
                positioning,
                narrative,
                communication_assets,
            ) = await self._run_multi_wave(
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
        else:
            (
                extracted_visuals,
                positioning,
                narrative,
                communication_assets,
            ) = await self._run_single_wave(
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
        # Retrieve the per-section results that were set during wave execution
        identity = self._last_identity
        story = self._last_story
        strategy = self._last_strategy
        people_contact = self._last_people_contact
        testimonials_data = self._last_testimonials
        authority_data = self._last_authority

        results = {
            "identity": not is_empty(identity),
            "story": not is_empty(story),
            "strategy": not is_empty(strategy),
            "people_contact": not is_empty(people_contact),
            "testimonials": not is_empty(testimonials_data),
            "authority": not is_empty(authority_data),
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

        # 4. Merge & Save
        if trace:
            trace.merge_start()
        merge_t0 = time.time()
        result = self._merge_and_save(
            identity,
            story,
            strategy,
            people_contact,
            testimonials_data,
            authority_data,
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
                    enriched_visual_content, current_data_str, update_instructions
                )
            )

        logger.info("extraction_wave_starting", wave=1, sections=wave1_sections)
        if trace:
            trace.wave_start(1, wave1_sections)
        wave1_results = await asyncio.gather(*wave1_coros)
        identity, story, testimonials_data = (
            wave1_results[0],
            wave1_results[1],
            wave1_results[2],
        )
        extracted_visuals = wave1_results[3] if len(wave1_results) > 3 else None
        if progress_callback:
            progress_callback(45, "Analizando identidad y narrativa...")

        # Pause between waves to let TPM budget recover
        logger.info("extraction_wave_pause", delay=svc.profile.wave_delay_seconds)
        if trace:
            trace.wave_pause(1, svc.profile.wave_delay_seconds)
        await asyncio.sleep(svc.profile.wave_delay_seconds)

        # Wave 2: strategy, people_contact, authority
        wave2_sections = ["strategy", "people_contact", "authority"]
        logger.info("extraction_wave_starting", wave=2, sections=wave2_sections)
        if trace:
            trace.wave_start(2, wave2_sections)
        strategy, people_contact, authority_data = await asyncio.gather(
            svc._extract_strategy(content, current_data_str, update_instructions),
            svc._extract_people_contact(content, current_data_str, update_instructions),
            svc._extract_authority(content, current_data_str, update_instructions),
        )
        if progress_callback:
            progress_callback(65, "Extrayendo estrategia...")

        # Wave 3: positioning, narrative
        logger.info("extraction_wave_pause", delay=svc.profile.wave_delay_seconds)
        if trace:
            trace.wave_pause(2, svc.profile.wave_delay_seconds)
        await asyncio.sleep(svc.profile.wave_delay_seconds)

        wave3_sections = ["positioning", "narrative"]
        logger.info("extraction_wave_starting", wave=3, sections=wave3_sections)
        if trace:
            trace.wave_start(3, wave3_sections)
        positioning, narrative = await asyncio.gather(
            svc._extract_positioning(content, current_data_str, update_instructions),
            svc._extract_narrative(content, current_data_str, update_instructions),
        )
        if progress_callback:
            progress_callback(85, "Extrayendo posicionamiento y narrativa...")

        # Wave 4: communication_assets (depends on positioning + narrative) — only if requested
        communication_assets = CommunicationAssets()
        if include_assets:
            logger.info("extraction_wave_pause", delay=svc.profile.wave_delay_seconds)
            if trace:
                trace.wave_pause(3, svc.profile.wave_delay_seconds)
            await asyncio.sleep(svc.profile.wave_delay_seconds)

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

            logger.info(
                "extraction_wave_starting", wave=4, sections=["communication_assets"]
            )
            if trace:
                trace.wave_start(4, ["communication_assets"])
            communication_assets = await svc._extract_communication_assets(
                content,
                current_data_str,
                update_instructions,
                positioning_ctx,
                narrative_ctx,
            )
        if progress_callback:
            progress_callback(95, "Finalizando extraccion...")

        # Store per-section results for summary logging
        self._last_identity = identity
        self._last_story = story
        self._last_strategy = strategy
        self._last_people_contact = people_contact
        self._last_testimonials = testimonials_data
        self._last_authority = authority_data

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
        if want_visuals:
            all_sections.append("visuals")
        if trace:
            trace.wave_start(1, all_sections)
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
            coros.append(
                svc._extract_visuals(
                    enriched_visual_content, current_data_str, update_instructions
                )
            )
        all_results = await asyncio.gather(*coros)
        identity, story, strategy, people_contact, testimonials_data, authority_data = (
            all_results[:6]
        )
        positioning, narrative = all_results[6], all_results[7]
        extracted_visuals = all_results[8] if len(all_results) > 8 else None
        if progress_callback:
            progress_callback(80, "Extrayendo secciones...")

        # Communication assets depend on positioning + narrative — only if requested
        communication_assets = CommunicationAssets()
        if include_assets:
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
            communication_assets = await svc._extract_communication_assets(
                content,
                current_data_str,
                update_instructions,
                positioning_ctx,
                narrative_ctx,
            )
        if progress_callback:
            progress_callback(95, "Finalizando extraccion...")

        # Store per-section results for summary logging
        self._last_identity = identity
        self._last_story = story
        self._last_strategy = strategy
        self._last_people_contact = people_contact
        self._last_testimonials = testimonials_data
        self._last_authority = authority_data

        return extracted_visuals, positioning, narrative, communication_assets

    # ------------------------------------------------------------------
    # Merge & Save
    # ------------------------------------------------------------------

    def _merge_and_save(  # noqa: C901
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

        # Merge Identity (Update non-null fields)
        updated_identity = (
            current_settings.identity.model_dump() if current_settings.identity else {}
        )
        new_identity_dict = new_identity.model_dump(
            exclude_unset=True, exclude_none=True
        )
        updated_identity.update(new_identity_dict)

        # Merge Story
        updated_story = (
            current_settings.story.model_dump() if current_settings.story else {}
        )
        new_story_dict = new_story.model_dump(exclude_unset=True, exclude_none=True)
        if new_story_dict.get("milestones"):
            updated_story["milestones"] = new_story_dict["milestones"]
            del new_story_dict["milestones"]
        updated_story.update(new_story_dict)

        # Merge Strategy
        updated_strategy = (
            current_settings.strategy.model_dump() if current_settings.strategy else {}
        )
        new_strategy_dict = new_strategy.model_dump(
            exclude_unset=True, exclude_none=True
        )
        if new_strategy_dict.get("competitors"):
            updated_strategy["competitors"] = new_strategy_dict["competitors"]
            del new_strategy_dict["competitors"]
        if new_strategy_dict.get("methodology_pillars"):
            updated_strategy["methodology_pillars"] = new_strategy_dict[
                "methodology_pillars"
            ]
            del new_strategy_dict["methodology_pillars"]
        updated_strategy.update(new_strategy_dict)

        # Merge Team (from people_contact)
        updated_team = current_settings.team
        if new_people_contact.key_leadership:
            updated_team = new_people_contact.key_leadership

        # Merge team_metadata (culture_vibe, locations)
        updated_team_metadata = current_settings.team_metadata
        if new_people_contact.culture_vibe or new_people_contact.locations:
            existing_meta = (
                updated_team_metadata.model_dump() if updated_team_metadata else {}
            )
            if new_people_contact.culture_vibe:
                existing_meta["culture_vibe"] = new_people_contact.culture_vibe
            if new_people_contact.locations:
                # BrandTeam.locations expects List[str], but LLM may return a plain string
                raw_locations = new_people_contact.locations
                if isinstance(raw_locations, str):
                    existing_meta["locations"] = [
                        loc.strip() for loc in raw_locations.split(",") if loc.strip()
                    ]
                elif isinstance(raw_locations, list):
                    existing_meta["locations"] = raw_locations
                else:
                    existing_meta["locations"] = [str(raw_locations)]
            updated_team_metadata = BrandTeam(**existing_meta)

        # Merge Contact (from people_contact)
        updated_contact = current_settings.contact
        if new_people_contact.contact:
            if updated_contact:
                existing_contact_dict = updated_contact.model_dump()
                new_contact_dict = new_people_contact.contact.model_dump(
                    exclude_unset=True, exclude_none=True
                )
                existing_contact_dict.update(new_contact_dict)
                updated_contact = BrandContact(**existing_contact_dict)
            else:
                updated_contact = new_people_contact.contact

        # Merge Testimonials (replace if non-empty)
        updated_testimonials = current_settings.testimonials or []
        if new_testimonials.testimonials:
            updated_testimonials = new_testimonials.testimonials

        # Merge Authority (replace if non-empty)
        updated_authority = current_settings.authority_vault or []
        if new_authority.authority_vault:
            updated_authority = new_authority.authority_vault

        # Merge Visuals
        updated_visuals = (
            current_settings.visuals.model_dump() if current_settings.visuals else {}
        )
        if new_visuals:
            new_visuals_dict = new_visuals.model_dump(
                exclude_unset=True, exclude_none=True
            )
            updated_visuals.update(new_visuals_dict)

        # Merge Positioning (deep merge — preserve existing if new is None/empty)
        updated_positioning = current_settings.positioning
        if new_positioning and not is_empty(new_positioning):
            if updated_positioning:
                existing_pos = updated_positioning.model_dump()
                new_pos = new_positioning.model_dump(
                    exclude_unset=True, exclude_none=True
                )
                # Lists replace if non-empty
                for list_field in ("reasons_to_believe",):
                    if new_pos.get(list_field):
                        existing_pos[list_field] = new_pos.pop(list_field)
                # Nested objects: deep merge
                for nested in (
                    "competitive_environment",
                    "insight",
                    "benefits",
                    "values",
                ):
                    if new_pos.get(nested):
                        existing_nested = existing_pos.get(nested) or {}
                        existing_nested.update(new_pos.pop(nested))
                        existing_pos[nested] = existing_nested
                existing_pos.update(new_pos)
                updated_positioning = BrandPositioning(**existing_pos)
            else:
                updated_positioning = new_positioning

        # Merge Narrative (deep merge)
        updated_narrative = current_settings.narrative
        if new_narrative and not is_empty(new_narrative):
            if updated_narrative:
                existing_narr = updated_narrative.model_dump()
                new_narr = new_narrative.model_dump(
                    exclude_unset=True, exclude_none=True
                )
                if new_narr.get("plan"):
                    existing_narr["plan"] = new_narr.pop("plan")
                for nested in ("hero", "problem", "guide", "cta", "outcome"):
                    if new_narr.get(nested):
                        existing_nested = existing_narr.get(nested) or {}
                        existing_nested.update(new_narr.pop(nested))
                        existing_narr[nested] = existing_nested
                existing_narr.update(new_narr)
                updated_narrative = BrandNarrative(**existing_narr)
            else:
                updated_narrative = new_narrative

        # Merge Communication Assets (replace concepts and assets if non-empty)
        updated_comm_assets = current_settings.communication_assets
        if new_communication_assets and not is_empty(new_communication_assets):
            if updated_comm_assets:
                existing_ca = updated_comm_assets.model_dump()
                if new_communication_assets.creative_concepts:
                    existing_ca["creative_concepts"] = (
                        new_communication_assets.model_dump()["creative_concepts"]
                    )
                if new_communication_assets.assets:
                    existing_ca["assets"] = new_communication_assets.model_dump()[
                        "assets"
                    ]
                if new_communication_assets.custom_asset_types:
                    existing_ca["custom_asset_types"] = (
                        new_communication_assets.model_dump()["custom_asset_types"]
                    )
                updated_comm_assets = CommunicationAssets(**existing_ca)
            else:
                updated_comm_assets = new_communication_assets

        # Construct new Settings
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
            }
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
