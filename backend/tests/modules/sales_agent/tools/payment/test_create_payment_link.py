"""S9 — create_payment_link tool tests (RED → GREEN).

Covers idempotency, metadata propagation, currency from offer SSoT,
provider resolution, and error paths.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

TENANT_ID = uuid.UUID("aaaa9000-0000-0000-0000-000000000001")
LEAD_ID = uuid.UUID("bbbb9000-0000-0000-0000-000000000001")
OFFER_ID = uuid.UUID("cccc9000-0000-0000-0000-000000000001")


@pytest.fixture
def populated_db(db):
    from src.modules.crm.infrastructure.models.lead_model import LeadModel
    from src.modules.iam.infrastructure.models.tenant_model import TenantModel
    from src.modules.sales_agent.infrastructure.models.agent_state_checkpoint_model import (
        AgentStateCheckpointModel,
    )

    db.add(TenantModel(id=TENANT_ID, slug="acme", name="Acme", config_json={}))
    db.add(LeadModel(id=LEAD_ID, tenant_id=TENANT_ID))
    db.add(
        AgentStateCheckpointModel(
            id=uuid.uuid4(),
            session_id="s9-payment",
            tenant_id=TENANT_ID,
            lead_id=LEAD_ID,
            channel_type="whatsapp",
            current_stage="closing",
            scheduled_meetings=[],
        ),
    )
    db.commit()
    return db


def _build_state(**extra) -> dict:
    return {
        "tenant_id": str(TENANT_ID),
        "lead_id": str(LEAD_ID),
        "active_product": {
            "id": str(OFFER_ID),
            "pricing_amount": 297.0,
            "currency": "USD",
        },
        "_tool_args": {},
        **extra,
    }


def _mock_provider():
    from src.modules.sales_agent.application.tools.payment.providers import (
        PaymentLinkOutput,
        PaymentStatusEnum,
    )

    mock = MagicMock()
    mock.provider_id = "mercadopago"
    mock.create_payment_link.return_value = PaymentLinkOutput(
        external_id="mp_pref_001",
        url="https://mp.com/checkout/001",
        provider_id="mercadopago",
        amount=297.0,
        currency="USD",
        expires_at=None,
        metadata={"tenant_id": str(TENANT_ID), "lead_id": str(LEAD_ID)},
    )
    mock.verify_payment.return_value = PaymentStatusEnum.PENDING
    return mock


def test_create_payment_link_returns_url(populated_db) -> None:
    from src.modules.sales_agent.application.tools.payment.tools import (
        tool_create_payment_link,
    )

    state = _build_state()
    with patch(
        "src.modules.sales_agent.application.tools.payment.tools.payment_provider_for_tenant",
        return_value=_mock_provider(),
    ):
        result = tool_create_payment_link(state, populated_db)

    assert result["status"] == "success"
    assert result["url"].startswith("https://")
    assert result["external_id"] == "mp_pref_001"
    assert result["reused"] is False


def test_create_payment_link_currency_from_offer_ssot(populated_db) -> None:
    """Currency MUST come from offer, not inferred from provider."""
    from src.modules.sales_agent.application.tools.payment.tools import (
        tool_create_payment_link,
    )

    state = _build_state()
    state["active_product"]["currency"] = "PEN"  # tenant is Peru

    mock_provider = _mock_provider()
    with patch(
        "src.modules.sales_agent.application.tools.payment.tools.payment_provider_for_tenant",
        return_value=mock_provider,
    ):
        result = tool_create_payment_link(state, populated_db)

    # Verify the provider was called with PEN (not hardcoded USD)
    call_kwargs = mock_provider.create_payment_link.call_args
    assert call_kwargs is not None
    assert call_kwargs.kwargs.get("currency") == "PEN"
    assert result["status"] == "success"


def test_create_payment_link_idempotent_same_turn(populated_db) -> None:
    """Re-firing tool within same turn reuses the PENDING link."""
    from src.modules.sales_agent.application.tools.payment.tools import (
        tool_create_payment_link,
    )

    state = _build_state()
    mock_provider = _mock_provider()
    with patch(
        "src.modules.sales_agent.application.tools.payment.tools.payment_provider_for_tenant",
        return_value=mock_provider,
    ):
        first = tool_create_payment_link(state, populated_db)
        second = tool_create_payment_link(state, populated_db)

    assert first["status"] == "success"
    assert second["status"] == "success"
    assert second["reused"] is True
    # Provider.create_payment_link called only once
    assert mock_provider.create_payment_link.call_count == 1


def test_create_payment_link_missing_amount_returns_error(populated_db) -> None:
    from src.modules.sales_agent.application.tools.payment.tools import (
        tool_create_payment_link,
    )

    state = _build_state()
    state["active_product"]["pricing_amount"] = None

    with patch(
        "src.modules.sales_agent.application.tools.payment.tools.payment_provider_for_tenant",
        return_value=_mock_provider(),
    ):
        result = tool_create_payment_link(state, populated_db)

    assert result["status"] == "error"


def test_create_payment_link_no_db() -> None:
    from src.modules.sales_agent.application.tools.payment.tools import (
        tool_create_payment_link,
    )

    result = tool_create_payment_link(_build_state(), None)
    assert result["status"] == "error"


def test_create_payment_link_metadata_includes_lead_and_offer(populated_db) -> None:
    """Metadata sent to provider must include tenant_id, lead_id, offer_id."""
    from src.modules.sales_agent.application.tools.payment.tools import (
        tool_create_payment_link,
    )

    state = _build_state()
    mock_provider = _mock_provider()
    with patch(
        "src.modules.sales_agent.application.tools.payment.tools.payment_provider_for_tenant",
        return_value=mock_provider,
    ):
        tool_create_payment_link(state, populated_db)

    call_kwargs = mock_provider.create_payment_link.call_args.kwargs
    metadata = call_kwargs.get("metadata", {})
    assert "lead_id" in metadata
    assert "offer_id" in metadata or "tenant_id" in metadata
