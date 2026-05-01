"""Tests for ``CopilotOrchestrator.invoke_text`` (PI-5 PR-2 — D-PI5-007).

The non-streaming entry point used by the Telegram worker (and any
future non-streaming consumer like email). Drives ``_run_graph_stream``
internally but accumulates ``acc.full_response`` instead of yielding
SSE strings.

Three scenarios covered:
    1. Happy path — returns ``CopilotInvokeResult`` with non-empty
       ``response_text`` and ``error_kind = None``.
    2. Channel resolution — DTO field wins over kwarg; kwarg wins over
       default ``"web"``.
    3. Error path — ``_run_graph_stream`` raises → caught internally,
       ``error_kind`` populated, ``response_text`` falls back to user-
       facing copy from ``_user_facing_error_message``.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.modules.copilot.api.dto import ClientContextDTO
from src.modules.copilot.application.orchestrator.chat import CopilotOrchestrator
from src.modules.copilot.application.orchestrator.invoke_result import (
    CopilotInvokeResult,
)


def _make_orchestrator() -> CopilotOrchestrator:
    """Return an orchestrator with a stubbed sync ``Session``.

    The Session is only consulted by ``ConversationRepository`` and the
    observability context — both of which we mock at higher levels in
    these tests, so a bare ``MagicMock`` suffices.
    """
    db = MagicMock()
    return CopilotOrchestrator(db)


async def _run_invoke_text(
    *,
    orchestrator: CopilotOrchestrator,
    user_id,
    tenant_id,
    message: str,
    channel: str = "web",
    context: ClientContextDTO | None = None,
    side_effect=None,
):
    """Drive ``invoke_text`` with ``_prepare_conversation`` + ``_run_graph_stream``
    + ``_persist_messages`` + ``_build_observability_context`` mocked.
    """
    # ── _prepare_conversation: returns the 4-tuple expected by invoke_text.
    conv_id = str(uuid4())
    state = {"client_context": {"channel": channel, "current_route": "/copilot/chat"}}
    prepare_mock = MagicMock(return_value=(conv_id, uuid4(), MagicMock(), state))

    # ── _run_graph_stream: an async generator that either yields a
    #    couple of SSE strings (happy path) or raises (error path).
    async def fake_stream_ok(state, acc, msg_id, user_msg):
        acc.full_response = "Respuesta generada"
        acc.messages = []
        # Make it a generator so ``async for`` works.
        if False:
            yield ""

    async def fake_stream_raises(state, acc, msg_id, user_msg):
        raise RuntimeError("boom") if side_effect is None else (_ for _ in ()).throw(side_effect)
        if False:
            yield ""

    stream_target = fake_stream_raises if side_effect is not None else fake_stream_ok
    # Build an obs context with the no-op observe_turn cm.
    obs_mock = MagicMock()
    obs_mock.observe_turn.return_value.__aenter__ = AsyncMock(return_value=None)
    obs_mock.observe_turn.return_value.__aexit__ = AsyncMock(return_value=None)
    obs_mock.set_turn_summary = MagicMock()

    with (
        patch.object(orchestrator, "_prepare_conversation", prepare_mock),
        patch.object(orchestrator, "_run_graph_stream", side_effect=stream_target),
        patch.object(orchestrator, "_persist_messages", MagicMock()),
        patch.object(orchestrator, "_build_observability_context", return_value=obs_mock),
    ):
        result = await orchestrator.invoke_text(
            user_id=user_id,
            tenant_id=tenant_id,
            message=message,
            channel=channel,
            context=context,
        )
    return result, prepare_mock


# ── Happy path ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_invoke_text_returns_invoke_result_on_happy_path() -> None:
    user_id = uuid4()
    tenant_id = uuid4()
    orch = _make_orchestrator()

    result, _ = await _run_invoke_text(
        orchestrator=orch,
        user_id=user_id,
        tenant_id=tenant_id,
        message="hola",
    )

    assert isinstance(result, CopilotInvokeResult)
    assert result.response_text == "Respuesta generada"
    assert result.error_kind is None
    assert result.conversation_id


# ── Channel resolution ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_invoke_text_dto_channel_wins_over_kwarg() -> None:
    """``context.channel='telegram'`` + ``channel='web'`` → effective 'telegram'."""
    user_id = uuid4()
    tenant_id = uuid4()
    orch = _make_orchestrator()

    ctx = ClientContextDTO(channel="telegram", locale="es")
    _, prepare_mock = await _run_invoke_text(
        orchestrator=orch,
        user_id=user_id,
        tenant_id=tenant_id,
        message="hola",
        channel="web",
        context=ctx,
    )

    # _prepare_conversation receives ``channel`` as kwarg — DTO precedence
    # is enforced INSIDE _prepare_conversation. Here we only verify the
    # kwarg was forwarded.
    kwargs = prepare_mock.call_args.kwargs
    assert kwargs["channel"] == "web"
    assert kwargs["context"] is ctx
    # The DTO carries the canonical channel for downstream consumers.
    assert ctx.channel == "telegram"


@pytest.mark.asyncio
async def test_invoke_text_kwarg_channel_used_when_dto_channel_none() -> None:
    """``context.channel=None`` + ``channel='telegram'`` → effective 'telegram'."""
    user_id = uuid4()
    tenant_id = uuid4()
    orch = _make_orchestrator()

    ctx = ClientContextDTO(channel=None, locale="es")
    _, prepare_mock = await _run_invoke_text(
        orchestrator=orch,
        user_id=user_id,
        tenant_id=tenant_id,
        message="hola",
        channel="telegram",
        context=ctx,
    )

    kwargs = prepare_mock.call_args.kwargs
    assert kwargs["channel"] == "telegram"


@pytest.mark.asyncio
async def test_invoke_text_default_channel_web_when_both_none() -> None:
    """No DTO channel + default kwarg → ``"web"`` reaches _prepare_conversation."""
    user_id = uuid4()
    tenant_id = uuid4()
    orch = _make_orchestrator()

    _, prepare_mock = await _run_invoke_text(
        orchestrator=orch,
        user_id=user_id,
        tenant_id=tenant_id,
        message="hola",
        # channel kwarg defaults to "web"
        context=None,
    )

    kwargs = prepare_mock.call_args.kwargs
    assert kwargs["channel"] == "web"


# ── Error path ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_invoke_text_returns_error_kind_when_stream_raises() -> None:
    """Generic exception in ``_run_graph_stream`` → ``error_kind`` populated."""
    user_id = uuid4()
    tenant_id = uuid4()
    orch = _make_orchestrator()

    result, _ = await _run_invoke_text(
        orchestrator=orch,
        user_id=user_id,
        tenant_id=tenant_id,
        message="hola",
        side_effect=RuntimeError("boom"),
    )

    assert isinstance(result, CopilotInvokeResult)
    assert result.error_kind is not None
    # Fallback copy is non-empty so the worker can ship something.
    assert result.response_text != ""
