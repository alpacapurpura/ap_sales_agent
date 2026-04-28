"""S9 — verify_payment_status tool tests (RED → GREEN).

Covers status mapping, pull-check fallback, state update.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

TENANT_ID = uuid.UUID("aaaa9003-0000-0000-0000-000000000001")
LEAD_ID = uuid.UUID("bbbb9003-0000-0000-0000-000000000001")
PAYMENT_ID = uuid.UUID("dddd9003-0000-0000-0000-000000000001")


@pytest.fixture
def populated_db(db):
    from src.modules.crm.infrastructure.models.lead_model import LeadModel
    from src.modules.iam.infrastructure.models.tenant_model import TenantModel
    from src.modules.sales_agent.infrastructure.models.agent_state_checkpoint_model import (
        AgentStateCheckpointModel,
    )
    from src.modules.sales_agent.infrastructure.models.payment_link_model import (
        PaymentLinkModel,
    )

    db.add(TenantModel(id=TENANT_ID, slug="acme", name="Acme", config_json={}))
    db.add(LeadModel(id=LEAD_ID, tenant_id=TENANT_ID))
    db.add(
        AgentStateCheckpointModel(
            id=uuid.uuid4(),
            session_id="s9-verify",
            tenant_id=TENANT_ID,
            lead_id=LEAD_ID,
            channel_type="whatsapp",
            current_stage="closing",
            scheduled_meetings=[],
            payment_state=[],
        ),
    )
    db.add(
        PaymentLinkModel(
            id=PAYMENT_ID,
            tenant_id=TENANT_ID,
            lead_id=LEAD_ID,
            offer_id=uuid.uuid4(),
            provider="mercadopago",
            external_id="mp_verify_001",
            url="https://mp.com/verify/001",
            status="pending",
            currency="USD",
            amount=100.0,
        ),
    )
    db.commit()
    return db


def _build_state(**kwargs) -> dict:
    return {
        "tenant_id": str(TENANT_ID),
        "lead_id": str(LEAD_ID),
        "_tool_args": {"payment_id": str(PAYMENT_ID), **kwargs.get("args", {})},
    }


def test_verify_payment_status_pending(populated_db) -> None:
    from src.modules.sales_agent.application.tools.payment.providers import (
        PaymentStatusEnum,
    )
    from src.modules.sales_agent.application.tools.payment.tools import (
        tool_verify_payment_status,
    )

    mock_provider = MagicMock()
    mock_provider.provider_id = "mercadopago"
    mock_provider.verify_payment.return_value = PaymentStatusEnum.PENDING

    state = _build_state()
    with patch(
        "src.modules.sales_agent.application.tools.payment.tools.payment_provider_for_tenant",
        return_value=mock_provider,
    ):
        result = tool_verify_payment_status(state, populated_db)

    assert result["status"] == "success"
    assert result["payment_status"] == "pending"


def test_verify_payment_status_paid_updates_local(populated_db) -> None:
    """Provider says PAID → local payment_link row updated to paid."""
    from src.modules.sales_agent.application.tools.payment.providers import (
        PaymentStatusEnum,
    )
    from src.modules.sales_agent.application.tools.payment.tools import (
        tool_verify_payment_status,
    )
    from src.modules.sales_agent.infrastructure.models.payment_link_model import (
        PaymentLinkModel,
    )

    mock_provider = MagicMock()
    mock_provider.provider_id = "mercadopago"
    mock_provider.verify_payment.return_value = PaymentStatusEnum.PAID

    state = _build_state()
    with patch(
        "src.modules.sales_agent.application.tools.payment.tools.payment_provider_for_tenant",
        return_value=mock_provider,
    ):
        result = tool_verify_payment_status(state, populated_db)

    assert result["payment_status"] == "paid"

    # Local DB updated
    link = populated_db.query(PaymentLinkModel).filter_by(id=PAYMENT_ID).first()
    assert link.status == "paid"


def test_verify_payment_status_not_found_returns_error(populated_db) -> None:
    from src.modules.sales_agent.application.tools.payment.tools import (
        tool_verify_payment_status,
    )

    state = _build_state(args={"payment_id": str(uuid.uuid4())})
    result = tool_verify_payment_status(state, populated_db)
    assert result["status"] == "error"


def test_verify_payment_status_no_db() -> None:
    from src.modules.sales_agent.application.tools.payment.tools import (
        tool_verify_payment_status,
    )

    result = tool_verify_payment_status(_build_state(), None)
    assert result["status"] == "error"
