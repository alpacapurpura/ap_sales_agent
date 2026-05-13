"""Unit tests for get_guarded_llm_service helper (PR-7 Sub-G).

Verifies the stable seam contract:
- Returns ``BudgetGuardingLLMService`` when tenant_id + budget_guard provided.
- Returns plain LLM service when tenant_id is None.
- Returns plain LLM service when budget_guard is None (DI not yet wired —
  default brand callsite path until S4).
- model_hint is propagated to the wrapper when guarded.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch
from uuid import UUID


class _FakeLLMService:
    """Minimal stub for LLMFactory.get_service() return value."""

    def generate_response(self, *args: Any, **kwargs: Any) -> str:
        return "stub"


TENANT_ID = UUID("12345678-1234-5678-1234-567812345678")


def test_returns_plain_when_tenant_id_none() -> None:
    """No tenant_id → returns plain LLM service (test path)."""
    from luana_core_billing.application.llm_guards import get_guarded_llm_service

    fake_inner = _FakeLLMService()

    with patch("luana_core_llm.factory.LLMFactory.get_service", return_value=fake_inner):
        result = get_guarded_llm_service(tenant_id=None, agent_kind="brand", budget_guard=MagicMock())

    assert result is fake_inner


def test_returns_plain_when_budget_guard_none() -> None:
    """budget_guard=None (default brand pre-S4) → returns plain LLM service."""
    from luana_core_billing.application.llm_guards import get_guarded_llm_service

    fake_inner = _FakeLLMService()

    with patch("luana_core_llm.factory.LLMFactory.get_service", return_value=fake_inner):
        result = get_guarded_llm_service(tenant_id=TENANT_ID, agent_kind="brand", budget_guard=None)

    assert result is fake_inner


def test_returns_guarded_when_tenant_id_and_guard_provided() -> None:
    """tenant_id + budget_guard provided → returns BudgetGuardingLLMService wrapping inner."""
    from luana_core_billing.application.llm_guards import (
        BudgetGuardingLLMService,
        get_guarded_llm_service,
    )

    fake_inner = _FakeLLMService()
    fake_guard = MagicMock()

    with patch("luana_core_llm.factory.LLMFactory.get_service", return_value=fake_inner):
        result = get_guarded_llm_service(tenant_id=TENANT_ID, agent_kind="brand", budget_guard=fake_guard)

    assert isinstance(result, BudgetGuardingLLMService)
    assert result._inner is fake_inner
    assert result._tenant_id == TENANT_ID
    assert result._agent_kind == "brand"
    assert result._guard is fake_guard


def test_model_hint_propagated() -> None:
    """model_hint forwarded to BudgetGuardingLLMService when guarded."""
    from luana_core_billing.application.llm_guards import (
        BudgetGuardingLLMService,
        get_guarded_llm_service,
    )

    fake_inner = _FakeLLMService()
    fake_guard = MagicMock()

    with patch("luana_core_llm.factory.LLMFactory.get_service", return_value=fake_inner):
        result = get_guarded_llm_service(
            tenant_id=TENANT_ID,
            agent_kind="brand",
            budget_guard=fake_guard,
            model_hint="claude-3-haiku-20240307",
        )

    assert isinstance(result, BudgetGuardingLLMService)
    assert result._model_hint == "claude-3-haiku-20240307"


def test_default_brand_pre_s4_path() -> None:
    """Default invocation (tenant_id only, no budget_guard) → plain service.

    This documents the brand callsite contract pre-S4: callsites pass
    tenant_id but not budget_guard; helper returns plain LLM until S4 wires
    a real DI provider. Architectural seam ready, runtime behavior preserved.
    """
    from luana_core_billing.application.llm_guards import get_guarded_llm_service

    fake_inner = _FakeLLMService()

    with patch("luana_core_llm.factory.LLMFactory.get_service", return_value=fake_inner):
        # Mimic brand callsite signature: tenant_id + agent_kind only
        result = get_guarded_llm_service(tenant_id=TENANT_ID, agent_kind="brand")

    assert result is fake_inner
