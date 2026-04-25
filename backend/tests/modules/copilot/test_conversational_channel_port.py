"""Tests for the ``ConversationalChannelPort`` + InMemoryChannel (Fase 09.D)."""

from __future__ import annotations

import pytest

from src.modules.copilot.infrastructure.channels.in_memory_channel import (
    InMemoryConversationalChannel,
)
from src.shared.domain.field_contract import (
    FieldContract,
    FieldStatus,
    FieldType,
)
from src.shared.links.ports.conversational_channel import ConversationalChannelPort


def _contract(path: str, *, question: str | None = None) -> FieldContract:
    return FieldContract(
        path=path,
        owner_module="test",
        type=FieldType.TEXT,
        is_required_structural=False,
        section="main",
        priority=10,
        is_required_semantic=True,
        can_propose=True,
        status=FieldStatus.ACTIVE,
        human_question_es=question,
    )


def test_in_memory_channel_implements_port() -> None:
    """InMemoryConversationalChannel cumple el contract abstracto."""
    adapter = InMemoryConversationalChannel()
    assert isinstance(adapter, ConversationalChannelPort)


@pytest.mark.asyncio
async def test_ask_captures_outbound() -> None:
    adapter = InMemoryConversationalChannel()
    c = _contract("brand_name", question="¿Cómo se llama tu marca?")
    await adapter.ask(c)

    assert len(adapter.outbound) == 1
    captured_contract, captured_context = adapter.outbound[0]
    assert captured_contract is c
    assert captured_context == {}


@pytest.mark.asyncio
async def test_ask_preserves_order_across_multiple_calls() -> None:
    adapter = InMemoryConversationalChannel()
    a = _contract("a")
    b = _contract("b")
    c = _contract("c")

    await adapter.ask(a)
    await adapter.ask(b)
    await adapter.ask(c)

    assert [contract.path for contract, _ in adapter.outbound] == ["a", "b", "c"]


@pytest.mark.asyncio
async def test_ask_records_context() -> None:
    adapter = InMemoryConversationalChannel()
    c = _contract("brand_name")

    await adapter.ask(c, context={"conversation_id": "abc-123"})

    _, captured_context = adapter.outbound[0]
    assert captured_context == {"conversation_id": "abc-123"}


def test_clear_drops_outbound() -> None:
    adapter = InMemoryConversationalChannel()
    adapter.outbound.append((_contract("a"), {}))
    adapter.clear()
    assert adapter.outbound == []


def test_port_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        ConversationalChannelPort()  # type: ignore[abstract]
