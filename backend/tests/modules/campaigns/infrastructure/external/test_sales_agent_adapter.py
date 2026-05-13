"""Tests for SalesAgentAdapter — campaigns/infrastructure/external.

TDD RED → GREEN per layer.

Covers:
- dispatch happy path: OutboundOrchestrator mock returns success
- dispatch step_type mismatch: raises ValueError (caller bug)
- dispatch agent_kind unsupported: returns failure result
- dispatch OutboundOrchestrator raises: returns failure with error_code="adapter_failure"

PR-7 Sub-D PI-1 S3.
"""

from __future__ import annotations

import datetime as dt
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from luana_core_campaigns.domain.campaign_step import CampaignStep
from luana_core_campaigns.domain.campaign_task import CampaignTask
from luana_core_campaigns.domain.enums import StepType, TaskStatus
from luana_core_campaigns.infrastructure.external.sales_agent_adapter import (
    SalesAgentAdapter,
    SalesAgentDispatchResult,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

_NOW = dt.datetime(2026, 4, 30, 12, 0, 0, tzinfo=dt.timezone.utc)

_REGISTRY_PATH = "luana_core_campaigns.infrastructure.channels.registry.ChannelRouterRegistry"
_ORCHESTRATOR_PATH = (
    "luana_core_sales_agent.application.orchestrator.outbound_orchestrator.OutboundOrchestrator.send_outbound"
)
_SYNC_DB_PATH = "luana_core_campaigns.infrastructure.external.sales_agent_adapter.SalesAgentAdapter._create_sync_db"


def _make_task(
    *,
    tenant_id: UUID | None = None,
    lead_id: UUID | None = None,
    campaign_id: UUID | None = None,
    step_id: UUID | None = None,
) -> CampaignTask:
    """Factory for a minimal CampaignTask domain object."""
    tid = tenant_id or uuid4()
    lid = lead_id or uuid4()
    cid = campaign_id or uuid4()
    sid = step_id or uuid4()
    return CampaignTask(
        id=uuid4(),
        tenant_id=tid,
        campaign_id=cid,
        lead_id=lid,
        step_id=sid,
        status=TaskStatus.PENDING,
        scheduled_at=_NOW,
        idempotency_key=f"task:{cid}:{lid}:{sid}",
        created_at=_NOW,
        updated_at=_NOW,
    )


def _make_step(
    *,
    step_type: StepType = StepType.CALL_SUBAGENT_BRIEF,
    step_config: dict | None = None,
    tenant_id: UUID | None = None,
    campaign_id: UUID | None = None,
) -> CampaignStep:
    """Factory for a minimal CampaignStep domain object."""
    tid = tenant_id or uuid4()
    cid = campaign_id or uuid4()
    cfg = step_config if step_config is not None else {"agent_kind": "sales_agent", "brief": "Di hola"}
    return CampaignStep(
        id=uuid4(),
        tenant_id=tid,
        campaign_id=cid,
        step_type=step_type,
        step_index=0,
        step_config=cfg,
        created_at=_NOW,
        updated_at=_NOW,
    )


def _make_sync_db_ctx() -> MagicMock:
    """Return a MagicMock context manager simulating _create_sync_db."""
    mock_db = MagicMock()
    mock_db.__enter__ = MagicMock(return_value=mock_db)
    mock_db.__exit__ = MagicMock(return_value=False)
    return mock_db


def _make_mock_registry() -> MagicMock:
    """Return a MagicMock ChannelRouterRegistry with a stub router."""
    mock_registry = MagicMock()
    mock_registry.get.return_value = MagicMock()
    return mock_registry


# ── Tests ──────────────────────────────────────────────────────────────────────


class TestSalesAgentAdapterStepTypeGuard:
    """step_type != CALL_SUBAGENT_BRIEF must raise ValueError (caller bug)."""

    @pytest.mark.asyncio
    async def test_wrong_step_type_raises_value_error(self) -> None:
        """Dispatch with SEND_MESSAGE step_type raises ValueError."""
        session = MagicMock()
        task = _make_task()
        step = _make_step(step_type=StepType.SEND_MESSAGE, step_config={"template_slug": "hi"})

        with pytest.raises(ValueError, match="CALL_SUBAGENT_BRIEF"):
            await SalesAgentAdapter.dispatch(
                session=session,
                task=task,
                step=step,
                budget_guard=None,
            )

    @pytest.mark.asyncio
    async def test_wait_delay_step_type_raises_value_error(self) -> None:
        """Dispatch with WAIT_DELAY step_type raises ValueError."""
        session = MagicMock()
        task = _make_task()
        step = _make_step(
            step_type=StepType.WAIT_DELAY,
            step_config={"delay_seconds": 60},
        )

        with pytest.raises(ValueError, match="CALL_SUBAGENT_BRIEF"):
            await SalesAgentAdapter.dispatch(
                session=session,
                task=task,
                step=step,
                budget_guard=None,
            )


class TestSalesAgentAdapterUnsupportedAgentKind:
    """agent_kind != 'sales_agent' returns failure SalesAgentDispatchResult."""

    @pytest.mark.asyncio
    async def test_unsupported_agent_kind_returns_failure(self) -> None:
        """Dispatch with agent_kind='whatsapp_agent' returns failure."""
        session = MagicMock()
        task = _make_task()
        step = _make_step(
            step_config={"agent_kind": "whatsapp_agent", "brief": "Saluda al lead"},
        )

        result = await SalesAgentAdapter.dispatch(
            session=session,
            task=task,
            step=step,
            budget_guard=None,
        )

        assert isinstance(result, SalesAgentDispatchResult)
        assert result.success is False
        assert result.error_code == "unsupported_agent_kind"
        assert result.external_message_id is None

    @pytest.mark.asyncio
    async def test_missing_agent_kind_defaults_to_sales_agent(self) -> None:
        """step_config with no 'agent_kind' key defaults to 'sales_agent' — proceeds."""
        session = MagicMock()
        task = _make_task()
        # No 'agent_kind' key in config — defaults to "sales_agent"
        step = _make_step(step_config={"brief": "Hola al lead"})

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.external_message_id = "msg-123"
        mock_result.error_code = None
        mock_result.error_message = None

        mock_sync_db = _make_sync_db_ctx()
        mock_registry = _make_mock_registry()

        with (
            patch(_SYNC_DB_PATH, return_value=mock_sync_db),
            patch(_REGISTRY_PATH, return_value=mock_registry),
            patch(_ORCHESTRATOR_PATH, new_callable=AsyncMock, return_value=mock_result),
        ):
            result = await SalesAgentAdapter.dispatch(
                session=session,
                task=task,
                step=step,
                budget_guard=None,
            )

        assert result.success is True
        assert result.external_message_id == "msg-123"


class TestSalesAgentAdapterHappyPath:
    """Dispatch happy path: OutboundOrchestrator mock returns success."""

    @pytest.mark.asyncio
    async def test_dispatch_happy_path_returns_success(self) -> None:
        """dispatch returns SalesAgentDispatchResult(success=True) when orchestrator succeeds."""
        session = MagicMock()
        task = _make_task()
        step = _make_step(
            step_config={"agent_kind": "sales_agent", "brief": "Saluda al lead y presenta el servicio."},
        )

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.external_message_id = "tg-msg-abc123"
        mock_result.error_code = None
        mock_result.error_message = None

        mock_sync_db = _make_sync_db_ctx()
        mock_registry = _make_mock_registry()

        with (
            patch(_SYNC_DB_PATH, return_value=mock_sync_db),
            patch(_REGISTRY_PATH, return_value=mock_registry),
            patch(_ORCHESTRATOR_PATH, new_callable=AsyncMock, return_value=mock_result),
        ):
            result = await SalesAgentAdapter.dispatch(
                session=session,
                task=task,
                step=step,
                budget_guard=None,
            )

        assert isinstance(result, SalesAgentDispatchResult)
        assert result.success is True
        assert result.external_message_id == "tg-msg-abc123"
        assert result.error_code is None

    @pytest.mark.asyncio
    async def test_dispatch_propagates_orchestrator_failure(self) -> None:
        """When orchestrator returns success=False, adapter returns failure result."""
        session = MagicMock()
        task = _make_task()
        step = _make_step()

        mock_result = MagicMock()
        mock_result.success = False
        mock_result.external_message_id = None
        mock_result.error_code = "lead_not_found"
        mock_result.error_message = "Lead does not exist"

        mock_sync_db = _make_sync_db_ctx()
        mock_registry = _make_mock_registry()

        with (
            patch(_SYNC_DB_PATH, return_value=mock_sync_db),
            patch(_REGISTRY_PATH, return_value=mock_registry),
            patch(_ORCHESTRATOR_PATH, new_callable=AsyncMock, return_value=mock_result),
        ):
            result = await SalesAgentAdapter.dispatch(
                session=session,
                task=task,
                step=step,
                budget_guard=None,
            )

        assert result.success is False
        assert result.error_code == "lead_not_found"


class TestSalesAgentAdapterOrchestratorRaises:
    """OutboundOrchestrator raises exception → failure with error_code='adapter_failure'."""

    @pytest.mark.asyncio
    async def test_orchestrator_raises_returns_adapter_failure(self) -> None:
        """When OutboundOrchestrator.send_outbound raises, adapter returns adapter_failure."""
        session = MagicMock()
        task = _make_task()
        step = _make_step()

        mock_sync_db = _make_sync_db_ctx()
        mock_registry = _make_mock_registry()

        with (
            patch(_SYNC_DB_PATH, return_value=mock_sync_db),
            patch(_REGISTRY_PATH, return_value=mock_registry),
            patch(
                _ORCHESTRATOR_PATH,
                new_callable=AsyncMock,
                side_effect=RuntimeError("LangGraph graph crashed"),
            ),
        ):
            result = await SalesAgentAdapter.dispatch(
                session=session,
                task=task,
                step=step,
                budget_guard=None,
            )

        assert isinstance(result, SalesAgentDispatchResult)
        assert result.success is False
        assert result.error_code == "adapter_failure"
        assert "LangGraph graph crashed" in (result.error_message or "")

    @pytest.mark.asyncio
    async def test_orchestrator_connection_error_returns_adapter_failure(self) -> None:
        """ConnectionError from orchestrator returns failure with error_code='adapter_failure'."""
        session = MagicMock()
        task = _make_task()
        step = _make_step()

        mock_sync_db = _make_sync_db_ctx()
        mock_registry = _make_mock_registry()

        with (
            patch(_SYNC_DB_PATH, return_value=mock_sync_db),
            patch(_REGISTRY_PATH, return_value=mock_registry),
            patch(
                _ORCHESTRATOR_PATH,
                new_callable=AsyncMock,
                side_effect=ConnectionError("DB connection lost"),
            ),
        ):
            result = await SalesAgentAdapter.dispatch(
                session=session,
                task=task,
                step=step,
                budget_guard=None,
            )

        assert result.success is False
        assert result.error_code == "adapter_failure"


class TestSalesAgentAdapterResultType:
    """SalesAgentDispatchResult dataclass invariants."""

    def test_result_is_frozen_dataclass(self) -> None:
        """SalesAgentDispatchResult is immutable (frozen=True)."""
        from dataclasses import FrozenInstanceError

        result = SalesAgentDispatchResult(success=True)
        with pytest.raises(FrozenInstanceError):
            result.success = False  # type: ignore[misc]

    def test_result_success_true_defaults(self) -> None:
        """SalesAgentDispatchResult(success=True) has None optional fields."""
        result = SalesAgentDispatchResult(success=True, external_message_id="msg-1")
        assert result.external_message_id == "msg-1"
        assert result.error_code is None
        assert result.error_message is None

    def test_result_failure_fields(self) -> None:
        """SalesAgentDispatchResult failure captures error_code + message."""
        result = SalesAgentDispatchResult(
            success=False,
            error_code="adapter_failure",
            error_message="some error",
        )
        assert result.success is False
        assert result.error_code == "adapter_failure"
        assert result.error_message == "some error"
