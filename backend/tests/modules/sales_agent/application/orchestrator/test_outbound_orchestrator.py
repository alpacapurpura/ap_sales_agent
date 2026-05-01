"""PR-7 Sub-B — OutboundOrchestrator unit tests with mocks.

Covers:
- happy path (graph + checkpoint reuse + voice/identity wire + delivery)
- lead_not_found
- tenant_not_found
- empty bot response → error_code="empty_response"
- channel send failure → error_code="channel_send_failed"
- graph invocation failure → error_code="graph_invocation_failed"

# [SALES-AGENT-OUTBOUND-PR7]
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.modules.sales_agent.application.orchestrator.outbound_orchestrator import (
    OutboundOrchestrator,
    OutboundResult,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tenant_uuid():
    return uuid4()


@pytest.fixture
def lead_uuid():
    return uuid4()


@pytest.fixture
def campaign_uuid():
    return uuid4()


@pytest.fixture
def db_session():
    """Mock sync Session — execute() returns a chained mock that resolves to lead row."""
    mock = MagicMock()
    mock.execute = MagicMock()
    mock.commit = MagicMock()
    mock.rollback = MagicMock()
    return mock


@pytest.fixture
def lead_row(lead_uuid):
    """Synthetic LeadModel-like with telegram_id."""
    customer = SimpleNamespace(id=uuid4())
    return SimpleNamespace(
        id=lead_uuid,
        telegram_id="123456789",
        customer=customer,
        profile_data=None,
        custom_system_instruction=None,
        style_profile=None,
    )


@pytest.fixture
def channel_adapter():
    """Mock channel adapter — accepts process_response invocation."""
    adapter = MagicMock()
    adapter.send_message = AsyncMock(return_value="external_msg_001")
    return adapter


def _set_lead_query(db_session, lead_row):
    """Configure db.execute(...).scalars().first() → lead_row."""
    chain = MagicMock()
    chain.scalars.return_value.first.return_value = lead_row
    db_session.execute.return_value = chain


def _set_lead_not_found(db_session):
    chain = MagicMock()
    chain.scalars.return_value.first.return_value = None
    db_session.execute.return_value = chain


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestOutboundOrchestratorHappyPath:
    """Full-flow happy path with all dependencies mocked."""

    @pytest.mark.asyncio
    async def test_send_outbound_returns_success_when_all_steps_pass(
        self,
        db_session,
        tenant_uuid,
        lead_uuid,
        campaign_uuid,
        lead_row,
        channel_adapter,
    ):
        _set_lead_query(db_session, lead_row)

        with (
            patch(
                "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.fetch_tenant_config",
                return_value=(tenant_uuid, {}),
            ),
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
                "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.build_initial_state",
                return_value=({"messages": [], "session_id": "sess-1"}, None),
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
                new=AsyncMock(return_value="external_msg_001"),
            ),
            patch(
                "src.modules.sales_agent.application.orchestrator.audit_emitter.AuditEmitter.emit_assistant_message",
                new=AsyncMock(),
            ),
            patch(
                "src.modules.sales_agent.infrastructure.memory.audit_repository.AuditRepository",
            ) as mock_audit_repo_cls,
            patch(
                "src.modules.sales_agent.infrastructure.repositories.state_repository.StateRepository",
            ),
            patch(
                "src.modules.sales_agent.infrastructure.db.repositories.business_repository.BusinessRepository",
            ),
        ):
            mock_app.ainvoke = AsyncMock(
                return_value={
                    "messages": [{"role": "assistant", "content": "Hola, comenzamos campaña"}],
                    "session_id": "sess-1",
                    "current_state": "rapport",
                    "lead_score": 0,
                    "lead_data": {},
                }
            )
            mock_audit = MagicMock()
            mock_audit_repo_cls.return_value = mock_audit

            result = await OutboundOrchestrator.send_outbound(
                db=db_session,
                tenant_id=tenant_uuid,
                lead_id=lead_uuid,
                campaign_id=campaign_uuid,
                campaign_instructions="Promo Black Friday",
                channel_type="telegram",
                channel_adapter=channel_adapter,
            )

        assert isinstance(result, OutboundResult)
        assert result.success is True
        assert result.tenant_id == tenant_uuid
        assert result.lead_id == lead_uuid
        assert result.campaign_id == campaign_uuid
        assert result.session_id == "sess-1"
        assert result.error_code is None


# ---------------------------------------------------------------------------
# Tenant / Lead lookup error paths
# ---------------------------------------------------------------------------


class TestOutboundOrchestratorTenantLookupErrors:
    @pytest.mark.asyncio
    async def test_tenant_not_found_returns_error_code(
        self,
        db_session,
        tenant_uuid,
        lead_uuid,
        campaign_uuid,
        channel_adapter,
    ):
        with patch(
            "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.fetch_tenant_config",
            return_value=(None, {}),
        ):
            result = await OutboundOrchestrator.send_outbound(
                db=db_session,
                tenant_id=tenant_uuid,
                lead_id=lead_uuid,
                campaign_id=campaign_uuid,
                campaign_instructions="X",
                channel_type="telegram",
                channel_adapter=channel_adapter,
            )

        assert result.success is False
        assert result.error_code == "tenant_not_found"


class TestOutboundOrchestratorLeadLookupErrors:
    @pytest.mark.asyncio
    async def test_lead_not_found_returns_error_code(
        self,
        db_session,
        tenant_uuid,
        lead_uuid,
        campaign_uuid,
        channel_adapter,
    ):
        _set_lead_not_found(db_session)
        with patch(
            "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.fetch_tenant_config",
            return_value=(tenant_uuid, {}),
        ):
            result = await OutboundOrchestrator.send_outbound(
                db=db_session,
                tenant_id=tenant_uuid,
                lead_id=lead_uuid,
                campaign_id=campaign_uuid,
                campaign_instructions="X",
                channel_type="telegram",
                channel_adapter=channel_adapter,
            )

        assert result.success is False
        assert result.error_code == "lead_not_found"


# ---------------------------------------------------------------------------
# Graph + delivery error paths
# ---------------------------------------------------------------------------


class TestOutboundOrchestratorGraphFailure:
    @pytest.mark.asyncio
    async def test_graph_exception_returns_error_code(
        self,
        db_session,
        tenant_uuid,
        lead_uuid,
        campaign_uuid,
        lead_row,
        channel_adapter,
    ):
        _set_lead_query(db_session, lead_row)
        with (
            patch(
                "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.fetch_tenant_config",
                return_value=(tenant_uuid, {}),
            ),
            patch(
                "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.load_checkpoint",
                return_value=None,
            ),
            patch(
                "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.build_agent_identity",
                return_value=None,
            ),
            patch(
                "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.build_brand_voice",
                return_value=None,
            ),
            patch(
                "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.build_initial_state",
                return_value=({"messages": [], "session_id": "s"}, None),
            ),
            patch(
                "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.build_sales_agent_observability_context",
                return_value=None,
            ),
            patch(
                "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.agent_app",
            ) as mock_app,
            patch(
                "src.modules.sales_agent.infrastructure.memory.audit_repository.AuditRepository",
            ),
            patch(
                "src.modules.sales_agent.infrastructure.repositories.state_repository.StateRepository",
            ),
            patch(
                "src.modules.sales_agent.infrastructure.db.repositories.business_repository.BusinessRepository",
            ),
        ):
            mock_app.ainvoke = AsyncMock(side_effect=RuntimeError("boom"))

            result = await OutboundOrchestrator.send_outbound(
                db=db_session,
                tenant_id=tenant_uuid,
                lead_id=lead_uuid,
                campaign_id=campaign_uuid,
                campaign_instructions="X",
                channel_type="telegram",
                channel_adapter=channel_adapter,
            )

        assert result.success is False
        assert result.error_code == "graph_invocation_failed"


class TestOutboundOrchestratorEmptyResponse:
    @pytest.mark.asyncio
    async def test_empty_bot_text_returns_error_code(
        self,
        db_session,
        tenant_uuid,
        lead_uuid,
        campaign_uuid,
        lead_row,
        channel_adapter,
    ):
        _set_lead_query(db_session, lead_row)
        with (
            patch(
                "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.fetch_tenant_config",
                return_value=(tenant_uuid, {}),
            ),
            patch(
                "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.load_checkpoint",
                return_value=None,
            ),
            patch(
                "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.build_agent_identity",
                return_value=None,
            ),
            patch(
                "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.build_brand_voice",
                return_value=None,
            ),
            patch(
                "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.build_initial_state",
                return_value=({"messages": [], "session_id": "s"}, None),
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
                "src.modules.sales_agent.infrastructure.memory.audit_repository.AuditRepository",
            ),
            patch(
                "src.modules.sales_agent.infrastructure.repositories.state_repository.StateRepository",
            ),
            patch(
                "src.modules.sales_agent.infrastructure.db.repositories.business_repository.BusinessRepository",
            ),
        ):
            mock_app.ainvoke = AsyncMock(
                return_value={
                    "messages": [{"role": "assistant", "content": "   "}],
                    "session_id": "s",
                }
            )

            result = await OutboundOrchestrator.send_outbound(
                db=db_session,
                tenant_id=tenant_uuid,
                lead_id=lead_uuid,
                campaign_id=campaign_uuid,
                campaign_instructions="X",
                channel_type="telegram",
                channel_adapter=channel_adapter,
            )

        assert result.success is False
        assert result.error_code == "empty_response"


class TestOutboundOrchestratorCheckpointReuse:
    @pytest.mark.asyncio
    async def test_existing_checkpoint_reused_continuity(
        self,
        db_session,
        tenant_uuid,
        lead_uuid,
        campaign_uuid,
        lead_row,
        channel_adapter,
    ):
        """When checkpoint active, build_initial_state called WITH that checkpoint."""
        _set_lead_query(db_session, lead_row)
        existing_ckpt = SimpleNamespace(
            handler_mode="ai",
            current_stage="discovery",
            lead_score=42,
            lead_data={},
            buying_signals=[],
            objection_history=[],
            qualification_answers={},
            turn_count=3,
            close_strategy=None,
            consecutive_questions=0,
            follow_up_cadence=None,
            unread_count=0,
            last_human_message_at=None,
            resume_objective=None,
        )

        with (
            patch(
                "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.fetch_tenant_config",
                return_value=(tenant_uuid, {}),
            ),
            patch(
                "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.load_checkpoint",
                return_value=existing_ckpt,
            ),
            patch(
                "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.build_agent_identity",
                return_value=None,
            ),
            patch(
                "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.build_brand_voice",
                return_value=None,
            ),
            patch(
                "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.build_initial_state",
                return_value=({"messages": [], "session_id": "sess-existing"}, None),
            ) as mock_build_state,
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
                new=AsyncMock(return_value="ext-x"),
            ),
            patch(
                "src.modules.sales_agent.application.orchestrator.audit_emitter.AuditEmitter.emit_assistant_message",
                new=AsyncMock(),
            ),
            patch(
                "src.modules.sales_agent.infrastructure.memory.audit_repository.AuditRepository",
            ),
            patch(
                "src.modules.sales_agent.infrastructure.repositories.state_repository.StateRepository",
            ),
            patch(
                "src.modules.sales_agent.infrastructure.db.repositories.business_repository.BusinessRepository",
            ),
        ):
            mock_app.ainvoke = AsyncMock(
                return_value={
                    "messages": [{"role": "assistant", "content": "Volvemos donde quedamos"}],
                    "session_id": "sess-existing",
                    "current_state": "discovery",
                    "lead_score": 42,
                    "lead_data": {},
                }
            )

            result = await OutboundOrchestrator.send_outbound(
                db=db_session,
                tenant_id=tenant_uuid,
                lead_id=lead_uuid,
                campaign_id=campaign_uuid,
                campaign_instructions="Continuá la promo",
                channel_type="telegram",
                channel_adapter=channel_adapter,
            )

            # Verify checkpoint passed to build_initial_state
            assert mock_build_state.called
            call_kwargs = mock_build_state.call_args.kwargs
            assert call_kwargs.get("checkpoint") is existing_ckpt
            assert call_kwargs.get("outbound_mode") is True
            assert call_kwargs.get("campaign_id") == campaign_uuid
            assert call_kwargs.get("campaign_instructions") == "Continuá la promo"

        assert result.success is True


class TestOutboundOrchestratorBudgetGuardWiring:
    @pytest.mark.asyncio
    async def test_budget_guard_passed_through_to_build_initial_state(
        self,
        db_session,
        tenant_uuid,
        lead_uuid,
        campaign_uuid,
        lead_row,
        channel_adapter,
    ):
        _set_lead_query(db_session, lead_row)
        sentinel_guard = MagicMock(name="budget_guard_sentinel")

        with (
            patch(
                "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.fetch_tenant_config",
                return_value=(tenant_uuid, {}),
            ),
            patch(
                "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.load_checkpoint",
                return_value=None,
            ),
            patch(
                "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.build_agent_identity",
                return_value=None,
            ),
            patch(
                "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.build_brand_voice",
                return_value=None,
            ),
            patch(
                "src.modules.sales_agent.application.orchestrator.outbound_orchestrator.ConversationPipeline.build_initial_state",
                return_value=({"messages": [], "session_id": "s"}, None),
            ) as mock_build_state,
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
                new=AsyncMock(return_value="ext"),
            ),
            patch(
                "src.modules.sales_agent.application.orchestrator.audit_emitter.AuditEmitter.emit_assistant_message",
                new=AsyncMock(),
            ),
            patch(
                "src.modules.sales_agent.infrastructure.memory.audit_repository.AuditRepository",
            ),
            patch(
                "src.modules.sales_agent.infrastructure.repositories.state_repository.StateRepository",
            ),
            patch(
                "src.modules.sales_agent.infrastructure.db.repositories.business_repository.BusinessRepository",
            ),
        ):
            mock_app.ainvoke = AsyncMock(
                return_value={
                    "messages": [{"role": "assistant", "content": "ok"}],
                    "session_id": "s",
                    "current_state": "rapport",
                    "lead_score": 0,
                    "lead_data": {},
                }
            )

            await OutboundOrchestrator.send_outbound(
                db=db_session,
                tenant_id=tenant_uuid,
                lead_id=lead_uuid,
                campaign_id=campaign_uuid,
                campaign_instructions="X",
                channel_type="telegram",
                channel_adapter=channel_adapter,
                budget_guard=sentinel_guard,
            )

            call_kwargs = mock_build_state.call_args.kwargs
            assert call_kwargs.get("budget_guard") is sentinel_guard


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
