"""FP2 — channel-format auto-trigger integration (B24).

Validates that:

* AC1-AC3 — when the user message names a channel (whatsapp / email / sms),
  ``state["channel_intent"]`` is populated by the orchestrator before the
  graph is built.
* The deep-agent system prompt receives an explicit instruction forcing
  ``format_for_channel`` invocation.
* AC4 — bare "copy paste" requests without a channel keyword leave
  ``state["channel_intent"]`` as ``None`` and the prompt does NOT include
  the channel hint.
* AC7 — URL mentions of ``whatsapp.com`` do NOT trigger the hint.

These tests stub ``build_system_prompt`` so we exercise the wiring (intent
detection → state mutation → prompt suffix) without an LLM call. End-to-end
validation that the AGENT actually invokes the tool lives in the live curl
+ trace event SQL probe section of the FP2 results doc.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from langchain_core.messages import HumanMessage

from src.modules.copilot.application.orchestrator.channel_intent_detector import (
    detect_channel_intent,
)
from src.modules.copilot.application.orchestrator.deep_agent import (
    _build_combined_system_prompt,
)
from src.modules.copilot.application.orchestrator.state import (
    create_initial_copilot_state,
)


@pytest.fixture(autouse=True)
def _stub_system_prompt(monkeypatch):
    """Hermetic: skip the DB-touching ``build_system_prompt``."""
    monkeypatch.setattr(
        "src.modules.copilot.application.orchestrator.deep_agent.build_system_prompt",
        lambda _state: "Eres el Copilot de Nicolify.",
    )


def _state_with_message(msg: str) -> dict:
    """Mirror ``CopilotOrchestrator._prepare_conversation`` channel intent wiring."""
    state = create_initial_copilot_state(
        user_id=uuid4(),
        tenant_id=uuid4(),
        conversation_id=str(uuid4()),
        client_context={"current_route": "/brand-studio/identity"},
    )
    state["messages"] = [HumanMessage(content=msg)]
    intent = detect_channel_intent(msg)
    state["channel_intent"] = (
        {
            "channel": intent.channel,
            "label": intent.label,
            "matched_span": list(intent.matched_span),
        }
        if intent is not None
        else None
    )
    return state


class TestChannelIntentInState:
    """AC1-AC3 — intent populated for channel-bearing messages."""

    @pytest.mark.parametrize(
        ("msg", "expected_channel"),
        [
            ("armame copy para WhatsApp", "whatsapp"),
            ("dame esto para email", "email"),
            ("redacta un SMS de invitación", "sms"),
            ("para Telegram dame el resumen", "telegram"),
            ("formato Instagram DM", "instagram_dm"),
            ("para audio", "voice"),
        ],
    )
    def test_intent_populated(self, msg: str, expected_channel: str) -> None:
        state = _state_with_message(msg)
        assert state["channel_intent"] is not None
        assert state["channel_intent"]["channel"] == expected_channel

    def test_intent_none_for_unrelated_msg(self) -> None:
        state = _state_with_message("dame ideas para el headline")
        assert state["channel_intent"] is None


class TestSystemPromptHintInjection:
    """AC1-AC3 — prompt suffix carries the format_for_channel instruction."""

    @pytest.mark.parametrize(
        ("msg", "channel_id", "label"),
        [
            ("armame copy para WhatsApp", "whatsapp", "WhatsApp"),
            ("dame esto para email", "email", "Email"),
            ("redacta un SMS de invitación", "sms", "SMS"),
            ("para Telegram dame el resumen", "telegram", "Telegram"),
        ],
    )
    def test_prompt_includes_channel_hint(self, msg: str, channel_id: str, label: str) -> None:
        state = _state_with_message(msg)
        prompt = _build_combined_system_prompt(state)
        assert "format_for_channel" in prompt
        assert f"channel_id='{channel_id}'" in prompt
        assert f"Canal de salida: {label}" in prompt
        assert "OBLIGATORIA" in prompt  # mandatory wording forces tool invocation

    def test_prompt_does_not_include_hint_when_no_intent(self) -> None:
        """AC4 — no channel keyword ⇒ no hint, prompt baseline unchanged."""
        state = _state_with_message("dame un headline cualquiera")
        prompt = _build_combined_system_prompt(state)
        assert "Canal de salida" not in prompt
        assert "format_for_channel" not in prompt

    def test_hint_is_voseo_free(self) -> None:
        """Regla 11 — hint inyectado debe ser tuteo neutro LatAm."""
        state = _state_with_message("armame copy para WhatsApp")
        prompt = _build_combined_system_prompt(state)
        # Sample voseo tokens that would fail B23-TP11 compliance.
        for voseo in ("producilo", "armá", "dale", "fijate", "mirá", "podés"):
            assert voseo not in prompt, f"voseo {voseo!r} leaked into channel hint"


class TestURLFalsePositive:
    """AC7 — channel URLs do NOT trigger the hint."""

    @pytest.mark.parametrize(
        "msg",
        [
            "una landing en https://whatsapp.com/business",
            "abre gmail.com en otra pestaña",
            "copia el link https://wa.me/12345",
            "telegram.org tiene buen docs",
        ],
    )
    def test_url_msg_leaves_intent_none(self, msg: str) -> None:
        state = _state_with_message(msg)
        assert state["channel_intent"] is None
        prompt = _build_combined_system_prompt(state)
        assert "Canal de salida" not in prompt


class TestHintIdempotency:
    """The hint builder is pure — same state produces same prompt suffix."""

    def test_two_calls_same_output(self) -> None:
        state = _state_with_message("armame copy WhatsApp")
        prompt_a = _build_combined_system_prompt(state)
        prompt_b = _build_combined_system_prompt(state)
        assert prompt_a == prompt_b

    def test_missing_intent_key_is_safe(self) -> None:
        state = create_initial_copilot_state(
            user_id=uuid4(),
            tenant_id=uuid4(),
            conversation_id=str(uuid4()),
        )
        # Simulate a legacy state dict missing ``channel_intent`` entirely.
        state.pop("channel_intent", None)
        # Should not KeyError + should not inject the hint.
        prompt = _build_combined_system_prompt(state)
        assert "Canal de salida" not in prompt
