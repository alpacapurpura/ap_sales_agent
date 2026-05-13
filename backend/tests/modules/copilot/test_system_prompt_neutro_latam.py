"""TP6 / regla 11 — system prompt + synthesizer fallback strings must
explicitly forbid voseo (Spanish neutro LatAm).

Origin: TP6 matrix run 2026-04-26 surfaced AGENT (Kimi K2.6) emitting
voseo (``podés / Tenés / Empezá / Querés``) across 5 of 16 channel
scenarios despite ``copilot_system_static.j2`` saying only ``Tuteas al
usuario``. The phrase ``tuteas`` is interpreted differently across
LatAm — explicit "sin voseo" + a few canonical examples are required
to keep the AGENT in neutro tuteo.

These tests guard the invariant going forward: if a future edit drops
the explicit prohibition or reintroduces voseo in the synthesizer
fallback strings, CI fails.
"""

from __future__ import annotations

import re

import pytest

from luana_core_copilot.application.tools.ask_tenant_data.synthesizer import (
    _empty_window_reply,
    _unknown_intent_reply,
)
from luana_core_platform.workers.brand_summary_regen import _VOSEO_RE


def _render(template_name: str, **ctx: object) -> str:
    """Render a copilot j2 template via the same loader the orchestrator uses."""
    from luana_core_copilot.infrastructure.prompts.base import prompt_loader

    return prompt_loader.render(template_name, **ctx)


class TestSystemStaticTemplateForbidsVoseo:
    """The base behavior template must explicitly disallow voseo."""

    def test_static_template_mentions_neutro_explicitly(self) -> None:
        rendered = _render("copilot_system_static")
        # Look for canonical phrases used in the regla 11 doc
        # so the AGENT cannot misread ``tuteas`` as Argentine voseo.
        assert "neutro" in rendered.lower(), "system prompt must mention 'neutro'"
        assert "voseo" in rendered.lower(), "system prompt must mention 'voseo' (forbidden)"

    def test_static_template_lists_canonical_neutro_examples(self) -> None:
        rendered = _render("copilot_system_static")
        # At least one canonical pair tú/tienes/puedes vs vos/tenés/podés
        # must appear so the model has a concrete contrast to anchor on.
        canonical_neutro = re.search(r"\b(tú|tienes|puedes|quieres)\b", rendered, re.IGNORECASE)
        canonical_voseo = re.search(r"\b(vos|tenés|podés|querés)\b", rendered, re.IGNORECASE)
        assert canonical_neutro is not None, "system prompt must show a neutro example (tú / tienes / puedes / quieres)"
        assert canonical_voseo is not None, (
            "system prompt must contrast with a voseo example (vos / tenés / podés / querés) so "
            "the model recognises what to avoid"
        )

    def test_static_template_body_has_no_voseo(self) -> None:
        """Even examples must not be the verb forms — only inside a 'NO'/'EVITA' contrast."""
        rendered = _render("copilot_system_static")
        # Strip lines that contain the explicit prohibition contrast
        # (those legitimately list voseo terms as forbidden examples).
        prohibition_markers = ("evita", "no usar", "no uses", "prohibido", "no:", "incorrecto", "✗")
        body_lines = [
            line for line in rendered.splitlines() if not any(marker in line.lower() for marker in prohibition_markers)
        ]
        body = "\n".join(body_lines)
        match = _VOSEO_RE.search(body)
        assert match is None, f"system prompt body contains voseo outside a prohibition contrast: {match.group()!r}"


class TestToolsHintAdvertisesChannelFormatter:
    """When ``format_for_channel`` is bound, the tools hint must brief the
    AGENT on when to call it. Otherwise it never picks the tool and the
    output overflows SMS / leaves WhatsApp markdown noise."""

    def test_tools_hint_mentions_format_for_channel_when_available(self) -> None:
        rendered = _render(
            "copilot_system_tools_hint",
            available_tools=["format_for_channel", "get_module_data"],
        )
        assert "format_for_channel" in rendered, "tools hint must name the channel formatter"
        # Must explain when to use it so the AGENT picks it up on its own.
        assert any(keyword in rendered.lower() for keyword in ("whatsapp", "sms", "canal", "email")), (
            "tools hint must mention at least one canonical channel keyword"
        )


class TestSynthesizerFallbackStringsAreNeutro:
    """A2 sweep — static fallback strings used when LLM cannot run."""

    @pytest.mark.parametrize("channel", ["chat", "whatsapp", "email", "sms"])
    def test_unknown_intent_reply_has_no_voseo(self, channel: str) -> None:
        text = _unknown_intent_reply(channel)
        match = _VOSEO_RE.search(text)
        assert match is None, f"unknown_intent_reply({channel!r}) contains voseo: {match.group()!r}"

    @pytest.mark.parametrize("channel", ["chat", "whatsapp", "email", "sms"])
    def test_empty_window_reply_has_no_voseo(self, channel: str) -> None:
        from luana_core_copilot.domain.ports import DataQueryPlan

        plan = DataQueryPlan(kind="lead_count", filters={})
        text = _empty_window_reply(plan, channel)
        match = _VOSEO_RE.search(text)
        assert match is None, f"empty_window_reply({channel!r}) contains voseo: {match.group()!r}"
