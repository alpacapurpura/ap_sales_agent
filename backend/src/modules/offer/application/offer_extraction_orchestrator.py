"""Offer extraction orchestrator — wave-based LLM section coordination.

Coordinates the multi-section extraction pipeline for offers: schedules
waves of concurrent LLM calls, tracks progress, and persists results into
the Offer entity via OfferService.patch_offer after each wave.

Invariant: ``_merge_and_save`` persists BEFORE ``_announce_sections`` emits
section-completed events. This guarantees that any copilot nav pill pointing
at a section arrives after the data is already in the database.

Wave assignments (based on copilot_editable_fields.py catalog):
  - W1: identity, promise, strategy
  - W2: psychology, value_stack, pricing
  - W3: closing_system, onboarding, classification
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import TYPE_CHECKING, Literal

import structlog

from src.modules.offer.application.offer_service import OfferService
from src.shared.application.progress_emitter import (
    emit_progress,
    fields_from_model,
    supports_rich_progress,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from uuid import UUID

    from src.modules.offer.application.offer_extraction_service import (
        OfferExtractionService,
    )
    from src.modules.offer.application.offer_extraction_trace import (
        OfferExtractionTraceCollector,
    )

logger = structlog.get_logger()

# Seconds to wait between waves to let TPM budget recover.
_WAVE_DELAY_SECONDS: float = 1.0

# Offer waves — section slugs used for announce and logging.
_WAVE1_SECTIONS = ["identity", "promise", "strategy"]
_WAVE2_SECTIONS = ["psychology", "value_stack", "pricing"]
_WAVE3_SECTIONS = ["closing_system", "onboarding", "classification"]


class OfferExtractionOrchestrator:
    """Coordinates wave-based LLM extraction and persists results into Offer.

    Receives a reference to the OfferExtractionService for individual section
    extraction methods. This class owns the scheduling (waves, pauses, progress)
    and the merge-and-save step.
    """

    def __init__(self, service: OfferExtractionService) -> None:
        """Initialize offer extraction orchestrator."""
        self.service = service
        self._offer_service: OfferService | None = None  # lazy init inside run()

    async def run(
        self,
        url: str | None = None,
        text: str | None = None,
        mode: Literal["initial", "update"] = "initial",
        update_instructions: str | None = None,
        progress_callback: Callable[..., None] | None = None,
        trace: OfferExtractionTraceCollector | None = None,
        user_id: UUID | None = None,
    ) -> None:
        """Orchestrate the full offer extraction process.

        Args:
            url: Optional URL to crawl for content.
            text: Optional pre-supplied text (combined with crawled content).
            mode: "initial" (first extraction) or "update" (merge over existing).
            update_instructions: Free-text instructions for update mode.
            progress_callback: Optional callback(pct, stage, *, new_fields, section_completed).
            trace: Optional trace collector for observability.
            user_id: The user triggering the extraction (for future social-proof sync).

        Returns:
            None — results are persisted in the database via OfferService.patch_offer.
        """
        svc = self.service
        self._offer_service = OfferService(svc.db)

        # 1. Gather content
        emit_progress(progress_callback, 10, "Recopilando contenido...")
        content = text or ""

        if url:
            logger.info("offer_extraction_crawl_start", url=url)
            if trace:
                trace.crawl_start(url)
            t0 = time.time()
            try:
                from src.shared.infrastructure.web.crawler import WebCrawler

                crawler = WebCrawler()
                crawled = await crawler.crawl_content(url)
                if crawled:
                    content = f"{content}\n\n{crawled}" if content else crawled
            except Exception as e:
                logger.exception("offer_extraction_crawl_failed", error=str(e))
            crawl_dur = time.time() - t0
            if trace:
                trace.crawl_end(crawl_dur, content_len=len(content))

        if not content.strip() and not update_instructions:
            logger.warning(
                "offer_extraction_no_content",
                tenant_id=str(svc.tenant_id),
                offer_id=str(svc.offer_id),
            )
            return

        # 2. Load current offer data
        emit_progress(progress_callback, 15, "Cargando datos actuales de la oferta...")
        offer = self._offer_service.get_offer(svc.offer_id, svc.tenant_id)
        archetype: str | None = None
        current_data_str = "None"

        if offer:
            archetype = offer.archetype.value if offer.archetype else None
            current_data_str = json.dumps(
                offer.model_dump(mode="json", exclude_none=True),
                ensure_ascii=False,
                default=str,
            )

        instructions = update_instructions if mode == "update" else None

        total_sections = 9  # 3 per wave x 3 waves
        if trace:
            trace.set_content_length(len(content))
            trace.set_sections_total(total_sections)

        logger.info(
            "offer_extraction_starting",
            tenant_id=str(svc.tenant_id),
            offer_id=str(svc.offer_id),
            content_length=len(content),
            mode=mode,
        )

        if trace:
            trace.merge_start()
        merge_t0 = time.time()

        await self._run_multi_wave(
            svc=svc,
            content=content,
            current_data_str=current_data_str,
            update_instructions=instructions,
            archetype=archetype,
            progress_callback=progress_callback,
            trace=trace,
        )

        if trace:
            trace.merge_end(time.time() - merge_t0)
            trace.finish(status="completed", sections_succeeded=total_sections)

        emit_progress(progress_callback, 100, "¡Análisis de oferta completado!")
        logger.info(
            "offer_extraction_complete",
            tenant_id=str(svc.tenant_id),
            offer_id=str(svc.offer_id),
        )

    # ------------------------------------------------------------------
    # Wave execution strategies
    # ------------------------------------------------------------------

    def _announce_sections(
        self,
        progress_callback: Callable[..., None] | None,
        sections: list[str],
        results: list,
        *,
        pct: int,
    ) -> None:
        """Emit per-section progress for callbacks that support the rich signature.

        Legacy 2-arg callbacks (REST endpoints) never see these calls.
        Each (section, result) pair is published via ``section_completed`` +
        ``new_fields``. Empty sections (failed extractions) are silently
        skipped so the UI doesn't flash false badges.
        """
        if not supports_rich_progress(progress_callback):
            return
        for section_slug, result in zip(sections, results, strict=False):
            fields = fields_from_model(section_slug, result)
            if not fields:
                continue
            emit_progress(
                progress_callback,
                pct,
                f"Sección {section_slug} lista",
                new_fields=fields,
                section_completed=section_slug,
            )

    async def _run_wave(
        self,
        wave_num: int,
        sections: list[str],
        coros: list,
        trace: OfferExtractionTraceCollector | None,
    ) -> list:
        """Execute a single wave of concurrent extractions with logging."""
        logger.info("offer_extraction_wave_starting", wave=wave_num, sections=sections)
        if trace:
            trace.wave_start(wave_num, sections)
        return await asyncio.gather(*coros)

    async def _pause_between_waves(
        self,
        wave_num: int,
        trace: OfferExtractionTraceCollector | None,
    ) -> None:
        """Pause between waves to let TPM budget recover."""
        logger.info("offer_extraction_wave_pause", delay=_WAVE_DELAY_SECONDS)
        if trace:
            trace.wave_pause(wave_num, _WAVE_DELAY_SECONDS)
        await asyncio.sleep(_WAVE_DELAY_SECONDS)

    async def _run_multi_wave(
        self,
        svc: OfferExtractionService,
        content: str,
        current_data_str: str,
        update_instructions: str | None,
        archetype: str | None = None,
        progress_callback: Callable[..., None] | None = None,
        trace: OfferExtractionTraceCollector | None = None,
        *,
        dry_run: bool = False,
    ) -> None:
        """Execute extraction in multiple waves.

        Each wave persists its subset via ``_merge_and_save`` BEFORE
        ``_announce_sections`` publishes its section-completed events — so when
        a nav pill lands in the copilot conversation, the offer data it points
        at is already in the DB.
        """
        # Wave 1: identity (promise fields), promise, strategy
        wave1_results = await self._run_wave(
            1,
            _WAVE1_SECTIONS,
            [
                svc._extract_promise(content, current_data_str, update_instructions, archetype),
                svc._extract_strategy(content, current_data_str, update_instructions, archetype),
                # identity fields overlap with promise in offer (headline_promise,
                # primary_outcome, time_to_value) — promise extractor covers them.
                svc._extract_promise(content, current_data_str, update_instructions, archetype),
            ],
            trace,
        )
        # Use unique results: promise (index 0) covers both "identity" and "promise" sections.
        # strategy is index 1.
        promise_result = wave1_results[0]
        strategy_result = wave1_results[1]

        self._merge_and_save(
            svc=svc,
            results=[promise_result, strategy_result],
            wave_num=1,
            dry_run=dry_run,
        )

        emit_progress(progress_callback, 40, "Analizando identidad, promesa y estrategia...")
        self._announce_sections(
            progress_callback,
            ["identity", "promise", "strategy"],
            [promise_result, promise_result, strategy_result],
            pct=40,
        )

        # Wave 2: psychology, value_stack, pricing
        await self._pause_between_waves(1, trace)
        wave2_results = await self._run_wave(
            2,
            _WAVE2_SECTIONS,
            [
                svc._extract_psychology(content, current_data_str, update_instructions, archetype),
                svc._extract_value_stack(content, current_data_str, update_instructions, archetype),
                svc._extract_closing(content, current_data_str, update_instructions, archetype),
            ],
            trace,
        )
        psychology_result = wave2_results[0]
        value_stack_result = wave2_results[1]
        pricing_result = wave2_results[2]

        self._merge_and_save(
            svc=svc,
            results=[psychology_result, value_stack_result, pricing_result],
            wave_num=2,
            dry_run=dry_run,
        )

        emit_progress(progress_callback, 65, "Analizando psicología, stack de valor y precios...")
        self._announce_sections(
            progress_callback,
            _WAVE2_SECTIONS,
            [psychology_result, value_stack_result, pricing_result],
            pct=65,
        )

        # Wave 3: closing_system, onboarding, classification
        await self._pause_between_waves(2, trace)
        wave3_results = await self._run_wave(
            3,
            _WAVE3_SECTIONS,
            [
                svc._extract_closing(content, current_data_str, update_instructions, archetype),
                svc._extract_details(content, current_data_str, update_instructions, archetype),
                svc._extract_strategy(content, current_data_str, update_instructions, archetype),
            ],
            trace,
        )
        closing_result = wave3_results[0]
        details_result = wave3_results[1]
        classification_result = wave3_results[2]

        self._merge_and_save(
            svc=svc,
            results=[closing_result, details_result, classification_result],
            wave_num=3,
            dry_run=dry_run,
        )

        emit_progress(progress_callback, 85, "Analizando cierre, onboarding y clasificación...")
        self._announce_sections(
            progress_callback,
            _WAVE3_SECTIONS,
            [closing_result, details_result, classification_result],
            pct=85,
        )

    async def _run_single_wave(
        self,
        svc: OfferExtractionService,
        content: str,
        current_data_str: str,
        update_instructions: str | None,
        archetype: str | None = None,
        progress_callback: Callable[..., None] | None = None,
        trace: OfferExtractionTraceCollector | None = None,
        *,
        dry_run: bool = False,
    ) -> None:
        """Execute all extractions concurrently (for high-TPM models).

        Save-before-announce invariant holds here too: persist once after all
        sections complete, THEN announce.
        """
        all_sections = [
            "identity",
            "promise",
            "strategy",
            "psychology",
            "value_stack",
            "pricing",
            "closing_system",
            "onboarding",
            "classification",
        ]
        all_coros = [
            svc._extract_promise(content, current_data_str, update_instructions, archetype),
            svc._extract_promise(content, current_data_str, update_instructions, archetype),
            svc._extract_strategy(content, current_data_str, update_instructions, archetype),
            svc._extract_psychology(content, current_data_str, update_instructions, archetype),
            svc._extract_value_stack(content, current_data_str, update_instructions, archetype),
            svc._extract_closing(content, current_data_str, update_instructions, archetype),
            svc._extract_closing(content, current_data_str, update_instructions, archetype),
            svc._extract_details(content, current_data_str, update_instructions, archetype),
            svc._extract_strategy(content, current_data_str, update_instructions, archetype),
        ]

        if trace:
            trace.wave_start(1, all_sections)

        all_results = list(await asyncio.gather(*all_coros))

        # Persist all at once before announcing
        self._merge_and_save(
            svc=svc,
            results=all_results,
            wave_num=1,
            dry_run=dry_run,
        )

        emit_progress(progress_callback, 80, "Extrayendo secciones de la oferta...")
        self._announce_sections(
            progress_callback,
            all_sections,
            all_results,
            pct=80,
        )

    # ------------------------------------------------------------------
    # Merge & Save
    # ------------------------------------------------------------------

    def _merge_and_save(
        self,
        *,
        svc: OfferExtractionService,
        results: list,
        wave_num: int,
        dry_run: bool = False,
    ) -> None:
        """Merge extracted sections into the offer and persist via patch_offer.

        Invariant: called once per wave BEFORE ``_announce_sections`` emits any
        section-completed event, so any nav pill points at already-persisted data.

        All exceptions are swallowed per-result so partial wave failures don't
        abort the entire extraction — the same resilience pattern as the original
        ``extract_all`` which used ``return_exceptions=True`` in asyncio.gather.
        """
        if dry_run:
            logger.info(
                "offer_extraction_dry_run_wave",
                wave=wave_num,
                tenant_id=str(svc.tenant_id),
            )
            return

        if self._offer_service is None:
            self._offer_service = OfferService(svc.db)

        merged: dict = {}
        for result in results:
            if isinstance(result, BaseException):
                logger.error(
                    "offer_extraction_wave_section_exception",
                    wave=wave_num,
                    error=str(result),
                )
                continue
            if result is None:
                continue
            try:
                merged.update(result.model_dump(exclude_unset=True, exclude_none=True))
            except Exception as e:
                logger.exception(
                    "offer_extraction_merge_section_failed",
                    wave=wave_num,
                    error=str(e),
                )

        if not merged:
            logger.info(
                "offer_extraction_wave_empty",
                wave=wave_num,
                tenant_id=str(svc.tenant_id),
            )
            return

        try:
            self._offer_service.patch_offer(svc.offer_id, svc.tenant_id, merged)
            logger.info(
                "offer_extraction_wave_saved",
                wave=wave_num,
                tenant_id=str(svc.tenant_id),
                offer_id=str(svc.offer_id),
                fields=list(merged.keys()),
            )
        except Exception as e:
            logger.exception(
                "offer_extraction_wave_save_failed",
                wave=wave_num,
                tenant_id=str(svc.tenant_id),
                offer_id=str(svc.offer_id),
                error=str(e),
            )
