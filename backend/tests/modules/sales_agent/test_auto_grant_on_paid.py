"""S9 — auto_grant_on_paid subscriber tests (RED → GREEN).

Covers:
- offer.auto_grant_on_payment=True → grant_access fired on PAID event
- offer.auto_grant_on_payment=False → no auto grant (human confirmation required)
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

TENANT_ID = uuid.UUID("aaaa9020-0000-0000-0000-000000000001")
LEAD_ID = uuid.UUID("bbbb9020-0000-0000-0000-000000000001")
OFFER_ID = uuid.UUID("cccc9020-0000-0000-0000-000000000001")
PAYMENT_ID = uuid.UUID("dddd9020-0000-0000-0000-000000000001")


def _build_paid_event(auto_grant: bool = True):
    from src.shared.domain.events import PaymentReceivedEvent

    return PaymentReceivedEvent.create(
        tenant_id=TENANT_ID,
        lead_id=LEAD_ID,
        offer_id=OFFER_ID,
        payment_id=PAYMENT_ID,
        auto_grant=auto_grant,
    )


def test_auto_grant_subscriber_importable() -> None:
    from src.modules.sales_agent.application.payment_event_handlers import (
        auto_grant_on_paid,
        register_payment_subscribers,
    )


def test_auto_grant_fires_when_auto_grant_true() -> None:
    """PaymentReceivedEvent with auto_grant=True triggers grant_access."""
    from src.modules.sales_agent.application.payment_event_handlers import (
        auto_grant_on_paid,
    )

    event = _build_paid_event(auto_grant=True)

    with (
        patch("src.modules.sales_agent.application.payment_event_handlers._run_grant_access") as mock_grant,
        patch("src.modules.sales_agent.application.payment_event_handlers.SessionLocal") as mock_session,
    ):
        mock_session.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_session.return_value.__exit__ = MagicMock(return_value=False)
        auto_grant_on_paid(event)

    mock_grant.assert_called_once()


def test_auto_grant_skipped_when_auto_grant_false() -> None:
    """PaymentReceivedEvent with auto_grant=False → no grant_access."""
    from src.modules.sales_agent.application.payment_event_handlers import (
        auto_grant_on_paid,
    )

    event = _build_paid_event(auto_grant=False)

    with patch("src.modules.sales_agent.application.payment_event_handlers._run_grant_access") as mock_grant:
        auto_grant_on_paid(event)

    mock_grant.assert_not_called()


def test_payment_received_event_importable() -> None:
    from src.shared.domain.events import (
        AccessGrantedEvent,
        PaymentLinkCreatedEvent,
        PaymentReceivedEvent,
    )


def test_payment_link_created_event_fields() -> None:
    from src.shared.domain.events import PaymentLinkCreatedEvent

    event = PaymentLinkCreatedEvent.create(
        tenant_id=TENANT_ID,
        lead_id=LEAD_ID,
        external_id="mp_001",
        provider_id="mercadopago",
        url="https://mp.com/001",
        amount=100.0,
        currency="USD",
    )
    assert event.tenant_id == TENANT_ID
    assert event.lead_id == LEAD_ID
    assert event.external_id == "mp_001"


def test_access_granted_event_fields() -> None:
    from src.shared.domain.events import AccessGrantedEvent

    event = AccessGrantedEvent.create(
        tenant_id=TENANT_ID,
        lead_id=LEAD_ID,
        offer_id=OFFER_ID,
        payment_id=PAYMENT_ID,
        channels=["email"],
    )
    assert event.channels == ["email"]
    assert event.offer_id == OFFER_ID
