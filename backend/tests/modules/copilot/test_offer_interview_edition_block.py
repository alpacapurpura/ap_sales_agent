"""Tests for the ``first_edition_date`` block in the offer interview (Phase 7)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.modules.copilot.domain.interview_configs.first_edition import (
    FirstEditionInput,
)
from src.modules.copilot.domain.interview_configs.offer_config import (
    FIRST_EDITION_DATE_BLOCK,
    get_offer_interview_config,
)


class TestBlockPresence:
    """The extra block appears only for archetypes that launch by editions."""

    @pytest.mark.parametrize("archetype", ["programa", "servicio", "experiencia"])
    def test_edition_supporting_archetype_gets_block(self, archetype: str) -> None:
        config = get_offer_interview_config(archetype)
        ids = [b.id for b in config.bloques]
        assert "first_edition_date" in ids
        assert ids[-1] == "first_edition_date", "must be the final block"

    @pytest.mark.parametrize("archetype", ["producto", "membresia"])
    def test_evergreen_archetype_skips_block(self, archetype: str) -> None:
        config = get_offer_interview_config(archetype)
        ids = [b.id for b in config.bloques]
        assert "first_edition_date" not in ids

    def test_unknown_archetype_uses_static_config(self) -> None:
        # Static config (no dynamic factory) has 6 blocks and no edition date.
        config = get_offer_interview_config("not_a_real_archetype")
        ids = [b.id for b in config.bloques]
        assert "first_edition_date" not in ids
        assert len(ids) == 6


class TestBlockMetadata:
    def test_block_id_and_fields(self) -> None:
        assert FIRST_EDITION_DATE_BLOCK.id == "first_edition_date"
        assert "first_edition.start_date" in FIRST_EDITION_DATE_BLOCK.campos_objetivo

    def test_coverage_threshold_allows_skip(self) -> None:
        # Low threshold → skipping is still allowed as a valid completion.
        assert FIRST_EDITION_DATE_BLOCK.coverage_threshold <= 0.5


class TestFirstEditionInputSchema:
    def test_skip_path_accepts_nulls(self) -> None:
        schema = FirstEditionInput()
        assert schema.start_date is None
        assert schema.end_date is None
        assert schema.location_override is None

    def test_full_path_parses_iso(self) -> None:
        schema = FirstEditionInput(
            start_date=datetime(2026, 7, 15, 19, 0, tzinfo=timezone.utc),
            location_override={"format": "virtual", "platform": "Zoom"},
        )
        assert schema.start_date is not None
        assert schema.location_override["platform"] == "Zoom"
