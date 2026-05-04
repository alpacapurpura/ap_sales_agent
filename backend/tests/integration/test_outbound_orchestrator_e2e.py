"""PR-7 Sub-B integration — OutboundOrchestrator end-to-end con DB real (SQLite in-memory).

Real DB fixtures: TenantModel + LeadModel (with telegram_id). LLM
``agent_app.ainvoke`` mocked so the test does not require real model
keys; OutputManager.process_response mocked so it doesn't hit Telegram.

Asserts:
- Tenant + lead resolved via real DB query (tenant isolation works).
- ``OutboundResult.success`` reflects the real flow.
- AsyncSession not required — sync Session path validated.

Markers: ``integration``.

# [SALES-AGENT-OUTBOUND-PR7]
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

pytestmark = pytest.mark.integration


def _ensure_tables(db):
    """Make sure CRM + IAM tables are present (they should be via session fixture)."""
    # Smoke check — fail fast if model registration regresses
    from src.modules.iam.infrastructure.models.tenant_model import TenantModel
    from src.shared.infrastructure.models.crm import LeadModel


@pytest.mark.asyncio
async def test_outbound_orchestrator_success_with_real_db_tenant_and_lead(db):
    """E2E: real Tenant + real Lead row → OutboundOrchestrator.send_outbound success."""
    from src.modules.iam.infrastructure.models.tenant_model import TenantModel
    from src.modules.sales_agent.application.orchestrator.outbound_orchestrator import (
        OutboundOrchestrator,
    )
    from src.shared.infrastructure.models.crm import CustomerProfileModel, LeadModel

    _ensure_tables(db)

    # --- Real DB fixture: tenant + customer + lead with telegram_id ---
    tenant_id = uuid4()
    tenant = TenantModel(
        id=tenant_id,
        name="Test Tenant Outbound",
        slug=f"tenant-outbound-{tenant_id.hex[:8]}",
        config_json={},
    )
    db.add(tenant)
    db.flush()

    customer = CustomerProfileModel(id=uuid4(), tenant_id=tenant_id, full_name="Cliente Test")
    db.add(customer)
    db.flush()

    lead_id = uuid4()
    lead = LeadModel(
        id=lead_id,
        tenant_id=tenant_id,
        customer_id=customer.id,
        telegram_id="987654321",
        profile_data={},
    )
    db.add(lead)
    db.flush()

    campaign_id = uuid4()
    channel_adapter = MagicMock()

    with (
        patch(
            "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.build_initial_state",
            return_value=({"messages": [], "session_id": "sess-int"}, None),
        ) as mock_build_state,
        patch(
            "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.load_checkpoint",
            return_value=None,
        ),
        patch(
            "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.build_agent_identity",
            return_value="# Identidad",
        ),
        patch(
            "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.build_brand_voice",
            return_value="# Voz",
        ),
        patch(
            "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.save_checkpoint",
        ),
        patch(
            "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.sanitize_text",
            new=AsyncMock(side_effect=lambda txt, *_a, **_kw: txt),
        ),
        patch(
            "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.build_sales_agent_observability_context",
            return_value=None,
        ),
        patch(
            "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.agent_app",
        ) as mock_app,
        patch(
            "src.modules.sales_agent.infrastructure.external.output_manager.OutputManager.process_response",
            new=AsyncMock(return_value="ext-tg-001"),
        ),
        patch(
            "src.modules.sales_agent.application.orchestrator.audit_emitter.AuditEmitter.emit_assistant_message",
            new=AsyncMock(),
        ),
    ):
        mock_app.ainvoke = AsyncMock(
            return_value={
                "messages": [{"role": "assistant", "content": "¡Hola! Tenemos novedades de la promo."}],
                "session_id": "sess-int",
                "current_state": "rapport",
                "lead_score": 0,
                "lead_data": {},
            }
        )

        result = await OutboundOrchestrator.send_outbound(
            db=db,
            tenant_id=tenant_id,
            lead_id=lead_id,
            campaign_id=campaign_id,
            campaign_instructions="Promo Black Friday — 30% off hasta viernes",
            channel_type="telegram",
            channel_adapter=channel_adapter,
        )

        # build_initial_state must have received outbound_mode=True + campaign fields
        call_kwargs = mock_build_state.call_args.kwargs
        assert call_kwargs["outbound_mode"] is True
        assert call_kwargs["campaign_id"] == campaign_id
        assert call_kwargs["campaign_instructions"].startswith("Promo Black Friday")
        # And tenant context is correct
        assert call_kwargs["tenant_uuid"] == tenant_id

    assert result.success is True
    assert result.tenant_id == tenant_id
    assert result.lead_id == lead_id
    assert result.campaign_id == campaign_id
    assert result.error_code is None


@pytest.mark.asyncio
async def test_outbound_orchestrator_tenant_isolation_real_db(db):
    """Lead from a different tenant must NOT be found (tenant isolation invariant)."""
    from src.modules.iam.infrastructure.models.tenant_model import TenantModel
    from src.modules.sales_agent.application.orchestrator.outbound_orchestrator import (
        OutboundOrchestrator,
    )
    from src.shared.infrastructure.models.crm import CustomerProfileModel, LeadModel

    _ensure_tables(db)

    # Tenant A owns the lead
    tenant_a = uuid4()
    tenant_b = uuid4()
    db.add(TenantModel(id=tenant_a, name="A", slug=f"a-{tenant_a.hex[:8]}", config_json={}))
    db.add(TenantModel(id=tenant_b, name="B", slug=f"b-{tenant_b.hex[:8]}", config_json={}))
    db.flush()

    customer = CustomerProfileModel(id=uuid4(), tenant_id=tenant_a, full_name="Cliente A")
    db.add(customer)
    db.flush()

    lead_id = uuid4()
    db.add(
        LeadModel(
            id=lead_id,
            tenant_id=tenant_a,
            customer_id=customer.id,
            telegram_id="555000",
            profile_data={},
        )
    )
    db.flush()

    # Try to send outbound for lead_id but as tenant B → must fail lead_not_found
    result = await OutboundOrchestrator.send_outbound(
        db=db,
        tenant_id=tenant_b,
        lead_id=lead_id,  # exists, but in tenant_a
        campaign_id=uuid4(),
        campaign_instructions="X",
        channel_type="telegram",
        channel_adapter=MagicMock(),
    )

    # Tenant B doesn't have a TenantModel row missing — tenant_b row was created → so we get past tenant lookup
    # But the lead query filters tenant_id == tenant_b → returns None → lead_not_found
    assert result.success is False
    assert result.error_code == "lead_not_found"
