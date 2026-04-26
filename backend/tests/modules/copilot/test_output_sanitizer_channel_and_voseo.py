"""TP6 — output sanitizer last-line-of-defense for voseo + channel format.

Two safety nets added in TP6 because the AGENT (Kimi K2.6 thinking-disabled)
ignores the system prompt rules in a non-trivial fraction of turns:

1. **Voseo autocorrect** — when the AGENT lapses into voseo (``podés`` /
   ``Querés`` / ``mirá``) despite the explicit "sin voseo" rule, the
   sanitizer rewrites to neutro tuteo (``puedes`` / ``Quieres`` / ``mira``).

2. **Channel format enforcement** — when the user message asks for
   output for a non-chat channel (``"para WhatsApp"`` / ``"un SMS de…"``)
   and the AGENT's text exceeds the channel's ``max_chars``, the
   sanitizer applies ``format_for_channel_impl`` deterministically so
   the response is copy-paste safe.

Both functions are pure + idempotent; they run after the LLM emits its
final block but before SSE ``block_end``.
"""

from __future__ import annotations

import pytest

from src.modules.copilot.application.orchestrator.output_sanitizer import (
    correct_voseo_in_text,
    detect_channel_in_user_msg,
    enforce_channel_format_if_needed,
)


class TestVoseoAutocorrect:
    @pytest.mark.parametrize(
        ("voseo", "neutro"),
        [
            ("podés", "puedes"),
            ("querés", "quieres"),
            ("tenés", "tienes"),
            ("sabés", "sabes"),
            ("hacés", "haces"),
            ("decís", "dices"),
            ("mirá", "mira"),
            ("dejá", "deja"),
            ("escribí", "escribe"),
            ("usá", "usa"),
            ("acordate", "recuerda"),
            ("fijate", "ten en cuenta"),
        ],
    )
    def test_lowercase_voseo_to_neutro(self, voseo: str, neutro: str) -> None:
        text = f"Si {voseo} ayuda, dime."
        out = correct_voseo_in_text(text)
        assert voseo not in out, f"voseo {voseo!r} still present in {out!r}"
        assert neutro in out, f"expected {neutro!r} in {out!r}"

    @pytest.mark.parametrize(
        ("voseo_cap", "neutro_cap"),
        [
            ("Podés", "Puedes"),
            ("Querés", "Quieres"),
            ("Tenés", "Tienes"),
            ("Mirá", "Mira"),
        ],
    )
    def test_capitalized_voseo_preserves_case(self, voseo_cap: str, neutro_cap: str) -> None:
        out = correct_voseo_in_text(f"{voseo_cap} mi sugerencia.")
        assert out.startswith(neutro_cap), f"expected case-preserved replacement, got {out!r}"

    def test_idempotent(self) -> None:
        text = "Si quieres ayuda, dime. Tienes opciones."
        assert correct_voseo_in_text(text) == text

    def test_does_not_break_castellano_vosotros(self) -> None:
        text = "Vosotros podéis pasar."
        assert correct_voseo_in_text(text) == text

    def test_empty(self) -> None:
        assert correct_voseo_in_text("") == ""


class TestDetectChannelInUserMsg:
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
    def test_detection(self, msg: str, expected: str | None) -> None:
        assert detect_channel_in_user_msg(msg) == expected


class TestEnforceChannelFormatIfNeeded:
    def test_sms_long_text_gets_truncated_to_160(self) -> None:
        text = "Promo limitada en cursos de marketing. " * 20  # ~780 chars
        user_msg = "Armame un SMS para promocionar"
        out = enforce_channel_format_if_needed(text, user_msg)
        assert len(out) <= 160

    def test_whatsapp_strips_standard_markdown_when_user_asked(self) -> None:
        text = "**Promo activa** revisa [los detalles](https://x.com)"
        user_msg = "dame esto para WhatsApp"
        out = enforce_channel_format_if_needed(text, user_msg)
        assert "**" not in out
        assert "[los detalles](" not in out

    def test_chat_passthrough_when_no_channel_in_user_msg(self) -> None:
        text = "**Hola** 👋 esta es _una_ respuesta con [link](https://x.com)."
        out = enforce_channel_format_if_needed(text, "explica mejor por favor")
        assert out == text

    def test_short_sms_passthrough(self) -> None:
        text = "Webinar jueves 7pm. Inscribete: link.io/x"
        user_msg = "armame un SMS"
        out = enforce_channel_format_if_needed(text, user_msg)
        assert out == text

    def test_no_user_msg_passthrough(self) -> None:
        text = "**Hola** quien sabe"
        out = enforce_channel_format_if_needed(text, "")
        assert out == text


class TestSanitizerOrchestration:
    """``sanitize_assistant_text`` must compose all 3 safety nets in order:
    JSON strip → voseo correction → channel enforcement."""

    def test_signature_accepts_user_msg(self) -> None:
        from src.modules.copilot.application.orchestrator.output_sanitizer import (
            sanitize_assistant_text,
        )

        text_in = "Para vos, podés probar esto."
        out = sanitize_assistant_text(text_in, user_msg="qué opinas?")
        assert "podés" not in out
        assert "puedes" in out

    def test_sms_voseo_combo(self) -> None:
        from src.modules.copilot.application.orchestrator.output_sanitizer import (
            sanitize_assistant_text,
        )

        text_in = "Hola! Si querés inscribirte, mirá el link " + "x" * 200
        out = sanitize_assistant_text(text_in, user_msg="armame un SMS de invitacion")
        assert len(out) <= 160
        assert "querés" not in out
        assert "mirá" not in out
