"""F7 — `ChannelFormat` dataclass + `CHANNEL_FORMATS` registry tests.

The registry replaces F5's tiny ``_CHANNEL_HINTS`` dict and is consumed by:

* the ``ask_tenant_data`` synthesizer (channel-aware prose generation);
* the new ``format_for_channel`` tool (post-processing arbitrary text);
* providers that register their own channels via ``register_channel``.
"""

from __future__ import annotations

import pytest

from luana_core_channels.format import (
    CHANNEL_FORMATS,
    SUPPORTED_CHANNELS,
    ChannelFormat,
    get_channel_format,
    register_channel,
    reset_registry_for_tests,
)


@pytest.fixture(autouse=True)
def _reset_registry():
    """Restore baseline registry between tests so ``register_channel`` calls
    don't leak across cases."""
    reset_registry_for_tests()
    yield
    reset_registry_for_tests()


def test_channel_format_is_frozen() -> None:
    """Frozen dataclasses raise ``FrozenInstanceError`` (subclass of
    ``AttributeError``) on attribute mutation."""
    fmt = ChannelFormat(
        id="x",
        label_es="X",
        max_chars=100,
        emoji_allowed=True,
        line_break_style="\n",
        markdown_allowed=False,
        structure_hint="hint",
    )
    with pytest.raises((AttributeError, TypeError)):
        fmt.id = "y"  # type: ignore[misc]


def test_baseline_registry_has_seven_canonical_channels() -> None:
    expected = {"chat", "whatsapp", "email", "sms", "voice", "instagram_dm", "telegram"}
    assert frozenset(expected) == SUPPORTED_CHANNELS
    assert set(CHANNEL_FORMATS.keys()) == expected


@pytest.mark.parametrize(
    "channel_id",
    ["chat", "whatsapp", "email", "sms", "voice", "instagram_dm", "telegram"],
)
def test_every_channel_has_required_metadata(channel_id: str) -> None:
    fmt = CHANNEL_FORMATS[channel_id]
    assert fmt.id == channel_id, "id field must match registry key"
    assert fmt.label_es and fmt.label_es.strip(), "label_es must be populated"
    assert fmt.max_chars > 0, "max_chars must be positive"
    assert fmt.line_break_style, "line_break_style must be populated"
    assert fmt.structure_hint and fmt.structure_hint.strip(), "structure_hint must be populated"


def test_sms_disallows_emoji_and_markdown() -> None:
    """SMS uses GSM-7 by default; emojis flip the message to UCS-2 (70-char
    cap) and markdown chars consume budget without rendering."""
    sms = CHANNEL_FORMATS["sms"]
    assert sms.emoji_allowed is False
    assert sms.markdown_allowed is False
    assert sms.max_chars <= 160, "GSM-7 single-segment safety budget"


def test_whatsapp_disallows_markdown() -> None:
    """WhatsApp Business has its own *bold*/_italic_ subset, but standard
    markdown is not rendered. Telling the LLM markdown_allowed=False keeps
    output clean for copy-paste."""
    wa = CHANNEL_FORMATS["whatsapp"]
    assert wa.markdown_allowed is False
    assert wa.emoji_allowed is True
    assert wa.max_chars <= 4096, "WhatsApp text-message hard ceiling"


def test_chat_allows_markdown_and_emoji() -> None:
    chat = CHANNEL_FORMATS["chat"]
    assert chat.markdown_allowed is True
    assert chat.emoji_allowed is True


def test_get_channel_format_returns_known_channel() -> None:
    assert get_channel_format("whatsapp").id == "whatsapp"


def test_get_channel_format_falls_back_to_chat_on_unknown() -> None:
    assert get_channel_format("does-not-exist").id == "chat"


def test_get_channel_format_falls_back_on_empty_or_none() -> None:
    assert get_channel_format("").id == "chat"
    assert get_channel_format(None).id == "chat"


def test_register_channel_adds_new_channel() -> None:
    custom = ChannelFormat(
        id="custom_x",
        label_es="Canal X",
        max_chars=500,
        emoji_allowed=True,
        line_break_style="\n",
        markdown_allowed=False,
        structure_hint="hint custom",
    )
    register_channel(custom)
    assert "custom_x" in CHANNEL_FORMATS
    assert get_channel_format("custom_x").label_es == "Canal X"


def test_register_channel_rejects_duplicate_id() -> None:
    custom = ChannelFormat(
        id="whatsapp",  # already in registry
        label_es="dup",
        max_chars=100,
        emoji_allowed=True,
        line_break_style="\n",
        markdown_allowed=False,
        structure_hint="dup",
    )
    with pytest.raises(ValueError, match="already registered"):
        register_channel(custom)


def test_register_channel_rejects_empty_id() -> None:
    bad = ChannelFormat(
        id="",
        label_es="x",
        max_chars=10,
        emoji_allowed=True,
        line_break_style="\n",
        markdown_allowed=False,
        structure_hint="x",
    )
    with pytest.raises(ValueError, match="non-empty id"):
        register_channel(bad)


def test_register_channel_rejects_mismatch_with_id_field() -> None:
    """Registry key must equal ``ChannelFormat.id`` — guards against silent
    typos where a provider hand-rolls the wrapper dict."""
    fmt = ChannelFormat(
        id="custom_y",
        label_es="x",
        max_chars=10,
        emoji_allowed=True,
        line_break_style="\n",
        markdown_allowed=False,
        structure_hint="x",
    )
    with pytest.raises(ValueError, match="id mismatch"):
        register_channel(fmt, key="not_custom_y")
