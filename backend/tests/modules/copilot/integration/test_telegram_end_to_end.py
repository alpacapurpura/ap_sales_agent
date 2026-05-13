"""End-to-end-ish tests for ``process_copilot_telegram_turn`` (PI-5 PR-2).

Three scenarios:
    1. Linked happy path — orchestrator runs, format_for_channel_impl
       transforms output, ``CopilotTelegramBot.send_message`` called once
       with MarkdownV2 escaping.
    2. Unlinked CTA — ``resolve_chat_id_to_tenant_user`` returns None;
       worker sends the onboarding-URL CTA; orchestrator NOT invoked.
    3. ``/start TOKEN`` linking — ``consume_link_token`` succeeds; bot
       sends the bound-confirmation message; orchestrator NOT invoked.

We mock at the module-import boundary (services + bot + sync session
factory + orchestrator) so the worker logic is fully exercised without
DB / network dependencies.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from luana_core_copilot.application.orchestrator.invoke_result import (
    CopilotInvokeResult,
)
from luana_core_copilot.infrastructure.workers import telegram_worker as worker_mod


def _make_link_obj():
    """Stub ``CopilotChannelLinkModel`` row for resolve_chat_id_to_tenant_user."""
    link = MagicMock()
    link.id = uuid4()
    link.tenant_id = uuid4()
    link.user_id = uuid4()
    link.role = "owner"
    return link


@asynccontextmanager
async def _async_session_cm(db_mock):
    """Stand-in for ``copilot_async_session_factory()`` async context manager."""
    yield db_mock


def _patch_session_factory():
    """Patch the async session factory to yield a MagicMock db."""
    db_mock = MagicMock()
    return patch.object(
        worker_mod,
        "copilot_async_session_factory",
        return_value=_async_session_cm(db_mock),
    ), db_mock


# ── 1. Linked happy path ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_linked_happy_path_invokes_orchestrator_and_sends_response() -> None:
    link = _make_link_obj()

    # Bot mock — capture send_message calls.
    bot_send = AsyncMock()
    bot_instance = MagicMock()
    bot_instance.send_message = bot_send

    # Orchestrator mock — invoke_text returns a CopilotInvokeResult.
    orchestrator_mock = MagicMock()
    orchestrator_mock.invoke_text = AsyncMock(
        return_value=CopilotInvokeResult(
            conversation_id=str(uuid4()),
            response_text="Aquí tienes los datos pedidos.",
            error_kind=None,
        )
    )

    # ConversationRepository.get_or_create_by_channel — sync method, returns a stub.
    conv_stub = MagicMock(id=uuid4())
    conv_repo_mock = MagicMock()
    conv_repo_mock.get_or_create_by_channel = MagicMock(return_value=conv_stub)

    # SessionLocal sync — returned mock session does .commit / .rollback / .close.
    sync_db = MagicMock()
    session_local_mock = MagicMock(return_value=sync_db)

    # async session factory.
    sf_patch, db_mock = _patch_session_factory()

    with (
        sf_patch,
        patch.object(worker_mod, "resolve_chat_id_to_tenant_user", AsyncMock(return_value=link)),
        patch.object(worker_mod, "touch_last_seen", AsyncMock()),
        patch.object(worker_mod, "CopilotTelegramBot", return_value=bot_instance),
        patch.object(worker_mod, "ConversationRepository", return_value=conv_repo_mock),
        patch.object(worker_mod, "CopilotOrchestrator", return_value=orchestrator_mock),
        patch("luana_core_platform.core.database.SessionLocal", session_local_mock),
    ):
        await worker_mod.process_copilot_telegram_turn(
            ctx={},
            payload={
                "update_id": 1,
                "chat_id": "555111222",
                "message_id": 10,
                "text": "cuántos leads tengo este mes",
                "username": "alice",
                "received_at": "2026-05-01T00:00:00Z",
            },
        )

    # Orchestrator was invoked exactly once with channel='telegram'.
    assert orchestrator_mock.invoke_text.await_count == 1
    kwargs = orchestrator_mock.invoke_text.await_args.kwargs
    assert kwargs["channel"] == "telegram"
    assert kwargs["tenant_id"] == link.tenant_id
    assert kwargs["user_id"] == link.user_id

    # Bot.send_message called once with the formatted text + MarkdownV2.
    assert bot_send.await_count == 1
    send_kwargs = bot_send.await_args.kwargs
    assert send_kwargs["chat_id"] == "555111222"
    assert send_kwargs.get("parse_mode") == "MarkdownV2"
    assert send_kwargs["text"]  # non-empty


# ── 2. Unlinked → CTA template ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_unlinked_chat_sends_cta_and_skips_orchestrator() -> None:
    bot_send = AsyncMock()
    bot_instance = MagicMock()
    bot_instance.send_message = bot_send

    orchestrator_mock = MagicMock()
    orchestrator_mock.invoke_text = AsyncMock()

    sf_patch, _ = _patch_session_factory()

    with (
        sf_patch,
        patch.object(worker_mod, "resolve_chat_id_to_tenant_user", AsyncMock(return_value=None)),
        patch.object(worker_mod, "CopilotTelegramBot", return_value=bot_instance),
        patch.object(worker_mod, "CopilotOrchestrator", return_value=orchestrator_mock),
    ):
        await worker_mod.process_copilot_telegram_turn(
            ctx={},
            payload={
                "update_id": 2,
                "chat_id": "777999",
                "message_id": 1,
                "text": "hola",
                "username": "bob",
                "received_at": "2026-05-01T00:00:00Z",
            },
        )

    # Orchestrator NOT invoked.
    orchestrator_mock.invoke_text.assert_not_awaited()

    # CTA was sent — text contains the onboarding URL pattern.
    assert bot_send.await_count == 1
    send_kwargs = bot_send.await_args.kwargs
    assert send_kwargs["chat_id"] == "777999"
    assert "settings/copilot/telegram" in send_kwargs["text"]


# ── 3. /start TOKEN linking ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_start_token_consumes_and_confirms_link() -> None:
    new_link = _make_link_obj()

    bot_send = AsyncMock()
    bot_instance = MagicMock()
    bot_instance.send_message = bot_send

    orchestrator_mock = MagicMock()
    orchestrator_mock.invoke_text = AsyncMock()

    sf_patch, _ = _patch_session_factory()

    with (
        sf_patch,
        # On the /start TOKEN path the worker calls resolve first; return None
        # (chat_id not yet linked) so the /start branch fires.
        patch.object(worker_mod, "resolve_chat_id_to_tenant_user", AsyncMock(return_value=None)),
        patch.object(worker_mod, "consume_link_token", AsyncMock(return_value=new_link)),
        patch.object(worker_mod, "CopilotTelegramBot", return_value=bot_instance),
        patch.object(worker_mod, "CopilotOrchestrator", return_value=orchestrator_mock),
    ):
        await worker_mod.process_copilot_telegram_turn(
            ctx={},
            payload={
                "update_id": 3,
                "chat_id": "888000",
                "message_id": 1,
                "text": "/start ABCD-EFGH-IJKL-MNOP",
                "username": "carol",
                "received_at": "2026-05-01T00:00:00Z",
            },
        )

    # Orchestrator NOT invoked on linking turn.
    orchestrator_mock.invoke_text.assert_not_awaited()

    # Confirmation message sent ("Listo. Ya puedes usar..." per worker code).
    assert bot_send.await_count == 1
    send_kwargs = bot_send.await_args.kwargs
    assert send_kwargs["chat_id"] == "888000"
    assert "Listo" in send_kwargs["text"] or "puedes usar" in send_kwargs["text"]
