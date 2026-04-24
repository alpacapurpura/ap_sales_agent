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
    BrandTestimonial,
    BrandVisuals,
    CommunicationAssets,
    KeyFigure,
)
from src.shared.application.extraction.base_orchestrator import (
    BaseExtractionOrchestrator,
)
from src.shared.application.progress_emitter import emit_progress

if TYPE_CHECKING:
    from collections.abc import Callable
    from uuid import UUID

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
            settings.contact and (settings.contact.support_email or settings.contact.phone),
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


def _parse_locations(raw_locations: str | list[str] | object) -> list[str]:
    """Normalize locations from LLM output (string, list, or other)."""
    if isinstance(raw_locations, str):
        return [loc.strip() for loc in raw_locations.split(",") if loc.strip()]
    if isinstance(raw_locations, list):
        return raw_locations
    return [str(raw_locations)]


def _merge_people(
    current_team: list | None,
    people_contact: BrandPeopleContactExtraction,
) -> list | None:
    """Merge team members from people_contact extraction.

    team_metadata (BrandTeam) was removed in Sprint 2.D — culture_vibe and
    locations from extraction are now silently dropped since there is no
    longer a destination field for them in BrandSettings.
    """
    if people_contact.key_leadership:
        return people_contact.key_leadership
    return current_team


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


