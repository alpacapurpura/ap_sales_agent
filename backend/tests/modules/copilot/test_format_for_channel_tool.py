"""F7 — ``format_for_channel`` tool tests.

The tool is a deterministic post-processor: takes raw content + channel id,
applies the channel's spec (markdown / emoji / max_chars) and returns the
adjusted text plus a list of warnings describing what was modified.

No LLM call. Composes with the synthesizer (which already knows the spec via
prompt) for a "trust but verify" final pass — and stands alone when the user
wants a simple "give me this text ready for WhatsApp".
"""

from __future__ import annotations

import json

import pytest

from src.modules.copilot.application.tools.format_for_channel import (
    format_for_channel,
    format_for_channel_impl,
)
from src.modules.copilot.domain.output_channels import (
    ChannelFormat,
    register_channel,
    reset_registry_for_tests,
)


@pytest.fixture(autouse=True)
def _reset_registry():
    reset_registry_for_tests()
    yield
    reset_registry_for_tests()


def test_chat_passes_through_markdown_and_emoji() -> None:
    text = "**Hola** 👋 esta es _una_ respuesta con [link](https://x.com)."
    result = format_for_channel_impl(content=text, channel_id="chat")
    assert result["channel"] == "chat"
    assert result["content"] == text
    assert result["warnings"] == []


def test_whatsapp_strips_standard_markdown() -> None:
    text = "**Promo activa** — visita [la página](https://nico.lat) para ver _detalles_."
    result = format_for_channel_impl(content=text, channel_id="whatsapp")
    assert result["channel"] == "whatsapp"
    assert "**" not in result["content"]
    assert "[la página](" not in result["content"]
    assert "https://nico.lat" in result["content"], "URLs should be preserved as plain text"
    assert "markdown_stripped" in result["warnings"]


def test_whatsapp_keeps_emojis() -> None:
    result = format_for_channel_impl(
        content="Hola 👋, ¿cómo estás? 🎯",
        channel_id="whatsapp",
    )
    assert "👋" in result["content"]
    assert "🎯" in result["content"]
    assert "emoji_stripped" not in result["warnings"]


def test_sms_strips_emoji() -> None:
    result = format_for_channel_impl(
        content="Hola 👋, hoy 50% off 🎉 link.io/x",
        channel_id="sms",
    )
    assert "👋" not in result["content"]
    assert "🎉" not in result["content"]
    assert "emoji_stripped" in result["warnings"]


def test_sms_truncates_to_160() -> None:
    long = "Promo limitada. " * 20  # ~320 chars
    result = format_for_channel_impl(content=long, channel_id="sms")
    assert len(result["content"]) <= 160
    assert "truncated" in result["warnings"]


def test_truncation_uses_ellipsis_marker() -> None:
    long = "x" * 500
    result = format_for_channel_impl(content=long, channel_id="sms")
    assert result["content"].endswith("…")


def test_unknown_channel_falls_back_to_chat() -> None:
    text = "**bold** stays"
    result = format_for_channel_impl(content=text, channel_id="not-a-channel")
    assert result["channel"] == "chat"
    assert result["content"] == text


def test_result_includes_char_count_and_label() -> None:
    result = format_for_channel_impl(content="hola", channel_id="whatsapp")
    assert result["char_count"] == len(result["content"])
    assert result["label"] == "WhatsApp"


def test_telegram_keeps_markdown() -> None:
    """Telegram supports MarkdownV2 — markdown should pass through."""
    text = "*bold* y _italic_ con [link](https://x.com)"
    result = format_for_channel_impl(content=text, channel_id="telegram")
    assert "*bold*" in result["content"]
    assert "[link](https://x.com)" in result["content"]
    assert "markdown_stripped" not in result["warnings"]


def test_provider_registered_channel_works() -> None:
    register_channel(
        ChannelFormat(
            id="discord",
            label_es="Discord",
            max_chars=2000,
            emoji_allowed=True,
            line_break_style="\n\n",
            markdown_allowed=True,
            structure_hint="Discord — markdown OK, hasta 2000 chars.",
        )
    )
    result = format_for_channel_impl(content="**hola**", channel_id="discord")
    assert result["channel"] == "discord"
    assert "**hola**" in result["content"]


@pytest.mark.asyncio
async def test_tool_callable_returns_json_string() -> None:
    """The LangChain ``@tool`` wrapper exposes the impl. Ensure the callable
    interface is reachable and returns parseable JSON."""
    raw = await format_for_channel.ainvoke({"content": "**hola**", "channel_id": "whatsapp"})
    payload = json.loads(raw)
    assert payload["channel"] == "whatsapp"
    assert "warnings" in payload


def test_strip_markdown_handles_headings_and_lists() -> None:
    text = "# Titulo\n## Sub\n- item 1\n- item 2\n> quote\n```code```"
    result = format_for_channel_impl(content=text, channel_id="sms")
    assert "#" not in result["content"]
    assert "```" not in result["content"]


def test_empty_content_produces_empty_output_with_no_warnings() -> None:
    result = format_for_channel_impl(content="", channel_id="whatsapp")
    assert result["content"] == ""
    assert result["warnings"] == []
    assert result["char_count"] == 0
