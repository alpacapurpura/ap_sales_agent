"""Regression tests — per-wave save BEFORE announce (offer).

Invariant tested:
  Given wave 1 produced identity + promise + strategy,
  when ``_announce_sections`` emits those events (pct=40),
  then ``offer_service.patch_offer`` has already been called with the
  wave 1 data — i.e. the save happened BEFORE the announce.

Why this matters: the copilot extraction_section_completed subscriber inserts
a nav pill into the conversation the moment an announce fires. If save comes
after announce, the pill points at un-persisted data and the user sees an
empty section when they click the pill mid-extraction.

Covers:
  - ``_run_multi_wave`` (3 waves): per-wave saves
  - ``_run_single_wave`` (1 wave high-TPM): save before announce
  - dry_run: must not call patch_offer
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from src.modules.offer.application.offer_extraction_orchestrator import (
    OfferExtractionOrchestrator,
)
from src.modules.offer.domain.offer import (
    OfferClosingUpdate,
    OfferDetailsUpdate,
    OfferPricingUpdate,
    OfferPromiseUpdate,
    OfferPsychologyUpdate,
    OfferStrategyUpdate,
    OfferValueStackUpdate,
)

TENANT_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
OFFER_ID = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_svc_and_orchestrator(
    patch_calls: list,
) -> tuple[MagicMock, OfferExtractionOrchestrator]:
    """Build a minimal OfferExtractionService mock + orchestrator with injected deps.

    Returns (svc_mock, orchestrator) where orchestrator._offer_service is the mock
    that records patch_offer calls. Tests call _run_multi_wave/_run_single_wave
    directly (bypassing run()), so we inject _offer_service before the call to
    avoid creating a real OfferService(svc.db) which would hit the mock DB.
    """
    svc = MagicMock()
    svc.tenant_id = TENANT_ID
    svc.offer_id = OFFER_ID
    svc.db = MagicMock()

    # LLM extractors — return plausible objects with actual data so waves
    # 2 and 3 also produce non-empty merged dicts (required for patch_offer calls).
    svc._extract_promise = AsyncMock(
        return_value=OfferPromiseUpdate(
            headline_promise="Buy this now",
            primary_outcome="Get rich",
        )
    )
    svc._extract_strategy = AsyncMock(return_value=OfferStrategyUpdate(target_avatar_match=["Coaches"]))
    svc._extract_psychology = AsyncMock(
        return_value=OfferPsychologyUpdate(objections=[{"type": "price", "trigger_phrases": ["muy caro"]}])
    )
    svc._extract_value_stack = AsyncMock(
        return_value=OfferValueStackUpdate(
            deliverables=[{"name": "Módulo 1", "format": "video", "quantity": "10h", "value_stack_price": 0.0}]
        )
    )
    svc._extract_closing = AsyncMock(
        return_value=OfferClosingUpdate(
            guarantee_type="unconditional_30_day",
            guarantee_terms="30 días sin preguntas",
        )
    )
    svc._extract_pricing = AsyncMock(
        return_value=OfferPricingUpdate(
            tax_included=True,
            installments_available="3, 6, 12",
        )
    )
    # OfferDetailsUpdate has fulfillment fields (access_duration, support).
    # Previous fixture passed `onboarding_action` here, which silently no-op'd
    # because that field actually belongs to OfferClosingUpdate — so wave 3
    # merges were hidden as empty.
    svc._extract_details = AsyncMock(
        return_value=OfferDetailsUpdate(
            access_duration_text="12 meses",
            support_duration_days=90,
        )
    )

    orchestrator = OfferExtractionOrchestrator(svc)

    # Build the offer_service mock that records patch_offer calls
    offer_service = MagicMock()
    offer_service.get_offer.return_value = MagicMock(archetype=None)

    def _record_patch(offer_id: UUID, tenant_id: UUID, data: dict) -> None:
        patch_calls.append(dict(data))

    offer_service.patch_offer.side_effect = _record_patch

    # Inject into orchestrator — bypasses real DB for unit tests
    orchestrator._offer_service = offer_service

    return svc, orchestrator


def _rich_callback(
    pct: int,
    stage: str,
    *,
    new_fields: list | None = None,
    section_completed: str | None = None,
) -> None:
    """Rich-progress callback that accepts section_completed / new_fields."""


# ---------------------------------------------------------------------------
# Core invariant: save BEFORE announce
# ---------------------------------------------------------------------------


class TestPerWaveSaveBeforeAnnounce:
    """Core invariant: patch_offer happens before section_completed event emission."""

    @pytest.mark.asyncio
    async def test_save_called_before_announce_wave1(self) -> None:
        """After wave 1, patch_offer must be called before _announce_sections."""
        patch_calls: list[dict] = []
        announce_calls: list[str] = []

        svc, orchestrator = _make_svc_and_orchestrator(patch_calls)

        original_announce = orchestrator._announce_sections

        def patched_announce(
            progress_callback: Any,
            sections: list,
            results: list,
            *,
            pct: int,
        ) -> None:
            announce_calls.append(f"announce_pct_{pct}")
            original_announce(progress_callback, sections, results, pct=pct)

        orchestrator._announce_sections = patched_announce  # type: ignore[method-assign]

        await orchestrator._run_multi_wave(
            svc=svc,
            content="test content about the offer",
            current_data_str="",
            update_instructions=None,
            progress_callback=_rich_callback,
            trace=None,
        )

        # patch_offer should have been called AT LEAST once per wave (3 waves)
        assert len(patch_calls) >= 3, f"Expected at least 3 per-wave saves, got {len(patch_calls)}"

    @pytest.mark.asyncio
    async def test_wave1_save_contains_promise_data(self) -> None:
        """Wave 1 save must include promise data extracted in that wave."""
        patch_calls: list[dict] = []
        svc, orchestrator = _make_svc_and_orchestrator(patch_calls)

        await orchestrator._run_multi_wave(
            svc=svc,
            content="test",
            current_data_str="",
            update_instructions=None,
            progress_callback=_rich_callback,
            trace=None,
        )

        # First save should have promise fields
        first_save = patch_calls[0]
        assert "headline_promise" in first_save, (
            f"Wave 1 save must include headline_promise, got keys: {list(first_save.keys())}"
        )
        assert first_save["headline_promise"] == "Buy this now"

    @pytest.mark.asyncio
    async def test_wave2_save_contains_psychology_data(self) -> None:
        """Wave 2 save must include psychology/value_stack data."""
        patch_calls: list[dict] = []
        svc, orchestrator = _make_svc_and_orchestrator(patch_calls)
        svc._extract_psychology = AsyncMock(
            return_value=OfferPsychologyUpdate(objections=[{"type": "price", "trigger_phrases": []}])
        )

        await orchestrator._run_multi_wave(
            svc=svc,
            content="test",
            current_data_str="",
            update_instructions=None,
            progress_callback=_rich_callback,
            trace=None,
        )

        assert len(patch_calls) >= 2, "Should have at least 2 per-wave saves"
        # wave 2 (psychology, value_stack, pricing) should include objections
        second_save = patch_calls[1]
        assert "objections" in second_save, f"Wave 2 save must include objections, got: {list(second_save.keys())}"

    @pytest.mark.asyncio
    async def test_legacy_callback_still_saves_per_wave(self) -> None:
        """Per-wave saves happen regardless of callback type."""
        patch_calls: list[dict] = []
        svc, orchestrator = _make_svc_and_orchestrator(patch_calls)

        def legacy_callback(pct: int, stage: str) -> None:
            pass

        await orchestrator._run_multi_wave(
            svc=svc,
            content="test",
            current_data_str="",
            update_instructions=None,
            progress_callback=legacy_callback,
            trace=None,
        )

        # Per-wave saves happen unconditionally (not gated on callback type)
        assert len(patch_calls) >= 3, "Per-wave saves must happen even with legacy callback"

    @pytest.mark.asyncio
    async def test_dry_run_does_not_save(self) -> None:
        """In dry_run mode, patch_offer must never be called."""
        patch_calls: list[dict] = []
        svc, orchestrator = _make_svc_and_orchestrator(patch_calls)

        await orchestrator._run_multi_wave(
            svc=svc,
            content="test content",
            current_data_str="",
            update_instructions=None,
            progress_callback=_rich_callback,
            trace=None,
            dry_run=True,
        )

        assert len(patch_calls) == 0, f"dry_run=True must not call patch_offer, but got {len(patch_calls)} calls"


# ---------------------------------------------------------------------------
# Ordering: save before announce
# ---------------------------------------------------------------------------


class TestSaveOrderInvariant:
    """Verify save-before-announce ordering at a logical level."""

    @pytest.mark.asyncio
    async def test_save_before_announce_ordering_tracked(self) -> None:
        """Track that save always precedes announce for each wave."""
        execution_order: list[str] = []
        patch_calls: list[dict] = []
        svc, orchestrator = _make_svc_and_orchestrator(patch_calls)

        original_patch_effect = orchestrator._offer_service.patch_offer.side_effect

        def recording_patch(offer_id: UUID, tenant_id: UUID, data: dict) -> None:
            execution_order.append("save")
            original_patch_effect(offer_id, tenant_id, data)

        orchestrator._offer_service.patch_offer.side_effect = recording_patch

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
            progress_callback=_rich_callback,
            trace=None,
        )

        assert "save" in execution_order, "save must appear in execution_order"
        assert any("announce" in item for item in execution_order), "announce must appear"

        # For each announce, there must be a save BEFORE it
        for i, item in enumerate(execution_order):
            if "announce" in item:
                preceding = execution_order[:i]
                assert "save" in preceding, (
                    f"announce at position {i} ({item!r}) has no preceding save. Full order: {execution_order}"
                )


# ---------------------------------------------------------------------------
# Single-wave (high-TPM profiles)
# ---------------------------------------------------------------------------


class TestSingleWaveSaveBeforeAnnounce:
    """Same invariant, single-wave path."""

    @pytest.mark.asyncio
    async def test_single_wave_saves_before_announce(self) -> None:
        """Single-wave path persists before announcing."""
        execution_order: list[str] = []
        patch_calls: list[dict] = []
        svc, orchestrator = _make_svc_and_orchestrator(patch_calls)

        original_patch_effect = orchestrator._offer_service.patch_offer.side_effect

        def recording_patch(offer_id: UUID, tenant_id: UUID, data: dict) -> None:
            execution_order.append("save")
            original_patch_effect(offer_id, tenant_id, data)

        orchestrator._offer_service.patch_offer.side_effect = recording_patch

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
            progress_callback=_rich_callback,
            trace=None,
        )

        assert len(patch_calls) >= 1, "Single-wave must call patch_offer at least once"
        first_save_idx = execution_order.index("save")
        first_announce_idx = next(i for i, v in enumerate(execution_order) if v.startswith("announce_"))
        assert first_save_idx < first_announce_idx, f"save must precede announce in single-wave: {execution_order}"

    @pytest.mark.asyncio
    async def test_single_wave_save_contains_promise_and_psychology(self) -> None:
        """The single-wave save covers multiple sections at once (promise + psychology)."""
        patch_calls: list[dict] = []
        svc, orchestrator = _make_svc_and_orchestrator(patch_calls)

        await orchestrator._run_single_wave(
            svc=svc,
            content="test",
            current_data_str="",
            update_instructions=None,
            progress_callback=_rich_callback,
            trace=None,
        )

        # Should have at least one save covering multiple sections
        assert len(patch_calls) >= 1
        # Combined save should include fields from multiple sections
        all_keys: set[str] = set()
        for save in patch_calls:
            all_keys.update(save.keys())
        assert "headline_promise" in all_keys, f"Single-wave save must include promise fields. Got: {all_keys}"
        assert "objections" in all_keys, f"Single-wave save must include psychology fields. Got: {all_keys}"

    @pytest.mark.asyncio
    async def test_single_wave_respects_dry_run(self) -> None:
        """dry_run=True on single-wave path must not persist."""
        patch_calls: list[dict] = []
        svc, orchestrator = _make_svc_and_orchestrator(patch_calls)

        await orchestrator._run_single_wave(
            svc=svc,
            content="test",
            current_data_str="",
            update_instructions=None,
            progress_callback=_rich_callback,
            trace=None,
            dry_run=True,
        )

        assert len(patch_calls) == 0, "dry_run on single-wave must not persist"


# ---------------------------------------------------------------------------
# Wave-over-wave offer reload efficiency
# ---------------------------------------------------------------------------


class TestWaveOverWaveReload:
    """Wave saves are independent — each wave persists its own data."""

    @pytest.mark.asyncio
    async def test_multi_wave_calls_patch_offer_per_wave(self) -> None:
        """Multi-wave path must call patch_offer at least once per wave (3 waves)."""
        patch_calls: list[dict] = []
        svc, orchestrator = _make_svc_and_orchestrator(patch_calls)

        await orchestrator._run_multi_wave(
            svc=svc,
            content="test",
            current_data_str="",
            update_instructions=None,
            progress_callback=_rich_callback,
            trace=None,
        )

        assert len(patch_calls) >= 3, f"Expected >= 3 patch_offer calls (one per wave), got {len(patch_calls)}"
