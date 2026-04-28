"""S9 — PaymentStateService JSONB SSoT tests (RED → GREEN).

Mirrors test_meeting_state_service.py pattern from S8.
"""

from __future__ import annotations

import uuid

import pytest

TENANT_ID = uuid.UUID("aaaa9002-0000-0000-0000-000000000001")
LEAD_ID = uuid.UUID("bbbb9002-0000-0000-0000-000000000001")


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
            session_id="s9-state",
            tenant_id=TENANT_ID,
            lead_id=LEAD_ID,
            channel_type="whatsapp",
            current_stage="closing",
            scheduled_meetings=[],
            payment_state=[],
        ),
    )
    db.commit()
    return db


def test_payment_state_service_importable() -> None:
    from src.modules.sales_agent.application.services.payment_state_service import (
        PaymentEntry,
        PaymentEntryStatus,
        PaymentStateService,
    )


def test_append_link_creates_entry(populated_db) -> None:
    import datetime as dt

    from src.modules.sales_agent.application.services.payment_state_service import (
        PaymentStateService,
    )
    from src.modules.sales_agent.application.tools.payment.providers import (
        PaymentLinkOutput,
    )

    service = PaymentStateService(populated_db)
    link = PaymentLinkOutput(
        external_id="mp_001",
        url="https://mp.com/001",
        provider_id="mercadopago",
        amount=100.0,
        currency="USD",
        expires_at=dt.datetime.now(dt.UTC) + dt.timedelta(hours=24),
        metadata={},
    )
    entry = service.append_link(TENANT_ID, LEAD_ID, link)
    assert entry.external_id == "mp_001"
    assert entry.status.value == "link_created"


def test_find_pending_link_returns_existing(populated_db) -> None:
    import datetime as dt

    from src.modules.sales_agent.application.services.payment_state_service import (
        PaymentStateService,
    )
    from src.modules.sales_agent.application.tools.payment.providers import (
        PaymentLinkOutput,
    )

    service = PaymentStateService(populated_db)
    link = PaymentLinkOutput(
        external_id="mp_002",
        url="https://mp.com/002",
        provider_id="mercadopago",
        amount=200.0,
        currency="PEN",
        expires_at=dt.datetime.now(dt.UTC) + dt.timedelta(hours=24),
        metadata={},
    )
    service.append_link(TENANT_ID, LEAD_ID, link)
    populated_db.commit()

    existing = service.find_pending_link(TENANT_ID, LEAD_ID, "mercadopago")
    assert existing is not None
    assert existing.external_id == "mp_002"


def test_update_status_by_external_id(populated_db) -> None:
    import datetime as dt

    from src.modules.sales_agent.application.services.payment_state_service import (
        PaymentEntryStatus,
        PaymentStateService,
    )
    from src.modules.sales_agent.application.tools.payment.providers import (
        PaymentLinkOutput,
    )

    service = PaymentStateService(populated_db)
    link = PaymentLinkOutput(
        external_id="mp_003",
        url="https://mp.com/003",
        provider_id="mercadopago",
        amount=50.0,
        currency="ARS",
        expires_at=dt.datetime.now(dt.UTC) + dt.timedelta(hours=24),
        metadata={},
    )
    service.append_link(TENANT_ID, LEAD_ID, link)
    populated_db.commit()

    updated = service.update_status_by_external_id(
        TENANT_ID,
        LEAD_ID,
        external_id="mp_003",
        status=PaymentEntryStatus.PAID,
    )
    assert updated is not None
    assert updated.status == PaymentEntryStatus.PAID
