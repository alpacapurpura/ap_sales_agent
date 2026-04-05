from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, TypeVar

import structlog
from pydantic import BaseModel, ValidationError

from src.core.enums import ModelRole
from src.shared.infrastructure.llm.factory import LLMFactory

if TYPE_CHECKING:
    from uuid import UUID

TModel = TypeVar("TModel", bound=BaseModel)


@dataclass(frozen=True)
class AIModelPolicy:
    model_type: str | ModelRole = ModelRole.REASONING
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
        tenant_id: UUID | None,
        system_prompt: str,
        user_prompt: str,
        response_model: type[TModel],
        policy: AIActionPolicy | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TModel:
        resolved_policy = policy or AIActionPolicy()
        request_metadata = metadata or {}
        self._validate_inputs(action_name, system_prompt, user_prompt, resolved_policy)
        started_at = time.perf_counter()
        last_error: Exception | None = None

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
                self.logger.debug(
                    "ai_action_raw_response",
                    action_name=action_name,
                    response_length=len(llm_response),
                    response_preview=llm_response[:500],
                )
                cleaned = self._extract_json(llm_response)
                payload = json.loads(cleaned)
                parsed = response_model.model_validate(payload)
                self.logger.info(
                    "ai_action_success",
                    action_name=action_name,
                    tenant_id=str(tenant_id) if tenant_id else None,
                    attempt=attempt,
                    duration_ms=round(
                        (time.perf_counter() - attempt_started_at) * 1000, 2
                    ),
                    total_duration_ms=round(
                        (time.perf_counter() - started_at) * 1000, 2
                    ),
                    model_type=resolved_policy.model.model_type,
                )
                return parsed
            except (json.JSONDecodeError, ValidationError, Exception) as error:
                last_error = error
                raw_preview = (
                    llm_response[:300] if "llm_response" in locals() else "N/A"
                )
                self.logger.warning(
                    "ai_action_retry",
                    action_name=action_name,
                    tenant_id=str(tenant_id) if tenant_id else None,
                    attempt=attempt,
                    retries=resolved_policy.retries,
                    error=str(error),
                    raw_response_preview=raw_preview,
                    duration_ms=round(
                        (time.perf_counter() - attempt_started_at) * 1000, 2
                    ),
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
        raise ValueError(
            "La IA generó una respuesta inválida para la acción solicitada."
        )

    @staticmethod
    def _extract_json(raw: str) -> str:
        """Extract JSON from LLM response that may contain markdown code blocks or preamble text."""
        # Try markdown code block first: ```json ... ``` or ``` ... ```
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
        if match:
            return match.group(1).strip()
        # Fallback: find outermost { ... } or [ ... ]
        for open_char, close_char in [("{", "}"), ("[", "]")]:
            start = raw.find(open_char)
            if start != -1:
                end = raw.rfind(close_char)
                if end > start:
                    return raw[start : end + 1]
        return raw

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
