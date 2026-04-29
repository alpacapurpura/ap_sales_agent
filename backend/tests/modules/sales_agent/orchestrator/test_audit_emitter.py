"""Unit tests for AuditEmitter — S11B Strangler Fig step 1.

Drives each method in isolation: every side-effect (journey_repo, EventBus,
ws_manager) is mocked at its definition site so the test reflects what
external systems observe when the orchestrator publishes a chat event.

# [SALES-AGENT-AUDIT-EMITTER-S11B] -> docs/domains/sales-agent/redesign-2026-04/phases/S11-shared-lift-orchestrator-decomp.md
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import UUID

import pytest

from src.modules.sales_agent.application.orchestrator.audit_emitter import AuditEmitter
from src.shared.domain.messages import IncomingMessage

TENANT_ID = UUID("44444444-4444-4444-4444-444444444444")
CUSTOMER_ID = UUID("aaaaaaaa-1111-1111-1111-aaaaaaaaaaaa")
LEAD_ID = UUID("55555555-5555-5555-5555-555555555555")


# ── track_message_received ─────────────────────────────────────────────


def test_track_message_received_emits_track_event(monkeypatch: pytest.MonkeyPatch) -> None:
    journey_repo = MagicMock()
    monkeypatch.setattr(
        "src.shared.links.ports.crm_repos.get_journey_event_repository",
        lambda _db: journey_repo,
    )

    customer = SimpleNamespace(id=CUSTOMER_ID)
    incoming = IncomingMessage(
        user_id="tg_user_1",
        text="Hola",
        channel_type="telegram",
        metadata={"message_id": "tg_msg_42"},
    )

    AuditEmitter.track_message_received(
        db=MagicMock(),
        tenant_uuid=TENANT_ID,
        customer=customer,
        capture_slug="telegram-dm",
        channel_type="telegram",
        incoming=incoming,
    )

    journey_repo.track_event.assert_called_once_with(
        profile_id=CUSTOMER_ID,
        tenant_id=TENANT_ID,
        event_name="message_received",
        event_type="track",
        properties={
            "channel_slug": "telegram-dm",
            "channel_type": "telegram",
            "message_direction": "inbound",
            "message_id": "tg_msg_42",
        },
    )


def test_track_message_received_omits_message_id_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    journey_repo = MagicMock()
    monkeypatch.setattr(
        "src.shared.links.ports.crm_repos.get_journey_event_repository",
        lambda _db: journey_repo,
    )
    customer = SimpleNamespace(id=CUSTOMER_ID)
    incoming = IncomingMessage(user_id="u", text="t", channel_type="whatsapp", metadata={})

    AuditEmitter.track_message_received(
        db=MagicMock(),
        tenant_uuid=TENANT_ID,
        customer=customer,
        capture_slug="whatsapp-inbound",
        channel_type="whatsapp",
        incoming=incoming,
    )

    props = journey_repo.track_event.call_args.kwargs["properties"]
    assert "message_id" not in props


def test_track_message_received_swallows_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(_db: object) -> None:
        msg = "repo down"
        raise RuntimeError(msg)

    monkeypatch.setattr(
        "src.shared.links.ports.crm_repos.get_journey_event_repository",
        _raise,
    )
    customer = SimpleNamespace(id=CUSTOMER_ID)
    incoming = IncomingMessage(user_id="u", text="t", channel_type="telegram", metadata={})

    # Must not raise
    AuditEmitter.track_message_received(
        db=MagicMock(),
        tenant_uuid=TENANT_ID,
        customer=customer,
        capture_slug="telegram-dm",
        channel_type="telegram",
        incoming=incoming,
    )


# ── publish_lead_captured ──────────────────────────────────────────────


def test_publish_lead_captured_publishes_event(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[tuple] = []

    def _capture_publish(event: object, session: object = None) -> None:
        captured.append((event, session))

    monkeypatch.setattr(
        "src.shared.domain.events.EventBus.publish",
        staticmethod(_capture_publish),
    )

    customer = SimpleNamespace(id=CUSTOMER_ID)
    db = MagicMock()

    AuditEmitter.publish_lead_captured(
        db=db,
        tenant_uuid=TENANT_ID,
        customer=customer,
        capture_slug="telegram-dm",
        channel_type="telegram",
    )

    assert len(captured) == 1
    event, session = captured[0]
    assert event.event_name == "lead_captured"
    assert event.tenant_id == TENANT_ID
    assert str(event.payload["profile_id"]) == str(CUSTOMER_ID)
    assert event.payload["channel_slug"] == "telegram-dm"
    assert event.payload["source_channel_type"] == "telegram"
    assert session is db


# ── emit_assistant_message ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_emit_assistant_message_sends_ws_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[tuple] = []

    async def _capture_emit(tenant_id: str, payload: dict) -> None:
        captured.append((tenant_id, payload))

    monkeypatch.setattr(
        "src.modules.sales_agent.infrastructure.ws_manager.ws_manager.emit",
        _capture_emit,
    )

    user = SimpleNamespace(id=LEAD_ID)
    result = {"lead_score": 42, "current_state": "discovery"}

    await AuditEmitter.emit_assistant_message(TENANT_ID, user, "respuesta del bot", result)

    assert len(captured) == 1
    tenant_id, payload = captured[0]
    assert tenant_id == str(TENANT_ID)
    assert payload == {
        "type": "new_message",
        "lead_id": str(LEAD_ID),
        "role": "assistant",
        "content": "respuesta del bot",
        "handler_mode": "ai",
        "lead_score": 42,
        "funnel_stage": "discovery",
    }


@pytest.mark.asyncio
async def test_emit_assistant_message_truncates_to_200_chars(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[dict] = []

    async def _capture_emit(_tid: str, payload: dict) -> None:
        captured.append(payload)

    monkeypatch.setattr(
        "src.modules.sales_agent.infrastructure.ws_manager.ws_manager.emit",
        _capture_emit,
    )

    long_text = "x" * 500
    await AuditEmitter.emit_assistant_message(
        TENANT_ID,
        SimpleNamespace(id=LEAD_ID),
        long_text,
        {},
    )

    assert len(captured[0]["content"]) == 200


@pytest.mark.asyncio
async def test_emit_assistant_message_swallows_ws_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _raise(*_a: object, **_kw: object) -> None:
        msg = "ws broken"
        raise RuntimeError(msg)

    monkeypatch.setattr(
        "src.modules.sales_agent.infrastructure.ws_manager.ws_manager.emit",
        _raise,
    )
    # Must not raise
    await AuditEmitter.emit_assistant_message(
        TENANT_ID,
        SimpleNamespace(id=LEAD_ID),
        "anything",
        {},
    )


# ── emit_human_mode_message ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_emit_human_mode_message_sends_user_role(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[tuple] = []

    async def _capture_emit(tenant_id: str, payload: dict) -> None:
        captured.append((tenant_id, payload))

    monkeypatch.setattr(
        "src.modules.sales_agent.infrastructure.ws_manager.ws_manager.emit",
        _capture_emit,
    )

    user = SimpleNamespace(id=LEAD_ID)
    incoming = IncomingMessage(
        user_id="tg_u",
        text="mensaje del lead durante human mode",
        channel_type="telegram",
        metadata={},
    )

    await AuditEmitter.emit_human_mode_message(TENANT_ID, user, incoming)

    assert len(captured) == 1
    tenant_id, payload = captured[0]
    assert tenant_id == str(TENANT_ID)
    assert payload == {
        "type": "new_message",
        "lead_id": str(LEAD_ID),
        "role": "user",
        "content": "mensaje del lead durante human mode",
        "handler_mode": "human",
    }
