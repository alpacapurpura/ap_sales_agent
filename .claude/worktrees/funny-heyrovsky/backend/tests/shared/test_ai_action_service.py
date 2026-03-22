from uuid import uuid4
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from src.shared.application.ai_action_service import AIActionService, AIActionPolicy


class PsychologyPayload(BaseModel):
    pains: list[str]
    desires: list[str]


def test_run_structured_action_parses_valid_json():
    service = AIActionService()
    llm_service = MagicMock()
    llm_service.generate_response.return_value = '{"pains":["p1"],"desires":["d1"]}'

    with patch("src.shared.application.ai_action_service.LLMFactory.get_service", return_value=llm_service):
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

    with patch("src.shared.application.ai_action_service.LLMFactory.get_service", return_value=llm_service):
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

    with patch("src.shared.application.ai_action_service.LLMFactory.get_service", return_value=llm_service):
        with pytest.raises(ValueError, match="respuesta inválida"):
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
