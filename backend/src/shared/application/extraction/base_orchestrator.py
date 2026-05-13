"""Base class for wave-based LLM extraction orchestrators.

Shared helpers used by :class:`ExtractionOrchestrator` (brand),
:class:`OfferExtractionOrchestrator` (offer), and future modules
(buyer_persona, landing, etc.). Only the genuinely duplicated mechanics
live here; wave composition and merge-and-save stay in subclasses
because the entities and wave layouts differ per domain.

Shared behaviour:
- ``_run_wave``        — execute one wave of concurrent coros + trace log
- ``_pause_between_waves`` — sleep to let TPM budget recover
- ``_announce_sections``   — per-section progress emission (rich callbacks)
- ``_get_wave_delay``  — hook; override for profile-driven delays

Subclasses implement their own ``run`` entry point, their own wave
composition (``_run_multi_wave`` / ``_run_single_wave``), and their own
``_merge_and_save`` that persists domain entities.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

import structlog
from luana_core_platform.application.progress_emitter import (
    emit_progress,
    fields_from_model,
    supports_rich_progress,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

logger = structlog.get_logger()


@runtime_checkable
class _TraceCollector(Protocol):
    """Duck-typed trace collector: brand + offer both implement these two methods."""

    def wave_start(self, wave_num: int, sections: list[str]) -> None: ...

    def wave_pause(self, wave_num: int, delay: float) -> None: ...


class BaseExtractionOrchestrator:
    """Shared wave scheduling + progress emission for extraction orchestrators.

    Subclasses drive the extraction from their own ``run(...)`` entry point
    and compose the waves. The base class only contributes the cross-module
    mechanics that were verbatim-duplicated before this abstraction existed.
    """

    # Default wave pause. Brand overrides via ``_get_wave_delay`` to read
    # ``svc.profile.wave_delay_seconds``. Offer keeps the constant.
    default_wave_delay_seconds: float = 1.0

    # Structlog event prefix — lets subclasses keep their pre-existing
    # log event names (``extraction_wave_starting`` for brand,
    # ``offer_extraction_wave_starting`` for offer) without rewriting
    # dashboards or alerts tied to them.
    log_prefix: str = "extraction"

    def _get_wave_delay(self) -> float:
        """Return the seconds to sleep between waves.

        Override in subclasses that read the delay from a profile. Default
        returns ``default_wave_delay_seconds``.
        """
        return self.default_wave_delay_seconds

    async def _run_wave(
        self,
        wave_num: int,
        sections: list[str],
        coros: list[Awaitable[Any]],
        trace: _TraceCollector | None = None,
    ) -> list[Any]:
        """Execute a wave of concurrent extractions with logging + trace.

        ``trace`` is duck-typed via :class:`_TraceCollector`: brand and offer
        collectors both implement ``wave_start`` and ``wave_pause`` with this
        signature, so the base class can stay generic across domains.
        """
        event = f"{self.log_prefix}_wave_starting"
        logger.info(event, wave=wave_num, sections=sections)
        if trace is not None:
            trace.wave_start(wave_num, sections)
        return await asyncio.gather(*coros)

    async def _pause_between_waves(
        self,
        wave_num: int,
        trace: _TraceCollector | None = None,
    ) -> None:
        """Sleep between waves, recording the pause in ``trace`` if provided."""
        delay = self._get_wave_delay()
        event = f"{self.log_prefix}_wave_pause"
        logger.info(event, delay=delay)
        if trace is not None:
            trace.wave_pause(wave_num, delay)
        await asyncio.sleep(delay)

    def _announce_sections(
        self,
        progress_callback: Callable[..., None] | None,
        sections: list[str],
        results: list[Any],
        *,
        pct: int,
    ) -> None:
        """Emit per-section progress for callbacks that support rich kwargs.

        Legacy 2-arg callbacks (REST endpoints) are filtered out by
        ``supports_rich_progress``. Sections whose result dumps to zero
        filled leaves are silently skipped so the UI doesn't flash false
        completion badges.
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
