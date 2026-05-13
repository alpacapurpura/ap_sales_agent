from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from pydantic import BaseModel

from luana_core_platform.application.ai_action_service import (
    AIActionPolicy,
    AIActionService,
    AIModelPolicy,
)
from luana_core_llm.providers._response_validation import (
    ReasoningBudgetExhaustedError,
)


class PsychologyPayload(BaseModel):
    pains: list[str]
    desires: list[str]


def test_run_structured_action_parses_valid_json():
    service = AIActionService()
    llm_service = MagicMock()
    llm_service.generate_response.return_value = '{"pains":["p1"],"desires":["d1"]}'

    with patch(
        "luana_core_platform.application.ai_action_service.LLMFactory.get_service",
        return_value=llm_service,
    ):
        result = service.run_structured_action(
            action_name="offer_psychology_generation",
            tenant_id=uuid4(),
            system_prompt="PROMPT",
            user_prompt="USER",
            response_model=PsychologyPayload,
        )

    assert result.pains == ["p1"]
    assert result.desires == ["d1"]


def test_run_structured_action_retries_until_valid_payload():
    service = AIActionService()
    llm_service = MagicMock()
    llm_service.generate_response.side_effect = [
        '{"pains":["p1"]}',
        '{"pains":["p1"],"desires":["d1"]}',
    ]

    with patch(
        "luana_core_platform.application.ai_action_service.LLMFactory.get_service",
        return_value=llm_service,
    ):
        result = service.run_structured_action(
            action_name="offer_psychology_generation",
            tenant_id=uuid4(),
            system_prompt="PROMPT",
            user_prompt="USER",
            response_model=PsychologyPayload,
            policy=AIActionPolicy(retries=2, retry_delay_seconds=0),
        )

    assert result.desires == ["d1"]
    assert llm_service.generate_response.call_count == 2


def test_run_structured_action_fails_after_all_retries():
    service = AIActionService()
    llm_service = MagicMock()
    llm_service.generate_response.return_value = "not-json"

    with (
        patch(
            "luana_core_platform.application.ai_action_service.LLMFactory.get_service",
            return_value=llm_service,
        ),
        pytest.raises(ValueError, match="respuesta inválida"),
    ):
        service.run_structured_action(
            action_name="offer_psychology_generation",
            tenant_id=uuid4(),
            system_prompt="PROMPT",
            user_prompt="USER",
            response_model=PsychologyPayload,
            policy=AIActionPolicy(retries=2, retry_delay_seconds=0),
        )


def test_run_structured_action_validates_inputs():
    service = AIActionService()
    with pytest.raises(ValueError, match="action_name"):
        service.run_structured_action(
            action_name=" ",
            tenant_id=uuid4(),
            system_prompt="PROMPT",
            user_prompt="USER",
            response_model=PsychologyPayload,
        )


def test_reasoning_budget_exhaustion_propagates_without_retry():
    """The reasoning-budget trap is a *policy* bug (reserve too small or
    wrong role for the task), not a transient failure. Silent retry with
    a bumped cap would hide the diagnostic. The action service must let
    :class:`ReasoningBudgetExhaustedError` bubble up unchanged so the
    operator sees the typed error and picks the right lever."""
    service = AIActionService()
    llm_service = MagicMock()
    llm_service.generate_response.side_effect = ReasoningBudgetExhaustedError(
        "Model 'deepseek-v4-flash' consumed 800 reasoning tokens and emitted empty content with finish_reason=length.",
    )

    with (
        patch(
            "luana_core_platform.application.ai_action_service.LLMFactory.get_service",
            return_value=llm_service,
        ),
        pytest.raises(ReasoningBudgetExhaustedError, match="800 reasoning tokens"),
    ):
        service.run_structured_action(
            action_name="extraction",
            tenant_id=uuid4(),
            system_prompt="PROMPT",
            user_prompt="USER",
            response_model=PsychologyPayload,
            policy=AIActionPolicy(retries=3, retry_delay_seconds=0),
        )

    # Critical: only ONE call. No silent retry — fail fast.
    assert llm_service.generate_response.call_count == 1


def test_reasoning_effort_passed_through_when_set():
    """Callers opt into the provider's native reasoning-effort knob via
    the policy. The action service forwards the canonical key — the
    provider's spec routes it to the wire-param name (or drops it if
    the spec does not surface effort)."""
    service = AIActionService()
    llm_service = MagicMock()
    llm_service.generate_response.return_value = '{"pains":["p"],"desires":["d"]}'

    with patch(
        "luana_core_platform.application.ai_action_service.LLMFactory.get_service",
        return_value=llm_service,
    ):
        service.run_structured_action(
            action_name="x",
            tenant_id=uuid4(),
            system_prompt="PROMPT",
            user_prompt="USER",
            response_model=PsychologyPayload,
            policy=AIActionPolicy(model=AIModelPolicy(reasoning_effort="low")),
        )

    call_kwargs = llm_service.generate_response.call_args.kwargs
    assert call_kwargs.get("reasoning_effort") == "low"


def test_reasoning_effort_omitted_by_default():
    """Backwards-compat: callers that never opted in must keep working
    with no ``reasoning_effort`` key reaching the provider — same wire
    bytes as before the contract grew the optional field."""
    service = AIActionService()
    llm_service = MagicMock()
    llm_service.generate_response.return_value = '{"pains":["p"],"desires":["d"]}'

    with patch(
        "luana_core_platform.application.ai_action_service.LLMFactory.get_service",
        return_value=llm_service,
    ):
        service.run_structured_action(
            action_name="x",
            tenant_id=uuid4(),
            system_prompt="PROMPT",
            user_prompt="USER",
            response_model=PsychologyPayload,
        )

    call_kwargs = llm_service.generate_response.call_args.kwargs
    assert "reasoning_effort" not in call_kwargs
