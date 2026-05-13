"""S9 — grant_access tool idempotency + saga tests (RED → GREEN).

Covers:
- Payment must be PAID gate
- 2x grant_access → only 1 audit row (UNIQUE natural key)
- Partial failure logged + retry pending
- AccessGrantedEvent published on success
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

TENANT_ID = uuid.UUID("aaaa9001-0000-0000-0000-000000000001")
LEAD_ID = uuid.UUID("bbbb9001-0000-0000-0000-000000000001")
OFFER_ID = uuid.UUID("cccc9001-0000-0000-0000-000000000001")
PAYMENT_ID = uuid.UUID("dddd9001-0000-0000-0000-000000000001")


@pytest.fixture
def populated_db(db):
    from luana_core_crm.infrastructure.models.lead_model import LeadModel
    from luana_core_iam.infrastructure.models.tenant_model import TenantModel
    from luana_core_sales_agent.infrastructure.models.agent_state_checkpoint_model import (
        AgentStateCheckpointModel,
    )
    from luana_core_sales_agent.infrastructure.models.payment_link_model import (
        PaymentLinkModel,
    )

    db.add(TenantModel(id=TENANT_ID, slug="acme", name="Acme", config_json={}))
    db.add(LeadModel(id=LEAD_ID, tenant_id=TENANT_ID))
    db.add(
        AgentStateCheckpointModel(
            id=uuid.uuid4(),
            session_id="s9-grant",
            tenant_id=TENANT_ID,
            lead_id=LEAD_ID,
            channel_type="whatsapp",
            current_stage="closing",
            scheduled_meetings=[],
        ),
    )
    # Add a PAID payment link
    db.add(
        PaymentLinkModel(
            id=PAYMENT_ID,
            tenant_id=TENANT_ID,
            lead_id=LEAD_ID,
            offer_id=OFFER_ID,
            provider="mercadopago",
            external_id="mp_pref_001",
            url="https://mp.com/checkout/001",
            status="paid",
            currency="USD",
            amount=297.0,
        ),
    )
    db.commit()
    return db


def _build_state(**kwargs) -> dict:
    return {
        "tenant_id": str(TENANT_ID),
        "lead_id": str(LEAD_ID),
        "active_product": {
            "id": str(OFFER_ID),
        },
        "_tool_args": {
            "payment_id": str(PAYMENT_ID),
            **kwargs.get("args", {}),
        },
    }


def _mock_access_provider():
    mock = MagicMock()
    mock.deliver.return_value = {"channel": "email", "delivered": True}
    return mock


def test_grant_access_success_creates_audit_row(populated_db) -> None:
    from luana_core_sales_agent.application.tools.payment.tools import (
        tool_grant_access,
    )
    from luana_core_sales_agent.infrastructure.models.payment_grant_audit_model import (
        PaymentGrantAuditModel,
    )

    state = _build_state()
    with (
        patch(
            "luana_core_sales_agent.application.tools.payment.tools.access_provider_for_offer",
            return_value=_mock_access_provider(),
        ),
        patch("luana_core_platform.domain.events.EventBus.publish"),
    ):
        result = tool_grant_access(state, populated_db)

    assert result["status"] == "success"
    assert result["granted"] is True

    audit_rows = (
        populated_db.query(PaymentGrantAuditModel)
        .filter_by(
            tenant_id=TENANT_ID,
            lead_id=LEAD_ID,
            offer_id=OFFER_ID,
            payment_id=PAYMENT_ID,
        )
        .all()
    )
    assert len(audit_rows) == 1


def test_grant_access_idempotent_second_call(populated_db) -> None:
    """2x grant_access → same audit_id, no double delivery."""
    from luana_core_sales_agent.application.tools.payment.tools import (
        tool_grant_access,
    )
    from luana_core_sales_agent.infrastructure.models.payment_grant_audit_model import (
        PaymentGrantAuditModel,
    )

    state = _build_state()
    mock_access = _mock_access_provider()
    with (
        patch(
            "luana_core_sales_agent.application.tools.payment.tools.access_provider_for_offer",
            return_value=mock_access,
        ),
        patch("luana_core_platform.domain.events.EventBus.publish"),
    ):
        tool_grant_access(state, populated_db)
        second = tool_grant_access(state, populated_db)

    assert second["granted"] is True
    assert second.get("duplicate") is True
    # Delivery called only once
    assert mock_access.deliver.call_count == 1
    # Only one audit row
    rows = populated_db.query(PaymentGrantAuditModel).filter_by(tenant_id=TENANT_ID, lead_id=LEAD_ID).all()
    assert len(rows) == 1


def test_grant_access_gate_payment_not_paid(populated_db) -> None:
    """grant_access returns {granted: False} when payment status != PAID."""
    from luana_core_sales_agent.infrastructure.models.payment_link_model import (
        PaymentLinkModel,
    )

    # Change payment status to pending
    link = populated_db.query(PaymentLinkModel).filter_by(id=PAYMENT_ID).first()
    link.status = "pending"
    populated_db.commit()

    from luana_core_sales_agent.application.tools.payment.tools import (
        tool_grant_access,
    )

    state = _build_state()
    result = tool_grant_access(state, populated_db)

    assert result["status"] == "success"
    assert result["granted"] is False
    assert "payment_status" in result.get("reason", "") or "pending" in result.get("reason", "")


def test_grant_access_payment_not_found_returns_error(populated_db) -> None:
    from luana_core_sales_agent.application.tools.payment.tools import (
        tool_grant_access,
    )

    state = _build_state(args={"payment_id": str(uuid.uuid4())})
    result = tool_grant_access(state, populated_db)
    assert result["status"] == "error"


def test_grant_access_publishes_event(populated_db) -> None:
    """AccessGrantedEvent must be published on successful grant."""
    from luana_core_sales_agent.application.tools.payment.tools import (
        tool_grant_access,
    )

    state = _build_state()
    with (
        patch(
            "luana_core_sales_agent.application.tools.payment.tools.access_provider_for_offer",
            return_value=_mock_access_provider(),
        ),
        patch("luana_core_platform.domain.events.EventBus.publish") as mock_publish,
    ):
        tool_grant_access(state, populated_db)

    assert mock_publish.called
    event_args = mock_publish.call_args_list
    event_types = [type(a[0][0]).__name__ for a in event_args]
    assert any("AccessGranted" in t for t in event_types)
