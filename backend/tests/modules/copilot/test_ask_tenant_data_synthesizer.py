"""F5 — synthesizer tests (LLM stubbed, channel-aware)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from src.modules.copilot.application.tools.ask_tenant_data.synthesizer import (
    SUPPORTED_OUTPUT_CHANNELS,
    synthesize_answer,
)
from src.modules.copilot.domain.ports import DataQueryPlan, DataQueryResult


@dataclass
class _StubResponse:
    content: str


class _StubLLM:
    def __init__(self, text: str) -> None:
        self.text = text
        self.last_messages: list[Any] = []

    def invoke(self, messages: list[Any]) -> _StubResponse:
        self.last_messages = messages
        return _StubResponse(content=self.text)


@pytest.mark.asyncio
async def test_synthesizer_uses_stub_llm_text() -> None:
    plan = DataQueryPlan(kind="lead_count", filters={})
    result = DataQueryResult(rows=[], metadata={"count": 12})
    llm = _StubLLM("Esta semana te escribieron 12 personas.")
    answer = await synthesize_answer(
        question="cuántas personas escribieron",
        plan=plan,
        result=result,
        flags={},
        output_channel="chat",
        llm=llm,
    )
    assert "12" in answer
    assert llm.last_messages, "synthesizer should call the LLM"


@pytest.mark.asyncio
async def test_synthesizer_short_circuits_on_empty_window_without_llm() -> None:
    """Zero-result with window emits suggestion deterministically — saves an LLM call."""
    plan = DataQueryPlan(kind="lead_count", filters={"since": "x", "until": "y"})
    result = DataQueryResult(rows=[], metadata={"count": 0})
    llm = _StubLLM("LLM should not be called")

    answer = await synthesize_answer(
        question="cuántas personas escribieron esta semana",
        plan=plan,
        result=result,
        flags={"empty_window": True},
        output_channel="chat",
        llm=llm,
    )
    assert llm.last_messages == [], "no LLM call expected for deterministic empty path"
    assert any(token in answer.lower() for token in ("0", "ninguna", "no encontré"))


@pytest.mark.asyncio
async def test_synthesizer_short_circuits_on_unknown_intent() -> None:
    plan = DataQueryPlan(kind="unknown", filters={})
    result = DataQueryResult()
    llm = _StubLLM("ignored")
    answer = await synthesize_answer(
        question="qué tal el clima",
        plan=plan,
        result=result,
        flags={},
        output_channel="chat",
        llm=llm,
    )
    assert llm.last_messages == []
    assert "no entendí" in answer.lower() or "reformularla" in answer.lower()


@pytest.mark.asyncio
async def test_synthesizer_passes_channel_hint_in_system_prompt() -> None:
    plan = DataQueryPlan(kind="lead_count", filters={})
    result = DataQueryResult(rows=[], metadata={"count": 5})
    llm = _StubLLM("Te escribieron 5.")
    await synthesize_answer(
        question="cuántas",
        plan=plan,
        result=result,
        flags={},
        output_channel="whatsapp",
        llm=llm,
    )
    system_msg = llm.last_messages[0]
    assert "whatsapp" in str(getattr(system_msg, "content", "")).lower()


def test_supported_output_channels_includes_chat_and_whatsapp() -> None:
    assert "chat" in SUPPORTED_OUTPUT_CHANNELS
    assert "whatsapp" in SUPPORTED_OUTPUT_CHANNELS


@pytest.mark.asyncio
async def test_synthesizer_falls_back_to_chat_on_unknown_channel() -> None:
    plan = DataQueryPlan(kind="lead_count", filters={})
    result = DataQueryResult(rows=[], metadata={"count": 5})
    llm = _StubLLM("Te escribieron 5.")
    await synthesize_answer(
        question="cuántas",
        plan=plan,
        result=result,
        flags={},
        output_channel="some-unknown-channel",
        llm=llm,
    )
    system_msg = llm.last_messages[0]
    # Falls back to chat — must NOT mention whatsapp / email / sms.
    content = str(getattr(system_msg, "content", "")).lower()
    assert "whatsapp" not in content
    assert "email" not in content
