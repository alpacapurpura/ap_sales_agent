"""Reusable AI action service for structured LLM responses with retry logic."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, TypeVar

import structlog
from openai import APIError, RateLimitError
from pydantic import BaseModel, ValidationError

from src.core.enums import ModelRole
from src.shared.infrastructure.llm.factory import LLMFactory

if TYPE_CHECKING:
    from uuid import UUID

TModel = TypeVar("TModel", bound=BaseModel)


@dataclass(frozen=True)
class AIModelPolicy:
    """Configuration for AI model selection and generation parameters."""

    model_type: str | ModelRole = ModelRole.REASONING
    temperature: float = 0.7
    max_output_tokens: int = 800


@dataclass(frozen=True)
class AIActionPolicy:
    """Retry and model policy for AI actions."""

    retries: int = 2
    retry_delay_seconds: float = 0.35
    model: AIModelPolicy = field(default_factory=AIModelPolicy)


class AIActionService:
    """Execute structured AI actions with retry, validation, and logging."""

    def __init__(self) -> None:
        """Initialize the AI action service with a logger."""
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
        """Execute an AI action and parse the response into a Pydantic model."""
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
                        (time.perf_counter() - attempt_started_at) * 1000,
                        2,
                    ),
                    total_duration_ms=round(
                        (time.perf_counter() - started_at) * 1000,
                        2,
                    ),
                    model_type=resolved_policy.model.model_type,
                )
            except RateLimitError as error:
                # OpenAI TPM rate limit. The server hint "try again in Xs" lives
                # inside the message; regex it out. Without this, concurrent
                # extraction waves silently lose whatever section hit the TPM
                # wall (observed: identity extraction returns empty model under
                # wave-1 pressure when prompts are large).
                last_error = error
                wait_s = _parse_retry_after_seconds(str(error)) or (
                    resolved_policy.retry_delay_seconds * max(attempt, 1) * 10
                )
                self.logger.warning(
                    "ai_action_rate_limited",
                    action_name=action_name,
                    tenant_id=str(tenant_id) if tenant_id else None,
                    attempt=attempt,
                    retries=resolved_policy.retries,
                    wait_seconds=wait_s,
                    model_type=resolved_policy.model.model_type,
                )
                if attempt < resolved_policy.retries:
                    time.sleep(wait_s)
            except APIError as error:
                # Retryable transient API failures (5xx, connection drops). Not
                # retried here: InvalidRequestError (4xx other than 429) —
                # subclass hierarchy keeps that path raising.
                last_error = error
                self.logger.warning(
                    "ai_action_api_error",
                    action_name=action_name,
                    tenant_id=str(tenant_id) if tenant_id else None,
                    attempt=attempt,
                    retries=resolved_policy.retries,
                    error=str(error)[:300],
                    model_type=resolved_policy.model.model_type,
                )
                if attempt < resolved_policy.retries:
                    time.sleep(resolved_policy.retry_delay_seconds * attempt)
            except (json.JSONDecodeError, ValidationError) as error:
                last_error = error
                raw_preview = llm_response[:300] if "llm_response" in locals() else "N/A"
                self.logger.warning(
                    "ai_action_retry",
                    action_name=action_name,
                    tenant_id=str(tenant_id) if tenant_id else None,
                    attempt=attempt,
                    retries=resolved_policy.retries,
                    error=str(error),
                    raw_response_preview=raw_preview,
                    duration_ms=round(
                        (time.perf_counter() - attempt_started_at) * 1000,
                        2,
                    ),
                    model_type=resolved_policy.model.model_type,
                )
                if attempt < resolved_policy.retries:
                    time.sleep(resolved_policy.retry_delay_seconds * attempt)

            else:
                return parsed
        self.logger.error(
            "ai_action_failure",
            action_name=action_name,
            tenant_id=str(tenant_id) if tenant_id else None,
            retries=resolved_policy.retries,
            total_duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
            error=str(last_error) if last_error else "unknown",
            model_type=resolved_policy.model.model_type,
        )
        msg = "La IA generó una respuesta inválida para la acción solicitada."
        raise ValueError(msg)

    @staticmethod
    def _extract_json(raw: str) -> str:
        """Extract the first balanced JSON object/array from a noisy LLM response.

        Robust against the failure modes observed in production:

        * Multiple ```json``` markdown blocks back-to-back. The previous
          implementation used ``rfind`` which spanned across blocks and
          produced garbage. We now scan for the first balanced container.
        * Trailing text after a complete JSON object — the classic
          ``Extra data: line N column M`` ``json.JSONDecodeError`` cause.
          The scanner stops at the matching close brace.
        * String literals containing ``{`` / ``}`` / backslash-escaped
          quotes — the depth counter ignores anything inside an unescaped
          string segment.

        Falls back to ``raw`` only when no balanced container is found,
        so ``json.loads`` reproduces a clear error for the retry loop.
        """
        # 1) Try markdown code blocks first; scan inside the first non-empty one.
        for match in re.finditer(r"```(?:json)?\s*([\s\S]*?)```", raw):
            block = match.group(1).strip()
            if not block:
                continue
            extracted = AIActionService._first_balanced(block)
            if extracted is not None:
                return extracted
            return block  # Let json.loads complain with the precise position.

        # 2) No markdown — scan the raw text for the first balanced container.
        extracted = AIActionService._first_balanced(raw)
        if extracted is not None:
            return extracted

        return raw

    @staticmethod
    def _first_balanced(s: str) -> str | None:
        """Return the substring spanning the first balanced ``{...}`` or ``[...]``.

        ``None`` when no balanced container exists. Quote-aware so braces
        inside string literals don't break the depth counter.
        """
        depth = 0
        start = -1
        in_string = False
        escape = False
        opener: str | None = None
        for index, char in enumerate(s):
            if escape:
                escape = False
                continue
            if char == "\\":
                escape = True
                continue
            if char == '"':
                in_string = not in_string
                continue
            if in_string:
                continue

            if depth == 0 and char in "{[":
                opener = char
                start = index
                depth = 1
                continue

            if opener is None:
                continue

            if char == opener:
                depth += 1
            elif (opener == "{" and char == "}") or (opener == "[" and char == "]"):
                depth -= 1
                if depth == 0:
                    return s[start : index + 1]
        return None

    def _validate_inputs(
        self,
        action_name: str,
        system_prompt: str,
        user_prompt: str,
        policy: AIActionPolicy,
    ) -> None:
        if not action_name.strip():
            msg = "action_name is required"
            raise ValueError(msg)
        if not system_prompt.strip():
            msg = "system_prompt is required"
            raise ValueError(msg)
        if not user_prompt.strip():
            msg = "user_prompt is required"
            raise ValueError(msg)
        if policy.retries < 1:
            msg = "retries must be >= 1"
            raise ValueError(msg)
        if not (0 <= policy.model.temperature <= 2):
            msg = "temperature must be between 0 and 2"
            raise ValueError(msg)
        if policy.model.max_output_tokens < 64:
            msg = "max_output_tokens must be >= 64"
            raise ValueError(msg)


_RETRY_AFTER_RE = re.compile(r"try again in ([\d.]+)s", re.IGNORECASE)


def _parse_retry_after_seconds(error_message: str) -> float | None:
    """Extract the server-suggested retry delay from an OpenAI 429 message.

    OpenAI embeds the wait hint as ``"Please try again in 11.756s"`` inside
    the rate-limit error string. Parsing it lets us respect the provider's
    budget instead of guessing — avoids the same call failing on retry.
    Returns ``None`` when the hint is missing or malformed.
    """
    match = _RETRY_AFTER_RE.search(error_message)
    if not match:
        return None
    try:
        # Pad by 250ms so we land just past the window, not right at its edge.
        return float(match.group(1)) + 0.25
    except (ValueError, IndexError):
        return None
