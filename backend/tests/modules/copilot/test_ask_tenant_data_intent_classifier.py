"""F5 — intent_classifier tests (LLM stubbed)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pytest

from src.modules.copilot.application.tools.ask_tenant_data.intent_classifier import (
    IntentResult,
    classify_intent,
)


@dataclass
class _StubResponse:
    content: str


class _StubLLM:
    """LLM stub returning a fixed JSON payload, recording the messages."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.last_messages: list[Any] = []

    def invoke(self, messages: list[Any]) -> _StubResponse:
        self.last_messages = messages
        return _StubResponse(content=json.dumps(self.payload))


@pytest.mark.asyncio
async def test_classify_offer_lookup_with_name_query() -> None:
    llm = _StubLLM(
        {
            "kind": "offer_lookup",
            "name_query": "propósito y prosperidad",
            "period_phrase": None,
            "channel": None,
            "confidence": 0.92,
        },
    )
    result = await classify_intent(
        "dame un resumen del programa propósito y prosperidad",
        llm=llm,
    )
    assert isinstance(result, IntentResult)
    assert result.kind == "offer_lookup"
    assert result.name_query == "propósito y prosperidad"
    assert result.period_phrase is None
    assert result.confidence == pytest.approx(0.92)


@pytest.mark.asyncio
async def test_classify_lead_count_with_period_and_channel() -> None:
    llm = _StubLLM(
        {
            "kind": "lead_count",
            "name_query": None,
            "period_phrase": "esta semana",
            "channel": "whatsapp",
            "confidence": 0.85,
        },
    )
    result = await classify_intent(
        "cuántas personas escribieron por whatsapp esta semana",
        llm=llm,
    )
    assert result.kind == "lead_count"
    assert result.period_phrase == "esta semana"
    assert result.channel == "whatsapp"


@pytest.mark.asyncio
async def test_classify_conversation_count() -> None:
    llm = _StubLLM(
        {
            "kind": "conversation_count",
            "name_query": None,
            "period_phrase": "mes pasado",
            "channel": None,
            "confidence": 0.8,
        },
    )
    result = await classify_intent(
        "cuántas conversaciones tuve el mes pasado",
        llm=llm,
    )
    assert result.kind == "conversation_count"
    assert result.period_phrase == "mes pasado"


@pytest.mark.asyncio
async def test_classify_unknown_when_llm_returns_unrecognised_kind() -> None:
    llm = _StubLLM(
        {
            "kind": "no-existe",
            "name_query": None,
            "period_phrase": None,
            "channel": None,
            "confidence": 0.4,
        },
    )
    result = await classify_intent("recomendame un postre", llm=llm)
    assert result.kind == "unknown"
    assert result.confidence < 0.5


@pytest.mark.asyncio
async def test_classify_handles_garbled_llm_output() -> None:
    """Non-JSON / partial output → unknown intent, not exception."""

    class _GarbledLLM:
        def invoke(self, messages: list[Any]) -> _StubResponse:
            return _StubResponse(content="Sure, here is some text without json.")

    result = await classify_intent("dummy", llm=_GarbledLLM())
    assert result.kind == "unknown"
    assert result.confidence == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_classify_strips_voseo_normalises_phrase() -> None:
    llm = _StubLLM(
        {
            "kind": "lead_count",
            "name_query": None,
            "period_phrase": "esta semana",
            "channel": "telegram",
            "confidence": 0.9,
        },
    )
    result = await classify_intent("cuantos leads vinieron esta semana?", llm=llm)
    assert result.raw_question == "cuantos leads vinieron esta semana?"
    assert result.kind == "lead_count"


@pytest.mark.asyncio
async def test_classify_caps_confidence_in_range() -> None:
    llm = _StubLLM(
        {
            "kind": "offer_lookup",
            "name_query": "x",
            "period_phrase": None,
            "channel": None,
            "confidence": 1.5,  # out of range
        },
    )
    result = await classify_intent("dummy", llm=llm)
    assert 0.0 <= result.confidence <= 1.0
