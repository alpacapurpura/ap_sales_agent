"""Unit tests for IdentityResolver — S11B Strangler Fig step 2.

Drives each method in isolation. Cross-module crm models stay opaque (Any).

# [SALES-AGENT-IDENTITY-RESOLVER-S11B] -> docs/domains/sales-agent/redesign-2026-04/phases/
# S11-shared-lift-orchestrator-decomp.md
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import UUID

import pytest

from src.modules.sales_agent.application.orchestrator.identity_resolver import (
    IdentityResolver,
)
from src.shared.domain.enums import IdentityType
from src.shared.domain.messages import IncomingMessage

TENANT_ID = UUID("44444444-4444-4444-4444-444444444444")
CUSTOMER_ID = UUID("aaaaaaaa-1111-1111-1111-aaaaaaaaaaaa")
LEAD_ID = UUID("55555555-5555-5555-5555-555555555555")


# ── resolve_customer ───────────────────────────────────────────────────


def test_resolve_customer_telegram_uses_telegram_capture_slug() -> None:
    identity_service = MagicMock()
    customer_stub = SimpleNamespace(id=CUSTOMER_ID)
    identity_service.get_or_create_customer.return_value = (customer_stub, True)

    incoming = IncomingMessage(
        user_id="tg_u",
        text="t",
        channel_type="telegram",
        metadata={"first_name": "Ana", "last_name": "Solis"},
    )

    customer, was_created, slug, channel_type, identity_type = IdentityResolver.resolve_customer(
        identity_service,
        incoming,
        TENANT_ID,
    )

    assert customer is customer_stub
    assert was_created is True
    assert slug == "telegram-dm"
    assert channel_type == "telegram"
    assert identity_type == IdentityType.TELEGRAM


def test_resolve_customer_unknown_channel_falls_back_to_external_id() -> None:
    identity_service = MagicMock()
    identity_service.get_or_create_customer.return_value = (SimpleNamespace(id=CUSTOMER_ID), False)
    incoming = IncomingMessage(user_id="x", text="t", channel_type="unknown_channel", metadata={})

    _, _, slug, channel_type, identity_type = IdentityResolver.resolve_customer(
        identity_service,
        incoming,
        TENANT_ID,
    )

    assert identity_type == IdentityType.EXTERNAL_ID
    # capture_slug fallback to channel_type when not in CHANNEL_TYPE_TO_CAPTURE_SLUG
    assert slug == "unknown_channel"
    assert channel_type == "unknown_channel"


# ── enrich_instagram_profile ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_enrich_instagram_profile_skips_when_existing_username_set() -> None:
    customer = SimpleNamespace(traits={"instagram_username": "already_known"})
    db = MagicMock()
    # was_created=False AND username exists -> early return.
    await IdentityResolver.enrich_instagram_profile(
        db,
        TENANT_ID,
        "igsid_123",
        customer,
        was_created=False,
    )
    db.assert_not_called()  # no port created


@pytest.mark.asyncio
async def test_enrich_instagram_profile_swallows_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(_db: object) -> None:
        msg = "ig down"
        raise RuntimeError(msg)

    monkeypatch.setattr(
        "src.shared.links.ports.channel_adapter.create_connection_port",
        _raise,
    )
    customer = SimpleNamespace(traits={}, id=CUSTOMER_ID)
    # Must not raise
    await IdentityResolver.enrich_instagram_profile(
        MagicMock(),
        TENANT_ID,
        "igsid",
        customer,
        was_created=True,
    )


# ── update_customer_traits ────────────────────────────────────────────


def test_update_customer_traits_skips_when_metadata_empty() -> None:
    db = MagicMock()
    customer = SimpleNamespace(id=CUSTOMER_ID, traits={"a": 1})
    incoming = IncomingMessage(user_id="u", text="t", channel_type="telegram", metadata={})

    IdentityResolver.update_customer_traits(db, customer, incoming)
    db.execute.assert_not_called()


def test_update_customer_traits_skips_when_no_diff() -> None:
    db = MagicMock()
    # Existing traits already match incoming metadata -> no_op
    traits = {"first_name": "Ana"}
    customer = SimpleNamespace(id=CUSTOMER_ID, traits=traits)
    incoming = IncomingMessage(
        user_id="u",
        text="t",
        channel_type="telegram",
        metadata={"first_name": "Ana"},
    )
    IdentityResolver.update_customer_traits(db, customer, incoming)
    db.execute.assert_not_called()


# ── resolve_lead ──────────────────────────────────────────────────────


def test_resolve_lead_returns_existing_when_active() -> None:
    lead = SimpleNamespace(id=LEAD_ID)
    lead_repo = MagicMock()
    lead_repo.get_active_lead.return_value = lead

    result = IdentityResolver.resolve_lead(lead_repo, CUSTOMER_ID, "telegram", "tg_u")

    assert result is lead
    lead_repo.create_lead.assert_not_called()


def test_resolve_lead_creates_when_no_active_lead() -> None:
    new_lead = SimpleNamespace(id=LEAD_ID)
    lead_repo = MagicMock()
    lead_repo.get_active_lead.return_value = None
    lead_repo.create_lead.return_value = new_lead

    result = IdentityResolver.resolve_lead(lead_repo, CUSTOMER_ID, "whatsapp", "wa_u")

    assert result is new_lead
    lead_repo.create_lead.assert_called_once_with(
        customer_id=CUSTOMER_ID,
        channel="whatsapp",
        channel_user_id="wa_u",
    )


# ── process_customer_lifecycle ────────────────────────────────────────


@pytest.mark.asyncio
async def test_process_customer_lifecycle_publishes_event_for_new_customer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_events: list = []
    captured_journey: list = []

    monkeypatch.setattr(
        "src.modules.sales_agent.application.orchestrator.audit_emitter.AuditEmitter.publish_lead_captured",
        staticmethod(lambda *args, **kwargs: captured_events.append((args, kwargs))),
    )
    monkeypatch.setattr(
        "src.modules.sales_agent.application.orchestrator.audit_emitter.AuditEmitter.track_message_received",
        staticmethod(lambda *args, **kwargs: captured_journey.append((args, kwargs))),
    )
    # Suppress trait merge ORM
    monkeypatch.setattr(
        "src.modules.sales_agent.application.orchestrator.identity_resolver.IdentityResolver.update_customer_traits",
        staticmethod(lambda *_a, **_kw: None),
    )

    identity_service = MagicMock()
    customer = SimpleNamespace(id=CUSTOMER_ID, traits={})
    identity_service.get_or_create_customer.return_value = (customer, True)
    incoming = IncomingMessage(user_id="tg_u", text="hola", channel_type="telegram", metadata={})

    result = await IdentityResolver.process_customer_lifecycle(
        MagicMock(),
        identity_service,
        incoming,
        TENANT_ID,
    )

    assert result == (customer, True, "telegram-dm", "telegram")
    assert len(captured_events) == 1
    assert len(captured_journey) == 1


@pytest.mark.asyncio
async def test_process_customer_lifecycle_skips_publish_for_existing_customer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_events: list = []

    monkeypatch.setattr(
        "src.modules.sales_agent.application.orchestrator.audit_emitter.AuditEmitter.publish_lead_captured",
        staticmethod(lambda *args, **kwargs: captured_events.append((args, kwargs))),
    )
    monkeypatch.setattr(
        "src.modules.sales_agent.application.orchestrator.audit_emitter.AuditEmitter.track_message_received",
        staticmethod(lambda *_a, **_kw: None),
    )
    monkeypatch.setattr(
        "src.modules.sales_agent.application.orchestrator.identity_resolver.IdentityResolver.update_customer_traits",
        staticmethod(lambda *_a, **_kw: None),
    )

    identity_service = MagicMock()
    customer = SimpleNamespace(id=CUSTOMER_ID, traits={})
    identity_service.get_or_create_customer.return_value = (customer, False)
    incoming = IncomingMessage(user_id="u", text="t", channel_type="whatsapp", metadata={})

    await IdentityResolver.process_customer_lifecycle(
        MagicMock(),
        identity_service,
        incoming,
        TENANT_ID,
    )

    assert captured_events == []  # was_created=False, no event