class ExtractionOrchestrator(BaseExtractionOrchestrator):
    """Coordinates wave-based LLM extraction and merges results into BrandSettings.

    Receives a reference to the BrandExtractionService for individual section
    extraction methods. This class owns the scheduling (waves, pauses, progress)
    and the merge-and-save step. Wave + progress mechanics come from
    :class:`BaseExtractionOrchestrator`.
    """

    log_prefix = "extraction"

    def __init__(self, service: BrandExtractionService) -> None:
        """Initialize extraction orchestrator."""
        self.service = service

    def _get_wave_delay(self) -> float:
        """Read wave delay from the service's profile.

        Brand uses a profile-driven delay (fast vs slow models). The base
        default is ignored here.
        """
        return self.service.profile.wave_delay_seconds

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
                logger.exception("crawl_failed", error=str(e))
                return ""

        async def safe_crawl_styles() -> str:
            try:
                return await svc.crawler.crawl_content_with_styles(url)
            except Exception as e:
                logger.exception("crawl_styles_failed", error=str(e))
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
        emit_progress(progress_callback, 10, "Escaneando sitio web...")

        return crawled_content, enriched_visual_content

    def _log_extraction_summary(
        self,
        positioning: BrandPositioning,
        narrative: BrandNarrative,
        communication_assets: CommunicationAssets,
        extracted_visuals: BrandVisuals | None,
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
        user_id: UUID | None = None,
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
        want_visuals = include_visuals and has_url and bool(enriched_visual_content.strip())
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
        merge_t0 = time.time()
        if trace:
            trace.merge_start()

        # Waves persist their subset via ``_merge_and_save`` before announcing,
        # so ``result`` is already the final saved BrandSettings — no separate
        # post-wave save step is needed.
        extracted_visuals, positioning, narrative, communication_assets, result = await wave_fn(
            svc,
            content,
            current_data_str,
            update_instructions,
            enriched_visual_content,
            want_visuals,
            include_assets,
            progress_callback,
            trace,
            dry_run=dry_run,
        )

        if trace:
            trace.merge_end(time.time() - merge_t0)

        # Log extraction results summary
        succeeded = self._log_extraction_summary(
            positioning,
            narrative,
            communication_assets,
            extracted_visuals,
            include_assets,
            total_sections,
        )

        # Social-proof sync — mirror testimonials / authority / team into the
        # social_proof bounded context, which is what the Brand Studio UI reads
        # from. Legacy BrandSettings.{testimonials,authority_vault,team} are
        # already persisted by the wave saves above for backwards compatibility.
        if not dry_run and user_id is not None:
            self._sync_social_proof(
                tenant_id=svc.tenant_id,
                user_id=user_id,
                mode=mode,
                testimonials=self._last_testimonials.testimonials,
                authority_items=self._last_authority.authority_vault,
                team_members=self._last_people_contact.key_leadership,
            )
        elif not dry_run:
            logger.warning(
                "social_proof_sync_skipped_no_user_id",
                tenant_id=str(svc.tenant_id),
                hint="dispatch extraction with user_id so Brand Studio UI picks up the new items",
            )

        if trace:
            trace.finish(status="completed", sections_succeeded=succeeded)

        return result

    def _sync_social_proof(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        mode: str,
        testimonials: list[BrandTestimonial],
        authority_items: list[BrandAuthorityItem],
        team_members: list[KeyFigure],
    ) -> None:
        """Mirror extracted items into the social_proof bounded context.

        Uses the ``shared.links.ports.social_proof`` port to stay compliant
        with DDD boundaries (brand MUST NOT import social_proof directly).
        Swallows failures so a social_proof write issue doesn't abort the
        extraction — the legacy BrandSettings snapshot is the authoritative
        fallback until the legacy fields are removed.
        """
        from src.shared.links.ports.social_proof import (
            sync_authority_items_from_extraction,
            sync_team_members_from_extraction,
            sync_testimonials_from_extraction,
        )

        svc = self.service
        db = svc.db
        team_names = [m.name for m in (team_members or []) if getattr(m, "name", None)]
        try:
            t_count = sync_testimonials_from_extraction(
                db,
                tenant_id=tenant_id,
                user_id=user_id,
                mode=mode,
                items=[t.model_dump(mode="json") for t in testimonials],
                team_names=team_names,
            )
            a_count = sync_authority_items_from_extraction(
                db,
                tenant_id=tenant_id,
                user_id=user_id,
                mode=mode,
                items=[a.model_dump(mode="json") for a in authority_items],
            )
            m_count = sync_team_members_from_extraction(
                db,
                tenant_id=tenant_id,
                user_id=user_id,
                mode=mode,
                items=[m.model_dump(mode="json") for m in (team_members or [])],
            )
            db.commit()
            logger.info(
                "social_proof_sync_completed",
                tenant_id=str(tenant_id),
                testimonials_created=t_count,
                authority_items_created=a_count,
                team_members_created=m_count,
                mode=mode,
            )
        except Exception:
            logger.exception(
                "social_proof_sync_failed",
                tenant_id=str(tenant_id),
                mode=mode,
            )
            import contextlib

            with contextlib.suppress(Exception):
                db.rollback()

    # ------------------------------------------------------------------
    # Wave execution strategies
    # ------------------------------------------------------------------

    async def _extract_assets_if_requested(
        self,
        svc: BrandExtractionService,
        include_assets: bool,
        content: str,
        current_data_str: str,
        update_instructions: str | None,
        positioning: BrandPositioning,
        narrative: BrandNarrative,
        wave_num: int | None = None,
        trace: ExtractionTraceCollector | None = None,
    ) -> CommunicationAssets:
        """Extract communication assets if requested, otherwise return empty."""
        if not include_assets:
            return CommunicationAssets()

        if wave_num:
            await self._pause_between_waves(wave_num, trace)

        positioning_ctx = (
            json.dumps(positioning.model_dump(exclude_none=True), indent=2) if not is_empty(positioning) else ""
        )
        narrative_ctx = json.dumps(narrative.model_dump(exclude_none=True), indent=2) if not is_empty(narrative) else ""

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
        identity: BrandIdentity,
        story: BrandStory,
        strategy: BrandStrategy,
        people_contact: BrandPeopleContactExtraction,
        testimonials_data: BrandTestimonialsExtraction,
        authority_data: BrandAuthorityExtraction,
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
        *,
        dry_run: bool = False,
    ) -> tuple:
        """Execute extraction in multiple waves (for low-TPM models).

        Each wave persists its subset via ``_merge_and_save`` BEFORE
        ``_announce_sections`` publishes its section-completed events — so when
        a nav pill lands in the copilot conversation, the brand data it points
        at is already in the DB.  The cached ``last_saved`` threads wave-over-
        wave so only the first wave reads from the repository.
        """
        last_saved: BrandSettings | None = None

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

        wave1_results = await self._run_wave(1, wave1_sections, wave1_coros, trace)
        identity, story, testimonials_data = (
            wave1_results[0],
            wave1_results[1],
            wave1_results[2],
        )
        extracted_visuals = wave1_results[3] if len(wave1_results) > 3 else None

        last_saved = self._merge_and_save(
            identity=identity,
            story=story,
            testimonials=testimonials_data,
            visuals=extracted_visuals,
            dry_run=dry_run,
            current=last_saved,
        )

        # Aggregate progress — consumed by all callers (legacy REST + worker)
        emit_progress(progress_callback, 45, "Analizando identidad y narrativa...")
        # Per-section live progress — only emitted when the callback declares
        # ``new_fields``/``section_completed`` (or ``**kwargs``). Legacy 2-arg
        # callbacks never see these calls, guaranteeing byte-for-byte compat.
        self._announce_sections(
            progress_callback,
            wave1_sections,
            wave1_results,
            pct=45,
        )

        # Wave 2: strategy, people_contact, authority
        await self._pause_between_waves(1, trace)
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
            trace,
        )
        strategy, people_contact, authority_data = wave2_results
        wave2_section_names = ["strategy", "people_contact", "authority"]

        last_saved = self._merge_and_save(
            strategy=strategy,
            people_contact=people_contact,
            authority=authority_data,
            dry_run=dry_run,
            current=last_saved,
        )

        emit_progress(progress_callback, 65, "Extrayendo estrategia...")
        self._announce_sections(
            progress_callback,
            wave2_section_names,
            wave2_results,
            pct=65,
        )

        # Wave 3: positioning, narrative
        await self._pause_between_waves(2, trace)
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
            trace,
        )
        positioning, narrative = wave3_results
        wave3_section_names = ["positioning", "narrative"]

        last_saved = self._merge_and_save(
            positioning=positioning,
            narrative=narrative,
            dry_run=dry_run,
            current=last_saved,
        )

        emit_progress(progress_callback, 85, "Extrayendo posicionamiento y narrativa...")
        self._announce_sections(
            progress_callback,
            wave3_section_names,
            wave3_results,
            pct=85,
        )

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
        emit_progress(progress_callback, 95, "Finalizando extraccion...")
        if include_assets and communication_assets is not None:
            last_saved = self._merge_and_save(
                communication_assets=communication_assets,
                dry_run=dry_run,
                current=last_saved,
            )
            self._announce_sections(
                progress_callback,
                ["communication_assets"],
                [communication_assets],
                pct=95,
            )

        self._store_section_results(
            identity,
            story,
            strategy,
            people_contact,
            testimonials_data,
            authority_data,
        )
        return extracted_visuals, positioning, narrative, communication_assets, last_saved

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
        *,
        dry_run: bool = False,
    ) -> tuple:
        """Execute all extractions concurrently (for high-TPM models).

        Mirrors ``_run_multi_wave``'s save-before-announce invariant in a
        single merge: once every section has extracted, persist once, THEN
        announce.  The window between save and announce is tiny but still
        ordered correctly so nav pills never point at un-persisted data.
        """
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

        all_results = await self._run_wave(1, all_sections, coros, trace)
        identity, story, strategy, people_contact, testimonials_data, authority_data = all_results[:6]
        positioning, narrative = all_results[6], all_results[7]
        extracted_visuals = all_results[8] if len(all_results) > 8 else None

        last_saved = self._merge_and_save(
            identity=identity,
            story=story,
            strategy=strategy,
            people_contact=people_contact,
            testimonials=testimonials_data,
            authority=authority_data,
            positioning=positioning,
            narrative=narrative,
            visuals=extracted_visuals,
            dry_run=dry_run,
        )

        emit_progress(progress_callback, 80, "Extrayendo secciones...")
        # Announce all sections that ran in this single wave
        self._announce_sections(
            progress_callback,
            all_sections,
            list(all_results),
            pct=80,
        )

        communication_assets = await self._extract_assets_if_requested(
            svc,
            include_assets,
            content,
            current_data_str,
            update_instructions,
            positioning,
            narrative,
        )
        emit_progress(progress_callback, 95, "Finalizando extraccion...")
        if include_assets and communication_assets is not None:
            last_saved = self._merge_and_save(
                communication_assets=communication_assets,
                dry_run=dry_run,
                current=last_saved,
            )
            self._announce_sections(
                progress_callback,
                ["communication_assets"],
                [communication_assets],
                pct=95,
            )

        self._store_section_results(
            identity,
            story,
            strategy,
            people_contact,
            testimonials_data,
            authority_data,
        )
        return extracted_visuals, positioning, narrative, communication_assets, last_saved

    # ------------------------------------------------------------------
    # Merge & Save
    # ------------------------------------------------------------------

    def _merge_and_save(
        self,
        *,
        identity: BrandIdentity | None = None,
        story: BrandStory | None = None,
        strategy: BrandStrategy | None = None,
        people_contact: BrandPeopleContactExtraction | None = None,
        testimonials: BrandTestimonialsExtraction | None = None,
        authority: BrandAuthorityExtraction | None = None,
        visuals: BrandVisuals | None = None,
        positioning: BrandPositioning | None = None,
        narrative: BrandNarrative | None = None,
        communication_assets: CommunicationAssets | None = None,
        dry_run: bool = False,
        current: BrandSettings | None = None,
    ) -> BrandSettings:
        """Merge extracted sections into the current BrandSettings and persist.

        Invariant: callers invoke this once per wave BEFORE ``_announce_sections``
        emits a section-completed event, so any nav pill the subscriber inserts
        into the copilot conversation points at data that is already persisted.

        All section args are optional so the same function covers:
          - per-wave saves (subset of sections produced by one wave)
          - the single-wave path (every section in one call)

        ``current`` is the starting BrandSettings — pass the previous wave's
        return value to avoid a redundant ``get_settings`` round-trip between
        waves. When omitted the current state is read from the repository.

        ``dry_run`` computes the merge but skips persistence.
        """
        svc = self.service
        if current is None:
            current = svc.repository.get_settings(svc.tenant_id)

        merged = current.model_copy(
            update={
                "identity": BrandIdentity(**_merge_simple_model(current.identity, identity)),
                "story": BrandStory(
                    **(
                        _merge_story(current.story, story)
                        if story is not None
                        else (current.story.model_dump() if current.story else {})
                    ),
                ),
                "strategy": BrandStrategy(
                    **(
                        _merge_strategy(current.strategy, strategy)
                        if strategy is not None
                        else (current.strategy.model_dump() if current.strategy else {})
                    ),
                ),
                "team": (_merge_people(current.team, people_contact) if people_contact is not None else current.team),
                "contact": (
                    _merge_contact(current.contact, people_contact.contact)
                    if people_contact is not None
                    else current.contact
                ),
                "testimonials": (
                    testimonials.testimonials or (current.testimonials or [])
                    if testimonials is not None
                    else (current.testimonials or [])
                ),
                "authority_vault": (
                    authority.authority_vault or (current.authority_vault or [])
                    if authority is not None
                    else (current.authority_vault or [])
                ),
                "visuals": BrandVisuals(**_merge_simple_model(current.visuals, visuals)),
                "positioning": _merge_positioning(current.positioning, positioning),
                "narrative": _merge_narrative(current.narrative, narrative),
                "communication_assets": _merge_communication_assets(
                    current.communication_assets,
                    communication_assets,
                ),
            },
        )

        if dry_run:
            logger.info("dry_run_merge_completed", tenant_id=str(svc.tenant_id))
            return merged

        saved = svc.repository.save_settings(svc.tenant_id, merged)
        logger.info(
            "brand_settings_saved",
            tenant_id=str(svc.tenant_id),
            summary=summarize_settings(saved),
        )
        return saved
