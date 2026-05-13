"""S5 — channel intent detector tests (shared).

Mirror of copilot's F7 ``test_channel_intent_detector.py`` apuntando al nuevo
home cross-agent. Sales_agent puede consumir cuando el lead dice "mándame por
WhatsApp" — útil para forzar `format_for_channel` en pipelines.

# [SALES-AGENT-CHANNEL-REGISTRY-S5]
"""

from __future__ import annotations

import pytest

from luana_core_channels.intent_detector import (
    ChannelIntent,
    detect_channel_in_user_msg,
    detect_channel_intent,
)


class TestDetectChannelIntent:
    @pytest.mark.parametrize(
        ("user_msg", "expected"),
        [
            ("¿Me lo mandas por WhatsApp?", "whatsapp"),
            ("dame el contenido para Instagram DM", "instagram_dm"),
            ("armame un mensaje para Telegram", "telegram"),
            ("preferiría un correo electrónico", "email"),
            ("envíame un SMS", "sms"),
            ("quiero un audio", "voice"),
        ],
    )
    def test_recognises_canonical_keywords(self, user_msg: str, expected: str) -> None:
        intent = detect_channel_intent(user_msg)
        assert intent is not None
        assert intent.channel == expected

    def test_returns_none_when_no_keyword(self) -> None:
        assert detect_channel_intent("hola, ¿cómo estás?") is None

    def test_returns_none_for_empty(self) -> None:
        assert detect_channel_intent("") is None
        assert detect_channel_intent(None) is None

    def test_url_does_not_match_whatsapp(self) -> None:
        """AC7 — `whatsapp.com` and `https://wa.me/...` must NOT trigger."""
        assert detect_channel_intent("entra a https://whatsapp.com/business") is None
        assert detect_channel_intent("revisa wa.me/123456789") is None

    def test_url_does_not_match_telegram(self) -> None:
        assert detect_channel_intent("vé a t.me/foo o telegram.org/about") is None

    def test_intent_includes_matched_span(self) -> None:
        intent = detect_channel_intent("envíame por WhatsApp")
        assert isinstance(intent, ChannelIntent)
        assert intent.matched_span[1] > intent.matched_span[0]
        assert intent.label == "WhatsApp"


class TestLegacyStringApi:
    def test_detect_channel_in_user_msg_returns_id(self) -> None:
        assert detect_channel_in_user_msg("mándame por whatsapp") == "whatsapp"

    def test_detect_channel_in_user_msg_returns_none(self) -> None:
        assert detect_channel_in_user_msg("hola") is None
