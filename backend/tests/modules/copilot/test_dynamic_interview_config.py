"""Tests for dynamic offer interview config by archetype (Task 5)."""

import pytest

from src.modules.copilot.domain.interview_config import InterviewConfig
from src.modules.copilot.domain.interview_configs.offer_config import OFFER_INTERVIEW_CONFIG, get_offer_interview_config

# ---------------------------------------------------------------------------
# Universal block IDs — always present regardless of archetype
# ---------------------------------------------------------------------------

_UNIVERSAL_FIRST_IDS = ["identity_strategy", "promise", "psychology"]
_UNIVERSAL_FINAL_IDS = ["value_stack", "pricing", "closing"]
_ARCHETYPE_BLOCK_IDS = {
    "producto": "product_details",
    "programa": "program_details",
    "servicio": "service_details",
    "membresia": "subscription_details",
    "experiencia": "event_details",
}
# Archetypes that get an extra FIRST_EDITION_DATE_BLOCK appended after the
# universal final blocks (Phase 7). Kept in sync with
# ``src/modules/copilot/domain/interview_configs/offer_config.py``.
_EDITION_SUPPORTING_ARCHETYPES = frozenset({"programa", "servicio", "experiencia"})


# ---------------------------------------------------------------------------
# 1. Factory returns InterviewConfig for each archetype
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("archetype", list(_ARCHETYPE_BLOCK_IDS.keys()))
def test_factory_returns_interview_config(archetype: str) -> None:
    """get_offer_interview_config returns an InterviewConfig for every archetype."""
    config = get_offer_interview_config(archetype)
    assert isinstance(config, InterviewConfig)


# ---------------------------------------------------------------------------
# 2. Total block count is 7 (3 universal_first + 1 archetype + 3 universal_final)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("archetype", list(_ARCHETYPE_BLOCK_IDS.keys()))
def test_dynamic_config_block_count(archetype: str) -> None:
    """Dynamic config has 7 blocks (3 first + 1 archetype + 3 final); edition-
    supporting archetypes get one extra ``first_edition_date`` block (8 total)."""
    config = get_offer_interview_config(archetype)
    expected = 8 if archetype in _EDITION_SUPPORTING_ARCHETYPES else 7
    assert len(config.bloques) == expected, (
        f"Expected {expected} blocks for archetype '{archetype}', got "
        f"{len(config.bloques)}: {[b.id for b in config.bloques]}"
    )


# ---------------------------------------------------------------------------
# 3. Universal first blocks are always in positions 0-2
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("archetype", list(_ARCHETYPE_BLOCK_IDS.keys()))
def test_universal_first_blocks_positions(archetype: str) -> None:
    """Universal first blocks always occupy positions 0, 1, 2."""
    config = get_offer_interview_config(archetype)
    first_ids = [b.id for b in config.bloques[:3]]
    assert first_ids == _UNIVERSAL_FIRST_IDS, (
        f"Archetype '{archetype}': expected {_UNIVERSAL_FIRST_IDS}, got {first_ids}"
    )


# ---------------------------------------------------------------------------
# 4. Archetype-specific block is always at position 3
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("archetype", list(_ARCHETYPE_BLOCK_IDS.keys()))
def test_archetype_block_at_position_3(archetype: str) -> None:
    """Archetype-specific block is always at position 3."""
    config = get_offer_interview_config(archetype)
    block_at_3 = config.bloques[3]
    expected_id = _ARCHETYPE_BLOCK_IDS[archetype]
    assert block_at_3.id == expected_id, (
        f"Archetype '{archetype}': expected block id '{expected_id}' at position 3, got '{block_at_3.id}'"
    )


# ---------------------------------------------------------------------------
# 5. Universal final blocks are always in positions 4-6
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("archetype", list(_ARCHETYPE_BLOCK_IDS.keys()))
def test_universal_final_blocks_positions(archetype: str) -> None:
    """Universal final blocks always occupy positions 4, 5, 6. Edition-supporting
    archetypes may append ``first_edition_date`` as position 7."""
    config = get_offer_interview_config(archetype)
    final_ids = [b.id for b in config.bloques[4:7]]
    assert final_ids == _UNIVERSAL_FINAL_IDS, (
        f"Archetype '{archetype}': expected {_UNIVERSAL_FINAL_IDS}, got {final_ids}"
    )
    if archetype in _EDITION_SUPPORTING_ARCHETYPES:
        assert config.bloques[7].id == "first_edition_date"


# ---------------------------------------------------------------------------
# 6. All archetype configs have domain == "offer"
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("archetype", list(_ARCHETYPE_BLOCK_IDS.keys()))
def test_dynamic_config_domain_is_offer(archetype: str) -> None:
    """Dynamic config always has domain 'offer'."""
    config = get_offer_interview_config(archetype)
    assert config.domain == "offer"


# ---------------------------------------------------------------------------
# 7. Each archetype block has a non-empty label
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("archetype", list(_ARCHETYPE_BLOCK_IDS.keys()))
def test_archetype_block_has_label(archetype: str) -> None:
    """Archetype-specific block has a non-empty label."""
    config = get_offer_interview_config(archetype)
    archetype_block = config.bloques[3]
    assert archetype_block.label.strip(), f"Archetype '{archetype}': block '{archetype_block.id}' has no label"


# ---------------------------------------------------------------------------
# 8. Unknown archetype falls back to static OFFER_INTERVIEW_CONFIG
# ---------------------------------------------------------------------------


def test_unknown_archetype_returns_static_config() -> None:
    """Unknown archetype falls back to the static OFFER_INTERVIEW_CONFIG."""
    config = get_offer_interview_config("unknown_archetype")
    assert config is OFFER_INTERVIEW_CONFIG


# ---------------------------------------------------------------------------
# 9. Backward compatibility: OFFER_INTERVIEW_CONFIG still has 6 blocks
# ---------------------------------------------------------------------------


def test_static_config_still_has_6_blocks() -> None:
    """OFFER_INTERVIEW_CONFIG remains unchanged with 6 blocks for backward compat."""
    assert len(OFFER_INTERVIEW_CONFIG.bloques) == 6
    block_ids = [b.id for b in OFFER_INTERVIEW_CONFIG.bloques]
    assert block_ids == [
        "identity_strategy",
        "promise",
        "psychology",
        "pricing",
        "value_stack",
        "closing",
    ]
