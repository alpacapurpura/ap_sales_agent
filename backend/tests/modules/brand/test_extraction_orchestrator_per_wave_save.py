"""Regression tests — per-wave save BEFORE announce.

Invariant tested:
  Given wave 1 produced identity + story + testimonials,
  when ``_announce_sections`` emits those events (pct=45),
  then ``repository.save_settings`` has already been called with a
  BrandSettings that includes the identity data — i.e. the save happened
  BEFORE the announce.

Why this matters: the copilot extraction_section_completed subscriber inserts
a nav pill into the conversation the moment an announce fires. If save comes
after announce, the pill points at un-persisted data and the user sees an
empty section when they click the pill mid-extraction.

Covers both wave strategies:
  - ``_run_multi_wave`` (low-TPM profiles) — per-wave saves thread the
    previous wave's result via ``current`` to avoid redundant repo reads.
  - ``_run_single_wave`` (high-TPM profiles) — one save before announce.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from src.modules.brand.application.extraction_orchestrator import (
    BrandAuthorityExtraction,
    BrandPeopleContactExtraction,
    BrandTestimonialsExtraction,
    ExtractionOrchestrator,
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

TENANT_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_svc_mock(
    save_calls: list,
    current_settings: BrandSettings | None = None,
) -> MagicMock:
    """Build a minimal BrandExtractionService mock that tracks save calls."""
    svc = MagicMock()
    svc.tenant_id = TENANT_ID

    # Profile: 3 waves (safe), tiny delay
    profile = MagicMock()
    profile.concurrency_waves = 3
    profile.wave_delay_seconds = 0
    svc.profile = profile

    # Repository
    repo = MagicMock()
    repo.get_settings.return_value = current_settings or BrandSettings()

    def _record_save(tenant_id: UUID, settings: BrandSettings) -> BrandSettings:
        save_calls.append(settings)
        return settings

    repo.save_settings.side_effect = _record_save
    svc.repository = repo

    # LLM extractors — return plausible objects
    svc._extract_identity = AsyncMock(return_value=BrandIdentity(brand_name="TestBrand", tagline="Test tagline"))
    svc._extract_story = AsyncMock(return_value=BrandStory(origin_story="Founded in garage"))
    svc._extract_testimonials = AsyncMock(return_value=BrandTestimonialsExtraction())
    svc._extract_visuals = AsyncMock(return_value=BrandVisuals())
    svc._extract_strategy = AsyncMock(return_value=BrandStrategy())
    svc._extract_people_contact = AsyncMock(return_value=BrandPeopleContactExtraction())
    svc._extract_authority = AsyncMock(return_value=BrandAuthorityExtraction())
    svc._extract_positioning = AsyncMock(return_value=BrandPositioning())
    svc._extract_narrative = AsyncMock(return_value=BrandNarrative())
    svc._extract_communication_assets = AsyncMock(return_value=CommunicationAssets())

    return svc


def _rich_callback(
    pct: int,
    stage: str,
    *,
    new_fields: list | None = None,
    section_completed: str | None = None,
) -> None:
    """Rich-progress callback that accepts section_completed / new_fields."""


class TestPerWaveSaveBeforeAnnounce:
    """Core invariant: save happens before section_completed event emission."""

    @pytest.mark.asyncio
    async def test_save_called_before_announce_wave1(self) -> None:
        """After wave 1, save_settings must be called before _announce_sections."""
        save_calls: list[BrandSettings] = []
        announce_calls: list[str] = []

        svc = _make_svc_mock(save_calls)
        orchestrator = ExtractionOrchestrator(svc)

        # Patch _announce_sections to record when it's called
        original_announce = orchestrator._announce_sections

        def patched_announce(progress_callback: Any, sections: list, results: list, *, pct: int) -> None:
            announce_calls.append(f"announce_pct_{pct}")
            original_announce(progress_callback, sections, results, pct=pct)

        orchestrator._announce_sections = patched_announce  # type: ignore[method-assign]

        await orchestrator._run_multi_wave(
            svc=svc,
            content="test content",
            current_data_str="",
            update_instructions=None,
            enriched_visual_content="",
            want_visuals=False,
            include_assets=False,
            progress_callback=_rich_callback,
            trace=None,
        )

        # save_settings should have been called AT LEAST once per wave (3 waves)
        assert len(save_calls) >= 3, f"Expected at least 3 per-wave saves, got {len(save_calls)}"

        # After wave 1 (pct=45), check identity data was in the first save
        first_save = save_calls[0]
        assert first_save.identity is not None, "First per-wave save must include identity section from wave 1"
        assert first_save.identity.brand_name == "TestBrand", (
            "First per-wave save must have identity.brand_name from wave 1 extraction"
        )

    @pytest.mark.asyncio
    async def test_wave1_save_contains_story_data(self) -> None:
        """Wave 1 save must include story data extracted in that wave."""
        save_calls: list[BrandSettings] = []
        svc = _make_svc_mock(save_calls)
        orchestrator = ExtractionOrchestrator(svc)

        await orchestrator._run_multi_wave(
            svc=svc,
            content="test",
            current_data_str="",
            update_instructions=None,
            enriched_visual_content="",
            want_visuals=False,
            include_assets=False,
            progress_callback=_rich_callback,
            trace=None,
        )

        first_save = save_calls[0]
        assert first_save.story is not None, "First save must include story from wave 1"
        assert first_save.story.origin_story == "Founded in garage"

    @pytest.mark.asyncio
    async def test_wave2_save_contains_strategy_data(self) -> None:
        """Wave 2 save must include strategy data extracted in that wave."""
        save_calls: list[BrandSettings] = []
        svc = _make_svc_mock(save_calls)
        # Wave 2 extracts strategy — give it a meaningful value
        svc._extract_strategy = AsyncMock(return_value=BrandStrategy(methodology_name="The TestMethod"))
        orchestrator = ExtractionOrchestrator(svc)

        await orchestrator._run_multi_wave(
            svc=svc,
            content="test",
            current_data_str="",
            update_instructions=None,
            enriched_visual_content="",
            want_visuals=False,
            include_assets=False,
            progress_callback=_rich_callback,
            trace=None,
        )

        # Second save should include strategy
        assert len(save_calls) >= 2, "Should have at least 2 per-wave saves"
        second_save = save_calls[1]
        assert second_save.strategy is not None, "Second save must include strategy from wave 2"
        assert second_save.strategy.methodology_name == "The TestMethod"

    @pytest.mark.asyncio
    async def test_legacy_callback_still_saves_per_wave(self) -> None:
        """Per-wave saves happen regardless of callback type."""
        save_calls: list[BrandSettings] = []
        svc = _make_svc_mock(save_calls)
        orchestrator = ExtractionOrchestrator(svc)

        # Legacy 2-arg callback — does NOT accept new_fields/section_completed
        def legacy_callback(pct: int, stage: str) -> None:
            pass

        await orchestrator._run_multi_wave(
            svc=svc,
            content="test",
            current_data_str="",
            update_instructions=None,
            enriched_visual_content="",
            want_visuals=False,
            include_assets=False,
            progress_callback=legacy_callback,
            trace=None,
        )

        # Per-wave saves happen unconditionally (not gated on callback type)
        assert len(save_calls) >= 3, "Per-wave saves must happen even with legacy callback"

    @pytest.mark.asyncio
    async def test_dry_run_does_not_save(self) -> None:
        """In dry_run mode, save_settings must never be called."""
        save_calls: list[BrandSettings] = []
        svc = _make_svc_mock(save_calls)
        svc.db = MagicMock()
        orchestrator = ExtractionOrchestrator(svc)

        with patch.object(orchestrator, "_crawl_content", AsyncMock(return_value=("content", ""))):
            await orchestrator.run(
                url=None,
                text="test content",
                dry_run=True,
                progress_callback=_rich_callback,
            )

        # dry_run → zero saves
        assert len(save_calls) == 0, f"dry_run=True must not call save_settings, but got {len(save_calls)} calls"


class TestSaveOrderInvariant:
    """Verify save-before-announce ordering at a logical level."""

    @pytest.mark.asyncio
    async def test_save_before_announce_ordering_tracked(self) -> None:
        """Track that save always precedes announce for each wave."""
        execution_order: list[str] = []
        save_calls: list[BrandSettings] = []
        svc = _make_svc_mock(save_calls)

        # Patch repository to track order
        def recording_save(tenant_id: UUID, settings: BrandSettings) -> BrandSettings:
            execution_order.append("save")
            save_calls.append(settings)
            return settings

        svc.repository.save_settings.side_effect = recording_save

        orchestrator = ExtractionOrchestrator(svc)
        original_announce = orchestrator._announce_sections

        def recording_announce(callback: Any, sections: list, results: list, *, pct: int) -> None:
            execution_order.append(f"announce_{pct}")
            original_announce(callback, sections, results, pct=pct)

        orchestrator._announce_sections = recording_announce  # type: ignore[method-assign]

        await orchestrator._run_multi_wave(
            svc=svc,
            content="test",
            current_data_str="",
            update_instructions=None,
            enriched_visual_content="",
            want_visuals=False,
            include_assets=False,
            progress_callback=_rich_callback,
            trace=None,
        )

        # Verify: every announce is preceded by a save
        assert "save" in execution_order, "save must appear in execution_order"
        assert any("announce" in item for item in execution_order), "announce must appear"

        # For each announce, there must be a save BEFORE it
        for i, item in enumerate(execution_order):
            if "announce" in item:
                preceding = execution_order[:i]
                assert "save" in preceding, (
                    f"announce at position {i} ({item!r}) has no preceding save. Full order: {execution_order}"
                )


class TestSingleWaveSaveBeforeAnnounce:
    """Same invariant, single-wave path (high-TPM profiles with concurrency_waves=1).

    The single-wave path runs every section concurrently then announces them
    all together, so the save-announce gap is narrower than in multi-wave.
    The invariant still holds: ``_merge_and_save`` runs BEFORE
    ``_announce_sections`` so any nav pill points at persisted data.
    """

    @pytest.mark.asyncio
    async def test_single_wave_saves_before_announce(self) -> None:
        """Single-wave path persists before announcing."""
        execution_order: list[str] = []
        save_calls: list[BrandSettings] = []
        svc = _make_svc_mock(save_calls)

        def recording_save(tenant_id: UUID, settings: BrandSettings) -> BrandSettings:
            execution_order.append("save")
            save_calls.append(settings)
            return settings

        svc.repository.save_settings.side_effect = recording_save

        orchestrator = ExtractionOrchestrator(svc)
        original_announce = orchestrator._announce_sections

        def recording_announce(callback: Any, sections: list, results: list, *, pct: int) -> None:
            execution_order.append(f"announce_{pct}")
            original_announce(callback, sections, results, pct=pct)

        orchestrator._announce_sections = recording_announce  # type: ignore[method-assign]

        await orchestrator._run_single_wave(
            svc=svc,
            content="test",
            current_data_str="",
            update_instructions=None,
            enriched_visual_content="",
            want_visuals=False,
            include_assets=False,
            progress_callback=_rich_callback,
            trace=None,
        )

        assert len(save_calls) >= 1, "Single-wave must call save_settings at least once"
        # First save must precede the first announce
        first_save_idx = execution_order.index("save")
        first_announce_idx = next(i for i, v in enumerate(execution_order) if v.startswith("announce_"))
        assert first_save_idx < first_announce_idx, f"save must precede announce in single-wave: {execution_order}"

    @pytest.mark.asyncio
    async def test_single_wave_save_contains_all_sections(self) -> None:
        """The single-wave save covers every extracted section at once."""
        save_calls: list[BrandSettings] = []
        svc = _make_svc_mock(save_calls)
        svc._extract_strategy = AsyncMock(
            return_value=BrandStrategy(methodology_name="One-shot"),
        )
        orchestrator = ExtractionOrchestrator(svc)

        await orchestrator._run_single_wave(
            svc=svc,
            content="test",
            current_data_str="",
            update_instructions=None,
            enriched_visual_content="",
            want_visuals=False,
            include_assets=False,
            progress_callback=_rich_callback,
            trace=None,
        )

        first_save = save_calls[0]
        assert first_save.identity.brand_name == "TestBrand"
        assert first_save.story.origin_story == "Founded in garage"
        assert first_save.strategy.methodology_name == "One-shot"

    @pytest.mark.asyncio
    async def test_single_wave_respects_dry_run(self) -> None:
        """dry_run=True on single-wave path must not persist."""
        save_calls: list[BrandSettings] = []
        svc = _make_svc_mock(save_calls)
        orchestrator = ExtractionOrchestrator(svc)

        await orchestrator._run_single_wave(
            svc=svc,
            content="test",
            current_data_str="",
            update_instructions=None,
            enriched_visual_content="",
            want_visuals=False,
            include_assets=False,
            progress_callback=_rich_callback,
            trace=None,
            dry_run=True,
        )

        assert len(save_calls) == 0, "dry_run on single-wave must not persist"


class TestCurrentThreadingAvoidsRedundantReads:
    """Wave-over-wave threading: only the first wave reads from the repo.

    Without threading each ``_merge_and_save`` would call ``get_settings``
    — 4 extra reads per multi-wave extraction. Threading the previous
    wave's saved BrandSettings as ``current`` eliminates them.
    """

    @pytest.mark.asyncio
    async def test_multi_wave_reads_repo_only_once(self) -> None:
        """Only wave 1 should hit ``repository.get_settings``."""
        save_calls: list[BrandSettings] = []
        svc = _make_svc_mock(save_calls)
        orchestrator = ExtractionOrchestrator(svc)

        await orchestrator._run_multi_wave(
            svc=svc,
            content="test",
            current_data_str="",
            update_instructions=None,
            enriched_visual_content="",
            want_visuals=False,
            include_assets=False,
            progress_callback=_rich_callback,
            trace=None,
        )

        # Expect exactly 1 call: wave 1 reads; waves 2/3/4 reuse ``last_saved``.
        assert svc.repository.get_settings.call_count == 1, (
            f"Expected 1 get_settings call (wave 1 only), "
            f"got {svc.repository.get_settings.call_count} — threading broken"
        )
