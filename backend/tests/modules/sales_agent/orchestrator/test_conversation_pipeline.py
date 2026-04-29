"""Unit tests for ConversationPipeline — S11B Strangler Fig step 3.

Drives each method in isolation. Cross-module models stay opaque.

# [SALES-AGENT-CONVERSATION-PIPELINE-S11B] -> docs/domains/sales-agent/redesign-2026-04/phases/
# S11-shared-lift-orchestrator-decomp.md
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from src.modules.sales_agent.application.orchestrator.conversation_pipeline import (
    ConversationPipeline,
)
from src.shared.domain.messages import IncomingMessage

TENANT_ID = UUID("44444444-4444-4444-4444-444444444444")
LEAD_ID = UUID("55555555-5555-5555-5555-555555555555")
CUSTOMER_ID = UUID("aaaaaaaa-1111-1111-1111-aaaaaaaaaaaa")


# ── load_checkpoint ────────────────────────────────────────────────────


def test_load_checkpoint_returns_none_when_tenant_missing() -> None:
    state_repo = MagicMock()
    result = ConversationPipeline.load_checkpoint(MagicMock(), state_repo, None, LEAD_ID)
    assert result is None
    state_repo.get_active_checkpoint.assert_not_called()


def test_load_checkpoint_rolls_back_on_failure() -> None:
    db = MagicMock()
    state_repo = MagicMock()
    state_repo.get_active_checkpoint.side_effect = RuntimeError("boom")

    result = ConversationPipeline.load_checkpoint(db, state_repo, TENANT_ID, LEAD_ID)
    assert result is None
    db.rollback.assert_called_once()


# ── handle_human_mode ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_handle_human_mode_returns_false_when_no_checkpoint() -> None:
    user = SimpleNamespace(id=LEAD_ID)
    incoming = IncomingMessage(user_id="u", text="t", channel_type="telegram", metadata={})
    result = await ConversationPipeline.handle_human_mode(
        MagicMock(),
        None,
        user,
        TENANT_ID,
        str(TENANT_ID),
        incoming,
    )
    assert result is False


@pytest.mark.asyncio
async def test_handle_human_mode_returns_false_when_handler_mode_ai() -> None:
    checkpoint = SimpleNamespace(handler_mode="ai", unread_count=0)
    user = SimpleNamespace(id=LEAD_ID)
    incoming = IncomingMessage(user_id="u", text="t", channel_type="telegram", metadata={})

    result = await ConversationPipeline.handle_human_mode(
        MagicMock(),
        checkpoint,
        user,
        TENANT_ID,
        str(TENANT_ID),
        incoming,
    )
    assert result is False


@pytest.mark.asyncio
async def test_handle_human_mode_increments_unread_and_emits_ws(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list = []

    async def _capture_emit(_tid: object, _user: object, _incoming: object) -> None:
        captured.append(True)

    monkeypatch.setattr(
        "src.modules.sales_agent.application.orchestrator.audit_emitter.AuditEmitter.emit_human_mode_message",
        staticmethod(_capture_emit),
    )

    db = MagicMock()
    checkpoint = SimpleNamespace(
        handler_mode="human",
        unread_count=2,
        last_human_message_at=None,
    )
    user = SimpleNamespace(id=LEAD_ID)
    incoming = IncomingMessage(user_id="u", text="t", channel_type="telegram", metadata={})

    result = await ConversationPipeline.handle_human_mode(
        db,
        checkpoint,
        user,
        TENANT_ID,
        str(TENANT_ID),
        incoming,
    )

    assert result is True
    assert checkpoint.unread_count == 3
    assert isinstance(checkpoint.last_human_message_at, datetime)
    db.commit.assert_called_once()
    assert captured == [True]


# ── determine_session_state ───────────────────────────────────────────


def test_determine_session_state_no_history_returns_defaults() -> None:
    audit_repo = MagicMock()
    audit_repo.get_last_message.return_value = None

    result = ConversationPipeline.determine_session_state(audit_repo, SimpleNamespace(id=LEAD_ID))
    assert result == {
        "session_active": True,
        "last_intent": None,
        "session_gap_hours": None,
        "is_returning_user": False,
    }


def test_determine_session_state_returning_user_within_window() -> None:
    audit_repo = MagicMock()
    msg_time = datetime.now(timezone.utc) - timedelta(hours=2)
    audit_repo.get_last_message.return_value = SimpleNamespace(
        created_at=msg_time,
        metadata_log={"intent": "buying_signal"},
    )

    result = ConversationPipeline.determine_session_state(audit_repo, SimpleNamespace(id=LEAD_ID))
    assert result["is_returning_user"] is True
    assert result["session_active"] is True
    assert result["last_intent"] == "buying_signal"
    assert result["session_gap_hours"] is not None


# ── build_user_profile ────────────────────────────────────────────────


def test_build_user_profile_no_user_returns_empty() -> None:
    user = SimpleNamespace(profile_data=None, custom_system_instruction=None, style_profile=None)
    assert ConversationPipeline.build_user_profile(user) == {}


def test_build_user_profile_merges_custom_and_style() -> None:
    user = SimpleNamespace(
        profile_data={"first_name": "Ana"},
        custom_system_instruction="be concise",
        style_profile={"tone": "warm"},
    )
    result = ConversationPipeline.build_user_profile(user)
    assert result["first_name"] == "Ana"
    assert result["custom_instruction"] == "be concise"
    assert result["style_profile"] == {"tone": "warm"}


# ── build_agent_identity / build_brand_voice ─────────────────────────


def test_build_agent_identity_returns_none_when_tenant_missing() -> None:
    assert ConversationPipeline.build_agent_identity(MagicMock(), None) is None


def test_build_brand_voice_returns_none_when_tenant_missing() -> None:
    assert ConversationPipeline.build_brand_voice(MagicMock(), None) is None


# ── sanitize_text ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sanitize_text_returns_sanitized(monkeypatch: pytest.MonkeyPatch) -> None:
    safety_stub = SimpleNamespace(sanitize_content=AsyncMock(return_value=("clean text", True)))
    monkeypatch.setattr(
        "src.modules.sales_agent.infrastructure.external.safety_service.SafetyLayerService",
        lambda: safety_stub,
    )
    result = await ConversationPipeline.sanitize_text("dirty", "user_input")
    assert result == "clean text"


@pytest.mark.asyncio
async def test_sanitize_text_returns_original_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def _factory() -> object:
        msg = "safety down"
        raise RuntimeError(msg)

    monkeypatch.setattr(
        "src.modules.sales_agent.infrastructure.external.safety_service.SafetyLayerService",
        _factory,
    )
    assert await ConversationPipeline.sanitize_text("orig", "input") == "orig"


# ── save_checkpoint ──────────────────────────────────────────────────


def test_save_checkpoint_persists_and_commits() -> None:
    db = MagicMock()
    state_repo = MagicMock()
    user = SimpleNamespace(id=LEAD_ID)
    customer = SimpleNamespace(id=CUSTOMER_ID)
    initial_state = {"session_id": "sess-123"}
    result = {
        "current_state": "discovery",
        "lead_score": 30,
        "lead_data": {"name": "Ana"},
        "turn_count": 5,
        "next_node": "qualifier",
    }

    ConversationPipeline.save_checkpoint(
        db,
        state_repo,
        TENANT_ID,
        user,
        customer,
        "telegram",
        initial_state,
        result,
        last_session_summary=None,
    )

    state_repo.save_checkpoint.assert_called_once()
    db.commit.assert_called_once()


def test_save_checkpoint_rolls_back_on_failure() -> None:
    db = MagicMock()
    state_repo = MagicMock()
    state_repo.save_checkpoint.side_effect = RuntimeError("boom")

    ConversationPipeline.save_checkpoint(
        db,
        state_repo,
        TENANT_ID,
        SimpleNamespace(id=LEAD_ID),
        SimpleNamespace(id=CUSTOMER_ID),
        "telegram",
        {"session_id": "x"},
        {},
        last_session_summary=None,
    )
    db.rollback.assert_called_once()


# ── deliver_response ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_deliver_response_logs_sends_and_emits(monkeypatch: pytest.MonkeyPatch) -> None:
    safety_stub = SimpleNamespace(sanitize_content=AsyncMock(return_value=("respuesta", False)))
    monkeypatch.setattr(
        "src.modules.sales_agent.infrastructure.external.safety_service.SafetyLayerService",
        lambda: safety_stub,
    )

    output_calls: list = []

    async def _capture_output(uid: str, text: str, _adapter: object, channel_type: str) -> None:
        output_calls.append((uid, text, channel_type))

    monkeypatch.setattr(
        "src.modules.sales_agent.infrastructure.external.output_manager.OutputManager.process_response",
        _capture_output,
    )

    ws_calls: list = []

    async def _capture_ws(_tid: object, _user: object, _text: str, _result: dict) -> None:
        ws_calls.append(True)

    monkeypatch.setattr(
        "src.modules.sales_agent.application.orchestrator.audit_emitter.AuditEmitter.emit_assistant_message",
        staticmethod(_capture_ws),
    )

    audit_repo = MagicMock()
    user = SimpleNamespace(id=LEAD_ID)
    incoming = IncomingMessage(user_id="tg_u", text="hola", channel_type="telegram", metadata={})
    result = {"messages": [{"role": "user"}, {"role": "assistant", "content": "respuesta"}]}

    await ConversationPipeline.deliver_response(
        MagicMock(),
        incoming,
        result,
        audit_repo,
        user,
        "telegram",
        TENANT_ID,
    )

    audit_repo.log_message.assert_called_once()
    assert output_calls == [("tg_u", "respuesta", "telegram")]
    assert ws_calls == [True]
