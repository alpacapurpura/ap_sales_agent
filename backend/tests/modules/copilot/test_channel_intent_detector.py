"""FP2 — channel intent detection middleware (B24).

Detects when the user explicitly asks for output formatted for a specific
channel (WhatsApp / email / SMS / Instagram DM / Telegram / voice) so the
orchestrator can inject a system-prompt hint forcing the AGENT to invoke
``format_for_channel`` before finalising the turn. Replaces the lossy
``detect_channel_in_user_msg`` heuristic that lived inside
``output_sanitizer`` (post-output band-aid) with a richer dataclass that
carries channel id + label + match span, and adds AC7 false-positive guard
against URLs (``whatsapp.com``, ``https://wa.me/...``).
"""

from __future__ import annotations

import pytest

from src.modules.copilot.application.orchestrator.channel_intent_detector import (
    ChannelIntent,
    detect_channel_intent,
)


class TestChannelIntentDetectionBasic:
    """AC1-AC3 — channel keyword detection per channel."""

    @pytest.mark.parametrize(
        ("msg", "expected_channel"),
        [
            # AC1 — WhatsApp variants.
            ("armame copy para WhatsApp", "whatsapp"),
            ("dame esto para whatsapp", "whatsapp"),
            ("manda WA literal sin headers", "whatsapp"),
            ("formato wa por favor", "whatsapp"),
            # AC2 — Email variants.
            ("redactá un email de bienvenida", "email"),
            ("armame correo para los inscriptos", "email"),
            ("formato gmail para invitar", "email"),
            ("escribe un correo electrónico", "email"),
            # AC3 — SMS variants.
            ("armame un SMS para promocionar", "sms"),
            ("redacta mensaje de texto corto", "sms"),
            ("dame esto como sms", "sms"),
            # Telegram.
            ("para Telegram, hazme un resumen", "telegram"),
            # Instagram DM.
            ("formato Instagram DM por favor", "instagram_dm"),
            ("hazme un IG DM", "instagram_dm"),
            # Voice.
            ("dame la respuesta para audio", "voice"),
            ("formato voz para grabar", "voice"),
        ],
    )
    def test_detects_channel(self, msg: str, expected_channel: str) -> None:
        intent = detect_channel_intent(msg)
        assert intent is not None, f"expected detection for {msg!r}"
        assert intent.channel == expected_channel
        assert intent.label  # human label populated


class TestChannelIntentNoIntent:
    """AC4 — bare 'copy paste' or unrelated requests return None."""

    @pytest.mark.parametrize(
        "msg",
        [
            "dame un headline cualquiera",
            "explica mejor por favor",
            "armame algo para copy paste",  # AC4: no specific channel
            "hazme una copia y pega",  # AC4 variant
            "qué es un buen subject line",
            "",
        ],
    )
    def test_no_intent(self, msg: str) -> None:
        assert detect_channel_intent(msg) is None


class TestChannelIntentCaseAndAccent:
    """AC6 — match is case + accent insensitive across all channels."""

    @pytest.mark.parametrize(
        ("msg", "expected_channel"),
        [
            ("WHATSAPP", "whatsapp"),
            ("WhatsApp", "whatsapp"),
            ("whatsapp", "whatsapp"),
            ("WA", "whatsapp"),
            ("wa", "whatsapp"),
            ("EMAIL", "email"),
            ("Email", "email"),
            ("email", "email"),
            ("SMS", "sms"),
            ("Sms", "sms"),
            ("sms", "sms"),
            ("TELEGRAM", "telegram"),
            ("Telegram", "telegram"),
            ("INSTAGRAM DM", "instagram_dm"),
            ("instagram dm", "instagram_dm"),
            ("Instagram_DM", "instagram_dm"),
        ],
    )
    def test_case_variations(self, msg: str, expected_channel: str) -> None:
        intent = detect_channel_intent(msg)
        assert intent is not None
        assert intent.channel == expected_channel

    @pytest.mark.parametrize(
        "typo",
        [
            "Wassap",
            "WhatsAp",
            "Whasap",
            "WhatzApp",
        ],
    )
    def test_typos_do_not_match(self, typo: str) -> None:
        # Detection MUST NOT be too loose — typos return None so we don't
        # silently bind the formatter on a misspelt request.
        assert detect_channel_intent(typo) is None


class TestChannelIntentURLFalsePositive:
    """AC7 — URL mentions of a channel domain are NOT channel intent."""

    @pytest.mark.parametrize(
        "msg",
        [
            "mira esta landing https://whatsapp.com/landing",
            "una landing en whatsapp.com",
            "el link es https://wa.me/12345",
            "comparti https://www.whatsapp.com/business",
            "abre gmail.com en otra pestaña",
            "ver telegram.org documentation",
            "https://web.telegram.org/k/",
            "instagram.com/empresa",
            "el url sms.com.au",
            "https://t.me/canal",
        ],
    )
    def test_url_is_not_intent(self, msg: str) -> None:
        intent = detect_channel_intent(msg)
        assert intent is None, f"AC7 false positive — msg {msg!r} returned intent {intent!r}"

    def test_url_plus_channel_intent_in_same_msg_detects_intent(self) -> None:
        # Mixed: URL mentions whatsapp.com but the user also asks for WA copy.
        # The intent SHOULD be detected because there's a real ask.
        intent = detect_channel_intent(
            "armame copy para WhatsApp inspirado en https://whatsapp.com/business",
        )
        assert intent is not None
        assert intent.channel == "whatsapp"


class TestChannelIntentDataclass:
    """ChannelIntent contract — fields + immutability."""

    def test_contract_fields(self) -> None:
        intent = detect_channel_intent("armame copy WhatsApp")
        assert isinstance(intent, ChannelIntent)
        assert intent.channel == "whatsapp"
        assert intent.label  # human label
        assert intent.matched_span  # (start, end) of the keyword
        assert isinstance(intent.matched_span, tuple)
        assert len(intent.matched_span) == 2

    def test_dataclass_frozen(self) -> None:
        intent = detect_channel_intent("dame email")
        assert intent is not None
        with pytest.raises((AttributeError, Exception)):
            intent.channel = "sms"  # type: ignore[misc]


class TestChannelIntentBackwardsCompat:
    """Sanitizer's old ``detect_channel_in_user_msg`` keeps working via re-export."""

    @pytest.mark.parametrize(
        ("msg", "expected"),
        [
            ("Armame un SMS para invitar al webinar", "sms"),
            ("dame esto para WhatsApp", "whatsapp"),
            ("redactá un email de bienvenida", "email"),
            ("para Telegram, ¿podés hacerme un resumen?", "telegram"),
            ("formato Instagram DM por favor", "instagram_dm"),
            ("Hazlo para audio (voz)", "voice"),
            ("dime un headline cualquiera", None),
        ],
    )
    def test_legacy_string_api(self, msg: str, expected: str | None) -> None:
        from src.modules.copilot.application.orchestrator.output_sanitizer import (
            detect_channel_in_user_msg,
        )

        assert detect_channel_in_user_msg(msg) == expected
