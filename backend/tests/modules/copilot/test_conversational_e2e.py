"""E2E channel-agnostic conversational flow (Fase 09.E).

Drives a complete loop: ``next_question`` → ``adapter.ask`` → state
update → ``next_question`` … until ``None`` (module complete).

Channel-agnostic = same FieldContract sequence emitted regardless of
which port implementation runs. We assert two adapters
(two ``InMemoryConversationalChannel`` instances acting as different
channels) produce identical sequences for the same module + state +
section.

The synthetic registry uses required + optional + gated + section-
filtered contracts so the loop exercises selection rules end-to-end.
"""

from __future__ import annotations

from typing import Any

import pytest

from luana_core_copilot.application.orchestrator.conversational_questioning import (
    next_question,
)
from luana_core_copilot.infrastructure.channels.in_memory_channel import (
    InMemoryConversationalChannel,
)
from luana_core_platform.domain.field_contract import (
    FieldContract,
    FieldStatus,
    FieldType,
    register_module_contracts,
)

_MODULE = "_synthetic_e2e"


def teardown_module(module: object) -> None:
    """Drop synthetic module from the global registry to keep cross-test isolation."""
    register_module_contracts(_MODULE, ())


def _c(
    path: str,
    *,
    section: str = "main",
    priority: int = 0,
    is_required_semantic: bool = True,
    can_propose: bool = True,
    status: FieldStatus = FieldStatus.ACTIVE,
    gate: str | None = None,
    human_question_es: str | None = None,
) -> FieldContract:
    return FieldContract(
        path=path,
        owner_module=_MODULE,
        type=FieldType.TEXT,
        is_required_structural=False,
        section=section,
        priority=priority,
        is_required_semantic=is_required_semantic,
        can_propose=can_propose,
        status=status,
        gate=gate,
        human_question_es=human_question_es,
    )


def _setup_registry() -> None:
    register_module_contracts(
        _MODULE,
        (
            _c(
                "archetype",
                section="strategy",
                priority=20,
                human_question_es="¿Cuál es el archetype?",
            ),
            _c(
                "value_level",
                section="strategy",
                priority=10,
                gate="archetype",
                human_question_es="¿Qué nivel de valor tiene?",
            ),
            _c(
                "headline_promise",
                section="identity",
                priority=15,
                human_question_es="¿Cuál es la promesa principal?",
            ),
            _c(
                "primary_outcome",
                section="identity",
                priority=12,
                human_question_es="¿Cuál es el outcome principal?",
            ),
            _c(
                "deprecated_field",
                section="strategy",
                priority=99,
                status=FieldStatus.DEPRECATED,
                human_question_es="(deprecated)",
            ),
            _c(
                "readonly_field",
                section="strategy",
                priority=99,
                can_propose=False,
                human_question_es="(readonly)",
            ),
            _c(
                "extra_optional",
                section="extras",
                priority=5,
                is_required_semantic=False,
                human_question_es="¿Algún detalle extra?",
            ),
        ),
    )


async def _run_loop(adapter: InMemoryConversationalChannel) -> list[str]:
    """Drive a deterministic capture loop. Returns sequence of paths asked."""
    state: dict[str, Any] = {}
    paths_asked: list[str] = []

    while True:
        contract = next_question(_MODULE, state)
        if contract is None:
            break
        await adapter.ask(contract)
        paths_asked.append(contract.path)
        # Simulate user answering with a placeholder value.
        _set_path(state, contract.path, "ANSWERED")

    return paths_asked


def _set_path(state: dict[str, Any], path: str, value: Any) -> None:
    cursor = state
    parts = path.split(".")
    for seg in parts[:-1]:
        cursor.setdefault(seg, {})
        cursor = cursor[seg]
    cursor[parts[-1]] = value


@pytest.mark.asyncio
async def test_loop_visits_required_then_optional_in_order() -> None:
    _setup_registry()
    adapter = InMemoryConversationalChannel()
    paths = await _run_loop(adapter)

    # Required first: gate=archetype means archetype must be answered
    # before value_level enters candidates. identity has its own
    # required pair (headline_promise > primary_outcome by priority).
    # Strategy and identity tie on required — section lex (identity <
    # strategy) wins, so identity goes first within required.
    assert paths == [
        "headline_promise",
        "primary_outcome",
        "archetype",
        "value_level",
        "extra_optional",
    ]
    assert [c.path for c, _ in adapter.outbound] == paths


@pytest.mark.asyncio
async def test_skipped_until_gate_satisfied() -> None:
    _setup_registry()
    adapter = InMemoryConversationalChannel()
    paths = await _run_loop(adapter)

    archetype_idx = paths.index("archetype")
    value_level_idx = paths.index("value_level")
    assert archetype_idx < value_level_idx, "value_level requires archetype first"


@pytest.mark.asyncio
async def test_deprecated_and_readonly_never_asked() -> None:
    _setup_registry()
    adapter = InMemoryConversationalChannel()
    paths = await _run_loop(adapter)

    assert "deprecated_field" not in paths
    assert "readonly_field" not in paths


@pytest.mark.asyncio
async def test_two_channel_adapters_produce_same_sequence() -> None:
    """Channel-agnostic invariant: distinct adapters → identical sequences."""
    _setup_registry()

    web_channel = InMemoryConversationalChannel()
    chat_channel = InMemoryConversationalChannel()

    web_paths = await _run_loop(web_channel)
    chat_paths = await _run_loop(chat_channel)

    assert web_paths == chat_paths
    assert [c.path for c, _ in web_channel.outbound] == [c.path for c, _ in chat_channel.outbound]


@pytest.mark.asyncio
async def test_human_question_es_emitted_to_adapter() -> None:
    _setup_registry()
    adapter = InMemoryConversationalChannel()
    await _run_loop(adapter)

    questions = [c.human_question_es for c, _ in adapter.outbound]
    assert "¿Cuál es la promesa principal?" in questions
    assert "¿Cuál es el archetype?" in questions
    assert "¿Algún detalle extra?" in questions


@pytest.mark.asyncio
async def test_loop_terminates_after_module_complete() -> None:
    _setup_registry()
    adapter = InMemoryConversationalChannel()
    paths = await _run_loop(adapter)

    # After the loop, next_question against the final state must be None.
    state: dict[str, Any] = {}
    for path in paths:
        _set_path(state, path, "ANSWERED")
    assert next_question(_MODULE, state) is None
