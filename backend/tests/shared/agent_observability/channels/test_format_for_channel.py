"""S5 — `format_for_channel` post-processor tests (shared).

Mirror of copilot's F7 ``test_format_for_channel_tool.py`` apuntando al nuevo
home cross-agent. Adds Telegram MarkdownV2 escape coverage.

# [SALES-AGENT-CHANNEL-REGISTRY-S5]
"""

from __future__ import annotations

import pytest

from luana_core_channels.format import (
    escape_markdown_v2,
    reset_registry_for_tests,
)
from luana_core_channels.format_for_channel import (
    format_for_channel_impl,
)


@pytest.fixture(autouse=True)
def _reset():
    reset_registry_for_tests()
    yield
    reset_registry_for_tests()


class TestFormatForChannelStripsMarkdownWhenDisallowed:
    def test_whatsapp_strips_standard_markdown_bold(self) -> None:
        result = format_for_channel_impl(
            content="Hola **mundo** soy *italic*",
            channel_id="whatsapp",
        )
        assert "**" not in result["content"]
        # WhatsApp keeps the inner content visible
        assert "mundo" in result["content"]
        assert "markdown_stripped" in result["warnings"]

    def test_instagram_dm_strips_markdown(self) -> None:
        result = format_for_channel_impl(
            content="Hola **negrita** [link](https://example.com)",
            channel_id="instagram_dm",
        )
        assert "**" not in result["content"]
        assert "[link]" not in result["content"]
        assert "negrita" in result["content"]
        assert "https://example.com" in result["content"]

    def test_sms_strips_markdown(self) -> None:
        result = format_for_channel_impl(
            content="### Heading\n\n**Bold**",
            channel_id="sms",
        )
        assert "###" not in result["content"]
        assert "**" not in result["content"]


class TestFormatForChannelStripsEmojiWhenDisallowed:
    def test_sms_strips_emoji(self) -> None:
        result = format_for_channel_impl(
            content="Hola 👋 ¿cómo estás? 🚀",
            channel_id="sms",
        )
        assert "👋" not in result["content"]
        assert "🚀" not in result["content"]
        assert "emoji_stripped" in result["warnings"]
        assert "Hola" in result["content"]

    def test_voice_strips_emoji(self) -> None:
        result = format_for_channel_impl(content="Hola 😀", channel_id="voice")
        assert "😀" not in result["content"]


class TestFormatForChannelTruncates:
    def test_sms_truncates_at_160(self) -> None:
        long_content = "x" * 200
        result = format_for_channel_impl(content=long_content, channel_id="sms")
        assert len(result["content"]) <= 160
        assert "truncated" in result["warnings"]
        # Truncation marker appended.
        assert result["content"].endswith("…")

    def test_no_truncation_when_within_cap(self) -> None:
        result = format_for_channel_impl(content="short", channel_id="email")
        assert "truncated" not in result["warnings"]
        assert result["content"] == "short"


class TestFormatForChannelKeepsMarkdownWhenAllowed:
    def test_chat_preserves_markdown(self) -> None:
        result = format_for_channel_impl(
            content="**bold** and _italic_",
            channel_id="chat",
        )
        assert "markdown_stripped" not in result["warnings"]
        assert "**bold**" in result["content"]

    def test_telegram_preserves_markdown(self) -> None:
        result = format_for_channel_impl(
            content="**bold**",
            channel_id="telegram",
        )
        assert "markdown_stripped" not in result["warnings"]


class TestFormatForChannelEmojiPreservedWhenAllowed:
    def test_whatsapp_keeps_emoji(self) -> None:
        result = format_for_channel_impl(content="Hola 👋", channel_id="whatsapp")
        assert "👋" in result["content"]
        assert "emoji_stripped" not in result["warnings"]


class TestFormatForChannelFallback:
    def test_unknown_channel_uses_chat_spec(self) -> None:
        result = format_for_channel_impl(content="**bold**", channel_id="zzz")
        # chat allows markdown, so no strip.
        assert "markdown_stripped" not in result["warnings"]
        assert result["channel"] == "chat"


class TestEscapeMarkdownV2:
    """Telegram MarkdownV2 escape utility — chars per
    https://core.telegram.org/bots/api#markdownv2-style.
    """

    @pytest.mark.parametrize(
        "char",
        ["_", "*", "[", "]", "(", ")", "~", "`", ">", "#", "+", "-", "=", "|", "{", "}", ".", "!"],
    )
    def test_escapes_special_chars(self, char: str) -> None:
        text = f"hola{char}mundo"
        escaped = escape_markdown_v2(text)
        assert escaped == f"hola\\{char}mundo"

    def test_escapes_backslash(self) -> None:
        assert escape_markdown_v2("a\\b") == "a\\\\b"

    def test_idempotent_no_special_chars(self) -> None:
        assert escape_markdown_v2("hola mundo") == "hola mundo"

    def test_handles_unicode_safe(self) -> None:
        # Spanish accents NOT in escape set (they aren't markdown special).
        assert escape_markdown_v2("ñoño á é í ó ú") == "ñoño á é í ó ú"

    def test_escape_for_full_message(self) -> None:
        msg = "Tu plan para hoy:\n- Item 1.\n- Item 2!"
        escaped = escape_markdown_v2(msg)
        # Each `-`, `.`, `!` escaped; `:` is NOT in the escape list.
        assert "\\-" in escaped
        assert "\\." in escaped
        assert "\\!" in escaped
        assert ":" in escaped  # plain colon kept
