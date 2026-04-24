"""Offer extraction orchestrator — wave-based LLM section coordination.

Coordinates the multi-section extraction pipeline for offers: schedules
waves of concurrent LLM calls, tracks progress, and persists results into
the Offer entity via OfferService.patch_offer after each wave.

Invariant: ``_merge_and_save`` persists BEFORE ``_announce_sections`` emits
section-completed events. This guarantees that any copilot nav pill pointing
at a section arrives after the data is already in the database.

Wave assignments are 1:1 with the extractors in ``OfferExtractionService``.
Each slug maps to a real extractor — no aliases, no double-calls. Previous
layouts that reused extractors under virtual slugs (``identity``/``pricing``
/``classification``) wasted LLM budget and emitted nav pills whose payload
didn't match the slug.

  - W1: promise, strategy
  - W2: psychology, value_stack, closing, pricing
  - W3: details
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import TYPE_CHECKING, Literal

import structlog
from pydantic import ValidationError

from src.modules.offer.application.offer_service import OfferService
from src.shared.application.extraction.base_orchestrator import (
    BaseExtractionOrchestrator,
)
from src.shared.application.progress_emitter import emit_progress

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

# Offer waves — each slug maps 1:1 to a real extractor on OfferExtractionService.
_WAVE1_SECTIONS = ["promise", "strategy"]
_WAVE2_SECTIONS = ["psychology", "value_stack", "closing", "pricing"]
_WAVE3_SECTIONS = ["details"]
_TOTAL_SECTIONS = len(_WAVE1_SECTIONS) + len(_WAVE2_SECTIONS) + len(_WAVE3_SECTIONS)


class OfferExtractionOrchestrator(BaseExtractionOrchestrator):
    """Coordinates wave-based LLM extraction and persists results into Offer.

    Receives a reference to the OfferExtractionService for individual section
    extraction methods. This class owns the scheduling (waves, pauses, progress)
    and the merge-and-save step. Wave + progress mechanics come from
    :class:`BaseExtractionOrchestrator`.
    """

    log_prefix = "offer_extraction"

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

        if trace:
            trace.set_content_length(len(content))
            trace.set_sections_total(_TOTAL_SECTIONS)

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

        sections_succeeded = await self._run_multi_wave(
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
            trace.finish(status="completed", sections_succeeded=sections_succeeded)

        emit_progress(progress_callback, 100, "¡Análisis de oferta completado!")
        logger.info(
            "offer_extraction_complete",
            tenant_id=str(svc.tenant_id),
            offer_id=str(svc.offer_id),
        )

    # ------------------------------------------------------------------
    # Wave execution strategies
    # ------------------------------------------------------------------

    @staticmethod
    def _count_succeeded(results: list) -> int:
        """Count wave results that aren't None or exceptions."""
        return sum(1 for r in results if r is not None and not isinstance(r, BaseException))

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
    ) -> int:
        """Execute extraction in three waves, 1:1 with real extractors.

        Each wave persists its subset via ``_merge_and_save`` BEFORE
        ``_announce_sections`` publishes its section-completed events — so when
        a nav pill lands in the copilot conversation, the offer data it points
        at is already in the DB.

        Returns the number of sections that completed successfully (non-None,
        non-exception) across all waves, so the caller can record it on the
        trace finish row.
        """
        succeeded = 0

        # Wave 1: promise + strategy (identity fields live inside promise).
        wave1_results = await self._run_wave(
            1,
            _WAVE1_SECTIONS,
            [
                svc._extract_promise(content, current_data_str, update_instructions, archetype),
                svc._extract_strategy(content, current_data_str, update_instructions, archetype),
            ],
            trace,
        )
        succeeded += self._count_succeeded(wave1_results)

        self._merge_and_save(
            svc=svc,
            results=wave1_results,
            wave_num=1,
            dry_run=dry_run,
        )

        emit_progress(progress_callback, 40, "Analizando promesa y estrategia...")
        self._announce_sections(progress_callback, _WAVE1_SECTIONS, wave1_results, pct=40)

        # Wave 2: psychology, value_stack, closing, pricing (Fase 01 pilot).
        await self._pause_between_waves(1, trace)
        wave2_results = await self._run_wave(
            2,
            _WAVE2_SECTIONS,
            [
                svc._extract_psychology(content, current_data_str, update_instructions, archetype),
                svc._extract_value_stack(content, current_data_str, update_instructions, archetype),
                svc._extract_closing(content, current_data_str, update_instructions, archetype),
                svc._extract_pricing(content, current_data_str, update_instructions, archetype),
            ],
            trace,
        )
        succeeded += self._count_succeeded(wave2_results)

        self._merge_and_save(
            svc=svc,
            results=wave2_results,
            wave_num=2,
            dry_run=dry_run,
        )

        emit_progress(progress_callback, 65, "Analizando psicología, stack de valor y cierre...")
        self._announce_sections(progress_callback, _WAVE2_SECTIONS, wave2_results, pct=65)

        # Wave 3: details (fulfillment, access, onboarding).
        await self._pause_between_waves(2, trace)
        wave3_results = await self._run_wave(
            3,
            _WAVE3_SECTIONS,
            [
                svc._extract_details(content, current_data_str, update_instructions, archetype),
            ],
            trace,
        )
        succeeded += self._count_succeeded(wave3_results)

        self._merge_and_save(
            svc=svc,
            results=wave3_results,
            wave_num=3,
            dry_run=dry_run,
        )

        emit_progress(progress_callback, 85, "Analizando detalles de entrega...")
        self._announce_sections(progress_callback, _WAVE3_SECTIONS, wave3_results, pct=85)

        return succeeded

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
    ) -> int:
        """Execute all extractions concurrently (for high-TPM models).

        Save-before-announce invariant holds here too: persist once after all
        sections complete, THEN announce. 1:1 slug-to-extractor alignment
        mirrors ``_run_multi_wave``.

        Returns the number of sections that completed successfully.
        """
        all_sections = [
            "promise",
            "strategy",
            "psychology",
            "value_stack",
            "closing",
            "pricing",
            "details",
        ]
        all_coros = [
            svc._extract_promise(content, current_data_str, update_instructions, archetype),
            svc._extract_strategy(content, current_data_str, update_instructions, archetype),
            svc._extract_psychology(content, current_data_str, update_instructions, archetype),
            svc._extract_value_stack(content, current_data_str, update_instructions, archetype),
            svc._extract_closing(content, current_data_str, update_instructions, archetype),
            svc._extract_pricing(content, current_data_str, update_instructions, archetype),
            svc._extract_details(content, current_data_str, update_instructions, archetype),
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
        return self._count_succeeded(all_results)

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
            except (AttributeError, TypeError, ValidationError) as e:
                # AttributeError  — result lacks model_dump (unexpected shape)
                # TypeError       — unexpected arg pattern from a subclass
                # ValidationError — pydantic reports malformed payload
                # Broad Exception was hiding real bugs (e.g. AttributeError on
                # a test double). Keep the net narrow so transient LLM/IO
                # errors surface upstream where asyncio.gather already handles
                # them as BaseException results.
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
