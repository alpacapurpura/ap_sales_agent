"""S5 — `shared.agent_observability.channels` registry tests.

Mirror de los tests F7 que viven en ``tests/modules/copilot/test_output_channel_format.py``
pero apuntando al nuevo home cross-agent. Sales_agent y copilot consumen ambos.

# [SALES-AGENT-CHANNEL-REGISTRY-S5]
"""

from __future__ import annotations

import pytest

from src.shared.agent_observability.channels.format import (
    CHANNEL_FORMATS,
    SUPPORTED_CHANNELS,
    ChannelFormat,
    get_channel_format,
    register_channel,
    reset_registry_for_tests,
)

CANONICAL_CHANNEL_IDS = frozenset(
    {"chat", "whatsapp", "email", "sms", "voice", "instagram_dm", "telegram"},
)


@pytest.fixture(autouse=True)
def _reset_registry():
    reset_registry_for_tests()
    yield
    reset_registry_for_tests()


class TestChannelFormatDataclass:
    def test_is_frozen(self) -> None:
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

    def test_uses_slots(self) -> None:
        """Frozen + slots → cannot add ad-hoc attributes."""
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
            fmt.some_random_attr = "z"  # type: ignore[attr-defined]

    def test_default_optional_extension_fields_are_none(self) -> None:
        """Sales-specific extension fields default to None / 0 so the dataclass
        stays back-compat with copilot's pre-S5 callers."""
        fmt = ChannelFormat(
            id="x",
            label_es="X",
            max_chars=100,
            emoji_allowed=True,
            line_break_style="\n",
            markdown_allowed=False,
            structure_hint="hint",
        )
        assert fmt.chunk_size is None
        assert fmt.typing_simulation_cpm is None
        assert fmt.parse_mode is None

    def test_max_chars_required_positive(self) -> None:
        with pytest.raises((TypeError, ValueError)):
            ChannelFormat(  # type: ignore[call-arg]
                id="x",
                label_es="X",
                emoji_allowed=True,
                line_break_style="\n",
                markdown_allowed=False,
                structure_hint="hint",
            )


class TestBaselineRegistry:
    def test_seven_canonical_channels_present(self) -> None:
        assert frozenset(CHANNEL_FORMATS.keys()) == CANONICAL_CHANNEL_IDS
        assert SUPPORTED_CHANNELS == CANONICAL_CHANNEL_IDS

    @pytest.mark.parametrize("channel_id", sorted(CANONICAL_CHANNEL_IDS))
    def test_baseline_channel_has_required_fields(self, channel_id: str) -> None:
        fmt = CHANNEL_FORMATS[channel_id]
        assert isinstance(fmt, ChannelFormat)
        assert fmt.id == channel_id
        assert fmt.label_es and fmt.label_es.strip()
        assert fmt.max_chars > 0
        assert fmt.line_break_style
        assert fmt.structure_hint and fmt.structure_hint.strip()

    def test_telegram_has_markdown_v2_parse_mode(self) -> None:
        """Telegram baseline declares parse_mode for adapter consumption."""
        tg = CHANNEL_FORMATS["telegram"]
        assert tg.parse_mode == "MarkdownV2"
        assert tg.markdown_allowed is True

    def test_sms_invariants_gsm7(self) -> None:
        sms = CHANNEL_FORMATS["sms"]
        assert sms.max_chars <= 160
        assert sms.emoji_allowed is False
        assert sms.markdown_allowed is False

    def test_whatsapp_under_session_cap(self) -> None:
        wa = CHANNEL_FORMATS["whatsapp"]
        assert wa.max_chars <= 4096
        # Standard markdown disallowed (WhatsApp uses *bold*/_italic_/~strike~ subset).
        assert wa.markdown_allowed is False

    def test_instagram_dm_cap_1000(self) -> None:
        ig = CHANNEL_FORMATS["instagram_dm"]
        assert ig.max_chars <= 1000
        assert ig.markdown_allowed is False


