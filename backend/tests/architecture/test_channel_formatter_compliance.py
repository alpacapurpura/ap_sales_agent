"""Architecture fitness — F7 channel formatter registry invariants.

Guards against silent drift in ``copilot.domain.output_channels``:

* every baseline channel exposes the metadata required by the synthesizer
  (label_es, max_chars > 0, line_break_style, structure_hint);
* registry keys equal ``ChannelFormat.id`` (no typo where a wrapper dict and
  the value disagree);
* baseline ids cover the seven canonical channels declared in
  ``02-architecture-target.md §7``;
* booleans are real booleans (not truthy strings).

Lives next to the workflow / DDD fitness tests so CI catches problems before
runtime parses the registry.
"""

from __future__ import annotations

import pytest

from src.shared.agent_observability.channels.format import (
    CHANNEL_FORMATS,
    SUPPORTED_CHANNELS,
    ChannelFormat,
    reset_registry_for_tests,
)

CANONICAL_CHANNEL_IDS = frozenset({"chat", "whatsapp", "email", "sms", "voice", "instagram_dm", "telegram"})


@pytest.fixture(autouse=True)
def _restore_registry():
    """Restore baseline so a previous test's ``register_channel`` does not
    leak into invariants here."""
    reset_registry_for_tests()
    yield
    reset_registry_for_tests()


def test_baseline_covers_canonical_channels() -> None:
    missing = CANONICAL_CHANNEL_IDS - SUPPORTED_CHANNELS
    assert missing == set(), f"missing canonical channels: {sorted(missing)}"


def test_supported_channels_matches_registry_keys() -> None:
    assert frozenset(CHANNEL_FORMATS.keys()) == SUPPORTED_CHANNELS


def test_no_duplicate_or_mismatched_ids() -> None:
    """Every entry's key equals its ``ChannelFormat.id``. Catches the
    "wrapper dict typo'd the key" gotcha before anything reads the registry."""
    mismatches = [(key, fmt.id) for key, fmt in CHANNEL_FORMATS.items() if key != fmt.id]
    assert mismatches == [], f"key/id mismatches: {mismatches}"


@pytest.mark.parametrize("channel_id", sorted(CANONICAL_CHANNEL_IDS))
def test_required_fields_populated(channel_id: str) -> None:
    fmt = CHANNEL_FORMATS[channel_id]
    assert isinstance(fmt, ChannelFormat)
    assert fmt.id == channel_id
    assert fmt.label_es and fmt.label_es.strip(), "label_es must be Spanish populated"
    assert fmt.max_chars > 0, "max_chars must be a positive int"
    assert fmt.line_break_style, "line_break_style must be populated"
    assert fmt.structure_hint and fmt.structure_hint.strip(), (
        "structure_hint feeds the LLM system prompt — must be populated"
    )


@pytest.mark.parametrize("channel_id", sorted(CANONICAL_CHANNEL_IDS))
def test_boolean_flags_are_real_booleans(channel_id: str) -> None:
    """Truthy strings ('false') in ``emoji_allowed`` would silently bypass the
    formatter. Pin the type."""
    fmt = CHANNEL_FORMATS[channel_id]
    assert isinstance(fmt.emoji_allowed, bool)
    assert isinstance(fmt.markdown_allowed, bool)


def test_sms_invariants() -> None:
    """SMS GSM-7 single segment cap = 160. Emoji/markdown disallowed so the
    LLM does not flip the message to UCS-2 (70-char cap)."""
    sms = CHANNEL_FORMATS["sms"]
    assert sms.max_chars <= 160
    assert sms.emoji_allowed is False
    assert sms.markdown_allowed is False


def test_whatsapp_invariants() -> None:
    """WhatsApp Business — text messages 4096 chars, templates 1024. Default
    keeps under templates ceiling for safe copy-paste."""
    wa = CHANNEL_FORMATS["whatsapp"]
    assert wa.max_chars <= 4096
    assert wa.markdown_allowed is False  # WA uses *bold*/_italic_/~strike~ subset, not std markdown
