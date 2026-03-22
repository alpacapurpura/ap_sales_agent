import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Type, TypeVar
from uuid import UUID

import structlog
from pydantic import BaseModel, ValidationError

from src.shared.infrastructure.llm.factory import LLMFactory

TModel = TypeVar("TModel", bound=BaseModel)


@dataclass(frozen=True)
class AIModelPolicy:
    model_type: str = "smart"
    temperature: float = 0.7
    max_output_tokens: int = 800


@dataclass(frozen=True)
class AIActionPolicy:
    retries: int = 2
    retry_delay_seconds: float = 0.35
    model: AIModelPolicy = field(default_factory=AIModelPolicy)


class AIActionService:
    def __init__(self):
        self.logger = structlog.get_logger()

    def run_structured_action(
        self,
        *,
        action_name: str,
        tenant_id: Optional[UUID],
        system_prompt: str,
        user_prompt: str,
        response_model: Type[TModel],
        policy: Optional[AIActionPolicy] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TModel:
        resolved_policy = policy or AIActionPolicy()
        request_metadata = metadata or {}
        self._validate_inputs(action_name, system_prompt, user_prompt, resolved_policy)
        started_at = time.perf_counter()
        last_error: Optional[Exception] = None

        for attempt in range(1, resolved_policy.retries + 1):
            attempt_started_at = time.perf_counter()
            try:
                llm_response = LLMFactory.get_service().generate_response(
                    messages=[{"role": "user", "content": user_prompt}],
                    system_prompt=system_prompt,
                    model_type=resolved_policy.model.model_type,
                    temperature=resolved_policy.model.temperature,
                    max_output_tokens=resolved_policy.model.max_output_tokens,
                    metadata=request_metadata,
                )
                payload = json.loads(llm_response)
                parsed = response_model.model_validate(payload)
                self.logger.info(
                    "ai_action_success",
                    action_name=action_name,
                    tenant_id=str(tenant_id) if tenant_id else None,
                    attempt=attempt,
                    duration_ms=round((time.perf_counter() - attempt_started_at) * 1000, 2),
                    total_duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
                    model_type=resolved_policy.model.model_type,
                )
                return parsed
            except (json.JSONDecodeError, ValidationError, Exception) as error:
                last_error = error
                self.logger.warning(
                    "ai_action_retry",
                    action_name=action_name,
                    tenant_id=str(tenant_id) if tenant_id else None,
                    attempt=attempt,
                    retries=resolved_policy.retries,
                    error=str(error),
                    duration_ms=round((time.perf_counter() - attempt_started_at) * 1000, 2),
                    model_type=resolved_policy.model.model_type,
                )
                if attempt < resolved_policy.retries:
                    time.sleep(resolved_policy.retry_delay_seconds * attempt)

        self.logger.error(
            "ai_action_failure",
            action_name=action_name,
            tenant_id=str(tenant_id) if tenant_id else None,
            retries=resolved_policy.retries,
            total_duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
            error=str(last_error) if last_error else "unknown",
            model_type=resolved_policy.model.model_type,
        )
        raise ValueError("La IA generó una respuesta inválida para la acción solicitada.")

    def _validate_inputs(
        self,
        action_name: str,
        system_prompt: str,
        user_prompt: str,
        policy: AIActionPolicy,
    ) -> None:
        if not action_name.strip():
            raise ValueError("action_name is required")
        if not system_prompt.strip():
            raise ValueError("system_prompt is required")
        if not user_prompt.strip():
            raise ValueError("user_prompt is required")
        if policy.retries < 1:
            raise ValueError("retries must be >= 1")
        if not (0 <= policy.model.temperature <= 2):
            raise ValueError("temperature must be between 0 and 2")
        if policy.model.max_output_tokens < 64:
            raise ValueError("max_output_tokens must be >= 64")