class TestRegisterChannel:
    def test_idempotent_same_object(self) -> None:
        fmt = ChannelFormat(
            id="custom",
            label_es="Custom",
            max_chars=500,
            emoji_allowed=True,
            line_break_style="\n",
            markdown_allowed=False,
            structure_hint="custom hint",
        )
        register_channel(fmt)
        register_channel(fmt)  # same object → no raise
        assert CHANNEL_FORMATS["custom"] is fmt

    def test_rejects_duplicate_id_with_different_spec(self) -> None:
        a = ChannelFormat(
            id="dup",
            label_es="A",
            max_chars=100,
            emoji_allowed=True,
            line_break_style="\n",
            markdown_allowed=False,
            structure_hint="A",
        )
        b = ChannelFormat(
            id="dup",
            label_es="B",
            max_chars=200,
            emoji_allowed=True,
            line_break_style="\n",
            markdown_allowed=False,
            structure_hint="B",
        )
        register_channel(a)
        with pytest.raises(ValueError, match="dup"):
            register_channel(b)

    def test_rejects_empty_id(self) -> None:
        bad = ChannelFormat(
            id="",
            label_es="X",
            max_chars=100,
            emoji_allowed=True,
            line_break_style="\n",
            markdown_allowed=False,
            structure_hint="X",
        )
        with pytest.raises(ValueError, match="non-empty id"):
            register_channel(bad)

    def test_rejects_key_id_mismatch(self) -> None:
        fmt = ChannelFormat(
            id="alpha",
            label_es="A",
            max_chars=100,
            emoji_allowed=True,
            line_break_style="\n",
            markdown_allowed=False,
            structure_hint="A",
        )
        with pytest.raises(ValueError, match="mismatch"):
            register_channel(fmt, key="beta")

    def test_supported_channels_updated_after_register(self) -> None:
        fmt = ChannelFormat(
            id="brand_new",
            label_es="Brand New",
            max_chars=300,
            emoji_allowed=False,
            line_break_style="\n",
            markdown_allowed=False,
            structure_hint="brand new hint",
        )
        register_channel(fmt)
        # Re-import to pick up the rebound module-level constant after
        # registry mutation (the binding rebinds; tests read fresh).
        from src.shared.agent_observability.channels import format as fmt_module

        assert "brand_new" in fmt_module.SUPPORTED_CHANNELS


class TestGetChannelFormat:
    def test_returns_registered(self) -> None:
        fmt = get_channel_format("whatsapp")
        assert fmt.id == "whatsapp"

    def test_unknown_falls_back_to_chat(self) -> None:
        fmt = get_channel_format("nonexistent_channel")
        assert fmt.id == "chat"

    def test_none_falls_back_to_chat(self) -> None:
        fmt = get_channel_format(None)
        assert fmt.id == "chat"

    def test_empty_string_falls_back_to_chat(self) -> None:
        fmt = get_channel_format("")
        assert fmt.id == "chat"

    def test_alias_instagram_to_instagram_dm(self) -> None:
        """Sales_agent ChannelResolver uses ``instagram`` (no ``_dm`` suffix).
        The shared registry must accept either spelling so existing AgentState
        ``channel_type`` strings keep resolving."""
        fmt_alias = get_channel_format("instagram")
        fmt_canonical = get_channel_format("instagram_dm")
        assert fmt_alias is fmt_canonical


class TestResetRegistryForTests:
    def test_removes_custom_channels(self) -> None:
        custom = ChannelFormat(
            id="ephemeral",
            label_es="Ephemeral",
            max_chars=100,
            emoji_allowed=False,
            line_break_style="\n",
            markdown_allowed=False,
            structure_hint="x",
        )
        register_channel(custom)
        assert "ephemeral" in CHANNEL_FORMATS
        reset_registry_for_tests()
        assert "ephemeral" not in CHANNEL_FORMATS
        assert frozenset(CHANNEL_FORMATS.keys()) == CANONICAL_CHANNEL_IDS
